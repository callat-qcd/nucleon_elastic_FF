import os, sys
from datetime import datetime
import pytz
from tzlocal import get_localzone
local_tz = get_localzone()
# c51 imports
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
import c51_mdwf_hisq as c51
# Evan's tape hpss module
import hpss.hsi as hsi

from typing import Union, List, Dict, Optional, TypeVar
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
from lattedb.project.formfac.models.data.correlator import (
    CorrelatorMeta,
    DiskCorrelatorH5Dset,
    TapeCorrelatorH5Dset
)

def corr_disk_tape_update(corr_updates,dt='disk',debug=False):
    dt_push = []
    for ff,dd in corr_updates:
        if dt == 'disk':
            d = ff.disk
        elif dt == 'tape':
            d = ff.tape
        for k,v in dd.items():
            if debug:
                if k == 'exists':
                    print('DEBUG:',dt,ff.correlator,ff.source,'BEFORE UPDATE: exists',getattr(d,k),'AFTER UPDATE: exists',v)
            setattr(d,k,v)
        dt_push.append(d)
        #if debug:
        #    print('DEBUG:',dt,ff.correlator,ff.source,{k:getattr(d,k) for k,v in dd.items()})
    if dt == 'disk':
        DiskCorrelatorH5Dset.objects.bulk_update(dt_push, fields=list(dd.keys()))
    elif dt == 'tape':
        TapeCorrelatorH5Dset.objects.bulk_update(dt_push, fields=list(dd.keys()))
    else:
        sys.exit('unrecognized dt type',dt)

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
        utc = datetime.utcfromtimestamp(os.path.getmtime(d_path+'/'+d_file)).replace(microsecond=0)
        local_time = utc.replace(tzinfo=pytz.utc).astimezone(local_tz)
        d_dict['date_modified'] = local_time
    else:
        d_dict['exists']        = False
        d_dict['size']          = None
        d_dict['date_modified'] = None
    return d_dict

def corr_compare_tape_disk(h5_file, tape_dir, disk_dir, tmp_disk_dir, d_sets, atol, rtol, tape_push=False):
    ''' We want to compare h5 data files on tape and disk to decide if we should update
        input: 
            h5_file       name of h5 file
            tape_dir      location on tape
            disk_dir      location of disk dir where files are pushed/pulled from tape
            tmp_disk_dir  location of temporary disk_dir where new data is collected
            d_sets        list of data sets to inquire of existence in file
            tape_push     push disk file to tape

        t_e = exists on tape or not
        d_e = exists on disk or not

        t_e  d_e  date   action
        --------------------------------------------------
        n    n    --     collect = true
        n    y    --     if data in disk: push to tape, collect = false
                         else: push to tape, collect = true
        y    n    --     pull, if data in file: collect = false
                               else: collect = true
        y    y    t=d    if data in disk: collect = true
                         else: collect = false
        y    y    t!=d   pull, h5_compare d_sets, equilibrate or raise exception
    '''
    t_dict     = check_tape(tape_dir, h5_file)
    d_dict     = check_disk(disk_dir, h5_file)
    tmp_d_dict = check_dist(tmp_disk_dir, h5_file)
    d_file     = disk_dir +'/'+ h5_file
    tmp_d_file = tmp_disk_dir +'/'+ h5_file
    collect    = False

    # do we need to synchronize disk and tmp_disk?
    if d_dict['exists'] or tmp_d_dict['exists']:
        sync_disk_files(tmp_disk_dir, h5_file, disk_dir, h5_file, atol, rtol)
        d_dict = check_disk(disk_dir, h5_file)
        if not t_dict['exists'] and tape_push:
            hsi.cput(d_file, tape_dir+'/'+h5_file)

    # if tape does not exist, see if disk files exist
    if not t_dict['exists']:
        if d_dict['exists']:
            check_disk = True
        else:
            check_disk = False
            collect = True
    # if tape does exist, we have to synchronize with disk files or pull
    else:
        check_disk = True
        if sync_disk:
            sync_tape_disk = True
        else:
            sync_tape_disk = False
            hsi.cget(disk_dir, tape_dir +'/'+ h5_file)

    # if sync_tape_disk, mv disk to tmp_disk since we just synchronized
    if sync_tape_disk:
        # get meta info on disk_file again
        d_dict = check_disk(disk_dir, h5_file)
        if d_dict['date_modified'] != t_dict['date_modified']:
            # move file to temp location and pull from tape
            shutil.move(d_file, tmp_d_file)
            hsi.cget(disk_dir, tape_dir +'/'+ h5_file)
            # then check if any data in tmp_disk is not in disk
            with h5py.File(d_disk,'r') as f5_disk:
                dsets_disk = get_dsets(f5_disk, load_dsets=False)
            with h5py.File(tmp_d_disk,'r') as f5_tmp_disk:
                dsets_tmp_disk = get_dsets(f5_tmp_disk, load_dsets=False)
            new_data = [dset for dset in dsets_tmp_disk if dset not in dsets_disk]
            # an empty list is false
            if new_data:
                try:
                    h5_dset_migrate(tmp_d_file, d_file, atol=atol, rtol=rtol)
                    # then store back to tape
                    hsi.cput(d_file, tape_dir +'/'+ h5_file)
                except Exception as e:
                    print(e)

    # check disk_dir/h5_file for data
    if check_disk:
        with h5py.File(disk_dir+'/'+h5_file,'r') as f5_tmp:
            dsets_tmp  = get_dsets(f5_tmp, load_dsets=False)
        have_dsets = True
        for dset in d_sets:
            if dset not in dsets_tmp:
                have_dsets = False
        if not have_dsets:
            collect = True

    return collect

