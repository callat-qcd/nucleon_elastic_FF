import os, sys
from datetime import datetime
import pytz
from tzlocal import get_localzone
local_tz = get_localzone()
# c51 imports
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
import c51_mdwf_hisq as c51

''' LOGIC of DISK/TAPE check
if entry in db:
    if entry has tape attribute:
        if update or update_tape:
            check_tape
            if entry_tape_exists != tape_exists::
                add to update_tape list
    else:
        get tape status and append to list
    if disk in db entry:
        if update or update_disk:
            check disk
            if db.exists != disk.exists:
                append to upate_disk list
    else:
        get disk status and append to list
    if disk_exists and not tape_exists:
        add to put to tape list
    if tape_exists and not disk_exists and pull_tape:
        add to pull from tape list
else:
    create disk/tape status and append to list
'''

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
