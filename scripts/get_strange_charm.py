import os, sys, argparse
import numpy as np
import tables as h5
import subprocess
from glob import glob

# [strange, charm]
msc_ens = {
    'a15m400'  :[0.06730,0.8447],
    'a15m350'  :[0.06730,0.8447],
    'a15m310'  :[0.06730,0.8447],
    'a15m310L' :[0.06730,0.8447],
    'a15m260'  :[0.06730,0.8447],
    'a15m220'  :[0.06730,0.8447],
    'a15m220XL':[0.06730,0.8447],
    'a15m135XL':[0.06730,0.8447],
    'a12m400'  :[0.05252,0.6382],
    'a12m350'  :[0.05252,0.6382],
    'a12m310'  :[0.05252,0.6382],
    'a12m310L' :[0.05252,0.6382],
    'a12m310XL':[0.05252,0.6382],
    'a12m260'  :[0.05252,0.6382],
    'a12m220S' :[0.05252,0.6382],
    'a12m220'  :[0.05252,0.6382],
    'a12m220L' :[0.05252,0.6382],
    'a12m220XL':[0.05252,0.6382],
    'a12m180'  :[0.05252,0.6382],
    'a12m180L' :[0.05252,0.6382],
    'a12m130'  :[0.05252,0.6382],
    'a09m400'  :[0.03636,0.4313],
    'a09m350'  :[0.03636,0.4313],
    'a09m310'  :[0.03636,0.4313],
    'a09m220'  :[0.03636,0.4313],
    'a06m310L' :[0.02186,0.2579],
}
nt_ens = {
    'a15m400'  :48,# 300,5295,5
    'a15m350'  :48,# 300,5295,5
    'a15m310L' :48,# 300,5295,5
    'a15m310'  :48,# 300,5295,5
    'a15m260'  :48,# 300,5295,5
    'a15m220'  :48,# 300,5295,5
    'a12m400'  :64,# 485,5480,5
    'a12m350'  :64,# 485,5480,5
    'a12m310XL':64,# 485,5480,5
    'a12m310L' :64,# 485,5480,5
    'a12m310'  :64,# 485,5480,5
    'a12m260'  :64,# 485,5480,5
    'a12m220'  :64,# 485,5480,5
    'a12m220S' :64,# 485,5480,5
    'a12m220L' :64,# 485,5480,5
    'a12m220XL':64,# 485,5480,5
    'a12m180L' :64,# 485,5480,5
    'a12m130'  :64,# 300,5295,5
    'a09m400'  :64,# 300,6300,5
    'a09m350'  :64,# 300,6300,5
    'a09m310'  :96,# 300,4998,6
    'a09m220'  :96,# 300,6300,6
}

ens,stream = os.getcwd().split('/')[-1].split('_')
ens_s = ens+'_'+stream
print(ens,stream)

ms = msc_ens[ens][0]
mc = msc_ens[ens][1]
ms_s = str(ms)
if ms_s == '0.0673':
    ms_s = '0.06730'
mc_s = str(mc)
ms_sp = ms_s.replace('.','p')
mc_sp = mc_s.replace('.','p')

nt = nt_ens[ens]