def sync_disk_files(path_src,file_src,path_dest,file_dest, atol, rtol):
    src_dict  = check_disk(path_src, file_src)
    dest_dict = check_disk(path_dest, file_dest)
    if src_dict['exists'] and dest_dict['exists']:
        if src_dict['date_modified'] != dest_dict['date_modified']:
            h5_dset_migrate(path_src+'/'+file_src, path_dest+'/'+file_dest, atol=atol, rtol=rtol)
    if not dest_dict['exists'] and src_dict['exists']:
        # copy2 preserves metadata, such as timestamp
        shutil.copy2(path_src+'/'+file_src, path_dest+'/'+file_dest)

def sync_tape_disk(tape_dict,tape_file,disk_dict,disk_file,atol,rtol):
    print('complete me')    


def collect_ff_4D_tslice_src_avg(params, db_entries):
    f_type = 'formfac_4D_tslice_src_avg'
    disk_dir = params[f_type]
    f_dict = dict()
    f_dict['ensemble']      = params['ENS_S'].split('_')[0]
    f_dict['stream']        = params['STREAM']
    f_dict['configuration'] = int(params['CFG'])
    f_dict['source_set']    = params['SRC_SET']
    f_dict['t_separation']  = params['T_SEP']
    f_name                  = (c51.names[f_type]+'.h5') % params
    f_dict['name']          = f_name
    # filter db for unique entry
    entry = db_entries.filter(**f_dict).first()
    if not entry:
        print('something went wrong - this entry should have been created already')
        print(f_dict)
        sys.exit('exiting')
    t_exists = entry.tape.exists
    d_exists = entry.disk.exists
    # the disk and tape entries will have been created already, unless something went wrong
    if not t_exists and (params['UPDATE'] or params['TAPE_UPDATE']):
        t_dict = check_tape(entry.tape.path, entry.name)
        if t_dict['exists'] != t_exists:
            for k,v in t_dict.items():
                setattr(entry.tape, k, v)
            entry.tape.save()
        
    if not d_exists and t_exists and params['TAPE_GET']:
        print('retrieving from tape: %s' %entry.name)
        hsi.cget(entry.disk.path, entry.tape.path+'/'+entry.name)

    # if data does not exists on disk or tape, try src avg
    if not d_exists and not t_exists:
        d_dict = check_disk(entry.disk.path, entry.name)
        if not d_dict['exists']:
            os.system(c51.python+' %s/avg_4D.py formfac --cfgs %s -t %s --src_set %s %s %s %s' \
                      %(c51.script_dir, params['CFG'], params['T_SEP'], params['si'],params['sf'],params['ds'], params['bad_size']))
        d_dict = check_disk(entry.disk.path, entry.name)
        if d_dict['exists']:
            # save to tape
            hsi.cput(entry.disk.path+'/'+entry.name, entry.tape.path+'/'+entry.name)
            t_dict = check_tape(entry.tape.path, entry.name)
            # update DB
            print('updating lattedb')
            for k,v in d_dict.items():
                setattr(entry.disk, k, v)
            entry.disk.save()
            for k,v in t_dict.items():
                setattr(entry.tape, k, v)
            entry.tape.save()

