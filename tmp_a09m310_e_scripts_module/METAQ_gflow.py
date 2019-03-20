from __future__ import print_function
import os, sys
from glob import glob
import argparse

import xml_input
import metaq_input
import importlib
import management
import sources

try:
    ens_s = os.getcwd().split('/')[-3]
except:
    ens_s,junk = os.getcwd().split('/')[-3]
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

    milc_cfg = base_dir+'/production/'+ens+'/cfgs_scidac/'+params['ENS_LONG']+stream+'.'+no+'.scidac'
    cfg_flow = params['ENS_LONG']+stream+'.'+no+'_wflow'+params['FLOW_TIME']
    cfg_file = base_dir+'/production/'+ens+'/cfgs_flow/'+cfg_flow+'.lime'
    if not os.path.exists(cfg_file):
        if os.path.exists(milc_cfg):
            print('making flowed cfg input xml')
            metaq = 'cfg_flow_'+cfg_flow+'.sh'
            metaq_file = metaq_dir +'/'+q+'/gpu/'+'/'+metaq
            task_exist = False
            task_working = False
            if os.path.exists(metaq_file):
                task_exist = True
            for m_dir in ['todo/gpu','priority/gpu','hold']:
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
                params['OBJ_TYPE']  = 'LatticeColorMatrix'
                params['LIME_FILE'] = cfg_file
                fin.write(xml_input.qio_read % params)
                ''' close xml file '''
                fin.write(xml_input.tail % params)
                fin.close()
        else:
            print('missing MILC.scidac cfg',milc_cfg)
    else:
        print('flowed cfg exists',cfg_file)

for cs in cfg_srcs:
    no = cs.split()[0]
    print(no)
    #print(no,'x%sy%sz%st%s' %(x0,y0,z0,t0))
    for d in ['xml','stdout']:
        if not os.path.exists(base_dir+'/production/'+ens+'/'+d+'/'+no):
            os.makedirs(base_dir+'/production/'+ens+'/'+d+'/'+no)
    milc     = base_dir+'/production/'+ens+'/cfgs_scidac/'+milc_case+'.'+no+'.scidac'
    cfg      = milc_case+'.'+no+'_wflow1.0.lime'
    cfg_file = base_dir+'/production/'+ens+'/cfgs_flow/'+cfg
    if not os.path.exists(cfg_file) and os.path.exists(milc):
        print('  making ',cfg_file)
        if 'cfgs_scidac' in milc:
                cfg_type='SCIDAC'
        else:
                cfg_type='MILC'
        params = {'CFG_FLOW':cfg,'CFG_FLOW_FILE':cfg_file,'CFG_FILE':milc,'CFG_TYPE':cfg_type}

        xmlini = base_dir+'/production/'+ens+'/xml/'+no+'/gflow_'+ens+'_gf1.0_'+no+'.ini.xml'
        metaq  = 'gflow_'+ens+'_'+no+'.sh'
        metaq_file = metaq_dir+'/'+q+'/cpu/'+metaq
        task_exist = False
        task_working = False
        for m_dir in ['todo/cpu','priority/cpu','hold']:
            if os.path.exists(metaq_dir+'/'+m_dir+'/'+metaq):
                task_exist = True
        task_lst = glob(metaq_dir+'/working/*/*.sh')
        task_lst += glob(metaq_dir+'/working/*/*/*.sh')
        for task in task_lst:
            if metaq == task.split('/')[-1]:
                task_exist = True
                task_working = True
        if not task_exist or (args.o and not task_working):
            fin = open(xmlini,'w')
            fin.write(xml_input.gflow % params)
            fin.close()
            params = {'XML_IN':xmlini,'XML_OUT':xmlini.replace('.ini.xml','.out.xml'),
                      'STDOUT':xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/'),
                      'METAQ_LOG':metaq_dir+'/log/'+metaq.replace('.sh','.log')}
            m_in = open(metaq_file,'w')
            m_in.write(metaq_input.gflow % params)
            m_in.close()
            os.chmod(metaq_file,0o770)
    else:
        if os.path.exists(milc):
            print('  cfgs_flow exists')
        elif not os.path.exists(milc):
            print('  missing ',milc)
