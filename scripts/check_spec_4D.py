from __future__ import print_function
import os, sys, argparse, shutil, datetime, time
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
parser.add_argument('cfgs',      nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('-s','--src',type=str,help='src [xXyYzZtT] None=All')
parser.add_argument('--src_set', nargs=3,type=int,help='specify si sf ds')
parser.add_argument('-o',        default=False,action='store_const',const=True, help='overwrite? [%(default)s]')
parser.add_argument('--move',    default=False,action='store_const',const=True, help='move bad files? [%(default)s]')
parser.add_argument('-v',        default=True, action='store_const',const=False,help='verbose? [%(default)s]')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.complex64
data_dir = c51.data_dir % params
utils.ensure_dirExists(data_dir)

if 'si' in params and 'sf' in params and 'ds' in params:
    tmp_params = dict()
    tmp_params['si'] = params['si']
    tmp_params['sf'] = params['sf']
    tmp_params['ds'] = params['ds']
    params = sources.src_start_stop(params,ens,stream)
    params['si'] = tmp_params['si']
    params['sf'] = tmp_params['sf']
    params['ds'] = tmp_params['ds']
else:
    params = sources.src_start_stop(params,ens,stream)
if args.src_set:# override src index in sources and area51 files for collection
    params['si'] = args.src_set[0]
    params['sf'] = args.src_set[1]
    params['ds'] = args.src_set[2]
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,args.src,params)
src_ext = "%d-%d" %(params['si'],params['sf'])
smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
val_p = val.replace('.','p')

mv_l = params['MV_L']

print('MINING SPEC')

ps   = ['sh','pt']
spin = ['spin_up','spin_dn']
par  = ['proton','proton_np']
params['MQ'] = params['MV_L']

missing_spec_files = []
collect_files = []
for cfg in cfgs_run:
    no = str(cfg)
    print(no)
    params['CFG'] = no
    params = c51.ensemble(params)
    for src in srcs[cfg]:
        params['SRC'] = src
        spec_name = c51.names['spec_4D'] % params
        spec_file = params['spec_4D'] +'/'+ spec_name+'.h5'
        spec_name_tslice = c51.names['spec_4D_tslice'] % params
        spec_file_tslice = params['spec_4D_tslice'] +'/'+ spec_name_tslice+'.h5'
        if not os.path.exists(spec_file_tslice):
            if os.path.exists(spec_file):
                collect_files.append(no+'/'+spec_name)
            else:
                missing_spec_files.append(no+'/'+spec_name)

if len(missing_spec_files) > 0:
    print('missing %d spec_4D files' %(len(missing_spec_files)))
    tmp = open('missing_check_spec_4D_Srcs'+src_ext+'.lst','w')
    for f in missing_spec_files:
        no,ff = f.split('/')[-2],f.split('/')[-1]
        tmp.write(no+'/'+ff+'\n')
    tmp.close()

if len(collect_files) > 0:
    print('%d spec_4D files ready for collecting' %len(collect_files))
    tmp = open('collect_spec_4D_Srcs'+src_ext+'.lst','w')
    for f in collect_files:
        no,ff = f.split('/')[-2],f.split('/')[-1]
        tmp.write(no+'/'+ff+'\n')
    tmp.close()
