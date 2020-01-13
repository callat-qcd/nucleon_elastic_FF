#!/usr/local/bin/python
import os, sys, argparse, shutil
import tables as h5
import numpy as np
from glob import glob
import hadron_states as hs
proj_path=os.path.realpath(__file__).split('project_2')[0]+'project_2'
sys.path.append(proj_path+'/run_py_dls')

import funkyrunner as fr
sloppy, ens_base, ens_stream = fr.ens_metadata()
import skynet as sc
import importlib
ep = importlib.import_module('area51_'+ens_base)
import time
import fcntl # locks open files

if sloppy != 'exact':
    print('hisq spec on exact only')
    sys.exit()
np.set_printoptions(linewidth=180)

parser = argparse.ArgumentParser(description='get mres data and put in h5 file')
base_path = str(sc.volatile)
ens = str(ens_base)+str(ens_stream)
sloppy = str(sloppy)
parser.add_argument('--cfg',nargs='+',type=int,help='cfgs: [ni [nf dn]] None=All')
parser.add_argument('--src',type=str,help='specify src [eg x8y10z0t11]')
parser.add_argument('--base',type=str,default='mixed',help='base name for meson hadspec xml files [%(default)s]')
wflow = str(ep.flow_time)
M5 = str(ep.M5)
L5 = str(ep.L5)
a5 = str(ep.alpha5)
wv_smr = 'wv_w'+str(ep.wv_w)+'_n'+str(ep.wv_n)
parser.add_argument('--ml',type=str,help='quark mass [%(default)s]')
parser.add_argument('--ms',type=str,help='quark mass [%(default)s]')
nt = str(ep.nt)
parser.add_argument('--cfg_dir',default=True,action='store_const',const=False,\
    help='extra dir for each cfg? [%(default)s]')
parser.add_argument('--check_xml',default=True,action='store_const',const=False,\
    help='check xml file for integrity? [%(default)s]')
