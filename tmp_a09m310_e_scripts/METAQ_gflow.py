from __future__ import print_function
import os, sys
from glob import glob
import argparse

scriptPath=os.path.abspath(__file__).split('/METAQ_gflow.py')[0]
sys.path.insert(0,scriptPath)


import xml_input
import metaq_input

try:
    iens = os.getcwd().split('/')[-2].split('_')[0]
    stream = os.getcwd().split('/')[-2].split('_')[1][0]
except:
    sys.exit('Check ensemble name and stream')

ens=os.getcwd().split('/')[-2]

parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('run',nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-f',type=str,default=ens+'_src.lst',help='cfg/src file')
parser.add_argument('-p',default=False,action='store_const',const=True,\
    help='put task.sh in priority queue? [%(default)s]')
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
args = parser.parse_args()
print('%s: Arguments passed' %sys.argv[0].split('/')[-1])
print(args)
print('')

ri = args.run[0]
if len(args.run) == 1:
    rf = ri+1
else:
    rf = args.run[1]+1

if args.p:
    q = 'priority'
else:
    q = 'todo'

base_dir = '/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2'
metaq_dir='/ccs/proj/lgt100/c51/x_files/project_2/metaq'
cfgs_to_flow=os.listdir(base_dir+'/production/'+ens+'/cfgs_scidac')
if len(cfgs_to_flow)!=0:
    milc_case = cfgs_to_flow[0].split('.')[0][0:-1]+stream
    nl,nt=milc_case[1:3],milc_case[3:5]
    try:
        if input('Milc_case:'+milc_case+'\nare nl='+nl+', nt='+nt+' correct y/n? ')=='n':
            nl,nt=input('Enter nl,nt: ').split(',')
    except:
        if raw_input('Milc_case:'+milc_case+'\nare nl='+nl+', nt='+nt+' correct y/n? ')=='n':
            nl,nt=input('Enter nl,nt: ').split(',')
    vol= nl+' '+nl+ ' ' +nl+' ' +nt     
else:
    sys.exit('There are no cfgs for flowing')


print(milc_case,ens,args.f,vol)

cfg_srcs = open(args.f).readlines()[ri:rf]
if not os.path.exists(base_dir+'/production/'+ens+'/cfgs_flow'):
    os.makedirs(base_dir+'/production/'+ens+'/cfgs_flow')
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
        if not task_exist or (args.o and task_exist and not task_working):
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
