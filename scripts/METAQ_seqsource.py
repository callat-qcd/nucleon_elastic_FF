from __future__ import print_function
import os, sys, time, shutil
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
params['METAQ_PROJECT'] = 'seqsource_'+ens_s

'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs',nargs='+',type=int,help='start [stop] run cfg number')
parser.add_argument('-s','--src',type=str)
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('--mtype',default='cpu',help='specify metaq dir [%(default)s]')
parser.add_argument('-t','--t_sep',nargs='+',type=int,help='values of t_sep [default = all]')
parser.add_argument('-d','--debug',default=False,action='store_const',const=True,\
    help='run DEBUG? [%(default)s]')
parser.add_argument('-p','--priority',default=False,action='store_const',const=True,\
    help='put task in priority? [%(default)s]')
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
        print("Making coherent sources for cfg: ",no)

        ''' Do the 3pt files exist? '''
        have_3pts = True
        for dt_int in t_seps:
            dt = str(dt_int)
            params['T_SEP'] = dt
            params['N_SEQ'] = str(len(srcs[c]))
            for s0 in srcs[c]:
                params['SRC'] = s0
                coherent_formfac_name  = c51.names['coherent_ff'] % params
                coherent_formfac_file  = params['formfac'] +'/'+coherent_formfac_name + '.h5'
                coherent_formfac_file_4D = coherent_formfac_file.replace('formfac_','formfac_4D_')
                if not os.path.exists(coherent_formfac_file) and not os.path.exists(coherent_formfac_file_4D):
                    have_3pts = False

        if not have_3pts:
            # loop over props to make a time-dense seqsource for each prop
            for s0 in srcs[c]:
                params['SRC'] = s0
                prop_name = c51.names['prop'] % params
                prop_file = params['prop'] + '/' + prop_name+'.'+params['SP_EXTENSION']
                if os.path.exists(prop_file):
                    for fs in flav_spin:
                        flav,snk_spin,src_spin=fs.split('_')
                        params['FLAV']=flav
                        params['SOURCE_SPIN']=snk_spin
                        params['SINK_SPIN']=src_spin
                        params['FLAV_SPIN']=fs
                        spin = snk_spin+'_'+src_spin
                        have_seqsrc = True
                        for particle in params['particles']:
                            params['PARTICLE']=particle
                            seqsrc_name = c51.names['seqsrc'] %params
                            seqsrc_file = params['seqsrc']+'/'+seqsrc_name+'.'+params['SP_EXTENSION']
                            seqsrc_size      = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
                            utils.check_file(seqsrc_file,seqsrc_size,params['file_time_delete'],params['corrupt'])
                            if not os.path.exists(seqsrc_file):
                                have_seqsrc = False
                        if not have_seqsrc:
                            params['PARTICLE'] = params['particles'][0]
                            seqsrc_name = c51.names['seqsrc'] %params
                            metaq  = seqsrc_name+'.sh'
                            t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
                            try:
                                if params['metaq_split']:
                                    t_e2,t_w2 = scheduler.check_task(metaq,args.mtype+'_'+str(params['cpu_nodes']),params,folder=q,overwrite=args.o)
                                    t_w = t_w or t_w2
                                    t_e = t_e or t_e2
                            except:
                                pass
                            if not t_e or (args.o and not t_w):
                                xmlini = params['xml']+'/'+seqsrc_name+'.'+'ini.xml'
                                fin = open(xmlini,'w')
                                fin.write(xml_input.head)
                                ''' read prop '''
                                params['OBJ_TYPE']    = 'LatticePropagator'
                                params['H5_PATH']     = ''
                                params['H5_OBJ_NAME'] = 'propagator'
                                t0=int(s0.split('t')[1])
                                params['OBJ_ID']      = prop_name
                                ''' ADD SWITCH BASED ON PROP EXTENSION, H5 vs LIME '''
                                params['H5_FILE']     = prop_file
                                params['LIME_FILE']   = prop_file
                                params['PROP_NAME']   = prop_name
                                fin.write(xml_input.qio_read % params)
                                ''' do smearing if need be '''
                                if params['SS_PS'] == 'SS':
                                    params['SMEARED_PROP'] = prop_name+'_SS'
                                    fin.write(xml_input.shell_smearing % params)
                                    params['UP_QUARK']=prop_name+'_SS'
                                    params['DOWN_QUARK']=prop_name+'_SS'
                                else:
                                    params['UP_QUARK']=prop_name
                                    params['DOWN_QUARK']=prop_name

                                for particle in params['particles']:
                                    params['PARTICLE'] = particle
                                    params['SEQSOURCE'] = c51.names['seqsrc'] %params
                                    seqsrc_file  = params['seqsrc']+'/'+params['SEQSOURCE']+'.'+params['SP_EXTENSION']
                                    if not os.path.exists(seqsrc_file):
                                        ''' make seqsource '''
                                        fin.write(xml_input.lalibe_seqsource % params)
                                        params['OBJ_ID']    = params['SEQSOURCE']
                                        params['OBJ_TYPE']  = 'LatticePropagatorF'
                                        params['LIME_FILE'] = seqsrc_file
                                        fin.write(xml_input.qio_write % params)
                                ''' END '''
                                fin.write(xml_input.tail % params)
                                fin.close()

                                ''' Make METAQ task '''
                                params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')
                                params['INI']       = xmlini
                                params['OUT']       = xmlini.replace('.ini.xml','.out.xml')
                                params['STDOUT']    = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                                params['CLEANUP']   = 'cd '+params['ENS_DIR']+'\n'
                                params['CLEANUP']  += 'python '+params['SCRIPT_DIR']+'/METAQ_coherent_seqprop.py '
                                params['CLEANUP']  += params['CFG']+' -t'+params['T_SEP']+' '+params['PRIORITY']+'\n'
                                params['CLEANUP']  += 'sleep 5'
                                mtype = args.mtype
                                try:
                                    if params['metaq_split']:
                                        mtype = mtype + '_'+str(params['cpu_nodes'])
                                except:
                                    pass
                                scheduler.make_task(metaq,mtype,params,folder=q)
                            else:
                                if not args.verbose:
                                    print('    task exists:',metaq)
                else:
                    print('    missing',prop_file)
                    print('python METAQ_prop.py %s -s %s --force %s' %(c,s0,params['PRIORITY']))
                    os.system('python %s/METAQ_prop.py %s -s %s --force %s' %(params['SCRIPT_DIR'],c,s0,params['PRIORITY']))
                    #sys.exit()
        else:
            print('    coherent_formfacs exist')
    else:
        if not os.path.exists(cfg_file):
            print('  flowed cfg missing',cfg_file)
        elif not all_srcs:
            print('missing srcs [8]')
            print(c,srcs[c])
