from __future__ import print_function
import os, sys, shutil, time
from glob import glob
import argparse

'''
    NUCLEON_ELASTIC_FF IMPORTS
'''
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
import xml_input
import metaq_input
import importlib
import c51_mdwf_hisq as c51
import sources
import utils
import scheduler

ens,stream = c51.ens_base()
ens_s = ens+'_'+stream

area51 = importlib.import_module(ens)
params = area51.params
params['machine'] = c51.machine
params['ENS_LONG'] = c51.ens_long[ens]
params['ENS_S']    = ens_s
params['STREAM']   = stream
params['METAQ_PROJECT'] = 'formfac_'+ens_s

'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs',nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-s','--src',type=str)
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('--mtype',default='cpu',help='specify metaq dir [%(default)s]')
parser.add_argument('-t','--t_sep',nargs='+',type=int,help='values of t_sep [default = all]')
parser.add_argument('-d','--debug',default=False,action='store_const',const=True,\
    help='run DEBUG? [%(default)s]')
parser.add_argument('-p','--priority',default=False,action='store_const',const=True,help='put task in priority? [%(default)s]')
parser.add_argument('-v','--verbose',default=True,action='store_const',const=False,\
    help='run with verbose output? [%(default)s]')
args = parser.parse_args()
print('%s: Arguments passed' %sys.argv[0].split('/')[-1])
print(args)
print('')

'''
    RUN PARAMETER SET UP
'''
if 'si' in params and 'sf' in params and 'ds' in params:
    tmp_params = dict()
    tmp_params['si'] = params['si']
    tmp_params['sf'] = params['sf']
    tmp_params['ds'] = params['ds']
    params = sources.src_start_stop(params,ens,stream)
    params['si'] = tmp_params['si']
    params['sf'] = tmp_params['sf']
    params['ds'] = tmp_params['ds']
else:
    params = sources.src_start_stop(params,ens,stream)
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,args.src,params)
if args.src:
    params['N_SEQ'] = len(range(params['si'],params['sf']+params['ds'],params['ds']))
else:
    params['N_SEQ'] = len(srcs[cfgs_run[0]])
src_ext = "%d-%d" %(params['si'],params['sf'])
params['SRC_LST'] = src_ext

if args.priority:
    q = 'priority'
    params['PRIORITY'] = '-p'
else:
    q = 'todo'
    params['PRIORITY'] = ''

nt = int(params['NT'])
nl = int(params['NL'])

print('running ',cfgs_run[0],'-->',cfgs_run[-1])

smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
''' for now - just doing the light quark '''
params['MQ'] = params['MV_L']

if args.t_sep == None:
    t_seps  = params['t_seps']
else:
    t_seps = args.t_sep
flav_spin = []
for f in params['flavs']:
    for s in params['spins']:
        flav_spin.append(f+'_'+s)
''' ONLY doing snk_mom 0 0 0 now '''
snk_mom = params['snk_mom'][0]
m0,m1,m2 = snk_mom.split()
params['M0']=m0
params['M1']=m1
params['M2']=m2
params['MOM'] = 'px%spy%spz%s' %(m0,m1,m2)

params = area51.mpirun_params(c51.machine)
params['NODES']       = params['cpu_nodes']
params['METAQ_NODES'] = params['cpu_nodes']
params['METAQ_GPUS']  = params['cpu_gpus']
params['WALL_TIME']   = params['gflow_time']
params['ENS_DIR']     = c51.ens_dir % params
params['SCRIPT_DIR']  = c51.script_dir
params['MAXCUS']      = params['cpu_maxcus']
params['SOURCE_ENV']  = c51.env
params['PROG']        = '$LALIBE_CPU'
params['APP']         = 'APP='+c51.bind_dir+params['cpu_bind']
params['NRS']         = params['cpu_nrs']
params['RS_NODE']     = params['cpu_rs_node']
params['A_RS']        = params['cpu_a_rs']
params['G_RS']        = params['cpu_g_rs']
params['C_RS']        = params['cpu_c_rs']
params['L_GPU_CPU']   = params['cpu_latency']
params['IO_OUT']      = '-i $ini -o $out > $stdout 2>&1'

