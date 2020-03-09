from __future__ import print_function
import os, sys, argparse, shutil, datetime, time
import numpy as np
np.set_printoptions(linewidth=180)
import tables as h5
import h5py
import warnings
warnings.simplefilter('ignore', h5.NaturalNameWarning)
from glob import glob
fmt = '%Y-%m-%d %H:%M:%S'

'''
    NUCLEON_ELASTIC_FF IMPORTS
'''
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
# h5 utils
from nucleon_elastic_ff.data.h5io import get_dsets
# MDWF on HISQ info
import importlib
import c51_mdwf_hisq as c51
import utils
import sources
import collect_corr_utils as collect_utils
from nucleon_elastic_ff.data.scripts.h5migrate import dset_migrate as h5migrate

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
parser.add_argument('-m','--mq',           type=str,help='specify quark mass [default = all]')
parser.add_argument('-s','--src',          type=str,help='src [xXyYzZtT] None=All')
parser.add_argument('--src_set', nargs=3,  type=int,help='specify si sf ds')
parser.add_argument('-o',          default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('--move',      default=False,action='store_const',const=True,help='move bad files? [%(default)s]')
parser.add_argument('-v',          default=False,action='store_const',const=True,help='verbose? [%(default)s]')
parser.add_argument('-d','--debug',default=False,action='store_const',const=True,help='debug? [%(default)s]')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

params['verbose']   = args.v
params['overwrite'] = args.o
params['debug']     = args.debug

dtype = np.float64
data_dir = c51.data_dir % params
utils.ensure_dirExists(data_dir)
full_data_dir = c51.full_data_dir % params
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

if args.mq == None:
    try:
        if params['run_strange']:
            mq_lst = [params['MV_L'], params['MV_S']]
        else:
            mq_lst = [params['MV_L']]
    except:
        mq_lst = [params['MV_L']]
else:
    mq_lst = [args.mq]

print('MINING MRES and PHI_QQ')
print('ens_stream = ',ens_s)
print('srcs:',src_ext)
print('data dir',data_dir)

for cfg in cfgs_run:
    no = str(cfg)
    print(no)
    params['CFG']    = no
    params['srcs']   = srcs[cfg]
    params['MQ_LST'] = mq_lst
    params['mres_path']   = val_p+'/dwf_jmu'
    params['phi_qq_path'] = val_p+'/phi_qq'
    params = c51.ensemble(params)
    h5_full=full_data_dir+'/'+ens_s+'_'+no+'_srcs'+src_ext+'.h5'
    if os.path.exists(h5_full):
        with h5py.File(h5_full,'r') as f5_full:
            dsets_full = get_dsets(f5_full, load_dsets=False)
    else:
        print('DOES NOT EXIST: %s' %(full_data_dir+'/'+ens_s+'_'+no+'_srcs'+src_ext+'.h5'))
        dsets_full = dict()
    h5_tmp = data_dir+'/'+ens_s+'_'+no+'_srcs'+src_ext+'.h5'
    tmp_exists = os.path.exists(h5_tmp)
    if tmp_exists:
        with h5py.File(h5_tmp,'r') as f5_tmp:
            dsets_tmp  = get_dsets(f5_tmp, load_dsets=False)
    else:
        dsets_tmp = dict()

    # check res phi
    have_mres_full = collect_utils.get_res_phi(params,dsets_full)
    have_mres_tmp  = collect_utils.get_res_phi(params,dsets_tmp,h5_file=h5_tmp,collect=True)
    
    have_tmp  = have_mres_tmp
    have_full = have_mres_full

    # check spec
    params['MQ']   = 'ml'+params['MV_L']
    params['h5_spec_path'] = val_p+'/spec'

    have_spec_full = collect_utils.get_spec(params,dsets_full)
    have_spec_tmp  = collect_utils.get_spec(params,dsets_tmp,h5_file=h5_tmp,collect=True)

    if not have_spec_full:
        have_full = False
    if have_spec_tmp:
        have_tmp  = True

    # check hyperspec
    if params['run_strange']:
        params['MQ'] = 'ml'+params['MV_L']+'_ms'+params['MV_S']
        params['h5_spec_path'] = val_p+'/spec'

        have_hspec_full = collect_utils.get_spec(params,dsets_full,spec='hyperspec')
        have_hspec_tmp  = collect_utils.get_spec(params,dsets_tmp,h5_file=h5_tmp,collect=True,spec='hyperspec')

        if not have_hspec_full:
            have_full = False
        if have_hspec_tmp:
            have_tmpe = True

    if have_tmp and not have_full:
        print('h5migrate')
        if not os.path.exists(h5_full):
            os.system('touch '+h5_full)
        h5migrate(h5_tmp, h5_full, atol=0.0, rtol=1e-10)

    '''
    todo: put in logic of checking with lattedb first
          want overwrite feature for migrate
          only check tmp if full empty

    '''
