from __future__ import print_function
from __future__ import print_function
import os, sys, argparse
import numpy as np
np.set_printoptions(linewidth=180)
import tables as h5
import warnings
warnings.simplefilter('ignore', h5.NaturalNameWarning)
from glob import glob
from datetime import datetime
import pytz
from tzlocal import get_localzone
local_tz = get_localzone()
from django.db.models import Q
from tqdm import tqdm
# tape utils from Evan's hpss module
import hpss.hsi as hsi

script = sys.argv[0].split('/')[-1]

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
parser.add_argument('cfgs',          nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('--f_type',      type=str,default='all',help='what data type to average [formfac (soon to come spec)]?')
parser.add_argument('-t','--t_sep',  nargs='+',type=int,help='values of t_sep [default = all]')
parser.add_argument('-c','--current',type=str,nargs='+',help='pick a specific current or currents? [A3 V4 ...]')
parser.add_argument('--src_set',     nargs=3,type=int,help='specify si sf ds')
parser.add_argument('-v',            default=True ,action='store_const',const=False,help='verbose? [%(default)s]')
parser.add_argument('--collect',     default=True ,action='store_const',const=False,help='collect data? [%(default)s]')
parser.add_argument('--update',      default=False,action='store_const',const=True ,help='update disk and tape entries? [%(default)s]')
parser.add_argument('--disk_update', default=True ,action='store_const',const=False,help='update disk=exists entries? [%(default)s]')
parser.add_argument('--tape_update', default=True ,action='store_const',const=False,help='update tape=exists entries? [%(default)s]')
parser.add_argument('--tape_get'   , default=False,action='store_const',const=True ,help='retrieve from tape? [%(default)s]')
parser.add_argument('--save_tape',   default=True ,action='store_const',const=False,help='save files to tape? [%(default)s]')
parser.add_argument('--debug',       default=False,action='store_const',const=True ,help='debug? [%(default)s]')
parser.add_argument('--data',        default=True ,action='store_const',const=False,help='collect missing data? [%(default)s]')
parser.add_argument('--bad_size',    default=False,action='store_const',const=True, help='exit if bad file size encountered? [%(default)s]')
parser.add_argument('--delete',      default=False,action='store_const',const=True,help='delete entries? [%(default)s]')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

#
params['TAPE_GET']    = args.tape_get
params['UPDATE']      = args.update
params['DISK_UPDATE'] = args.disk_update
params['TAPE_UPDATE'] = args.tape_update
if args.bad_size:
    params['bad_size'] = '--bad_size'
else:
    params['bad_size'] = ''

# LATTEDB imports

if args.f_type == 'formfac':
    f_type = 'formfac_4D_tslice_src_avg'
elif args.f_type == 'spec':
    f_type = 'spec_4D_tslice_avg'
elif args.f_type == 'all':
    f_type = 'all'
else:
    sys.exit('you forgot to specify what type of data to collect, spec or formfac')
import lattedb_ff_disk_tape_functions as lattedb_ff
from lattedb.project.formfac.models import (
    TSlicedSAveragedFormFactor4DFile,
    DiskTSlicedSAveragedFormFactor4DFile,
    TapeTSlicedSAveragedFormFactor4DFile,
    TSlicedFormFactor4DFile,
    DiskTSlicedFormFactor4DFile,
    FormFactor4DFile,
    DiskFormFactor4DFile,
    TSlicedSAveragedSpectrum4DFile,
    TapeTSlicedSAveragedSpectrum4DFile,
    DiskTSlicedSAveragedSpectrum4DFile,
    TSlicedSpectrum4DFile,
    DiskTSlicedSpectrum4DFile,
)

# CREATE CONFIG AND SRC LISTS
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
src_set = "%d-%d" %(params['si'],params['sf'])
params['SRC_SET'] = src_set

# modify logging info and location
import logging
from nucleon_elastic_ff.utilities import set_up_logger
LOGGER = set_up_logger("nucleon_elastic_ff") # get the logger for the module
fh = [h for h in LOGGER.handlers if isinstance(h, logging.FileHandler)][0] # get the file logger
LOGGER.removeHandler(fh) # remove the file logger
new_fh = logging.FileHandler(c51.scratch+'/production/'+ens_s+'/lattedb_4D_'+ens_s+'_Srcs'+src_set+'.log')
new_fh.setLevel(logging.INFO)
new_fh.setFormatter(fh.formatter)
LOGGER.addHandler(new_fh)

# give empty '' to in place of args.src to generate all srcs/cfg
cfgs,srcs = utils.parse_cfg_src_argument(args.cfgs,'',params)
if args.delete and len(cfgs) > 1:
    sys.exit('you can only delete entries for one config at a time')

cfgs_set = "%d-%d" %(cfgs[0],cfgs[-1])
if 'indvdl' in ens:
    params['N_SEQ'] = 1
else:
    params['N_SEQ'] = len(srcs[cfgs[0]])

if args.t_sep != None:
    params['t_seps'] = args.t_sep
if args.current != None:
    params['curr_4d'] = args.current

# DEFINE PARAMS USED for file names
smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
val_p = val.replace('.','p')

mv_l = params['MV_L']
params['MQ'] = mv_l

flav_spin = []
for flav in params['flavs']:
    for spin in params['spins']:
        flav_spin.append(flav+'_'+spin)
''' ONLY doing snk_mom 0 0 0 now '''
snk_mom = params['snk_mom'][0]
m0,m1,m2 = snk_mom.split()
params['M0']=m0
params['M1']=m1
params['M2']=m2
params['MOM'] = 'px%spy%spz%s' %(m0,m1,m2)

print('STATUS CHECK: %s    cfgs=%s    srcs=%s    %s\n' %(ens_s, cfgs_set, src_set, f_type))

meta_entries = dict()
tape_entries = dict()
disk_entries = dict()

print('checking lattedb entries for %s' %f_type)
if f_type in ['formfac_4D_tslice_src_avg', 'all']:
    if args.delete:
        delete_ff4D_avg(ens, stream, src_set, params['t_seps'], cfgs)
        sys.exit()
    fs_type = 'formfac_4D_tslice_src_avg'
    meta_entries[fs_type] = lattedb_ff.get_or_create_ff4D_tsliced_savg(params, cfgs, ens, stream, src_set)
    disk_dir = c51.base_dir+'/'+fs_type+'/%(CFG)s'
    tape_dir = c51.tape+'/'+ens_s+'/'+fs_type+'/%(CFG)s'

    disk_entries[fs_type] = lattedb_ff.get_or_create_disk_entries(
        meta_entries = meta_entries[fs_type],
        disk_entries = DiskTSlicedSAveragedFormFactor4DFile, 
        path         = disk_dir, 
        machine      = c51.machine
    )
    tape_entries[fs_type] = lattedb_ff.get_or_create_tape_entries(
        meta_entries = meta_entries[fs_type],
        tape_entries = TapeTSlicedSAveragedFormFactor4DFile, 
        path         = tape_dir, 
        machine      = c51.machine
    )

if f_type in ['spec_4D_tslice_avg', 'all']:
    if args.delete:
        delete_spec4D_avg(ens, stream, src_set, cfgs)
        sys.exit()
    fs_type = 'spec_4D_tslice_avg'
    meta_entries[fs_type] = lattedb_ff.get_or_create_spec4D_tsliced_savg(params, cfgs, ens, stream, src_set)
    disk_dir = c51.base_dir+'/'+fs_type+'/%(CFG)s'
    tape_dir = c51.tape+'/'+ens_s+'/'+fs_type+'/%(CFG)s'

    disk_entries[fs_type] = lattedb_ff.get_or_create_disk_entries(
        meta_entries = meta_entries[fs_type],
        disk_entries = DiskTSlicedSAveragedSpectrum4DFile, 
        path         = disk_dir, 
        machine      = c51.machine
    )
    tape_entries[fs_type] = lattedb_ff.get_or_create_tape_entries(
        meta_entries = meta_entries[fs_type],
        tape_entries = TapeTSlicedSAveragedSpectrum4DFile, 
        path         = tape_dir, 
        machine      = c51.machine
    )

# loop over cfgs and try and collect and report missing
missing_spec_4D = []
missing_ff_4D   = []
if args.collect:
    for cfg in cfgs:
        no = str(cfg)
        params['CFG'] = no
        params = c51.ensemble(params)
        params['SOURCES'] = srcs[cfg]
        if f_type in ['spec_4D_tslice_avg', 'all']:
            lattedb_ff.collect_spec_ff_4D_tslice_src_avg('spec', params, meta_entries['spec_4D_tslice_avg'])

        if f_type in ['formfac_4D_tslice_src_avg', 'all']:
            for dt in params['t_seps']:
                params['T_SEP'] = str(dt)
                lattedb_ff.collect_spec_ff_4D_tslice_src_avg('formfac', params, meta_entries['formfac_4D_tslice_src_avg'])
    fs_type = 'formfac_4D_tslice_src_avg'
    meta_entries[fs_type] = lattedb_ff.get_or_create_ff4D_tsliced_savg(params, cfgs, ens, stream, src_set)
    fs_type = 'spec_4D_tslice_avg'
    meta_entries[fs_type] = lattedb_ff.get_or_create_spec4D_tsliced_savg(params, cfgs, ens, stream, src_set)

for cfg in cfgs:
    no = str(cfg)
    params['CFG'] = no
    params = c51.ensemble(params)
    params['SOURCES'] = srcs[cfg]
    f_dict = dict()
    f_dict['ensemble']      = ens
    f_dict['stream']        = stream
    f_dict['configuration'] = cfg
    f_dict['source_set']    = params['SRC_SET']
    entries = meta_entries['spec_4D_tslice_avg'].filter(**f_dict)
    for entry in entries:
        if not entry.tape.exists:
            missing_spec_4D.append('spec_4D_tslice_avg/'+no+'/'+entry.name)
    for dt in params['t_seps']:
        params['T_SEP'] = str(dt)
        f_dict['t_separation'] = dt
        entries = meta_entries['formfac_4D_tslice_src_avg'].filter(**f_dict)
        for entry in entries:
            if not entry.tape.exists:
                missing_ff_4D.append('formfac_4D_tslice_src_avg/'+no+'/'+entry.name)

fs = open('missing_spec_4D_'+ens_s+'_Srcs'+src_set+'.lst','w')
for entry in missing_spec_4D:
    fs.write(entry+'\n')
fs.close()
ff = open('missing_ff_4D_'+ens_s+'_Srcs'+src_set+'.lst','w')
for entry in missing_ff_4D:
    ff.write(entry+'\n')
ff.close()
