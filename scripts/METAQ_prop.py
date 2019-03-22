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
parser.add_argument('cfgs',nargs='+',type=int,help='start [stop] cfg numbers')
parser.add_argument('-s','--src',type=str)
parser.add_argument('-p',default=False,action='store_const',const=True,\
    help='put task.sh in priority queue? [%(default)s]')
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('-v','--verbose',default=True,action='store_const',const=False,\
    help='run with verbose output? [%(default)s]')
parser.add_argument('--force',default=False,action='store_const',const=True,\
    help='force create props? [%(default)s]')
args = parser.parse_args()
print('%s: Arguments passed' %sys.argv[0].split('/')[-1])
print(args)
print('')

''' time in minutes to define "old" file '''
time_delete = params['prop_time_delete']

ri = args.cfgs[0]
if len(args.cfgs) == 1:
    rf = ri+1
    dr = 1
elif len(args.cfgs) == 2:
    rf = args.cfgs[1]+1
    dr = 1
else:
    rf = args.cfgs[1]+1
    dr = args.cfgs[2]
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

smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
params['MQ'] = params['MV_L']

if args.p:
    priority = '-p'
    q = 'priority'
else:
    priority = ''
    q = 'todo'
params['PRIORITY'] = priority

base_dir = management.base_dir % params
params['NODES']      = params['gpu_nodes']
params['GPUS']       = params['gpu_gpus']
params['WALL_TIME']  = params['prop_time']
params['ENS_DIR']    = management.ens_dir % params
params['SCRIPT_DIR'] = management.script_dir
cfg_dir = base_dir+'/cfgs_flow'
metaq_dir  = management.metaq_dir

src_base      = management.src_base
prop_base     = management.prop_base
prop_xml_base = management.prop_xml_base
spec_base     = management.spec_base
sp_ext        = params['SP_EXTENSION']
prop_size     = nt* nl**3 * 3**2 * 4**2 * 2 * 4