def collect_spec_ff_4D_tslice_src_avg(fs_type, params, db_entries):
    if fs_type == 'spec':
        f_type = 'spec_4D_tslice_avg'
        params['SRC'] = 'src_avg'+params['SRC_SET']
    elif fs_type == 'formfac':
        f_type = 'formfac_4D_tslice_src_avg'
        params['SRC'] = 'src_avg'
    disk_dir = params[f_type]
    f_dict = dict()
    f_dict['ensemble']      = params['ENS_S'].split('_')[0]
    f_dict['stream']        = params['STREAM']
    f_dict['configuration'] = int(params['CFG'])
    f_dict['source_set']    = params['SRC_SET']
    if fs_type == 'formfac':
        f_dict['t_separation']  = params['T_SEP']
    f_dict['name']          = (c51.names[f_type]+'.h5') % params
    # filter db for unique entry
    entry = db_entries.filter(**f_dict).first()
    if not entry:
        print('something went wront - - this entry should have been created already')
        print(f_dict)
        sys.exit('exiting')
    t_exists = entry.tape.exists
    d_exists = entry.disk.exists
    # if tape exists but not disk and we want to retrieve
    if not d_exists and t_exists and params['TAPE_GET']:
        print('retrieving from tape: %s' %entry.name)
        hsi.cget(entry.disk.path, entry.tape.path+'/'+entry.name)
    # check tape, try and collect
    if not t_exists:
        # check disk, try and collect if missing
        print(entry.disk.path,entry.name)
        d_dict = check_disk(entry.disk.path, entry.name)
        print(d_dict)
        if not d_dict['exists']:
            if fs_type == 'spec':
                tsep_args = ''
            else:
                tsep_args = '-t '+params['T_SEP']
            os.system(c51.python+' %s/avg_4D.py %s --cfgs %s %s --src_set %s %s %s %s' \
                %(c51.script_dir, fs_type, params['CFG'], tsep_args, params['si'],params['sf'],params['ds'], params['bad_size']))
            d_dict = check_disk(entry.disk.path, entry.name)
        if d_dict['exists']:            
            # save to tape
            hsi.cput(entry.disk.path+'/'+entry.name, entry.tape.path+'/'+entry.name)
            t_dict = check_tape(entry.tape.path, entry.name)
            # update DB
            print('updating lattedb')
            for k,v in d_dict.items():
                setattr(entry.disk, k, v)
            entry.disk.save()
            for k,v in t_dict.items():
                setattr(entry.tape, k, v)
            entry.tape.save()
            if fs_type == 'spec':# we are saving individual spec_4D_tslice files for now as well
                for s0 in params['SOURCES']:
                    params['SRC']  = s0
                    spec_4D_tslice_file = (c51.names['spec_4D_tslice']+'.h5') % params
                    d_path = params['prod']+'/spec_4D_tslice/'+params['CFG']
                    t_path = c51.tape+'/'+params['ENS_S']+'/spec_4D_tslice/'+params['CFG']
                    hsi.cput(d_path+'/'+spec_4D_tslice_file, t_path+'/'+spec_4D_tslice_file)

