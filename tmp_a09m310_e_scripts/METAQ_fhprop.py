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
else:
    rf = args.run[1]+1

if args.p:
    q = 'priority'
else:
    q = 'todo'

ens = 'a09m310_e'
tol_test = 'a09m310_e_tol1e7'
tol_test = 'a09m310_e'
stream = ens.split('_')[-1]
base_dir = '/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/'
smr = 'gf1.0_w3.5_n45'
val = smr+'_M51.1_L56_a1.5'
mq = '0.00951'
params = {'CG_ITER':15000,'RSD_TARGET':1.e-7}

fh_tag = {'A3':'fhprop_A3','V4':'fhprop_V4'}

cfg_srcs = open(args.f).readlines()[ri:rf]
for ci,cs in enumerate(cfg_srcs):
    cr = ri+ci
    no,x0,y0,z0,t0 = cs.split()
    print(no,'x%sy%sz%st%s' %(x0,y0,z0,t0))
    if not os.path.exists(base_dir+'production/'+tol_test+'/spectrum/'+no):
        os.makedirs(base_dir+'production/'+tol_test+'/spectrum/'+no)
    cfg_file = base_dir+'production/'+ens+'/cfgs_flow/l3296f211b630m0074m037m440'+stream+'.'+no+'_wflow1.0.lime'
    s0 = 'x%sy%sz%st%s' %(x0,y0,z0,t0)
    prop_name = 'prop_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0
    prop_file = base_dir+'production/'+tol_test+'/props/'+no+'/'+prop_name+'.lime'
    fh_s_name = 'fhproton_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0
    for fh in ['A3','V4']:
        fh_p_name = 'fhprop_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0+'_'+fh
        fh_p_file = base_dir+'production/'+tol_test+'/props/'+no+'/'+fh_p_name+'.lime'
        params.update({
            'CFG_FILE':cfg_file,'PROP_NAME':prop_name,'PROP_FILE':prop_file,
            'FH_CURRENT':fh,'FH_PROP_FILE':fh_p_file,'FH_PROP_NAME':fh_p_name,'H5_OBJ_NAME':fh_tag[fh],
            })
        fh_s_name = 'fhproton_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0
        fh_s_file = base_dir+'production/'+tol_test+'/spectrum/'+no+'/'+fh_s_name+'.h5'

        if not os.path.exists(fh_p_file):
            if os.path.exists(prop_file):
                if os.path.exists(cfg_file):
                    print('  making ',fh_p_file)
                    xmlini = base_dir+'production/'+tol_test+'/xml/'+no+'/'+fh_p_name+'.ini.xml'
                    metaq  = fh_p_name+'.sh'
                    metaq_dir  = base_dir+'metaq'
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
                        fin.write(xml_input.fhprop % params)
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
                        m_in.write(metaq_input.fhprop % params)
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
            print('  fhprop exists:', fh_p_name)