parser.add_argument('-o',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('--oo',default=False,action='store_const',const=True,help='remove and overwrite? [%(default)s]')
parser.add_argument('--force',default=False,action='store_const',const=True,\
    help='run without prompting user? [%(default)s]')
parser.add_argument('--move',default=False,action='store_const',const=True,help='move bad files? [%(default)s]')
parser.add_argument('--fout',type=str,help='directory to output, need to end with /, leave empty for production')
parser.add_argument('--complete',default='get_meson_complete.txt',type=str,help='prints out completed masses to file')

args = parser.parse_args()
print('Arguments passed')
print args
print('')

#ens = args.ens
if args.fout == None:
    out_path = proj_path+'/data/'+ens+'/'
else:
    out_path = args.fout

if not os.path.exists(out_path):
    os.makedirs(out_path)
if sloppy == 'exact':
    bd_name = 'bad_mes_'+ens+'.lst'
    tmp_name = ens
else:
    bd_name = 'bad_mes_'+ens+'_'+sloppy+'.lst'
    tmp_name = ens+'_'+sloppy

cwd = os.getcwd()

dtype = np.float32
base = args.base
#wflow = args.wflow
#M5 = args.M5
#L5 = args.L5
#a5 = args.a5
#wv_smr = args.wv_smr
#ml = args.ml
#ms = args.ms
# valence light
if args.ml == None:
    if ep.tune:
        ml_list = [ep.mv_l]
    else:
        ml_list = ep.pq_ml
else:
    ml_list = [args.ml]
# valence strange
if args.ms == None:
    if ep.tune:
        ms_list = [ep.mv_s]
    else:
        ms_list = ep.pq_ms
else:
    ms_list = [args.ms]
nt = int(ep.nt)
ms_l = ep.ml
ms_s = ep.ms


#fpath = args.base_path +'/'+ ens
fpath = base_path.replace('lustre2','lustre1')
#fpath = base_path
if sloppy != 'exact':
    fpath += '/'+sloppy
corrupt_path = fpath +'/corrupt'
fpath += '/mixed'
if not os.path.exists(corrupt_path):
    os.makedirs(corrupt_path)
print('looking for data in ')
print(fpath+'\n')
print('output files:')
print(out_path)
if sloppy == 'exact':
    print('  '+ens+'_cfg.h5')
else:
    print('  '+ens+'_'+sloppy+'_cfg.h5')

val = 'wf'+str(wflow).replace('.','p')
val += '_m5'+str(M5).replace('.','p')
val += '_l5'+str(L5).replace('.','p')
val += '_a5'+str(a5).replace('.','p')
val += '_'+wv_smr.replace('.','p').replace('wv_','smr')
val_f = 'wflow%s_M5%s_L5%s_a%s' %(str(wflow),str(M5),L5,str(a5))
print('valence info')
print(val_f+'\n')

print('  ml = %s, ms = %s' %(ml_list,ms_list))
if args.cfg == None:
    print('  cfgs = ALL')
else:
    print('  cfgs = ',args.cfg)
if not args.force:
    proceed = raw_input('would you like to proceed?\t')
    if proceed not in ['y','yes']:
        os.system('python '+sys.argv[0]+' -h')
        sys.exit()
hadspec_stripper = sc.data_manage_dir + '/bin/strip_hadspec_old_robert '

if args.cfg == None:
    dirs = glob(fpath+'/*')
    cfgs = []
    print(dirs)
    for d in dirs:
        cfgs.append(int(d.split('/')[-1]))
    cfgs.sort()
    ni = cfgs[0]; nf = cfgs[-1]; dn = cfgs[1]-cfgs[0];
else:
    if len(args.cfg) == 1:
        ni = args.cfg[0]; nf = args.cfg[0]+1; dn = args.cfg[0];
    elif len(args.cfg) == 3:
        ni = args.cfg[0]; nf = args.cfg[1]+1; dn = args.cfg[2];
    cfgs = range(ni,nf,dn)

def read_milc(f,i,nt):
    #print 'reading correlator', f
    data = np.zeros([nt],dtype=np.complex64)
    for t in range(nt):
        data[t] = float(f[i+6+t].split()[1]) +1.j*float(f[i+6+t].split()[2])
    return data

mq_had = ep.mq_had

completeName = args.complete

bad_lst = open(cwd+'/'+bd_name,'a')
for cfg in cfgs:
    no = str(cfg)
    print no
    # TASTE_5,I SPECTRUM
    mesons = {
        'PION_5':'phi_jj_5','PION_I':'phi_jj_I',
        'KAON_5':'phi_jr_5','KAON_I':'phi_jr_I',
        'SS_5':'phi_rr_5','SS_I':'phi_rr_I',
        'PHI_UU':'phi_uu',
        'PHI_JU':'phi_ju','PHI_UJ':'phi_uj',
        'PHI_JS':'phi_js','PHI_SJ':'phi_sj',
        'PHI_RU':'phi_ru','PHI_UR':'phi_ur',
        'PHI_RS':'phi_rs','PHI_SR':'phi_sr',
        }
    # clean tmp_strip_path in case of prior bad files there
    #HACK TO WORK FOR NOW
    mv_l = ml_list[0]
    mv_s = ms_list[0]
    #
    if args.cfg_dir:
       spath = fpath+'/'+no
    else:
        spath = fpath
    if args.src == None:
        files = glob(spath+'/dwf_hisq_spec_'+ens+'_'+val_f+'_cfg_'+no+'_src*_'+wv_smr+'_ml'+mv_l+'_ms'+mv_s+'.corr')
    else:
        files = glob(spath+'/dwf_hisq_spec_'+ens+'_'+val_f+'_cfg_'+no+'_src'+args.src+'_'+wv_smr+'_ml'+mv_l+'_ms'+mv_s+'.corr')
    if len(files) > 0:
        mine_cfg = True
    else:
        mine_cfg = False
        print('no files in %s with %s' %(ens,val))
        print spath+'/dwf_hisq_spec_'+ens+'_'+val_f+'_cfg_'+no+'_src*_'+wv_smr+'_ml'+mv_l+'_ms'+mv_s+'.corr'
    if mine_cfg:
        if sloppy == 'exact':
            #print 'locking file', out_path+ ens+'_'+no+'.h5'
            f5 = h5.open_file(out_path+ ens+'_'+no+'.h5','a')
            fcntl.flock(f5,fcntl.LOCK_EX)
        else:
            #print 'locking file', out_path+ ens+'_'+sloppy+'_'+no+'.h5'
            f5 = h5.open_file(out_path+ ens+'_'+sloppy+'_'+no+'.h5','a')
            fcntl.flock(f5,fcntl.LOCK_EX)
        mls = 'ml'+ms_l.replace('.','p')
        mss = 'ms'+ms_s.replace('.','p')
        group = (val+'/hisq_spec/'+mls+'_'+mss).split('/')
        #print val+'/spectrum/'+mls+'_'+mss
        cdir = '/'
        for g_i in range(len(group)):
            if group[g_i] not in f5.get_node(cdir):
                f5.create_group(cdir,group[g_i])
            cdir += '/'+group[g_i]
        for ftmp in files:
            print "FTMP:", ftmp
            src = ftmp.split('src')[1].split('_')[0]
            t_src = int(src.split('t')[1])
            f_good = True
            if f_good:
                print 'reading spectrum'
                print "cwd:", os.getcwd()
                corr_input = open(ftmp).readlines()
                for i,l in enumerate(corr_input):
                    if 'correlator:' in l:
                        corr_name = l.split()[1]
                        state = mesons[corr_name]
                        print state, corr_name
                        data = read_milc(corr_input,i,nt)
                        #print data
                        if state not in f5.get_node(cdir):
                            f5.create_group(cdir,state)
                        sdir = cdir+'/'+state
                        if not np.any(np.isnan(data)):
                            if src not in f5.get_node(sdir):
                                f5.create_array(sdir,src,data)
                            elif src in f5.get_node(sdir) and args.o:
                                if args.oo:
                                    f5.remove_node(sdir,src)
                                    f5.create_array(sdir,src,data)
                                else:
                                    tmp = f5.get_node(sdir+'/'+src)
                                    tmp[:] = data
                            elif src in f5.get_node(sdir) and not args.o:
                                pass
                                print('  skipping %s: overwrite = False' %state)
                        else:
                            print('  NAN')
                            bad_lst.write('%s %s %s NAN' %(no,state,src))
                            bad_lst.flush()
        f5.close()
        #sys.exit()
bad_lst.close()
#completeFile.close()
print "DONE"