'''
    FF 4D get or create db entrie functions
'''
def get_or_create_ff4D_tsliced_savg(
        params:              dict,
        configuration_range: List[int],
        ensemble:            str,
        stream:              str,
        source_set:          str,
    ) -> List[TSlicedSAveragedFormFactor4DFile]:
    """Returns queryset of TSlicedSAveragedFormFactor4DFile entries for given input
    
    Creates entries in bulk if they do not exist.
    """
    f_type = 'formfac_4D_tslice_src_avg'
    params['SRC'] = 'src_avg'
    t_seps = params['t_seps']
    # Pull all relevant meta entries to local python script
    meta_entries = TSlicedSAveragedFormFactor4DFile.objects.filter(
        configuration__in = configuration_range,
        ensemble          = ensemble,
        stream            = stream,
        source_set        = source_set,
        t_separation__in  = t_seps,
    )

    kwargs = {
        "ensemble":   ensemble,
        "stream":     stream,
        "source_set": source_set,
    }

    # Check if all entries are present
    new_entries = []
    for cfg in configuration_range:
        params['CFG']   = str(cfg)
        for tsep in t_seps:
            params['T_SEP'] = str(tsep)
            meta_data = kwargs.copy()
            f_name = (c51.names[f_type]+'.h5') % params
            #print(f_name)
            #sys.exit()
            meta_data["name"]          = f_name
            meta_data["configuration"] = cfg
            meta_data["t_separation"]  = tsep

            if not meta_entries.filter(**meta_data).first():
                new_entries.append(TSlicedSAveragedFormFactor4DFile(**meta_data))

    # Create entries if not present
    if new_entries:
        created_entries = TSlicedSAveragedFormFactor4DFile.objects.bulk_create(new_entries)
        print(f"Created {len(created_entries)} FF_4D_Tslice_Savg entries")
        meta_entries = TSlicedSAveragedFormFactor4DFile.objects.filter(
            configuration__in=configuration_range,
            ensemble=ensemble,
            stream=stream,
            source_set=source_set,
            t_separation__in=t_seps,
        )

    # Return all entries
    return meta_entries.prefetch_related('disk','tape')

def get_or_create_spec4D_tsliced_savg(
        params:              dict,
        configuration_range: List[int],
        ensemble:            str,
        stream:              str,
        source_set:          str,
    ) -> List[TSlicedSAveragedSpectrum4DFile]:
    """Returns queryset of TSlicedSAveragedSpectrum4DFile entries for given input

    Creates entries in bulk if they do not exist.
    """
    f_type = 'spec_4D_tslice_avg'
    params['SRC'] = 'src_avg'+params['SRC_SET']
    meta_entries = TSlicedSAveragedSpectrum4DFile.objects.filter(
        configuration__in = configuration_range,
        ensemble          = ensemble,
        stream            = stream,
        source_set        = source_set,
    )

    kwargs = {
        "ensemble":   ensemble,
        "stream":     stream,
        "source_set": source_set,
    }

    # Check if all entries are present
    new_entries = []
    for cfg in configuration_range:
        params['CFG']              = str(cfg)
        meta_data                  = kwargs.copy()
        f_name                     = (c51.names[f_type]+'.h5') % params
        meta_data["name"]          = f_name
        meta_data["configuration"] = cfg
    
        if not meta_entries.filter(**meta_data).first():
            new_entries.append(TSlicedSAveragedSpectrum4DFile(**meta_data))

    # Create entries if not present
    if new_entries:
        created_entries = TSlicedSAveragedSpectrum4DFile.objects.bulk_create(new_entries)
        print(f"Created {len(created_entries)} SPEC_4D_Tslice_Savg entries")
        meta_entries = TSlicedSAveragedSpectrum4DFile.objects.filter(
            configuration__in=configuration_range,
            ensemble=ensemble,
            stream=stream,
            source_set=source_set,
        )

    # Return all entries
    return meta_entries.prefetch_related('disk','tape')

