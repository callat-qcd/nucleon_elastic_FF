from __future__ import print_function
import os, sys
from glob import glob
import argparse
import xml_input
import metaq_input

try:
    ens = os.getcwd().split('/')[-3]
except:
    ens,junk = os.getcwd().split('/')[-3]
stream = ens.split('_')[-1]
ens_long='l3296f211b630m0074m037m440'

parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs',nargs='+',type=int,help='start [stop] cfg numbers')
parser.add_argument('-s','--src',type=str)
parser.add_argument('-f',type=str,default='a09m310_e_src.lst',help='cfg/src file')
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
time_delete = 10

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
print(args.cfgs)

if args.src:
    if len(args.cfgs) > 1:
        print('if a src is passed, only 1 cfg can be specified which is presumably the right one')
        sys.exit(-1)
    else:
        cfgs = args.cfgs[0]
        srcs = {int(args.cfgs[0]):[args.src]}
else:
    cfg_srcs = open(args.f).readlines()
    cfgs = []
    srcs = {}
    for c in cfg_srcs:
        no = c.split()[0]
        cfg = int(no)
        if no not in cfgs and cfg in cfgs_run:
            cfgs.append(c.split()[0])
        if no not in srcs:
            srcs[no] = []
    for cs in cfg_srcs:
        no,x0,y0,z0,t0 = cs.split()
        src = 'x'+x0+'y'+y0+'z'+z0+'t'+t0
        if src not in srcs[no]:
            srcs[no].append(src)

print('running ',cfgs[0],'-->',cfgs[-1])

nt = '96'
nx = '32'
M5 = '1.1'
L5 = '6'
b5 = '1.25'
c5 = '0.25'
alpha5 = '1.5'
wf_s='3.5'
wf_n='45'
smr = 'gf1.0_w'+wf_s+'_n'+wf_n
val = smr+'_M5'+M5+'_L5'+L5+'_a'+alpha5
mq = '0.00951'
max_iter = '12000'
rsd_target = '1.e-7'
delta = '0.1'
rsd_tol = '80'

params = {
    'ENS':ens,
    'NL':nx,'NT':nt,
    'M5':M5,'L5':L5,'B5':b5,'C5':c5,'MQ':mq,
    'MAX_ITER':max_iter,'RSD_TARGET':rsd_target,'Q_DELTA':delta,'RSD_TOL':rsd_tol,
    'WF_S':wf_s,'WF_N':wf_n
    }
if args.p:
    priority = '-p'
else:
    priority = ''
params['PRIORITY'] = priority

base_dir = '/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/'+ens
params['SCRIPT_DIR'] = '/ccs/proj/lgt100/c51/x_files/project_2/production/'+ens+'/scripts'
cfg_dir = '/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/'+ens+'/cfgs_flow'
metaq_run_dir  = '/ccs/proj/lgt100/c51/x_files/project_2/metaq'
metaq_dir = metaq_run_dir

src_base      = 'src_'+ens+'_'+smr+'_%(CFG)s_%(SRC)s'
prop_base     = 'prop_'+ens+'_'+val+'_mq'+mq+'_%(CFG)s_%(SRC)s'
''' the xml generation may incluce multiple quark masses, so no mq info '''
prop_xml_base = 'prop_'+ens+'_'+val+'_%(CFG)s_%(SRC)s'
spec_base     = 'spec_'+ens+'_'+val+'_mq'+mq+'_%(CFG)s_%(SRC)s'
sp_ext = 'lime'
prop_size = int(nt)* int(nx)**3 * 3**2 * 4**2 * 2 * 4

if args.p:
    q = 'priority'
else:
    q = 'todo'

for c in cfgs:
    no = c
    params['CFG'] = c
    cfg_file = base_dir+'production/'+ens+'/cfgs_flow/l3296f211b630m0074m037m440'+stream+'.'+no+'_wflow1.0.lime'
    if os.path.exists(cfg_file):
        params.update({'CFG_FILE':cfg_file})
        print('Making props for cfg: ',c)
        if not os.path.exists(base_dir+'/props/'+c):
            os.makedirs(base_dir+'/props/'+c)
        if not os.path.exists(base_dir+'/xml/'+c):
            os.makedirs(base_dir+'/xml/'+c)
        if not os.path.exists(base_dir+'/stdout/'+c):
            os.makedirs(base_dir+'/stdout/'+c)
        if not os.path.exists(base_dir+'/corrupt'):
            os.makedirs(base_dir+'/corrupt')

        for s0 in srcs[c]:
            params['SRC'] = s0
            if args.verbose:
                print(c,s0)
            spec_name = spec_base % params
            spec_file = base_dir+'/spectrum/'+c+'/'+spec_name+'.h5'
            if not os.path.exists(spec_file) or args.force:
                prop_name = prop_base % params
                prop_file = base_dir+'/props/'+c+'/'+prop_name+'.'+sp_ext
                if os.path.exists(prop_file) and os.path.getsize(prop_file) < prop_size:
                    now = time.time()
                    file_time = os.stat(prop_file).st_mtime
                    if (now-file_time)/60 > time_delete:
                        print('DELETING BAD PROP',os.path.getsize(prop_file),prop_file.split('/')[-1])
                        shutil.move(prop_file,prop_file.replace('props/'+c+'/','corrupt/'))
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
                        if not task_exist or (args.o and task_exist and not task_working):
                            xmlini = base_dir+'/xml/'+c+'/'+(prop_xml_base %params)+'.out.xml'
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
                            params['PROP_XML'] += prop_file.replace('/props/','/xml/').replace(sp_ext,'.out.xml')
                            params['PROP_XML'] += '</xml_file>'
                            fin.write(xml_input.quda_nef % params)

                            ''' write prop to disk '''
                            params['OBJ_ID']    = src_name
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
                        #os.system('python METAQ_src.py %s -s %s %s -v' %(c,s0,priority))
                else:
                    if args.verbose:
                        print('    prop exists',prop_file)
            elif os.path.exists(spec_file) and not args.force:
                print('    spec exists and force make prop = False',spec_file.split('/')[-1])
    else:
        print('  flowed cfg missing',cfg_file)
