from __future__ import print_function
import os, sys
from glob import glob
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
import xml_input
import metaq_input
import importlib
import management
import sources

try:
    ens_s = os.getcwd().split('/')[-2]
except:
    ens_s,junk = os.getcwd().split('/')[-2]
ens,stream = ens_s.split('_')

sys.path.append('area51_files')
area51 = importlib.import_module(ens)
params = area51.params
ens_long=params['ENS_LONG']
params['ENS_S'] = ens_s

parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('run',nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('-p',default=False,action='store_const',const=True,\
    help='put task.sh in priority queue? [%(default)s]')
args = parser.parse_args()
print('%s: Arguments passed' %sys.argv[0].split('/')[-1])
print(args)
print('')

''' time in minutes to define "old" file '''
time_delete = params['prop_time_delete']

ri = args.run[0]
if len(args.run) == 1:
    rf = ri+1
    dr = 1
elif len(args.run) == 2:
    rf = args.run[1]+1
    dr = 1
else:
    rf = args.run[1]+1
    dr = args.run[2]
cfgs_run = range(ri,rf,dr)

if args.p:
    q = 'priority'
else:
    q = 'todo'

nt = int(params['NT'])
nl = int(params['NL'])

smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
params['MQ'] = params['MV_L']

base_dir = management.base_dir % params

params['NODES']     = params['gflow_nodes']
params['GPUS']      = params['gflow_gpus']
params['WALL_TIME'] = params['gflow_time']
params['SCRIPT_DIR'] = management.script_dir % params

cfg_dir = base_dir+'/cfgs_flow'
metaq_dir  = management.metaq_dir

if not os.path.exists(base_dir+'/production/'+ens+'/cfgs_flow'):
    os.makedirs(base_dir+'/production/'+ens+'/cfgs_flow')

for c in cfgs_run:
    no = str(c)
    params['CFG'] = c
    if not os.path.exists(base_dir+'/xml/'+no):
        os.makedirs(base_dir+'/xml/'+no)
    if not os.path.exists(base_dir+'/stdout/'+no):
        os.makedirs(base_dir+'/stdout/'+no)
    if not os.path.exists(base_dir+'/corrupt'):
        os.makedirs(base_dir+'/corrupt')
    if not os.path.exists(base_dir+'/cfgs_flow'):
        os.makedirs(base_dir+'/cfgs_flow')

    milc_cfg = base_dir+'/cfgs_scidac/'+params['ENS_LONG']+stream+'.'+no+'.scidac'
    cfg_flow = params['ENS_LONG']+stream+'.'+no+'_wflow'+params['FLOW_TIME']
    cfg_file = base_dir+'/cfgs_flow/'+cfg_flow+'.lime'
    if not os.path.exists(cfg_file) or (os.path.exists(cfg_file) and args.o):
        if os.path.exists(milc_cfg):
            print('making flowed cfg input xml')
            metaq = 'cfg_flow_'+cfg_flow+'.sh'
            metaq_file = metaq_dir +'/'+q+'/cpu/'+'/'+metaq
            task_exist = False
            task_working = False
            if os.path.exists(metaq_file):
                task_exist = True
            for m_dir in ['todo/cpu','priority/cpu','hold']:
                if os.path.exists(metaq_dir+'/'+m_dir+'/'+metaq):
                    task_exist = True
            task_lst = glob(metaq_dir+'/working/*/*.sh')
            task_lst += glob(metaq_dir+'/working/*/*/*.sh')
            for task in task_lst:
                if metaq == task.split('/')[-1]:
                    task_exist = True
                    task_working = True
            if not task_exist or (args.o and task_exist and not task_working):
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
                params['CFG_FILE'] = milc_cfg
                fin.write(xml_input.tail % params)
                fin.close()

                ''' Make METAQ task '''
                params['METAQ_LOG'] = base_dir+'/metaq/log/'+metaq.replace('.sh','.log')
                params['XML_IN']    = xmlini
                params['XML_OUT']   = xmlini.replace('.ini.xml','.out.xml')
                params['STDOUT']    = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                params['CR']        = c
                m_in = open(metaq_file,'w')
                m_in.write(metaq_input.gflow % params)
                m_in.close()
                os.chmod(metaq_file,0o770)
        else:
            print('missing MILC.scidac cfg',milc_cfg)
    else:
        print('flowed cfg exists',cfg_file)
