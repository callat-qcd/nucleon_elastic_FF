import os, sys
from datetime import datetime
import pytz
from tzlocal import get_localzone
local_tz = get_localzone()
# c51 imports
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
import c51_mdwf_hisq as c51

from typing import Union, List, Dict
from lattedb.project.formfac.models.data.correlator import (
    CorrelatorMeta,
    DiskCorrelatorH5Dset,
    TapeCorrelatorH5Dset,
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

def check_ff_4D_tslice_src_avg(
        params,            # a dictionary of information about the file names, locations, etc.
        db_entries,        # the db querry
        db_update_disk,    # list of disk updates
        db_new_disk,       # list of new disk entries
        db_update_tape,    # list of tape updates
        db_new_tape,       # list of new tape entries
        db_new_entry,      # list of new db entries
        save_to_tape,      # list of files to save to tape
        data_collect,      # list of files to try and collect
        ):
    f_type = 'formfac_4D_tslice_src_avg'
    no = params['CFG']
    disk_dir = params[f_type]
    for tsep in params['t_seps']:
        dt = str(tsep)
        params['T_SEP'] = dt
        # make file entry
        f_dict = dict()
        f_dict['ensemble']      = params['ENS_S'].split('_')[0]
        f_dict['stream']        = params['STREAM']
        f_dict['configuration'] = int(params['CFG'])
        f_dict['source_set']    = params['SRC_SET']
        f_dict['t_separation']  = tsep
        f_name                  = (c51.names[f_type]+'.h5') % params
        f_dict['name']          = f_name
        # filter db for unique entry
        entry = db_entries.filter(**f_dict).first()
        if entry:# if it exists, then check if it exists on tape
            # check tape
            if hasattr(entry, 'tape'):
                t_dict = dict()
                t_dict['exists'] = entry.tape.exists
            if hasattr(entry, 'tape') and (params['UPDATE'] or params['TAPE_UPDATE']):
                t_dict = check_tape(c51.tape+'/'+params['ENS_S']+'/'+f_type+'/'+no, f_name)
                if entry.tape.exists != t_dict['exists']:
                    t_dict['file'] = entry
                    db_update_tape.append((f_dict,t_dict))
            elif not hasattr(entry, 'tape'):
                t_dict = check_tape(c51.tape+'/'+params['ENS_S']+'/'+f_type+'/'+no, f_name)
                t_dict['file'] = entry
                db_new_tape.append(t_dict)
            # check disk
            if hasattr(entry, 'disk'):
                d_dict = dict()
                d_dict['exists'] = entry.disk.exists
            if hasattr(entry, 'disk') and (params['UPDATE'] or params['DISK_UPDATE']):
                d_dict = check_disk(disk_dir, f_name)
                if entry.disk.exists != d_dict['exists']:
                    d_dict['file'] = entry
                    db_update_disk.append((f_dict,d_dict))
            elif not hasattr(entry, 'disk'):
                d_dict = check_disk(disk_dir, f_name)
                d_dict['file'] = entry
                db_new_disk.append(d_dict)
        else:
            t_dict = check_tape(c51.tape+'/'+params['ENS_S']+'/'+f_type+'/'+no, f_name)
            d_dict = check_disk(disk_dir, f_name)
            db_new_entry.append((f_dict,d_dict,t_dict))
        # find files that exist on disk and not tape
        if d_dict['exists'] and not t_dict['exists']:
            save_to_tape.append([f_name, disk_dir, params['TAPE_DIR']])
        if not d_dict['exists'] and (not t_dict['exists'] or params['DISK_UPDATE'] or params['UPDATE']):
            data_collect.append(f_name)

def check_ff_4D_tslice(
        params,            # a dictionary of information about the file names, locations, etc.
        db_entries,        # the db querry
        db_update_disk,    # list of disk updates
        db_new_disk,       # list of new disk entries
        db_new_entry,      # list of new db entries
        check_exists=False,# return existence if True
        #data_collect,      # list of files to try and collect
        ):
    f_type = 'formfac_4D_tslice'
    no = params['CFG']
    disk_dir = params[f_type]
    for tsep in params['t_seps']:
        dt = str(tsep)
        params['T_SEP'] = dt
        # make file entry
        f_dict = dict()
        f_dict['ensemble']      = params['ENS_S'].split('_')[0]
        f_dict['stream']        = params['STREAM']
        f_dict['configuration'] = int(params['CFG'])
        f_dict['source_set']    = params['SRC_SET']
        f_dict['t_separation']  = tsep
        f_name                  = (c51.names[f_type]+'.h5') % params
        f_dict['name']          = f_name
        # filter db for unique entry
        entry = db_entries.filter(**f_dict).first()
        if entry:# if it exists, then check if it exists on tape
            # check disk
            if hasattr(entry, 'disk'):
                d_dict = dict()
                d_dict['exists'] = entry.disk.exists
            if hasattr(entry, 'disk') and (params['UPDATE'] or params['DISK_UPDATE']):
                d_dict = check_disk(disk_dir, f_name)
                if entry.disk.exists != d_dict['exists']:
                    d_dict['file'] = entry
                    db_update_disk.append((f_dict,d_dict))
            elif not hasattr(entry, 'disk'):
                d_dict = check_disk(disk_dir, f_name)
                d_dict['file'] = entry
                db_new_disk.append(d_dict)
        else:
            d_dict = check_disk(disk_dir, f_name)
            db_new_entry.append((f_dict,d_dict))


def collect_ff4D_tslice_src_avg(ff_list):
    return None

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

def get_or_create_disk_entries(meta_entries: List[CorrelatorMeta], name: str, path: str, machine: str,
        )-> List[DiskCorrelatorH5Dset]:
    """Returns queryset of DiskCorrelatorH5Dset entries for given CorrelatorMeta entries
    
    Creates entries in bulk with status does not exist if they do not exist in DB.
    """
    file_entries = DiskCorrelatorH5Dset.objects.filter(meta__in=meta_entries)
    
    # Create entries if not present
    kwargs = {
        "name"    : name,
        "path"    : path,
        "machine" : machine,
        "exists"  : False,
    }
    
    if not file_entries.count() == meta_entries.count():
        entries_to_create = []
        for meta in meta_entries:
            data = kwargs.copy()
            data["name"] = name %{'CFG':meta.configuration}
            data["dset"] = f"DUMMY_PLACE_HOLDER_H5_PATH"
            data["meta"] = meta
            if not file_entries.filter(**data).first():
                entries_to_create.append(DiskCorrelatorH5Dset(**data))
        
        created_entries = DiskCorrelatorH5Dset.objects.bulk_create(entries_to_create)
        print(f"Created {len(created_entries)} entries")
        file_entries = DiskCorrelatorH5Dset.objects.filter(meta__in=meta_entries)
    
    return file_entries

def get_or_create_tape_entries(meta_entries: List[CorrelatorMeta], name: str, path: str, machine: str,
        ) -> List[TapeCorrelatorH5Dset]:
    """Returns queryset of TapeCorrelatorH5Dset entries for given CorrelatorMeta entries
    
    Creates entries in bulk with status does not exist if they do not exist in DB.
    """
    file_entries = TapeCorrelatorH5Dset.objects.filter(meta__in=meta_entries)
    
    # Create entries if not present
    kwargs = {
        "name": name,
        "path": path,
        "machine": machine,
        "exists": False,
    }
    
    if file_entries.count() != meta_entries.count():
        entries_to_create = []
        for meta in meta_entries:
            data = kwargs.copy()
            data["name"] = name %{'CFG':meta.configuration}
            data["dset"] = f"DUMMY_PLACE_HOLDER_H5_PATH"
            data["meta"] = meta
            if not file_entries.filter(**data).first():
                entries_to_create.append(TapeCorrelatorH5Dset(**data))
        
        created_entries = TapeCorrelatorH5Dset.objects.bulk_create(entries_to_create)
        print(f"Created {len(created_entries)} entries")
        file_entries = TapeCorrelatorH5Dset.objects.filter(meta__in=meta_entries)
    
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

def del_entries(
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
    for de in meta_entries:
        de.delete()


'''
def get_corr_information(
        corr: str, configuration: int, source: str
    ) -> Union[CorrelatorMeta, None]:
    """Looks up if a given correlator can be found on disk or tape.
    
    Returns the corresponding object if found, else None.
    If both disk and tape object exists, return Disk object first.
    """
    meta = CorrelatorMeta.objects.filter(
        corr=corr, configuration=configuration, source=source
        )

    #if meta is not None:
    #    if hasattr(meta, "disk") and meta.disk.exists:
    #        obj = meta.disk
    #    elif hasattr(meta, "tape") and meta.tape.exists:
    #        obj = meta.tape

    return meta
'''
