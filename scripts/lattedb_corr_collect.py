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
# h5 and lattedb utils
from nucleon_elastic_ff.data.h5io import get_dsets
from nucleon_elastic_ff.data.scripts.h5migrate import dset_migrate as h5migrate
import lattedb_ff_disk_tape_functions as lattedb_ff
import collect_corr_utils as collect_utils
# tape utils from Evan's hpss module
import hpss.hsi as hsi
# MDWF on HISQ info
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
parser.add_argument('--corr',              type=str,default='all',help='corr type [res_phi, spec, formfac, hspec] [%(default)s]')
parser.add_argument('-m','--mq',           type=str,help='specify quark mass [default = all]')
parser.add_argument('-s','--src',          type=str,help='src [xXyYzZtT] None=All')
parser.add_argument('--src_set', nargs=3,  type=int,help='specify si sf ds')
parser.add_argument('-o',          default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('--move',      default=False,action='store_const',const=True,help='move bad files? [%(default)s]')
parser.add_argument('--update_db', default=False,action='store_const',const=True,help='update db without collection? [%(default)s]')
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
tmp_data_dir = c51.tmp_data_dir % params
utils.ensure_dirExists(tmp_data_dir)
bad_date_data_dir = (c51.data_dir % params).replace('/data','/bad_time_stamp_data')
utils.ensure_dirExists(bad_date_data_dir)

tape_dir = c51.tape+'/'+ens_s+'/data'

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
src_set = "%d-%d" %(params['si'],params['sf'])
params['SRC_SET'] = src_set
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

if args.corr == 'all':
    corrs = ['res_phi_ll','spec','ff']
    if params['run_strange']:
        corrs += ['res_phi_ss','h_spec']
else:
    corrs = [args.corr]

print('MINING',corrs)
print('ens_stream = ',ens_s)
print('srcs:',src_set)
print('data dir',data_dir)

#all_res_phi_tape = TapeCorrelatorH5Dset.objects.filter(meta__corr='res_phi',meta__ensemble=,meta__stream=,meta__source_set=)

meta_entries = dict()
tape_entries = dict()
disk_entries = dict()

for corr in corrs:
    meta_entries[corr] = lattedb_ff.get_or_create_meta_entries(corr, cfgs_run, ens, stream, src_set, srcs)
    tape_entries[corr] = lattedb_ff.get_or_create_tape_entries(meta_entries[corr],\
        name=ens_s+'_%(CFG)s_srcs'+src_set+'.h5', path=data_dir, machine=c51.machine)
    disk_entries[corr] = lattedb_ff.get_or_create_disk_entries(meta_entries[corr],\
        name=ens_s+'_%(CFG)s_srcs'+src_set+'.h5', path=tape_dir, machine=c51.machine)

for cfg in cfgs_run:
    no = str(cfg)
    print(no)
    params['CFG']         = no
    params['srcs']        = srcs[cfg]
    params = c51.ensemble(params)
    params['mres_path']   = val_p+'/dwf_jmu'
    params['phi_qq_path'] = val_p+'/phi_qq'

    db_filter = {'configuration':cfg, 'source_set':src_set}

    # check if corrs are on tape
    on_tape = True
    for corr in corrs:
        if not lattedb_ff.querry_corr_disk_tape(meta_entries, corr, db_filter, dt='tape'):
            on_tape = False

    # if data is not saved to tape, or user specifies overwrite - check files and collect
    if not on_tape or (on_tape and args.o):
        # first - try and get dset info from h5 files
        # get dict for tape and disk files
        tape_dict = lattedb_ff.check_tape(tape_dir, ens_s+'_'+no+'_srcs'+src_set+'.h5')
        disk_dict = lattedb_ff.check_disk(data_dir, ens_s+'_'+no+'_srcs'+src_set+'.h5')
        # if tape_file exists, make sure disk_file has same time stamp, or pull from tape
        tape_file = tape_dir+'/'+ens_s+'_'+no+'_srcs'+src_set+'.h5'
        h5_full= data_dir    +'/'+ens_s+'_'+no+'_srcs'+src_set+'.h5'
        h5_tmp = tmp_data_dir+'/'+ens_s+'_'+no+'_srcs'+src_set+'.h5'
        if tape_dict['exists']:
            if disk_dict['exists']:
                if tape_dict['date_modified'] != disk_dict['date_modified']:
                    if args.v:
                        print('TAPE and DISK times do not match')
                        print(h5_full)
                        print('  h5migrate from disk to tmp_disk, then pull from tape\n')
                    # copy data_file to tmp_data_file
                    # get file from tape
                    if not os.path.exists(h5_tmp):
                        os.system('touch '+h5_tmp)
                    h5migrate(h5_full, h5_tmp, atol=0.0, rtol=1e-10)
                    # use get which overwrites disk file with tape file
                    # shutil.move(h5_full, bad_date_data_dir+'/'+h5_full.split('/')[-1])
                    hsi.cget(data_dir, tape_file, preserve_time=True)
            else:# disk not exists -> pull from tape with cget
                if args.v:
                    print('FILE EXISTS on tape but not on disk - pulling from tape\n')
                    print(h5_full+'\n')
                hsi.cget(data_dir, tape_file)
        # now check dsets in tmp and full and tmp h5 files
        if disk_dict['exists']:
            with h5py.File(h5_full,'r') as f5_full:
                dsets_full = get_dsets(f5_full, load_dsets=False)
        else:
            dsets_full = dict()
            if args.v:
                print('DOES NOT EXIST: %s' %h5_full)
        if os.path.exists(h5_tmp):
            with h5py.File(h5_tmp,'r') as f5_tmp:
                dsets_tmp  = get_dsets(f5_tmp, load_dsets=False)
        else:
            dsets_tmp = dict()
        # if disk entries do not exist - collect data and migrate
        h5_migrate = False
        params['h5_spec_path'] = val_p+'/spec'
        for corr in corrs:
            if not lattedb_ff.querry_corr_disk_tape(meta_entries, corr, db_filter, dt='disk'):
                params['corr'] = corr
                if 'res_phi' in corr:
                    if not collect_utils.get_res_phi(params,dsets_full):
                        if collect_utils.get_res_phi(params, dsets_tmp, h5_file=h5_tmp, collect=True):
                            h5_migrate = True
                elif 'spec' in corr:
                    if not collect_utils.get_spec(params, dsets_full):
                        if collect_utils.get_spec(params, dsets_tmp, h5_file=h5_tmp, collect=True):
                            h5_migrate = True
                elif 'ff' == corr:
                    print('skipping formfac - need to add get_formfac function to collect_corr_utils')
        if h5_migrate:
            if not os.path.exists(h5_full):
                os.system('touch '+h5_full)
            h5migrate(h5_tmp, h5_full, atol=0.0, rtol=1e-10)
            # load updated dsets on disk
            with h5py.File(h5_full,'r') as f5_full:
                dsets_updated = get_dsets(f5_full, load_dsets=False)
        if h5_migrate or args.update_db:
            # update disk_db
            print('add update db function')
            # push to tape

            # if successful, updated tape_db