n_curr = len(params['curr_4d'])
n_flav = len(params['flavs'])
n_spin = len(params['spins'])
n_par  = len(params['particles'])
coherent_ff_size_4d = n_curr * n_flav * n_spin * n_par *int(nt)*int(nl)**3 * 2*8
src_ext = "%d-%d" %(params['si'],params['sf'])



for c in cfgs_run:
    no = str(c)
    params['CFG'] = no
    ''' set up ensemble and make sure all dirs exist '''
    params = c51.ensemble(params)
    params['RUN_DIR']     = params['prod']

    ''' check if flowed cfg exists and make if not '''
    scidac_cfg = params['scidac_cfg']
    cfg_flow   = params['ENS_LONG']+stream+'.'+no+'_wflow'+params['FLOW_TIME']
    cfg_file   = params['flowed_cfg']

    if os.path.exists(cfg_file):
        params['CFG_FILE'] = cfg_file
        print("Checking coherent formfactor for cfg: ",c)

        have_all_seqprops=True
        for dt_int in t_seps:
            dt = str(dt_int)
            ''' Do all seqprops exist? '''
            all_seqprops=True
            for fs in flav_spin:
                flav,snk_spin,src_spin=fs.split('_')
                params['FLAV']=flav
                params['SOURCE_SPIN']=snk_spin
                params['SINK_SPIN']=src_spin
                spin = snk_spin+'_'+src_spin
                params['FLAV_SPIN']=fs
                if args.debug:
                    print('DEBUG: len(srcs[c])',len(srcs[c]))
                    print(srcs[c])
                for particle in params['particles']:
                    params['PARTICLE'] = particle
                    if '_np' in particle:
                        params['T_SEP'] = '-'+dt
                    else:
                        params['T_SEP'] = dt
                    seqprop_name = c51.names['seqprop'] %params
                    seqprop_file = params['seqprop']+'/'+seqprop_name+'.'+params['SP_EXTENSION']
                    seqprop_size = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
                    utils.check_file(seqprop_file,seqprop_size,params['file_time_delete'],params['corrupt'],debug=args.debug)
                    if not os.path.exists(seqprop_file):
                        print('    missing:',seqprop_file)
                        all_seqprops=False
                        have_all_seqprops=False
            if all_seqprops:
                ''' loop over srcs '''
                for s0 in srcs[c]:
                    params['SRC'] = s0
                    ''' Does the 3pt file exist? '''
                    ''' dt and -dt in same file, labled by dt '''
                    params['T_SEP'] = dt
                    coherent_formfac_name  = c51.names['coherent_ff'] % params
                    coherent_formfac_file  = params['formfac'] +'/'+coherent_formfac_name + '.h5'
                    coherent_formfac_file_4D = coherent_formfac_file.replace('formfac','formfac_4D')
                    coherent_ff_4D_tslice = coherent_formfac_file_4D.replace('formfac_4D','formfac_4D_tslice')
                    coherent_ff_4D_tslice_avg = coherent_ff_4D_tslice.replace('formfac_4D_tslice','formfac_4D_tslice_src_avg').replace(s0,'src_avg'+src_ext)
                    if not (os.path.exists(coherent_ff_4D_tslice) or os.path.exists(coherent_ff_4D_tslice_avg)):
                        params['THREE_PT_FILE'] = coherent_formfac_file
                        params['THREE_PT_FILE_4D'] = coherent_formfac_file_4D
                        if args.debug:
                            print('coherent_ff_size_4d',coherent_ff_size_4d)
                        utils.check_file(coherent_formfac_file_4D,coherent_ff_size_4d,params['file_time_delete'],params['corrupt'],debug=args.debug)
                        utils.check_file(coherent_formfac_file,params['ff_size'],params['file_time_delete'],params['corrupt'],debug=args.debug)
                        if os.path.exists(coherent_formfac_file) and not os.path.exists(coherent_formfac_file_4D):
                            now = time.time()
                            file_time = os.stat(coherent_formfac_file).st_mtime
                            if (now-file_time)/60 > params['file_time_delete']:
                                print('MOVING TO CORRUPT:',coherent_formfac_file)
                                shutil.move(coherent_formfac_file,params['corrupt']+'/'+coherent_formfac_file.split('/')[-1])
                        if os.path.exists(coherent_formfac_file_4D) and not os.path.exists(coherent_formfac_file):
                            now = time.time()
                            file_time = os.stat(coherent_formfac_file_4D).st_mtime
                            if (now-file_time)/60 > params['file_time_delete']:
                                print('MOVING TO CORRUPT:',coherent_formfac_file_4D)
                                shutil.move(coherent_formfac_file_4D,params['corrupt']+'/'+coherent_formfac_file_4D.split('/')[-1])
                        if not os.path.exists(coherent_formfac_file) and not os.path.exists(coherent_formfac_file_4D):
                            # loop over FLAV and SPIN as all in 1 file
                            metaq  = coherent_formfac_name+'.sh'
                            t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
                            try:
                                if params['metaq_split']:
                                    t_e2,t_w2 = scheduler.check_task(metaq,args.mtype+'_'+str(params['cpu_nodes']),params,folder=q,overwrite=args.o)
                                    t_w = t_w or t_w2
                                    t_e = t_e or t_e2
                            except:
                                pass
                            if not t_e or (args.o and not t_w):
                                prop_name = c51.names['prop'] % params
                                prop_file = params['prop'] + '/' + prop_name+'.'+params['SP_EXTENSION']
                                prop_exists = os.path.exists(prop_file)
                                prop_h5 = False
                                if ens in ['a12m130'] and not prop_exists:
                                    prop_file = params['prop'] + '/' + prop_name+'.h5'
                                    if os.path.exists(prop_file):
                                        prop_h5 = True
                                        prop_exists = True
                                if prop_exists:
                                    xmlini = coherent_formfac_file.replace('/formfac/','/xml/').replace('.h5','.ini.xml')
                                    fin = open(xmlini,'w')
                                    fin.write(xml_input.head)
                                    ''' read all props '''
                                    params['OBJ_ID']    = prop_name
                                    params['OBJ_TYPE']  = 'LatticePropagator'
                                    if not prop_h5:
                                        params['LIME_FILE'] = prop_file
                                        fin.write(xml_input.qio_read % params)
                                    else:
                                        prop_file = params['prop'] + '/' + prop_name+'.h5'
                                        params['H5_FILE'] = prop_file
                                        if params['si'] in [0, 8]:
                                            params['H5_PATH'] = '48_64'
                                            params['H5_OBJ_NAME'] = 'prop1'
                                        else:
                                            params['H5_PATH'] = ''
                                            params['H5_OBJ_NAME'] = 'prop'
                                        fin.write(xml_input.hdf5_read % params)

                                    ''' read all seq props and do contractions '''
                                    for particle in params['particles']:
                                        params['PARTICLE'] = particle
                                        if '_np' in particle:
                                            t_sep = '-'+dt
                                        else:
                                            t_sep = dt
                                        params['T_SEP'] = t_sep
                                        for fs in flav_spin:
                                            flav,snk_spin,src_spin=fs.split('_')
                                            params['FLAV']=flav
                                            params['SOURCE_SPIN']=snk_spin
                                            params['SINK_SPIN']=src_spin
                                            spin = snk_spin+'_'+src_spin
                                            params['FLAV_SPIN']=fs
                                            seqprop_name  = c51.names['seqprop'] %params
                                            seqprop_file  = params['seqprop']+'/'+seqprop_name+'.'+params['SP_EXTENSION']
                                            params['LIME_FILE'] = seqprop_file
                                            params['OBJ_ID']    = seqprop_name
                                            params['SEQPROP_'+fs] = seqprop_name
                                            fin.write(xml_input.qio_read % params)
                                        #for s0 in srcs[c]:
                                        prop_name = c51.names['prop'] % params
                                        params['PROP_NAME'] = prop_name

                                        ''' make 3pt contractions '''
                                        #params['CURR_P'] = ''
                                        #for ci,curr in enumerate(params['curr_p']):
                                        #    params['CURR_P'] += '        <elem>'+curr+'</elem>'
                                        #    if ci < len(params['curr_p'])-1:
                                        #        params['CURR_P'] += '\n'
                                        params['CURR_4D'] = ''
                                        for ci,curr in enumerate(params['curr_4d']):
                                            params['CURR_4D'] += '        <elem>'+curr+'</elem>'
                                            if ci < len(params['curr_4d']) -1:
                                                params['CURR_4D'] += '\n'
                                        params['CURR_0P'] = ''
                                        for ci,curr in enumerate(params['curr_0p']):
                                            params['CURR_0P'] += '        <elem>'+curr+'</elem>'
                                            if ci < len(params['curr_0p']) -1:
                                                params['CURR_0P'] += '\n'
                                        fin.write(xml_input.lalibe_formfac % params)
                                        ''' erase seqprops to reduce memory footprint '''
                                        for fs in flav_spin:
                                            fin.write(xml_input.qio_erase %{'OBJ_ID':params['SEQPROP_'+fs]})

                                    fin.write(xml_input.tail % params)
                                    fin.close()

                                    ''' Make METAQ task '''
                                    params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')
                                    params['INI']       = xmlini
                                    params['OUT']       = xmlini.replace('.ini.xml','.out.xml')
                                    params['STDOUT']    = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                                    params['CLEANUP']   = ''
                                    mtype = args.mtype
                                    try:
                                        if params['metaq_split']:
                                            mtype = mtype + '_'+str(params['cpu_nodes'])
                                    except:
                                        pass
                                    scheduler.make_task(metaq,mtype,params,folder=q)
                                else:
                                    print('MISSING prop',prop_file)
                                    os.system('python %s/METAQ_prop.py %s %s -v' %(params['SCRIPT_DIR'],c,params['PRIORITY']))
                            else:
                                if args.verbose:
                                    print('  task exists:',metaq)
                        elif not (os.path.exists(coherent_formfac_file) and os.path.exists(coherent_formfac_file_4D)):
                            if args.verbose:
                                print('check logic: either coherent_formfac_file OR coherent_formfac_file_4D exists')
                                print(coherent_formfac_file,os.path.exists(coherent_formfac_file))
                                print(coherent_formfac_file_4D,os.path.exists(coherent_formfac_file_4D))
                        else:
                            if args.verbose:
                                print('exists:',coherent_formfac_name)
                    else:
                        if args.verbose:
                            print('tslice or tslice_src_avg exists')
                            print(coherent_ff_4D_tslice.split('/')[-1])
                            print(coherent_ff_4D_tslice_avg.split('/')[-1])
                        
            else:
                print('    missing FLAV or SPIN seqprops, dt=',dt)
        if not have_all_seqprops:
            print('    missing FLAV or SPIN seqprops')
            os.system('python %s/METAQ_coherent_seqprop.py %s %s -v' %(params['SCRIPT_DIR'],c,params['PRIORITY']))
        #else:
        #    print('    missing props')
    else:
        if not os.path.exists(cfg_file):
            print('  flowed cfg missing',cfg_file)
        elif not all_srcs:
            print('missing srcs [8]')
            print(c,srcs[c])
