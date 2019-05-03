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
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,args.src,params)

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

n_curr = len(params['curr_4d'])
n_flav = len(params['flavs'])
n_spin = len(params['spins'])
n_par  = len(params['particles'])
coherent_ff_size_4d = n_curr * n_flav * n_spin * n_par *int(nt)*int(nl)**3 * 2*8

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
                params['N_SEQ'] = str(len(srcs[c]))
                for particle in params['particles']:
                    params['PARTICLE'] = particle
                    if '_np' in particle:
                        params['T_SEP'] = '-'+dt
                    else:
                        params['T_SEP'] = dt
                    seqprop_name = c51.names['seqprop'] %params
                    seqprop_file = params['seqprop']+'/'+seqprop_name+'.'+params['SP_EXTENSION']
                    seqprop_size = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
                    utils.check_file(seqprop_file,seqprop_size,params['file_time_delete'],params['corrupt'])
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
                    params['THREE_PT_FILE'] = coherent_formfac_file
                    params['THREE_PT_FILE_4D'] = coherent_formfac_file_4D
                    utils.check_file(coherent_formfac_file_4D,coherent_ff_size_4d,params['file_time_delete'],params['corrupt'])
                    if os.path.exists(coherent_formfac_file) and not os.path.exists(coherent_formfac_file_4D):
                        now = time.time()
                        file_time = os.stat(coherent_formfac_file).st_mtime
                        if (now-file_time)/60 > params['file_time_delete']:
                            print('DELETING:',coherent_formfac_file)
                            shutil.move(coherent_formfac_file,params['corrupt']+'/'+coherent_formfac_file.split('/')[-1])
                    if not os.path.exists(coherent_formfac_file) and not os.path.exists(coherent_formfac_file_4D):
                        # loop over FLAV and SPIN as all in 1 file
                        metaq  = coherent_formfac_name+'.sh'
                        t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
                        if not t_e or (args.o and not t_w):
                            prop_name = c51.names['prop'] % params
                            prop_file = params['prop'] + '/' + prop_name+'.'+params['SP_EXTENSION']
                            if os.path.exists(prop_file):
                                xmlini = coherent_formfac_file.replace('/formfac/','/xml/').replace('.h5','.ini.xml')
                                fin = open(xmlini,'w')
                                fin.write(xml_input.head)
                                ''' read all props '''
                                #for s0 in srcs[c]:
                                params['H5_FILE']=prop_file
                                params['H5_PATH']=''
                                params['H5_OBJ_NAME']='propagator'
                                params['LIME_FILE'] = prop_file
                                params['OBJ_ID']    = prop_name
                                params['OBJ_TYPE']  = 'LatticePropagator'
                                fin.write(xml_input.qio_read % params)

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
                                scheduler.make_task(metaq,args.mtype,params,folder=q)
                            else:
                                print('MISSING prop',prop_file)
                        else:
                            if args.verbose:
                                print('  task exists:',metaq)
                    else:
                        if args.verbose:
                            print('    exists:',coherent_formfac_file)
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
