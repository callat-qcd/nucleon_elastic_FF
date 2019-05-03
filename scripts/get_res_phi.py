#!/sw/summit/python/3.7/anaconda3/5.3.0/bin/python
import os, sys, argparse, shutil
import numpy as np
import tables as h5
from glob import glob
np.set_printoptions(linewidth=180)

try:
    ens,stream = os.getcwd().split('/')[-1].split('_')
except:
    ens,stream,junk = os.getcwd().split('/')[-1].split('_')
base = ens+'_'+stream
base_dir='/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/'+base

parser = argparse.ArgumentParser(description='get mres data and phi_qq correlators from prop_mq.xml.out')
parser.add_argument('--cfg',nargs='+',type=int,help='cfgs: [ni [nf dn]] None=All')
parser.add_argument('-o',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('--move',default=False,action='store_const',const=True,help='move bad files? [%(default)s]')
parser.add_argument('-v',default=True,action='store_const',const=False,help='verbose? [%(default)s]')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.float32
data_dir = 'data'
corrupt_dir = 'corrupt'
for d in [data_dir,corrupt_dir]:
    if not os.path.exists(d): os.makedirs(d)
if args.cfg == None:
    print("finding xml files at:", base_dir+'/xml/*')
    print('  this has to be <production>/<ens>_<stream> or will break')
    dirs = glob('xml/*')
    cfgs = []
    for d in dirs:
        cfgs.append(int(d.split('/')[-1]))
    cfgs.sort()
    ni = cfgs[0]; nf = cfgs[-1]; dn = cfgs[1]-cfgs[0];
else:
    if len(args.cfg) == 1:
        ni = args.cfg[0]; nf = args.cfg[0]+1; dn = 1;
    elif len(args.cfg) == 3:
        ni = args.cfg[0]; nf = args.cfg[1]+args.cfg[2]; dn = args.cfg[2];
    cfgs = range(ni,nf,dn)

val_info = {
    'a15m135XL':'gf1.0_w3.0_n30_M51.3_L524_a3.5',
    'a12m130':'gf1.0_w3.0_n30_M51.2_L520_a3.0',
    'a09m130':'gf1.0_w3.5_n45_M51.1_L512_a2.0',
    'a06m310':'gf1.0_w3.5_n45_M51.0_L56_a1.5',
    'a09m220':'gf1.0_w3.5_n45_M51.1_L58_a1.5',
    'a09m310':'gf1.0_w3.5_n45_M51.1_L56_a1.5',
    }


val = val_info[ens]
val_p = val.replace('.','p')
mq_e = {'a15m135XL':'0.00237','a12m130':'0.00195','a09m130':'0.00137','a06m310':'0.00614','a09m220':'0.00449','a09m310':'0.00951'}

print('MINING MRES and PHI_QQ')
print('ens_stream = ',base)
print('ci:cf:dc = %d:%d:%d' %(ni,nf,dn))

for cfg in cfgs:
    no = str(cfg)
    files = glob(base_dir+'/xml/'+no+'/prop_'+base+'_'+val+'_mq'+mq_e[ens]+'_'+no+'_x*.out.xml')
    if len(files) > 0:
        for ftmp in files:
            src = ftmp.split('_')[-1].split('.')[0]
            t_src = int(src.split('t')[1])
            mq = mq_e[ens].replace('.','p')
            f_good = False
            print(ftmp)
            if os.path.getsize(ftmp) > 0:
                with open(ftmp) as f:
                    data = f.readlines()
                    #print(data[-1])
                    if data[-1] == '</propagator>':
                        f_good = True
            if not f_good:
                print('  corrupt:',ftmp)
                shutil.move(ftmp,corrupt_dir+'/'+ftmp.split('/')[-1])
            else:
                f5 = h5.open_file(data_dir+'/'+ens+'_'+no+'.h5','a')
                mpdir   = '/'+val_p+'/dwf_jmu/mq'+mq+'/midpoint_pseudo'
                ppdir   = '/'+val_p+'/dwf_jmu/mq'+mq+'/pseudo_pseudo'
                phi_dir = '/'+val_p+'/phi_qq/mq'+mq
                try:
                    f5.create_group('/'+val_p+'/dwf_jmu/mq'+mq,'midpoint_pseudo',createparents=True)
                    f5.create_group('/'+val_p+'/dwf_jmu/mq'+mq,'pseudo_pseudo',createparents=True)
                    f5.flush()
                except:
                    pass
                try:
                    f5.create_group('/'+val_p+'/phi_qq','mq'+mq,createparents=True)
                    f5.flush()
                except:
                    pass
                get_data = False
                if src not in f5.get_node(mpdir) or src not in f5.get_node(ppdir) or src not in f5.get_node(phi_dir):
                    get_data = True
                if args.o and (src in f5.get_node(mpdir) or src in f5.get_node(ppdir) or src in f5.get_node(phi_dir)):
                    get_data = True
                if get_data:
                    with open(ftmp) as file:
                        f = file.readlines()
                    have_data = False; l = 0
                    while not have_data:
                        if f[l].find('<DWF_MidPoint_Pseudo>') > 0 and f[l+3].find('<DWF_Psuedo_Pseudo>') > 0:
                            corr_mp = f[l+1].split('<mesprop>')[1].split('</mesprop>')[0].split()
                            corr_pp = f[l+4].split('<mesprop>')[1].split('</mesprop>')[0].split()
                            nt = len(corr_mp)
                            mp = np.array([float(d) for d in corr_mp],dtype=dtype)
                            pp = np.array([float(d) for d in corr_pp],dtype=dtype)
                            if not np.any(np.isnan(pp)) and not np.any(np.isnan(mp)):
                                if args.v:
                                    print(no,'mq'+mq,src,'mres collected')
                                if src not in f5.get_node(mpdir):
                                    f5.create_array(mpdir,src,mp)
                                elif src in f5.get_node(mpdir) and args.o:
                                    f5.get_node(mpdir+'/'+src)[:] = mp
                                elif src in f5.get_node(mpdir) and not args.o:
                                    print('  skipping midpoint_pseudo: overwrite = False')
                                if src not in f5.get_node(ppdir):
                                    f5.create_array(ppdir,src,pp)
                                elif src in f5.get_node(ppdir) and args.o:
                                    f5.get_node(ppdir+'/'+src)[:] = pp
                                elif src in f5.get_node(ppdir) and not args.o:
                                    print('  skipping pseudo_pseudo: overwrite = False')
                            else:
                                print('  NAN')
                        # phi_qq
                        if f[l].find('<prop_corr>') > 0:
                            corr = f[l].split('<prop_corr>')[1].split('</prop_corr>')[0].split()
                            phi_qq = np.array([float(d) for d in corr],dtype=dtype)
                            phi_qq = np.roll(phi_qq,-t_src)
                            if not np.any(np.isnan(phi_qq)):
                                print(no,'mq'+mq,src,'phi_qq collected')
                                if src not in f5.get_node(phi_dir):
                                    f5.create_array(phi_dir,src,phi_qq)
                                elif src in f5.get_node(phi_dir) and args.o:
                                    f5.get_node(phi_dir+'/'+src)[:] = phi_qq
                                elif src in f5.get_node(phi_dir) and not args.o:
                                    print('  skipping forward_prop: overwrite = False')
                            else:
                                print('  NAN')
                            have_data = True
                        else:
                            l += 1
                    
                f5.close()
