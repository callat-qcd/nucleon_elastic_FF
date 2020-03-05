from __future__ import print_function
import os, sys, argparse, shutil, datetime, time, subprocess
import numpy as np
np.set_printoptions(linewidth=180)
import tables as h5
import warnings
warnings.simplefilter('ignore', h5.NaturalNameWarning)
from glob import glob
fmt = '%Y-%m-%d %H:%M:%S'

'''
    NUCLEON_ELASTIC_FF IMPORTS
'''
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
import importlib
import c51_mdwf_hisq as c51
import utils
import sources
ens,stream = c51.ens_base()
ens_s = ens+'_'+stream

area51 = importlib.import_module(ens)
params = area51.params
params['machine'] = c51.machine
params['ENS_LONG'] = c51.ens_long[ens]
params['ENS_S']    = ens_s
params['STREAM']   = stream

print('ENSEMBLE:',ens_s)

'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='get spec data from h5 files')
parser.add_argument('cfgs',nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('-m','--mq', type=str,help='specify quark mass [default = all]')
parser.add_argument('-s','--src',type=str,help='src [xXyYzZtT] None=All')
parser.add_argument('-o',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('--move',default=False,action='store_const',const=True,help='move bad files? [%(default)s]')
parser.add_argument('-f','--force',    default=False,action='store_const',const=True,help='collect even if missing files? [%(default)s]')
parser.add_argument('-v',default=True,action='store_const',const=False,help='verbose? [%(default)s]')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.float64
data_dir = c51.data_dir % params
utils.ensure_dirExists(data_dir)

params = sources.src_start_stop(params,ens,stream)
cfgs   = utils.parse_cfg_argument(args.cfgs,params)

print('CONCATENATING WFLOW and Q')
print('ens_stream = ',ens_s)
out_file = data_dir+'/avg/'+ens_s+'_gauge_params.h5'

all_files = True
missing_cfgs = []
for cfg in cfgs:
    no = str(cfg)
    h5_file = data_dir+'/'+ens_s+'_'+no+'_gauge_params.h5'
    if not os.path.exists(h5_file):
        all_files = False
    missing_cfgs.append(cfg)

if all_files or (not all_files and args.force):
    d_sets = []
    f5_in = h5.open_file(data_dir+'/'+ens_s+'_'+str(cfgs[0])+'_gauge_params.h5','r')
    for k in f5_in.root:
        d_sets.append(k._v_name)
    f5_in.close()
    for i_d,d_set in enumerate(d_sets):
        print('concatenating %s' %d_set)
        first_data = True
        cfgs_collect = []
        for cfg in cfgs:
            no = str(cfg)
            sys.stdout.write('    cfgs = %s\r' %no)
            sys.stdout.flush()
            if os.path.exists(data_dir+'/'+ens_s+'_'+no+'_gauge_params.h5'):
                f5_in = h5.open_file(data_dir+'/'+ens_s+'_'+no+'_gauge_params.h5')
                data_no = f5_in.get_node('/'+d_set).read()
                f5_in.close()
                cfgs_collect.append(cfg)
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
        if d_set == 't_gf':
            data = data[0]
        if d_set not in f5_out.get_node('/'):
            f5_out.create_array('/',d_set,data)
            if i_d == 0:
                f5_out.create_array('/','cfgs',cfgs_collect)
            f5_out.flush()
        elif d_set in f5_out.get_node('/') and args.overwrite:
            if d_set in f5_out.get_node('/'):
                f5_out.remove_array('/'+d_set)
            if i_d == 0:
                if 'cfgs' in f5_out.get_node('/'):
                    f5_out.remove_array('/cfgs')
            f5_out.create_array('/',d_set,data)
            if i_d == 0:
                f5_out.create_array('/','cfgs',cfgs_collect)
            f5_out.flush()
        else:
            print('%s exists and overwrite = False' %args.overwrite)
        f5_out.close()
elif not all_files and not args.force:
    print('missing cfgs')
    for cfg in missing_cfgs:
        print(cfg)
