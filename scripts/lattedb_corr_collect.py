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
from nucleon_elastic_ff.data.scripts.h5migrate import dset_migrate as h5_dset_migrate
import lattedb_ff_disk_tape_functions as lattedb_ff
import collect_corr_utils as collect_utils
from lattedb.project.formfac.models.data.correlator import (
    CorrelatorMeta,
    DiskCorrelatorH5Dset,
    TapeCorrelatorH5Dset
)
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
parser.add_argument('cfgs',        nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('--corr',      nargs='+',type=str,default=['all'],help='corr type [mres_ll, phi_ll, spec, formfac, mres_ss, phi_ss, hspec] [%(default)s]')
parser.add_argument('-m','--mq',             type=str,help='specify quark mass [default = all]')
parser.add_argument('-s','--src',            type=str,help='src [xXyYzZtT] None=All')
parser.add_argument('--src_set',   nargs=3,  type=int,help='specify si sf ds')
parser.add_argument('-t','--t_sep',nargs='+',type=int,help='value of t_sep [default = all]')
parser.add_argument('-a','--atol',     default=0.0  , help='specify absolute tolerance for comparing h5 files [%(default)s]')
parser.add_argument('-r','--rtol',     default=1e-10, help='specify relative tolerance for comparing h5 files [%(default)s]')
parser.add_argument('-o',              default=False,action='store_true', help='overwrite? [%(default)s]')
parser.add_argument('--move',          default=False,action='store_true', help='move bad files? [%(default)s]')
parser.add_argument('tmp_sync',        default=False,action='store_true', help='force sync to tmp_data? [%(default)s]')
parser.add_argument('-u','--update_db',default=False,action='store_true', help='update db without collection? [%(default)s]')
parser.add_argument('-v',              default=False,action='store_true', help='verbose? [%(default)s]')
parser.add_argument('-d','--debug',    default=False,action='store_true', help='debug? [%(default)s]')
parser.add_argument('--delete',        default=False,action='store_true', help='delete entries? [%(default)s]')
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
if args.delete and len(cfgs_run) > 1:
    sys.exit('you can only delete entries for one config at a time')

src_set = "%d-%d" %(params['si'],params['sf'])
params['SRC_SET'] = src_set
smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
val_p = val.replace('.','p')

# modify logging info and location
import logging
from nucleon_elastic_ff.utilities import set_up_logger
LOGGER = set_up_logger("nucleon_elastic_ff") # get the logger for the module
fh = [h for h in LOGGER.handlers if isinstance(h, logging.FileHandler)][0] # get the file logger
LOGGER.removeHandler(fh) # remove the file logger
new_fh = logging.FileHandler(c51.scratch+'/production/'+ens_s+'/lattedb_corr_'+ens_s+'_Srcs'+src_set+'.log')
new_fh.setLevel(logging.INFO)
new_fh.setFormatter(fh.formatter)
LOGGER.addHandler(new_fh)

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

if args.t_sep == None:
    pass
else:
    for t in args.t_sep:
        if t not in params['t_seps']:
            sys.exit('you asked for a t_sep value not in area51 file: %d' %t)
    params['t_seps'] = args.t_sep

if args.corr == ['all']:
    corrs = ['mres_ll','phi_ll','spec']
    for dt in params['t_seps']:
        corrs.append('ff_tsep_'+str(dt))
    if params['run_strange']:
        corrs += ['mres_ss','phi_ss','h_spec']
elif 'ff' in args.corr:
    corrs = [c for c in args.corr if c != 'ff']
    for dt in params['t_seps']:
        corrs.append('ff_tsep_'+str(dt))
else:
    corrs = args.corr

print('MINING',corrs)
print('ens_stream = ',ens_s)
print('srcs:',src_set)
print('data dir',data_dir)

meta_entries = dict()
tape_entries = dict()
disk_entries = dict()

for corr in corrs:
    print('checking lattedb entries [meta, tape, disk] for %s' %corr)
    print(corr,': meta')
    meta_entries[corr] = lattedb_ff.get_or_create_meta_entries(corr, cfgs_run, ens, stream, src_set, srcs)
    print(corr,': tape')
    tape_entries[corr] = lattedb_ff.get_or_create_tape_entries(
        meta_entries = meta_entries[corr],
        tape_entries = TapeCorrelatorH5Dset, 
        path         = tape_dir, 
        machine      = c51.machine, 
        name         = ens_s+'_%(CFG)s_srcs'+src_set+'.h5')
    print(corr,': disk')
    disk_entries[corr] = lattedb_ff.get_or_create_disk_entries(
        meta_entries = meta_entries[corr],
        disk_entries = DiskCorrelatorH5Dset, 
        path         = data_dir, 
        machine      = c51.machine, 
        name         = ens_s+'_%(CFG)s_srcs'+src_set+'.h5')

if args.delete:
    for corr in corrs:
        lattedb_ff.del_corr_entries(corr, cfgs_run, ens, stream, src_set, srcs)
    sys.exit()


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
        h5_file_name = ens_s+'_'+no+'_srcs'+src_set+'.h5'
        tape_file    = tape_dir +'/'+ h5_file_name
        h5_full      = data_dir +'/'+ h5_file_name
        h5_tmp       = tmp_data_dir +'/'+ h5_file_name

        # synchronize files from tape to disk if need be
        lattedb_ff.sync_h5_data_files(tape_file, h5_full, h5_tmp, atol=args.atol, rtol=args.rtol, verbose=args.v)
        d_dict = lattedb_ff.check_disk(data_dir, h5_file_name)

        # if user wants to force tmp_disk sync, sync from tmp_disk to disk
        if args.tmp_sync:
            tmp_dict = lattedb_ff.check_disk(tmp_data_dir, h5_file_name)
            if d_dict['exists'] and tmp_dict['exists'] and \
               ((d_dict['date_modified'] != tmp_dict['date_modified']) or (d_dict['size'] != tmp_dict['size'])):
                h5_dset_migrate(h5_tmp, h5_full)
        
        # now check dsets in tmp and full and tmp h5 files
        if d_dict['exists']:
            with h5py.File(h5_full,'r') as f5_full:
                dsets_full = get_dsets(f5_full, load_dsets=False)
        else:
            dsets_full = dict()
        # if disk entries do not exist - collect data and migrate
        migrate_h5_data = False
        params['h5_spec_path'] = val_p+'/spec'
        params['ff_path'] = val_p+'/formfac'
        for corr in corrs:
            if not lattedb_ff.querry_corr_disk_tape(meta_entries, corr, db_filter, dt='disk', debug=args.debug):
                params['corr'] = corr
                if 'mres' in corr or 'phi' in corr:
                    if collect_utils.get_res_phi(params, dsets_full, h5_file=h5_full, collect=True):
                        migrate_h5_data=True
                elif 'spec' in corr:
                    if collect_utils.get_spec(params, dsets_full, h5_file=h5_full, collect=True):
                        migrate_h5_data=True
                elif 'ff' in corr:
                    for tsep in params['t_seps']:
                        params['corr'] = 'ff_tsep_'+str(tsep)
                        params['T_SEP'] = tsep
                        if collect_utils.get_formfac(params, dsets_full, h5_file=h5_full, collect=True):
                            migrate_h5_data = True
        if migrate_h5_data:
            t_dict = lattedb_ff.check_tape(tape_dir, h5_file_name)
            d_dict = lattedb_ff.check_disk(data_dir, h5_file_name)
            if d_dict['exists']:
                if not t_dict['exists']:
                    hsi.cput(h5_full, tape_file)
                else:
                    if d_dict['date_modified'] > t_dict['date_modified']:
                        hsi.cput(h5_full, tape_file)
                    elif t_dict['date_modified'] > d_dict['date_modified']:
                        sys.exit('ERROR - we collected data but tape file is newer than disk file')
                    else:
                        print('tape and disk time stamps match',d_dict['date_modified'], h5_full)
        if migrate_h5_data or args.update_db:
            # load updated dsets on disk
            if os.path.exists(h5_full):
                with h5py.File(h5_full,'r') as f5_full:
                    dsets_update = get_dsets(f5_full, load_dsets=False)
            else:
                dsets_update = {}
            # update disk_db
            disk_updates = []
            tape_updates = []
            for corr in corrs:
                db_filter.update({'correlator':corr})
                params_tmp = dict(params)
                update_entries = [e for e in meta_entries[corr].filter(**db_filter) if (e.disk.exists == False or e.tape.exists == False)]
                for ff in update_entries:
                    if args.debug:
                        print('DEBUG: exist from meta_read',ff.tape.exists)
                    params_tmp['corr'] = ff.correlator
                    params_tmp['srcs'] = [ff.source]
                    params_tmp['SRC']  = ff.source
                    dd = lattedb_ff.check_disk(data_dir,h5_file_name)
                    if 'size' in dd:# we don't track the size for these files now
                        del dd['size']
                    dd['name'] = h5_file_name
                    updates = False
                    if 'mres' in params_tmp['corr'] or 'phi' in params_tmp['corr']:
                        dd['dset'] = collect_utils.res_phi_dset(params_tmp,full_path=True)
                        if collect_utils.get_res_phi(params_tmp, dsets_update):
                            updates = True
                    if corr in ['spec','h_spec']:
                        dd['dset'] = collect_utils.spec_dset(params_tmp, params_tmp['corr'], full_path=True)
                        if collect_utils.get_spec(params_tmp, dsets_update):
                            updates = True
                    if 'ff' in corr:
                        dd['dset'] = collect_utils.ff_dset(params_tmp, full_path=True)
                        if collect_utils.get_formfac(params_tmp, dsets_update):
                            updates = True
                    if updates:
                        if not ff.disk.exists:
                            disk_updates.append((ff, dd))
                        if not ff.tape.exists:
                            tt = dict(dd)
                            tt['path'] = tape_dir
                            tape_updates.append((ff, tt))
                #print(meta_entries[corr].filter(**db_filter).disk.to_dataframe())
            print('updating DISK entries %d' %(len(disk_updates)))
            if len(disk_updates) > 0:
                lattedb_ff.corr_disk_tape_update(disk_updates,dt='disk', debug=args.debug)
            # push to tape
            try:
                print('updating TAPE entries %d' %(len(tape_updates)))
                if len(tape_updates) > 0:
                    lattedb_ff.corr_disk_tape_update(tape_updates, dt='tape',debug=args.debug)
            except Exception as e:
                print(e)