''' 
    2pt Correlator DB entry creation function
'''
def get_or_create_meta_entries(
        correlator:          str,
        configuration_range: List[int],
        ensemble:            str,
        stream:              str,
        source_set:          str,
        sources:             Dict[int,List[str]],
    ) -> List[CorrelatorMeta]:
    """Returns queryset of CorrelatorMeta entries for given input
    
    Creates entries in bulk if they do not exist.
    """
    # Pull all relevant meta entries to local python script
    meta_entries = CorrelatorMeta.objects.filter(
        correlator=correlator,
        configuration__in=configuration_range,
        ensemble=ensemble,
        stream=stream,
        source_set=source_set,
    )

    kwargs = {
        "correlator": correlator,
        "ensemble":   ensemble,
        "stream":     stream,
        "source_set": source_set,
    }

    # Check if all entries are present
    entries_to_create = []
    for cfg in configuration_range:
        for src in sources[cfg]:
            meta_data = kwargs.copy()
            meta_data["source"] = src
            meta_data["configuration"] = cfg

            if not meta_entries.filter(**meta_data).first():
                entries_to_create.append(CorrelatorMeta(**meta_data))

    # Create entries if not present
    if entries_to_create:
        created_entries = CorrelatorMeta.objects.bulk_create(entries_to_create)
        print(f"Created {len(created_entries)} entries")
        meta_entries = CorrelatorMeta.objects.filter(
            correlator=correlator,
            configuration__in=configuration_range,
            ensemble=ensemble,
            stream=stream,
            source_set=source_set,
        )

    # Return all entries
    return meta_entries.prefetch_related('disk','tape')

''' Get or create DISK and TAPE functions that work with both 4D and CORR data files

'''
DiskEntries = TypeVar("DiskEntries")
def get_or_create_disk_entries(meta_entries: List, disk_entries: DiskEntries, path: str, machine: str, name: Optional[str] = None,
        )-> List[DiskEntries]:
    """Returns queryset of DiskCorrelatorH5Dset entries for given CorrelatorMeta entries
    
    Creates entries in bulk with status does not exist if they do not exist in DB.
    """
    if disk_entries == DiskCorrelatorH5Dset:
        file_entries = disk_entries.objects.filter(meta__in=meta_entries)
    elif disk_entries in [DiskTSlicedSAveragedFormFactor4DFile, DiskTSlicedSAveragedSpectrum4DFile]:
        file_entries = disk_entries.objects.filter(file__in=meta_entries)
    else:
        print('Disk Entry Error: we dont know what this is',disk_entries)
        sys.exit()    

    # Create entries if not present
    kwargs = {
        "path"    : path,
        "machine" : machine,
        "exists"  : False,
    }
    
    if not file_entries.count() == meta_entries.count():
        entries_to_create = []
        for meta in meta_entries:
            if not hasattr(meta, 'disk'):
                data = kwargs.copy()
                if disk_entries == DiskCorrelatorH5Dset:
                    data["name"] = name %{'CFG':meta.configuration}
                    data["dset"] = f"DUMMY_PLACE_HOLDER_H5_PATH"
                    data["meta"] = meta
                else:# disk_entries in [DiskTSlicedSAveragedFormFactor4DFile, DiskTSlicedSAveragedSpectrum4DFile]:
                    data["path"] = data["path"] %{'ENS_S':meta.ensemble+'_'+meta.stream, 'CFG':str(meta.configuration)}
                    data["file"] = meta
                    d_dict = check_disk(data['path'], meta.name)
                    for k in d_dict:
                        data[k] = d_dict[k]
                entries_to_create.append(disk_entries(**data))
        
        if entries_to_create:
            created_entries = disk_entries.objects.bulk_create(entries_to_create)
            print(f"Created {len(created_entries)} DISK entries")
            if disk_entries == DiskCorrelatorH5Dset:
                file_entries = disk_entries.objects.filter(meta__in=meta_entries)
            else:
                file_entries = disk_entries.objects.filter(file__in=meta_entries)

    return file_entries