for c in cfgs_run:
    no = str(c)
    params['CFG'] = c
    cfg_file = base_dir+'/cfgs_flow/'+ens_long+stream+'.'+no+'_wflow1.0.lime'
    if os.path.exists(cfg_file):
        params.update({'CFG_FILE':cfg_file})
        print('Making props for cfg: ',c)
        if not os.path.exists(base_dir+'/prop/'+no):
            os.makedirs(base_dir+'/prop/'+no)
        if not os.path.exists(base_dir+'/xml/'+no):
            os.makedirs(base_dir+'/xml/'+no)
        if not os.path.exists(base_dir+'/stdout/'+no):
            os.makedirs(base_dir+'/stdout/'+no)
        if not os.path.exists(base_dir+'/corrupt'):
            os.makedirs(base_dir+'/corrupt')

        for s0 in srcs[c]:
            params['SRC'] = s0
            if args.verbose:
                print(c,s0)
            spec_name = spec_base % params
            spec_file = base_dir+'/spec/'+no+'/'+spec_name+'.h5'
            if not os.path.exists(spec_file) or args.force:
                prop_name = prop_base % params
                prop_file = base_dir+'/prop/'+no+'/'+prop_name+'.'+sp_ext
                if os.path.exists(prop_file) and os.path.getsize(prop_file) < prop_size:
                    now = time.time()
                    file_time = os.stat(prop_file).st_mtime
                    if (now-file_time)/60 > time_delete:
                        print('DELETING BAD PROP',os.path.getsize(prop_file),prop_file.split('/')[-1])
                        shutil.move(prop_file,prop_file.replace('prop/'+no+'/','corrupt/'))
                if not os.path.exists(prop_file):
                    src_name = src_base % params
                    src_file = base_dir+'/src/'+src_name+'.'+sp_ext
                    if os.path.exists(src_file) and os.path.getsize(src_file) < prop_size:
                        now = time.time()
                        file_time = os.stat(src_file).st_mtime
                        if (now-file_time)/60 > time_delete:
                            print('DELETING BAD SRC',os.path.getsize(src_file),src_file.split('/')[-1])
                            shutil.move(src_file,src_file.replace('src/','corrupt/'))
                    if os.path.exists(src_file):
                        print('  making ',prop_file)
                        metaq = prop_name+'.sh'
                        metaq_file = metaq_dir+'/'+q+'/gpu/'+metaq
                        task_exist = False
                        task_working = False
                        for m_dir in ['todo/gpu','priority/gpu','hold']:
                            if os.path.exists(metaq_dir+'/'+m_dir+'/'+metaq):
                                task_exist = True
                        task_lst = glob(metaq_dir+'/working/*/*.sh')
                        task_lst += glob(metaq_dir+'/working/*/*/*.sh')
                        for task in task_lst:
                            if metaq == task.split('/')[-1]:
                                task_exist = True
                                task_working = True
                        if not task_exist or (args.o and not task_working):
                            xmlini = base_dir+'/xml/'+no+'/'+(prop_xml_base %params)+'.ini.xml'
                            fin = open(xmlini,'w')
                            fin.write(xml_input.head)
                            ''' read src '''
                            params['OBJ_ID']    = src_name
                            params['OBJ_TYPE']  = 'LatticePropagator'
                            params['LIME_FILE'] = src_file
                            fin.write(xml_input.qio_read % params)

                            ''' solve prop '''
                            params['SRC_NAME'] = src_name
                            params['PROP_NAME'] = prop_name
                            params['QUARK_SPIN'] = 'FULL'
                            ''' this xml file contains mres info and is distinct from the chroma .out.xml '''
                            params['PROP_XML']  = '<xml_file>'
                            params['PROP_XML'] += prop_file.replace('/prop/','/xml/').replace(sp_ext,'out.xml')
                            params['PROP_XML'] += '</xml_file>'
                            fin.write(xml_input.quda_nef % params)

                            ''' write prop to disk '''
                            params['OBJ_ID']    = prop_name
                            params['OBJ_TYPE']  = 'LatticePropagatorF'
                            params['LIME_FILE'] = prop_file
                            fin.write(xml_input.qio_write % params)

                            ''' end xml file '''
                            fin.write(xml_input.tail % params)
                            fin.close()

                            ''' Make METAQ task '''
                            params['METAQ_LOG'] = base_dir+'/metaq/log/'+metaq.replace('.sh','.log')
                            params['XML_IN']    = xmlini
                            params['XML_OUT']   = xmlini.replace('.ini.xml','.out.xml')
                            params['STDOUT']    = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                            params['CR']        = c
                            params['CLEANUP']  = 'cd '+params['ENS_DIR']+'\n'
                            if os.path.exists(spec_file):
                                params['CLEANUP'] += '\n'
                            else:
                                params['CLEANUP'] += 'python %s/METAQ_spec.py %s -s %s %s\n' %(params['SCRIPT_DIR'],no,s0,priority)
                            if params['run_3pt']:
                                params['CLEANUP'] += 'python %s/METAQ_seqsource.py %s -s %s %s\n' %(params['SCRIPT_DIR'],no,s0,priority)

                            m_in = open(metaq_file,'w')
                            m_in.write(metaq_input.prop % params)
                            m_in.close()
                            os.chmod(metaq_file,0o770)
                            print('    making task',metaq)
                        else:
                            if args.verbose:
                                print('    task is in use or overwrite is false')
                    else:
                        if args.verbose:
                            print('    src missing',src_file)
                        print('python METAQ_src.py %s -s %s %s -v' %(c,s0,priority))
                        os.system('python %s/METAQ_src.py %s -s %s %s -v' %(params['SCRIPT_DIR'],c,s0,priority))
                else:
                    if args.verbose:
                        print('    prop exists',prop_file)
            elif os.path.exists(spec_file) and not args.force:
                print('    spec exists and force make prop = False',spec_file.split('/')[-1])
    else:
        print('  flowed cfg missing',cfg_file)
