from __future__ import print_function
import os, sys
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
params['METAQ_PROJECT'] = 'cfg_flow_'+ens_s

'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs',nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('--mtype',default='cpu',help='specify metaq dir [%(default)s]')
parser.add_argument('-p',default=False,action='store_const',const=True,\
    help='put task.sh in priority queue? [%(default)s]')
args = parser.parse_args()
print('%s: Arguments passed' %sys.argv[0].split('/')[-1])
print(args)
print('')

'''
    RUN PARAMETER SET UP
'''
''' time in minutes to define "old" file '''
time_delete = params['file_time_delete']

cfgs_run = utils.parse_cfg_argument(args.cfgs,params)

if args.p:
    q = 'priority'
    params['PRIORITY'] = '-p'
else:
    q = 'todo'
    params['PRIORITY'] = ''

nt = int(params['NT'])
nl = int(params['NL'])

smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
''' for now - just doing the light quark '''
params['MQ'] = params['MV_L']

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
    if not os.path.exists(cfg_file) or (os.path.exists(cfg_file) and args.o):
        if os.path.exists(scidac_cfg):
            print('making flowed cfg input xml',no)
            metaq = (c51.names['flow'] %params)+'.sh'
            t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
            try:
                if params['metaq_split']:
                    t_e2,t_w2 = scheduler.check_task(metaq,args.mtype+'_'+str(params['cpu_nodes']),params,folder=q,overwrite=args.o)
                    t_w = t_w or t_w2
                    t_e = t_e or t_e2
            except:
                pass
            if not t_e or (args.o and not t_w):
                xmlini = params['xml']+'/'+(c51.names['flow'] %params) +'.ini.xml'
                fin = open(xmlini,'w')
                fin.write(xml_input.head)
                ''' do  gradient flow '''
                params['CFG_PREFLOW'] = 'default_gauge_field'
                params['CFG_FLOW']    = cfg_flow
                fin.write(xml_input.wflow_cfg % params)
                ''' write cfg to disk '''
                params['OBJ_ID']    = cfg_flow
                params['OBJ_TYPE']  = 'Multi1dLatticeColorMatrixF'
                params['LIME_FILE'] = cfg_file
                fin.write(xml_input.qio_write % params)
                ''' close xml file '''
                params['CFG_FILE'] = scidac_cfg
                fin.write(xml_input.tail % params)
                fin.close()

                ''' Make METAQ task '''
                params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')
                params['INI']       = xmlini
                params['OUT']       = xmlini.replace('.ini.xml','.out.xml')
                params['STDOUT']    = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                params['CLEANUP']   = 'if [ "$cleanup" -eq 0 ]; then\n'
                params['CLEANUP']  += '    cd '+params['ENS_DIR']+'\n'
                params['CLEANUP']  += '    python '+params['SCRIPT_DIR']+'/METAQ_src.py '+params['CFG']+' '+params['PRIORITY']+'\n'
                params['CLEANUP']  += '    sleep 5\n'
                params['CLEANUP']  += 'else\n'
                params['CLEANUP']  += '    echo "mpirun failed"\n'
                params['CLEANUP']  += 'fi\n'
                mtype = args.mtype
                try:
                    if params['metaq_split']:
                        mtype = mtype + '_'+str(params['cpu_nodes'])
                except:
                    pass
                scheduler.make_task(metaq,mtype,params,folder=q)
        else:
            print('missing MILC.scidac cfg',scidac_cfg)
    else:
        print('flowed cfg exists',cfg_file)
