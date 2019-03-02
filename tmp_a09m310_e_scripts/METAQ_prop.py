from __future__ import print_function
import os, sys
from glob import glob
import argparse
import xml_input
import metaq_input

parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('run',nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-f',type=str,default='a09m310_e_src.lst',help='cfg/src file')
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
    dr = 1
elif len(args.run) == 2:
    rf = args.run[1]+1
    dr = 1
else:
    rf = args.run[1]+1
    dr = args.run[2]

if args.p:
    q = 'priority'
else:
    q = 'todo'

ens = 'a09m310_e'
tol_test = 'a09m310_e_src.lst_tol1e7'
stream = ens.split('_')[-1]
base_dir = '/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/'
smr = 'gf1.0_w3.5_n45'
val = smr+'_M51.1_L56_a1.5'
mq = '0.00951'
params = {'CG_ITER':15000,'RSD_TARGET':1.e-7}

cfg_srcs = open(args.f).readlines()[ri:rf:dr]
for ci,cs in enumerate(cfg_srcs):
    cr = ri+ci
    no,x0,y0,z0,t0 = cs.split()
    print(no,'x%sy%sz%st%s' %(x0,y0,z0,t0))
    if not os.path.exists(base_dir+'production/'+ens+'/props/'+no):
        os.makedirs(base_dir+'production/'+ens+'/props/'+no)
    cfg_file = base_dir+'production/'+ens+'/cfgs_flow/l3296f211b630m0074m037m440'+stream+'.'+no+'_wflow1.0.lime'
    s0 = 'x%sy%sz%st%s' %(x0,y0,z0,t0)
    src_name  = 'src_'+ens+'_'+smr+'_'+no+'_'+s0
    src_file  = base_dir+'production/'+ens+'/src/'+src_name+'.lime'
    prop_name = 'prop_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0
    prop_file = base_dir+'production/'+ens+'/props/'+no+'/'+prop_name+'.lime'
    prop_xml  = prop_file.replace('/props/','/xml/').replace('.lime','.out.xml')
    if not os.path.exists(prop_file):
        if os.path.exists(src_file):
            if os.path.exists(cfg_file):
                params.update({
                    'SRC_NAME':src_name,'SRC_FILE':src_file,'CFG_FILE':cfg_file,
                    'PROP_NAME':prop_name,'PROP_FILE':prop_file,'PROP_XML':prop_xml,
                    })
                print('  making ',prop_file)
                xmlini = base_dir+'production/'+ens+'/xml/'+no+'/prop_'+ens+'_'+val+'_'+no+'_'+s0+'.ini.xml'
                metaq  = 'prop_'+ens+'_'+val+'_'+no+'_'+s0+'.sh'
                metaq_dir  = '/ccs/proj/lgt100/c51/x_files/project_2/metaq'
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
                    fin = open(xmlini,'w')
                    fin.write(xml_input.prop % params)
                    fin.close()
                    params.update({'XML_IN':xmlini,'XML_OUT':xmlini.replace('.ini.xml','.out.xml'),
                              'STDOUT':xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/'),
                              'METAQ_LOG':metaq_dir+'/log/'+metaq.replace('.sh','.log'),
                              'BASE_DIR':base_dir,'CR':str(cr)})
                    if args.p:
                        params['PRIORITY'] = '-p'
                    else:
                        params['PRIORITY'] = ''
                    m_in = open(metaq_file,'w')
                    m_in.write(metaq_input.prop % params)
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
            print('  src does not exist - running METAQ_make_src.lrun.sh %d %s' %(cr,p))
            os.system('python METAQ_src.py %d %s' %(cr,p))
    else:
        print('  prop exists:', prop_file)
