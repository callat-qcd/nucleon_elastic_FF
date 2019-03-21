from __future__ import print_function
import os, sys, time
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

area51 = importlib.import_module(ens)
params = area51.params
ens_long=params['ENS_LONG']
params['ENS_S'] = ens_s

parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('run',nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-s','--src',type=str)
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('-p',default=False,action='store_const',const=True,\
    help='put task.sh in priority queue? [%(default)s]')
parser.add_argument('-v','--verbose',default=True,action='store_const',const=False,\
    help='run with verbose output? [%(default)s]')
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

''' BUILD SRC DICTIONARY '''
nt = int(params['NT'])
nl = int(params['NL'])

if args.src:
    if len(args.cfgs) > 1:
        print('if a src is passed, only 1 cfg can be specified which is presumably the right one')
        sys.exit(-1)
    else:
        cfgs = args.cfgs
        srcs = {int(args.cfgs[0]):[args.src]}
else:
    srcs = {}
    for c in cfgs_run:
        no = str(c)
        srcs_cfg = sources.make(no, nl=nl, nt=nt, t_shifts=params['t_shifts'],
            generator=params['generator'], seed=params['seed'][stream])
        srcs[c] = []
        for origin in srcs_cfg:
            try:
                src_gen = srcs_cfg[origin].iteritems()
            except AttributeError: # Python 3 automatically creates a generator
                src_gen = srcs_cfg[origin].items()
            for src_type, src in src_gen:
                srcs[c].append(sources.xXyYzZtT(src))
print('running ',cfgs_run[0],'-->',cfgs_run[-1])

if args.p:
    q = 'priority'
else:
    q = 'todo'

smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
params['MQ'] = params['MV_L']

base_dir  = management.base_dir % params
src_base  = management.src_base
src_size  = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4

prop_base = management.prop_base
sp_ext    = params['SP_EXTENSION']

params['NODES']     = params['src_nodes']
params['GPUS']      = params['src_gpus']
params['WALL_TIME'] = params['src_time']
params['SCRIPT_DIR'] = management.script_dir % params

cfg_dir = base_dir+'/cfgs_flow'
metaq_dir  = management.metaq_dir

if not os.path.exists(base_dir+'/src'):
    os.makedirs(base_dir+'/src')
if not os.path.exists(base_dir+'/corrupt'):
    os.makedirs(base_dir+'/corrupt')

for c in cfgs_run:
    no = str(c)
    params['CFG'] = no
    cfg_file = cfg_dir+'/'+ens_long+stream+'.'+no+'_wflow1.0.lime'
    if os.path.exists(cfg_file):
        params['CFG_FILE'] = cfg_file
        for d in ['xml','stdout']:
            if not os.path.exists(base_dir+'/'+d+'/'+no):
                os.makedirs(base_dir+'/'+d+'/'+no)
        for s0 in srcs[c]:
            params['SRC'] = s0
            prop_name = prop_base % params
            prop_file = base_dir+'/prop/'+no + '/' + prop_name+'.'+sp_ext
            if not os.path.exists(prop_file):
                src_name = src_base % params
                src_file = base_dir+'/src/'+src_name+'.'+sp_ext
                if os.path.exists(src_file) and os.path.getsize(src_file) < src_size:
                    now = time.time()
                    file_time = os.stat(src_file).st_mtime
                    if (now-file_time)/60 > time_delete:
                        print('DELETING BAD SRC',os.path.getsize(src_file),src_file.split('/')[-1])
                        shutil.move(src_file,seqsrc_file.replace('src/','corrupt/'))
                if not os.path.exists(src_file):
                    metaq = src_name + '.sh'
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
                    if not task_exist or (args.o and not task_working):
                        xmlini = base_dir+'/xml/'+no+'/'+src_name+'.'+'ini.xml'
                        fin = open(xmlini,'w')
                        fin.write(xml_input.head)
                        ''' create source '''
                        x0,y0,z0,t0 = sources.xyzt(s0)
                        params['X0'] = x0
                        params['Y0'] = y0
                        params['Z0'] = z0
                        params['T0'] = t0
                        params['SRC_NAME'] = src_name
                        fin.write(xml_input.shell_source % params)
                        ''' write source '''
                        params['OBJ_ID']    = src_name
                        params['OBJ_TYPE']  = 'LatticePropagatorF'
                        params['LIME_FILE'] = src_file
                        fin.write(xml_input.qio_write % params)
                        ''' close xml file '''
                        fin.write(xml_input.tail % params)
                        fin.close()
                else:
                    if args.verbose:
                        print('src exists',src_file)

            else:
                if args.verbose:
                    print('prop exists',prop_file)
"""
''' OLD BELOW '''

    s0 = 'x%sy%sz%st%s' %(x0,y0,z0,t0)
    src_name  = 'src_'+ens+'_'+smr+'_'+no+'_'+s0
    src_file  = base_dir+'production/'+ens+'/src/'+src_name+'.lime'
    prop_name = 'prop_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0
    prop_file = base_dir+'production/'+ens+'props/'+no+'/'+prop_name+'.lime'
    if not os.path.exists(prop_file):
        if not os.path.exists(src_file):
            if os.path.exists(cfg_file):
                print('  making ',src_file)
                params = {
                    'X0':x0,'Y0':y0,'Z0':z0,'T0':t0,
                    'SRC_NAME':src_name,'SRC_FILE':src_file,'CFG_FILE':cfg_file
                    }
                xmlini = base_dir+'production/'+ens+'/xml/'+no+'/'+src_name+'.ini.xml'

                metaq  = src_name+'.sh'
                metaq_dir  = '/ccs/proj/lgt100/c51/x_files/project_2/metaq'
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
                    print(xmlini)
                    fin = open(xmlini,'w')
                    fin.write(xml_input.src % params)
                    fin.close()
                    params = {'XML_IN':xmlini,'XML_OUT':xmlini.replace('.ini.xml','.out.xml'),
                              'STDOUT':xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/'),
                              'METAQ_LOG':metaq_dir+'/log/'+metaq.replace('.sh','.log'),'CR':str(cr)}
                    if args.p:
                        params['PRIORITY'] = '-p'
                    else:
                        params['PRIORITY'] = ''
                    m_in = open(metaq_file,'w')
                    m_in.write(metaq_input.src % params)
                    m_in.close()
                    os.chmod(metaq_file,0o770)
            else:
                print('  flowed cfg missing',cfg_file)
        else:
            print('  exists:',src_file)
    else:
        print('  prop exists')
"""
