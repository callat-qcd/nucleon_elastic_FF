from __future__ import print_function
import os, sys, time, shutil
from glob import glob
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
import xml_input
import metaq_input
import importlib
import c51_mdwf_hisq as c51
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
parser.add_argument('cfgs',nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-s','--src',type=str)
parser.add_argument('-p',default=False,action='store_const',const=True,\
    help='put task.sh in priority queue? [%(default)s]')
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('-v','--verbose',default=True,action='store_const',const=False,\
    help='run with verbose output? [%(default)s]')
parser.add_argument('--delete',default=False,action='store_const',const=True,\
    help='move props to corrupt folder if they are too small? [%(default)s]')
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

base_dir = c51.base_dir % params
params['NODES']      = params['cpu_nodes']
params['GPUS']       = params['cpu_gpus']
params['WALL_TIME']  = params['spec_time']
params['ENS_DIR']    = c51.ens_dir % params
params['SCRIPT_DIR'] = c51.script_dir
cfg_dir = base_dir+'/cfgs_flow'
metaq_dir  = c51.metaq_dir

src_base      = c51.src_base
prop_base     = c51.prop_base
prop_xml_base = c51.prop_xml_base
spec_base     = c51.spec_base
sp_ext        = params['SP_EXTENSION']
prop_size     = nt* nl**3 * 3**2 * 4**2 * 2 * 4
'''            spin*par* vol       * comp * dbl '''
spec_size_4D  = 2 * 2 * nt * nl**3 * 2 * 8

for c in cfgs_run:
    no = str(c)
    params['CFG'] = c
    cfg_file = base_dir+'/cfgs_flow/'+ens_long+stream+'.'+no+'_wflow1.0.lime'
    if os.path.exists(cfg_file):
        params.update({'CFG_FILE':cfg_file})
        print('Making props for cfg: ',c)
        if not os.path.exists(base_dir+'/spec/'+no):
            os.makedirs(base_dir+'/spec/'+no)
        if not os.path.exists(base_dir+'/spec_4D/'+no):
            os.makedirs(base_dir+'/spec_4D/'+no)
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
            spec_file_4D = spec_file.replace('spec_','spec_4D_').replace('/spec/','/spec_4D/')
            if os.path.exists(spec_file_4D) and os.path.getsize(spec_file_4D) < spec_size_4D:
                now = time.time()
                file_time = os.stat(spec_file_4D).st_mtime
                if (now-file_time)/60 > time_delete:
                    print('DELETING BAD SPEC',os.path.getsize(spec_file_4D),spec_file_4D.split('/')[-1])
                    shutil.move(spec_file_4D,spec_file_4D.replace('spec_4D/'+no+'/','corrupt/'))
                    if os.path.exists(spec_file):
                        shutil.move(spec_file,spec_file.replace('spec/'+no+'/','corrupt/'))
            if not os.path.exists(spec_file) and not os.path.exists(spec_file_4D):
                prop_name = prop_base % params
                prop_file = base_dir+'/prop/'+no + '/' + prop_name+'.'+sp_ext
                if os.path.exists(prop_file) and os.path.getsize(prop_file) < prop_size:
                    now = time.time()
                    file_time = os.stat(prop_file).st_mtime
                    if (now-file_time)/60 > time_delete:
                        print('DELETING BAD PROP',os.path.getsize(prop_file),prop_file.split('/')[-1])
                        shutil.move(prop_file,prop_file.replace('prop/'+no+'/','corrupt/'))
                if os.path.exists(prop_file):
                    print('  making ',spec_name)
                    metaq = spec_name+'.sh'
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
                        params['PROP_NAME'] = prop_name
                        params['SPEC_FILE'] = spec_file
                        xmlini = base_dir+'/xml/'+no+'/'+spec_name+'.'+'ini.xml'
                        fin = open(xmlini,'w')
                        fin.write(xml_input.head)
                        ''' read prop '''
                        params['OBJ_TYPE']  = 'LatticePropagator'
                        params['OBJ_ID']    = prop_name
                        params['LIME_FILE'] = prop_file
                        fin.write(xml_input.qio_read % params)
                        ''' smear prop '''
                        params['SMEARED_PROP'] = prop_name+'_SS'
                        fin.write(xml_input.shell_smearing % params)
                        ''' PS '''
                        params['BARYON_MOM'] = '    <p2_max>'+str(params['BARYONS_PSQ_MAX'])+'</p2_max>'
                        params['H5_PATH'] = 'pt'
                        params['UP_QUARK'] = prop_name
                        params['DN_QUARK'] = prop_name
                        fin.write(xml_input.meson_spec % params)
                        fin.write(xml_input.baryon_spec % params)
                        ''' SS '''
                        params['H5_PATH'] = 'sh'
                        params['UP_QUARK'] = prop_name+'_SS'
                        params['DN_QUARK'] = prop_name+'_SS'
                        fin.write(xml_input.meson_spec % params)
                        fin.write(xml_input.baryon_spec % params)
                        ''' BARYONS 4D '''
                        params['BARYON_MOM'] = ''
                        params['SPEC_FILE'] = spec_file_4D
                        fin.write(xml_input.baryon_spec % params)
                        ''' end '''
                        fin.write(xml_input.tail % params)
                        fin.close()

                        ''' make METAQ task '''
                        params['METAQ_LOG'] = base_dir+'/metaq/log/'+metaq.replace('.sh','.log')
                        params['XML_IN']    = xmlini
                        params['XML_OUT']   = xmlini.replace('.ini.xml','.out.xml')
                        params['STDOUT']    = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                        m_in = open(metaq_file,'w')
                        m_in.write(metaq_input.spec % params)
                        m_in.close()
                        os.chmod(metaq_file,0o770)
                        print('    making task',metaq)
                else:
                    if args.verbose:
                        print('missing prop',prop_file)
                    print('python METAQ_prop.py %s -s %s' %(c,s0))
                    os.system('python %s/METAQ_prop.py %s -s %s' %(params['SCRIPT_DIR'],c,s0))
            else:
                if args.verbose:
                    print('spec exists',spec_file)
    else:
        print('  flowed cfg missing',cfg_file)