parser = argparse.ArgumentParser(description='collect strange and charm disco loops and put in h5 files')
parser.add_argument('cfgs',nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('-o','--overwrite',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('-d','--debug',    default=False,action='store_const',const=True,help='debug? [%(default)s]')
args = parser.parse_args()

if len(args.cfgs) == 1:
    ci = args.cfgs[0]
    cf = args.cfgs[0]+1
    dc = 1
elif len(args.cfgs) == 3:
    ci = args.cfgs[0]
    dc = args.cfgs[2]
    cf = args.cfgs[1]+dc
else:
    sys.exit('you must specifify either a single cfg or a range')
print('collecting from cfgs %d - %d' %(ci,cf-dc))


#LASSEN specific
in_dir ='/p/gpfs1/walkloud/c51/x_files/project_2/production/'+ens_s
out_dir='/p/gpfs1/walkloud/c51/x_files/project_2/production/'+ens_s+'/data'
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

missing_cfgs = []

for cfg in range(ci,cf,dc):
    no = str(cfg)
    print(no)
    h5_file = out_dir+'/'+ens_s+'_'+no+'_strange_charm.h5'
    if not os.path.exists(h5_file) or (os.path.exists(h5_file) and args.overwrite):
        files = glob(in_dir+'/stdout/'+no+'/strange_charm_loops_hisq_'+ens_s+'_ms'+ms_s+'_n64_mc'+mc_s+'_n256_'+no+'.stdout')
        if len(files) > 0:
            f_in = files[0]
            try:
                naik = subprocess.check_output('grep naik_term_epsilon %s' %f_in, shell=True).decode('ascii')
                naik_vals = []
                for l in naik.split('\n'):
                    if len(l.split()) > 0:
                        naik_vals.append(l.split()[-1])
                npbp_s = int(f_in.split(ms_s)[1].split('_n')[1].split('_')[0])
                npbp_c = int(f_in.split(mc_s)[1].split('_n')[1].split('_')[0])
                sbars          = np.zeros([npbp_s,2],    dtype=np.complex64)
                sbars_tslice   = np.zeros([npbp_s,nt,2], dtype=np.complex64)
                cbarc_0        = np.zeros([npbp_c,2],    dtype=np.complex64)
                cbarc_tslice_0 = np.zeros([npbp_c,nt,2], dtype=np.complex64)
                cbarc_1        = np.zeros([npbp_c,2],    dtype=np.complex64)
                cbarc_tslice_1 = np.zeros([npbp_c,nt,2], dtype=np.complex64)
                pbp = subprocess.check_output('grep "PBP: mass" %s' %f_in, shell=True).decode('ascii').split('\n')
                # strange 
                for n in range(npbp_s):
                    tmp = pbp[n*(nt+1)].split()
                    mass = float(tmp[2])
                    if mass != ms:
                        sys.exit('strange masses do not match: '+str(mass)+' '+str(ms))
                    n_i  = int(tmp[8])
                    if n+1 != n_i:
                        sys.exit('you are counting noise indices incorrectly: '+str(n_i)+' '+str(n))
                    # PBP values are
                    # re_even re_odd im_even im_odd
                    e_re = float(tmp[3])
                    o_re = float(tmp[4])
                    e_im = float(tmp[5])
                    o_im = float(tmp[6])
                    sbars[n,0] = e_re + 1j*e_im
                    sbars[n,1] = o_re + 1j*o_im
                    # get time slices
                    for t in range(nt):
                        tmp_slice = pbp[n*(nt+1)+t+1].split()
                        mass = float(tmp_slice[2])
                        if mass != ms:
                            sys.exit('strange masses do not match: '+str(mass)+' '+str(ms))
                        n_i  = int(tmp_slice[10])
                        if n+1 != n_i:
                            sys.exit('you are counting noise indices incorrectly: '+str(n_i)+' '+str(n))
                        e_re = float(tmp_slice[5])
                        o_re = float(tmp_slice[6])
                        e_im = float(tmp_slice[7])
                        o_im = float(tmp_slice[8])
                        sbars_tslice[n,t,0] = e_re + 1j*e_im
                        sbars_tslice[n,t,1] = o_re + 1j*o_im
                # charm naik 0 and 1
                n_off = npbp_s * (nt+1)
                for n in range(npbp_c):
                    for n_naik in range(2):
                        i = n_off +(nt+1) * (2*n + n_naik)
                        tmp = pbp[i].split()
                        if args.debug:
                            print(i,tmp)
                        mass = float(tmp[2])
                        if mass != mc:
                            sys.exit('charm masses do not match: '+str(mass)+' '+str(mc))
                        n_i  = int(tmp[8])
                        if n+1 != n_i:
                            sys.exit('you are counting noise indices incorrectly: '+str(n_i)+' '+str(n+1))
                        # PBP values are
                        # re_even re_odd im_even im_odd
                        e_re = float(tmp[3])
                        o_re = float(tmp[4])
                        e_im = float(tmp[5])
                        o_im = float(tmp[6])
                        if n_naik == 0:
                            cbarc_0[n,0] = e_re + 1j*e_im
                            cbarc_0[n,1] = o_re + 1j*o_im
                        else:
                            cbarc_1[n,0] = e_re + 1j*e_im
                            cbarc_1[n,1] = o_re + 1j*o_im
                        # get time slices
                        for t in range(nt):
                            i_t = n_off +(nt+1) * (2*n + n_naik) + t+1
                            tmp_slice = pbp[i_t].split()
                            if args.debug:
                                print(i_t,tmp_slice)
                            mass = float(tmp_slice[2])
                            if mass != mc:
                                sys.exit('charm masses do not match: '+str(mass)+' '+str(mc))
                            n_i  = int(tmp_slice[10])
                            if n+1 != n_i:
                                sys.exit('you are counting noise indices incorrectly: '+str(n_i)+' '+str(n+9))
                            e_re = float(tmp_slice[5])
                            o_re = float(tmp_slice[6])
                            e_im = float(tmp_slice[7])
                            o_im = float(tmp_slice[8])
                            if n_naik == 0:
                                cbarc_tslice_0[n,t,0] = e_re + 1j*e_im
                                cbarc_tslice_0[n,t,1] = o_re + 1j*o_im
                            else:
                                cbarc_tslice_1[n,t,0] = e_re + 1j*e_im
                                cbarc_tslice_1[n,t,1] = o_re + 1j*o_im
                # write to h5 file
                f5 = h5.open_file(h5_file,'w')
                f5.create_array('/','sbars_ms'+ms_sp,sbars)
                f5.create_array('/','sbars_ms'+ms_sp+'_tslice',sbars_tslice)
                f5.create_array('/','cbarc_mc'+mc_sp+'_naik_'+naik_vals[1].replace('-','m').replace('.','p'),cbarc_0)
                f5.create_array('/','cbarc_mc'+mc_sp+'_naik_'+naik_vals[2].replace('-','m').replace('.','p'),cbarc_1)
                f5.create_array('/','cbarc_mc'+mc_sp+'_tslice_naik_'+naik_vals[1].replace('-','m').replace('.','p'),cbarc_tslice_0)
                f5.create_array('/','cbarc_mc'+mc_sp+'_tslice_naik_'+naik_vals[2].replace('-','m').replace('.','p'),cbarc_tslice_1)
                f5.close()
            except Exception as e:
                print(e)
                missing_cfgs.append(cfg)
        else:
            print('DOES NOT EXIST!',in_dir+'/stdout/'+no+'/strange_charm_loops_hisq_'+ens_s+'_ms'+ms_s+'_n*_mc'+mc_s+'_n*_'+no+'.stdout')
            missing_cfgs.append(cfg)
    else:
        print('exists and overwrite = False',h5_file)

missing = open('missing_strange_charm_cfgs_'+ens_s+'.lst','w')
for cfg in missing_cfgs:
    missing.write(str(cfg)+'\n')
missing.close()
