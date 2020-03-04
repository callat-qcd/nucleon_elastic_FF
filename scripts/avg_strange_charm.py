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
    'a06m310L' :[],
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
    'a12m260'  :64,# 300,5295,5
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
mc_s = str(mc)
ms_sp = ms_s.replace('.','p')
mc_sp = mc_s.replace('.','p')

nt = nt_ens[ens]

parser = argparse.ArgumentParser(description='collect strange and charm disco loops and put in h5 files')
parser.add_argument('cfgs',nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('-o','--overwrite',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('-d','--debug',    default=False,action='store_const',const=True,help='debug? [%(default)s]')
parser.add_argument('-f','--force',    default=False,action='store_const',const=True,help='collect even if missing files? [%(default)s]')

args = parser.parse_args()

if len(args.cfgs) == 1:
    ci = args.cfgs[0]
    cf = args.cfgs[0]
    dc = 1
elif len(args.cfgs) == 3:
    ci = args.cfgs[0]
    cf = args.cfgs[1]
    dc = args.cfgs[2]
else:
    sys.exit('you must specifify either a single cfg or a range')
print('collecting from cfgs %d - %d' %(ci,cf))


#LASSEN specific
in_dir='/p/gpfs1/walkloud/c51/x_files/project_2/production/'+ens_s+'/data'
out_dir='/p/gpfs1/walkloud/c51/x_files/project_2/production/'+ens_s+'/data/avg'
if not os.path.exists(out_dir):
    os.makedirs(out_dir)
out_file=out_dir+'/'+ens_s+'_avg_strange_charm.h5'

# make sure all files exist
all_files = True
missing_cfgs = []
for cfg in range(ci,cf+dc,dc):
    no = str(cfg)
    h5_file = in_dir+'/'+ens_s+'_'+no+'_strange_charm.h5'
    if not os.path.exists(h5_file):
        all_files = False
        missing_cfgs.append(cfg)

if all_files or (not all_files and args.force):
    d_sets = []
    f5_in = h5.open_file(in_dir+'/'+ens_s+'_'+str(ci)+'_strange_charm.h5','r')
    for k in f5_in.root:
        d_sets.append(k._v_name)
    f5_in.close()
    for i_d,d_set in enumerate(d_sets):
        print('concatenating %s' %d_set)
        first_data = True
        cfgs = []
        for cfg in range(ci,cf+dc,dc):
            no = str(cfg)
            sys.stdout.write('    cfgs = %s\r' %no)
            sys.stdout.flush()
            if os.path.exists(in_dir+'/'+ens_s+'_'+no+'_strange_charm.h5'):
                f5_in = h5.open_file(in_dir+'/'+ens_s+'_'+no+'_strange_charm.h5','r')
                data_no = f5_in.get_node('/'+d_set).read()
                f5_in.close()
                cfgs.append(cfg)
                if first_data:
                    data = np.zeros((1,)+data_no.shape,dtype=data_no.dtype)
                    data[0] = data_no
                    first_data = False
                else:
                    try:
                        data = np.append(data,[data_no],axis=0)
                    except Exception as e:
                        print(e)
                        print('first data:',data[0].shape)
                        print('  cfg=%s' %no,data_no.shape)
                        sys.exit()
        f5_out = h5.open_file(out_file,'a')
        if d_set not in f5_out.get_node('/'):
            f5_out.create_array('/',d_set,data)
            if i_d == 0:
                f5_out.create_array('/','cfgs',cfgs)
            f5_out.flush()
        elif d_set in f5_out.get_node('/') and args.overwrite:
            if d_set in f5_out.get_node('/'):
                f5_out.remove_array('/'+d_set)
            if i_d == 0:
                if 'cfgs' in f5_out.get_node('/'):
                    f5_out.remove_array('/cfgs')
            f5_out.create_array('/',d_set,data)
            if i_d == 0:
                f5_out.create_array('/','cfgs',cfgs)
            f5_out.flush()
        else:
            print('%s exists and overwrite = False' %args.overwrite)            
        f5_out.close()
elif not all_files and not args.force:
    print('missing cfgs')
    for cfg in missing_cfgs:
        print(cfg)
