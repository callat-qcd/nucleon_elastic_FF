from __future__ import print_function
import os, sys, time, shutil
from glob import glob
import argparse
import xml_input
import metaq_input

prop_size=3623878656

parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('run',nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-f',type=str,default='a09m310_e_src.lst',help='cfg/src file')
parser.add_argument('-p',default=False,action='store_const',const=True,\
    help='put task.sh in priority queue? [%(default)s]')
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('--delete',default=False,action='store_const',const=True,\
    help='move props to corrupt folder if they are too small? [%(default)s]')
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

ens = 'a09m310_e'
tol_test = 'a09m310_e_tol1e7'
stream = ens.split('_')[-1]
base_dir = '/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/'
smr = 'gf1.0_w3.5_n45'
val = smr+'_M51.1_L56_a1.5'
mq = '0.00951'
params = {'CG_ITER':15000,'RSD_TARGET':1.e-7}



cfg_srcs = open(args.f).readlines()[ri:rf]
for ci,cs in enumerate(cfg_srcs):
    cr = ri+ci
    no,x0,y0,z0,t0 = cs.split()
    print(no,'x%sy%sz%st%s' %(x0,y0,z0,t0))
    if not os.path.exists(base_dir+'production/'+ens+'/spectrum/'+no):
        os.makedirs(base_dir+'production/'+ens+'/spectrum/'+no)
    cfg_file = base_dir+'production/'+ens+'/cfgs_flow/l3296f211b630m0074m037m440'+stream+'.'+no+'_wflow1.0.lime'
    s0 = 'x%sy%sz%st%s' %(x0,y0,z0,t0)
    prop_name = 'prop_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0
    prop_file = base_dir+'production/'+ens+'/props/'+no+'/'+prop_name+'.lime'
    # check prop file size and delete if it is small and old
    if os.path.exists(prop_file) and os.path.getsize(prop_file) < prop_size and args.delete:
        now = time.time()
        prop_time = os.stat(prop_file).st_mtime
        if (now-prop_time)/60 > 20:
            print('DELETING BAD PROP',os.path.getsize(prop_file),prop_file.split('/')[-1])
            #os.system('sleep 2')
            if not os.path.exists(base_dir+'production/'+ens+'/corrupt'):
                os.makedirs(base_dir+'production/'+ens+'/corrupt')
            shutil.move(prop_file,base_dir+'production/'+ens+'/corrupt/')
            #os.remove(prop_file)
    prot_name = 'spec_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0
    spec_file = base_dir+'production/'+ens+'/spectrum/'+no+'/'+prot_name+'.h5'
    if not os.path.exists(spec_file):
        if os.path.exists(prop_file):
            if os.path.exists(cfg_file):
                params = {
                    'CFG_FILE':cfg_file,'PROP_NAME':prop_name,'PROP_FILE':prop_file,
                    'SPEC_FILE':spec_file,
                        }
                print('  making ',spec_file)
                spec_name = 'spec_'+ens+'_'+val+'_'+no+'_'+s0
                xmlini = base_dir+'production/'+ens+'/xml/'+no+'/'+spec_name+'.ini.xml'
                metaq  = spec_name+'.sh'
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
                    fin = open(xmlini,'w')
                    fin.write(xml_input.spec % params)
                    fin.close()
                    params = {'XML_IN':xmlini,'XML_OUT':xmlini.replace('.ini.xml','.out.xml'),
                              'STDOUT':xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/'),
                              'METAQ_LOG':metaq_dir+'/log/'+metaq.replace('.sh','.log'),
                              'BASE_DIR':base_dir,'CR':str(cr)}
                    m_in = open(metaq_file,'w')
                    m_in.write(metaq_input.spec % params)
                    m_in.close()
                    os.chmod(metaq_file,0o770)
                else:
                    print('  task exists:',metaq)
            else:
                print('  flowed cfg missing',cfg_file)            
        else:
            if args.p:
                p = '-p'
            else:
                p = ''
            print('  prop does not exist - running METAQ_prop.py %d %s' %(cr,p))
            os.system('python METAQ_prop.py %d %s' %(cr,p))
    else:
        print('  spec exists:', spec_file)
