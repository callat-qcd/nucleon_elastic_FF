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

ens,stream = c51.ens_base()
ens_s = ens+'_'+stream

area51 = importlib.import_module(ens)
params = area51.params
params['ENS_LONG'] = c51.ens_long[ens]
params['ENS_S']    = ens_s
params['STREAM']   = stream

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

base_dir = c51.base_dir % params

params['NODES']       = params['cpu_nodes']
params['METAQ_NODES'] = params['cpu_nodes']
params['METAQ_GPUS']  = params['cpu_gpus']
params['WALL_TIME']   = params['gflow_time']
params['ENS_DIR']     = c51.ens_dir % params
params['SCRIPT_DIR']  = c51.script_dir

cfg_dir = base_dir+'/cfgs_flow'
metaq_dir  = c51.metaq_dir

if not os.path.exists(base_dir+'/production/'+ens+'/cfgs_flow'):
    os.makedirs(base_dir+'/production/'+ens+'/cfgs_flow')

for c in cfgs_run:
    no = str(c)
    params['CFG'] = no
    ''' set up ensemble and make sure all dirs exist '''
    params = c51.ensemble(params)

    ''' check if flowed cfg exists and make if not '''
    scidac_cfg = params['scidac_cfg']
    cfg_flow   = params['ENS_LONG']+stream+'.'+no+'_wflow'+params['FLOW_TIME']
    cfg_file   = params['flowed_cfg']
    if not os.path.exists(cfg_file) or (os.path.exists(cfg_file) and args.o):
        if os.path.exists(scidac_cfg):
            print('making flowed cfg input xml')
            metaq = (c51.names['flow'] %params)+'.sh'
            t_exists,t_working = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
            if not t_exists or (args.o and not task_working):
                xmlini = base_dir+'/xml/'+no+'/cfg_flow_'+cfg_flow + '.ini.xml'
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
                params['CLEANUP'] = ''
                scheduler.make_task(metaq,args.mtype,params,folder=q)
        else:
            print('missing MILC.scidac cfg',scidac_cfg)
    else:
        print('flowed cfg exists',cfg_file)
