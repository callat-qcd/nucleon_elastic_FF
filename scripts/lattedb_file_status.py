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
parser.add_argument('f_type',type=str,help='what data type to average [formfac_4D_tslice_src_avg formfac_4D_tslice ...]?')
parser.add_argument('--cfgs',nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('-t','--t_sep',nargs='+',type=int,help='values of t_sep [default = all]')
parser.add_argument('-c','--current',type=str,nargs='+',help='pick a specific current or currents? [A3 V4 ...]')
parser.add_argument('-v',default=True,action='store_const',const=False,help='verbose? [%(default)s]')
parser.add_argument('--src_set',nargs=3,type=int,help='specify si sf ds')
parser.add_argument('--update',default=False,action='store_const',const=True,help='update disk and tape entries? [%(default)s]')
parser.add_argument('--disk_update',default=False,action='store_const',const=True,help='update disk=exists entries? [%(default)s]')
parser.add_argument('--tape_update',default=True,action='store_const',const=False,help='update tape=exists entries? [%(default)s]')
parser.add_argument('--save_tape',default=True,action='store_const',const=False,help='save files to tape? [%(default)s]')
parser.add_argument('--debug',default=False,action='store_const',const=True,help='debug? [%(default)s]')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

tape_lst = ['formfac_4D_tslice_src_avg','spec_4D_tslice','spec_4D_tslice_avg']

# LATTEDB imports
f_type = args.f_type
import lattedb_ff_disk_tape_functions as lattedb_ff
if f_type == 'formfac_4D_tslice_src_avg':
    from lattedb.project.formfac.models import TSlicedSAveragedFormFactor4DFile     as latte_file
    from lattedb.project.formfac.models import DiskTSlicedSAveragedFormFactor4DFile as latte_disk
    from lattedb.project.formfac.models import TapeTSlicedSAveragedFormFactor4DFile as latte_tape
elif f_type in ['prop','seqprop','spec','spec_4D','spec_4D_tslice','spec_4D_tslice_avg','formfac_4D','formfac_4D_tslice']:
    sys.exit('not yet supported file type: '+str(f_type))
else:
    sys.exit('unrecognized file type: '+str(f_type))

src_type = f_type in ['prop','spec','spec_4D','spec_4D_tslice','formfac_4D','formfac_4D_tslice']


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

# give empty '' to in place of args.src to generate all srcs/cfg
cfgs,srcs = utils.parse_cfg_src_argument(args.cfgs,'',params)
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

# QUERRY DB
db_entries = latte_file.objects.filter(
    ensemble = ens,
    stream   = stream,
    source_set = src_set,
    configuration__in=cfgs
    ).prefetch_related('disk').prefetch_related('tape')

if args.debug:
    print(db_entries.to_dataframe(fieldnames=['ensemble','stream','configuration','source_set','t_separation','name','last_modified']))

# search tape
def check_tape(t_path,t_file):
    t_dict = dict()
    t_dict['machine'] = c51.machine
    check = os.popen('hsi -P ls -l -D %s' %(t_path+'/'+t_file)).read().split('\n')
    #On Summit, the first line from hsi returns the directory one is looking at
    # the "-D" option in ls gives the full date/time information
    if check[0] == t_path+':':
        t_dict['path']          = t_path
        t_dict['exists']        = True
        t_dict['size']          = int(check[1].split()[4])
        local_time = datetime.strptime(" ".join(check[1].split()[5:10]),"%a %b %d %H:%M:%S %Y")
        if c51.machine == 'summit':
            timezone = pytz.timezone("US/Eastern")
        elif c51.machine == 'lassen':
            timezone = pytz.timezone("US/Pacific")
        else:
            sys.exit('ADD TIME ZONE FOR YOUR MACHINE!')
        t_dict['date_modified'] = timezone.localize(local_time)
    else:
        t_dict['exists'] = False
    return t_dict

def check_disk(d_path,d_file):
    d_dict = dict()
    d_dict['path'] = d_path
    d_dict['machine'] =  c51.machine
    if os.path.exists(d_path+'/'+d_file):
        d_dict['exists'] = True
        d_dict['size']   = os.path.getsize(d_path+'/'+d_file)
        utc = datetime.utcfromtimestamp(os.path.getmtime(d_path+'/'+d_file))
        local_time = utc.replace(tzinfo=pytz.utc).astimezone(local_tz)
        d_dict['date_modified'] = local_time
    else:
        d_dict['exists']        = False
        d_dict['size']          = None
        d_dict['date_modified'] = None
    return d_dict

# LOOP OVER FILES to check
print('checking database entries')
db_update_disk = []
db_new_disk    = []
db_update_tape = []
db_new_tape    = []
db_new_entry   = []
save_to_tape   = []
data_collect   = []

if args.disk_update:
    disk_entries = db_entries.all()
else:
    disk_entries = db_entries.filter(Q(disk__exists=False) | Q(disk__isnull=True))
if args.tape_update:
    tape_entries = db_entries.all()
else:
    tape_entries = db_entries.filter(Q(tape__exists=False) | Q(tape__isnull=True))

for cfg in cfgs:
    sys.stdout.write('    cfg = %d\r' %cfg)
    sys.stdout.flush()
    no = str(cfg)
    params['CFG'] = no
    params = c51.ensemble(params)
    params['RUN_DIR'] = params['prod']
    disk_dir = params[f_type]
    params['TAPE_DIR'] = c51.tape+'/'+ens_s+'/'+f_type+'/'+no
    params['UPDATE'] = args.update
    params['DISK_UPDATE'] = args.disk_update
    params['TAPE_UPDATE'] = args.tape_update
    # if the type of file we are checking has srcs (not src_averaged), then add this info
    if src_type:
        for s0 in srcs[cfg]:
            src = s0
            # complete this logic chain
    else:# src averaged file types
        params['SRC'] = 'src_avg'+src_set
        if args.debug:
            print('\nDEBUG:',disk_dir)
        if f_type == 'formfac_4D_tslice_src_avg':
            lattedb_ff.check_ff_4D_tslice_src_avg(params, db_entries, 
                db_update_disk, db_new_disk, db_update_tape, db_new_tape, db_new_entry, save_to_tape, data_collect)

# bulk create all completely new entries
print(db_new_entry)
try:
    print('pushing %d new entries' %len(db_new_entry))
    all_f = []
    all_d = []
    all_t = []
    for ff,dd,tt in db_new_entry:
        f = latte_file(**ff)
        all_f.append(f)
    print('  pushing file entries')
    latte_file.objects.bulk_create(all_f)
    for i,f in enumerate(all_f):
        d = latte_disk(file=f,**db_new_entry[i][1])
        all_d.append(d)
        t = latte_tape(file=f,**db_new_entry[i][2])
        all_t.append(t)
    print('  pushing disk entries')
    latte_disk.objects.bulk_create(all_d)
    print('  pushing tape entries')
    latte_tape.objects.bulk_create(all_t)
except Exception as e:
    print('you messed up')
    print(e)

# bulk tape entries for pre-existing file entries
try:
    print('pushing %d new TAPE entries for existing file entries' %len(db_new_tape))
    tape_push = []
    for tt in db_new_tape:
        tape_push.append(latte_tape(**tt))
    latte_tape.objects.bulk_create(tape_push)
except Exception as e:
    print(e)
    print('you messed up bulk TAPE create')

# bulk tape entries for pre-existing file entries
try:
    print('pushing %d new DISK entries for existing file entries' %len(db_new_disk))
    disk_push = []
    for dd in db_new_disk:
        disk_push.append(latte_disk(**dd))
    latte_disk.objects.bulk_create(disk_push)
except Exception as e:
    print(e)
    print('you messed up bulk DISK create')

# bulk update disk
print('updating %d DISK entries for existing file entries' %len(db_update_disk))
if len(db_update_disk) > 0:
    disk_push = []
    for ff,dd in tqdm(db_update_disk):
        # this is slow cause we querry the DB for each entry
        f = db_entries.filter(**ff).first()
        d = f.disk
        for k,v in dd.items():
            setattr(d,k,v)
        disk_push.append(d)
    latte_disk.objects.bulk_update(disk_push,fields=list(dd.keys()))

# bulk update tape
print('updating %d TAPE entries for existing file entries' %len(db_update_tape))
if len(db_update_tape) > 0:
    tape_push = []
    for ff,tt in tqdm(db_update_tape):
        # this is slow cause we querry the DB for each entry
        f = db_entries.filter(**ff).first()
        t = f.tape
        for k,v in tt.items():
            setattr(t,k,v)
        tape_push.append(t)
    latte_tape.objects.bulk_update(tape_push,fields=list(tt.keys()))

# save to tape
if args.save_tape:
    print('saving %d files to tape' %(len(save_to_tape)))
    for f in save_to_tape:
        #os.chdir(f[1])
        #os.system('hsi -P "mkdir -p %s; chmod ug+rwx %s"' %(f[2],f[2]))
        #os.system('hsi -P "cd %s; cput %s"' %(f[2],f[0]))
        #os.system('hsi -P chmod ug+rw %s' %(f[2]+'/'+f[0]))
        hsi.cput(f[1]+'/'+f[0],f[2]+'/'+f[0])
else:
    print('skipping %d files to save to tape' %(len(save_to_tape)))

# collect data
print('data collect')
for f in data_collect:
    print(f)

