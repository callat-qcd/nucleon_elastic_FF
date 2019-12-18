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
parser.add_argument('--disk_update',default=False,action='store_const',const=True,help='update disk=exists entries? [%(default)s]')
parser.add_argument('--tape_update',default=False,action='store_const',const=True,help='update tape=exists entries? [%(default)s]')
parser.add_argument('--debug',default=False,action='store_const',const=True,help='debug? [%(default)s]')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

tape_lst = ['formfac_4D_tslice_src_avg','spec_4D_tslice','spec_4D_tslice_avg']

f_type = args.f_type
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
def check_tape(t_path,t_file,t_dict):
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
    

# LOOP OVER FILES to check
print('checking database entries')
db_exists_disk  = []
db_nexists_disk = []
db_exists_tape  = []
db_nexists_tape = []

if args.disk_update:
    disk_entries = db_entries.all()
else:
    disk_entries = db_entries.filter(Q(disk__exists=False) | Q(disk__isnull=True))
if args.tape_update:
    tape_entries = db_entries.all()
else:
    tape_entries = db_entries.filter(Q(tape__exists=False) | Q(tape__isnull=True))

for cfg in cfgs:
    sys.stdout.write('    cfg = %d' %cfg)
    sys.stdout.flush()
    no = str(cfg)
    params['CFG'] = no
    params = c51.ensemble(params)
    params['RUN_DIR'] = params['prod']
    data_dir = params[f_type]
    # if the type of file we are checking has srcs (not src_averaged), then add this info
    if src_type:
        for s0 in srcs[cfg]:
            src = s0
            # complete this logic chain
    else:# src averaged file types
        params['SRC'] = 'src_avg'+src_set
        if args.debug:
            print('\nDEBUG:',data_dir)        
        f_dict = dict()
        f_dict['ensemble']      = ens
        f_dict['stream']        = stream        
        f_dict['configuration'] = cfg
        f_dict['source_set']    = src_set
        if 'formfac' in f_type:
            for tsep in params['t_seps']:
                dt = str(tsep)
                params['T_SEP'] = dt
                f_name = (c51.names['formfac'] % params).replace('formfac_','formfac_4D_tslice_src_avg_')+'.h5'
                f_dict['t_separation'] = tsep
                f_dict['name']         = f_name
                t_dict = dict()
                t_dict['machine']      = c51.machine
                print('BEFORE')
                for k in t_dict:
                    print(k,t_dict[k])
                print('AFTER')
                t_dict = check_tape(c51.tape+'/'+ens_s+'/'+f_type+'/'+no,f_name,t_dict)
                for k in t_dict:
                    print(k,t_dict[k])
                    if k == 'date_modified':
                        print(k,t_dict[k].astimezone(pytz.timezone("US/Pacific")))

'''
    OLD BELOW
'''
sys.exit()


print('querrying file system')
print('%11s %4s %5s %7s' %('ens_s','cfg','tsep','src_set'))
for cfg in cfgs:
    no = str(cfg)
    params['CFG'] = no
    ''' set up ensemble and make sure all dirs exist '''
    params = c51.ensemble(params)
    params['RUN_DIR'] = params['prod']
    ff_data_dir = params['formfac_4D_tslice']
    ff_data_dir = ff_data_dir.replace('tslice','tslice_src_avg')
    for tsep in params['t_seps']:
        dt = str(tsep)
        params['T_SEP'] = dt
        sys.stdout.write('%11s %4s %5s %7s\r' %(ens_s,no,dt,src_set))
        sys.stdout.flush()
        fout_name = ff_data_dir+'/formfac_4D_tslice_src_avg_'+ens_s+'_'+no+'_'+val+'_mq'+mv_l+'_'+params['MOM']+'_dt'+dt+'_Nsnk8_src_avg'+src_set+'_'+params['SS_PS']+'.h5'
        ff_file = fout_name.split('/')[-1]
        #print(os.path.exists(fout_name),fout_name)
        ff_dict = dict()
        ff_dict['name']          = ff_file
        ff_dict['ensemble']      = ens
        ff_dict['stream']        = stream
        ff_dict['configuration'] = cfg
        ff_dict['source_set']    = src_set
        ff_dict['t_separation']  = tsep
        #
        disk_dict = dict()
        disk_dict['path']                = ff_data_dir
        disk_dict['exists']              = os.path.exists(fout_name)
        disk_dict['machine']             = params['machine']
        if os.path.exists(fout_name):
            disk_dict['size']            = os.path.getsize(fout_name)
            utc = datetime.utcfromtimestamp(os.path.getmtime(fout_name))
            local_time = utc.replace(tzinfo=pytz.utc).astimezone(local_tz)
            disk_dict['date_modified']   = local_time
        else:
            disk_dict['size']            = None
            disk_dict['date_modified']   = None      
        # move this before looking on the file system
        # is this dictionary already in the db?
        if not disk_exist_db.filter(**ff_dict).exists():
            new_db_list.append((ff_dict,disk_dict))
        elif disk_tape_not_exist.filter(**ff_dict).exists():
            disk_tape_miss_list.append((ff_dict,disk_dict))

print('\nloading database')
print('pushing %d new entries' %(len(new_db_list)))

all_fs = []
all_ds = []
for ff,dd in new_db_list:
    f = TSlicedSAveragedFormFactor4DFile(**ff)
    all_fs.append(f)
TSlicedSAveragedFormFactor4DFile.objects.bulk_create(all_fs)
for i,f in enumerate(all_fs):
    d = DiskTSlicedSAveragedFormFactor4DFile(file=f,**new_db_list[i][1])
    all_ds.append(d)
DiskTSlicedSAveragedFormFactor4DFile.objects.bulk_create(all_ds)

if len(disk_tape_miss_list) > 0:
    print('updating %d existing entries' %(len(disk_tape_miss_list)))
    all_ds = []

    for ff,dd in tqdm(disk_tape_miss_list):
        #print(ff)
        f = disk_tape_not_exist.filter(**ff).first()
        # this is slow cause we are querrying for each ff,dd iteration
        d = f.disk.first()
        for k,v in dd.items():
            setattr(d,k,v)
        all_ds.append(d)
    DiskTSlicedSAveragedFormFactor4DFile.objects.bulk_update(all_ds,fields=list(dd.keys()))
else:
    print('nothing to update')