TapeEntries = TypeVar("TapeEntries")
def get_or_create_tape_entries(meta_entries: List, tape_entries: TapeEntries, path: str, machine: str, name: Optional[str] = None,
        ) -> List[TapeEntries]:
    """Returns queryset of TapeEntries entries for given CorrelatorMeta entries
    
    Creates entries in bulk with status does not exist if they do not exist in DB.
    """
    if tape_entries == TapeCorrelatorH5Dset:
        file_entries = tape_entries.objects.filter(meta__in=meta_entries)
    elif tape_entries in [TapeTSlicedSAveragedFormFactor4DFile, TapeTSlicedSAveragedSpectrum4DFile]:
        file_entries = tape_entries.objects.filter(file__in=meta_entries)
    else:
        print('Tape Entry Error: we dont know what this is',tape_entries)
        sys.exit()    
    
    # Create entries if not present
    kwargs = {
        "path"    : path,
        "machine" : machine,
        "exists"  : False,
    }
    
    if file_entries.count() != meta_entries.count():
        entries_to_create = []
        for meta in meta_entries:
            if not hasattr(meta, 'tape'):
                data = kwargs.copy()
                if tape_entries == TapeCorrelatorH5Dset:
                    data["name"] = name %{'CFG':meta.configuration}
                    data["dset"] = f"DUMMY_PLACE_HOLDER_H5_PATH"
                    data["meta"] = meta
                else:# tape_entries in [TapeTSlicedSAveragedFormFactor4DFile, TapeTSlicedSAveragedSpectrum4DFile]:
                    data["path"] = data["path"] %{'ENS_S':meta.ensemble+'_'+meta.stream, 'CFG':str(meta.configuration)}
                    data["file"] = meta
                    t_dict = check_tape(data['path'], meta.name)
                    for k in t_dict:
                        data[k] = t_dict[k]
                entries_to_create.append(tape_entries(**data))
        
        if entries_to_create:
            created_entries = tape_entries.objects.bulk_create(entries_to_create)
            print(f"Created {len(created_entries)} TAPE entries")
            if tape_entries == TapeCorrelatorH5Dset:
                file_entries = tape_entries.objects.filter(meta__in=meta_entries)
            else:
                file_entries = tape_entries.objects.filter(file__in=meta_entries)

    return file_entries


def querry_corr_disk_tape(meta_entries,corr,db_filter,dt='tape',debug=False):
    has_dt = True
    db_filter_copy = dict(db_filter)
    db_filter_copy.update({'correlator':corr})
    for entry in meta_entries[corr].filter(**db_filter):
        if dt == 'tape':
            if hasattr(entry, 'tape'):
                if debug:
                    print(corr,'tape exists',entry.tape.exists)
                if not entry.tape.exists:
                    has_dt = False
            else:
                has_dt = False
        elif dt == 'disk':
            if hasattr(entry, 'disk'):
                if debug:
                    print(corr,'disk exists',entry.tape.exists)
                if not entry.disk.exists:
                    has_dt = False
            else:
                has_dt = False
        else:
            sys.exit('unrecognized disk/tape options: %s' %dt)
    return has_dt

def del_corr_entries(
        correlator:          str,
        configuration_range: List[int],
        ensemble:            str,
        stream:              str,
        source_set:          str,
        sources:             Dict[int,List[str]],
    ) -> List[CorrelatorMeta]:
    """ Delete entries of type CorrelatorMeta
    """
    # Pull all relevant meta entries to local python script
    meta_entries = CorrelatorMeta.objects.filter(
        correlator=correlator,
        configuration__in=configuration_range,
        ensemble=ensemble,
        stream=stream,
        source_set=source_set,
    )
    for de in meta_entries:
        de.delete()

def delete_ff4D_avg(
        ensemble            : str,
        stream              : str,
        source_set          : str,
        t_seps              : List[int],
        configuration_range : List[int],
    ) -> List[TSlicedSAveragedFormFactor4DFile]:
    """Delete entries of TSlicedSAveragedFormFactor4DFile type
    """
    meta_entries = CorrelatorMeta.objects.filter(
        ensemble=ensemble,
        stream=stream,
        source_set=source_set,
        configuration__in=configuration_range,
        t_separation__in=t_seps,
    )
    for de in meta_entries:
        de.delete()

def delete_spec4D_avg(
        ensemble            : str,
        stream              : str,
        source_set          : str,
        configuration_range : List[int],
    ) -> List[TSlicedSAveragedFormFactor4DFile]:
    """Delete entries of TSlicedSAveragedFormFactor4DFile type
    """
    meta_entries = CorrelatorMeta.objects.filter(
        ensemble=ensemble,
        stream=stream,
        source_set=source_set,
        configuration__in=configuration_range,
    )
    for de in meta_entries:
        de.delete()

