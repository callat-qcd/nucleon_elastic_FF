import os, sys, time
import numpy as np

import sources

# A little template that looks all the way through symbolic links to see if there's anything down at the bottom.
def recursiveLinkCheck(existence_checker):
    def existsQ(path):
        real_path = os.path.realpath(path)
        if existence_checker(real_path):
            return real_path
        return False
    return existsQ

# Use the template to build functions that check for files and directories at the bottom:
dirExists =  recursiveLinkCheck(os.path.isdir)
def fileExists(path):
    return recursiveLinkCheck(os.path.isfile)(path) and os.path.getsize(path) > 0

def ensure_dirExists(path):
    if not dirExists(path):
        if not fileExists(path):
            os.makedirs(path)
        else:
            print("You tried to create a directory that is already the name of a file.")
            print("Exiting for safety.")
            exit(-1)

def check_file(f_name,f_size,time_delete,bad_file_dir):
    if os.path.exists(f_name) and os.path.getsize(f_name) < f_size:
        now = time.time()
        file_time = os.stat(f_name).st_mtime
        ''' check last update of file in minutes '''
        if (now-file_time)/60 > time_delete:
            print('DELETING BAD FILE',os.path.getsize(f_name),f_name.split('/')[-1])
            shutil.move(f_name,bad_file_dir+'/'+f_name.split('/')[-1])
    return os.path.exists(f_name)

def parse_cfg_argument(cfg_arg, params):
    if cfg_arg == []:
        ci = params['cfg_i']
        cf = params['cfg_f']
        dc = params['cfg_d']
    elif len(cfg_arg) == 1:
        ci = int(cfg_arg[0])
        cf = int(cfg_arg[0])
        dc = 1
    elif len(cfg_arg) == 3:
        ci = int(cfg_arg[0])
        cf = int(cfg_arg[1])
        dc = int(cfg_arg[2])
    else:
        print('unrecognized use of cfg arg')
        print('cfg_i [cfg_f cfg_d]')
        sys.exit()
    return range(ci,cf+dc,dc)

def parse_cfg_src_argument(cfg_arg,src_arg,params):
    cfgs_run = parse_cfg_argument(cfg_arg,params)
    if src_arg:
        if len(cfgs_run) > 1:
            print('if a src is passed, only 1 cfg can be specified: len(cfgs) = ',len(cfgs_run))
            sys.exit(-1)
        else:
            srcs = {cfgs_run[0]:[src_arg]}
            ''' make sure this src is in the expected list '''
            no = str(cfgs_run[0])
            src_check = []
            srcs_cfg = sources.make(no, nl=params['NL'], nt=params['NT'], t_shifts=params['t_shifts'],
                generator=params['generator'], seed=params['seed'][params['STREAM']])
            for origin in srcs_cfg:
                try:
                    src_gen = srcs_cfg[origin].iteritems()
                except AttributeError: # Python 3 automatically creates a generator
                    src_gen = srcs_cfg[origin].items()
                for src_type, src in src_gen:
                    src_check.append(sources.xXyYzZtT(src))
            if srcs[cfgs_run[0]][0] not in src_check:
                print('you supplied a src not in the current src list: allowed srcs')
                print(src_check)
                sys.exit(-1)
    else:
        srcs = {}
        for c in cfgs_run:
            no = str(c)
            srcs_cfg = sources.make(no, nl=params['NL'], nt=params['NT'], t_shifts=params['t_shifts'],
                generator=params['generator'], seed=params['seed'][params['STREAM']])
            srcs[c] = []
            for origin in srcs_cfg:
                try:
                    src_gen = srcs_cfg[origin].iteritems()
                except AttributeError: # Python 3 automatically creates a generator
                    src_gen = srcs_cfg[origin].items()
                for src_type, src in src_gen:
                    srcs[c].append(sources.xXyYzZtT(src))
    return cfgs_run, srcs

def nsq_vectors(nsq):
    n = int(np.ceil(np.sqrt(nsq)))+1
    r = range(-(n+1),n,1)
    return  [ [x,y,z] for x in r for y in r for z in r if x**2+y**2+z**2 == nsq ]

def p_lst(nsq):
    n = int(np.ceil(np.sqrt(nsq)))+1
    r = range(-(n+1),n,1)
    n_lst = [ [x,y,z] for x in r for y in r for z in r if x**2+y**2+z**2 <= nsq ]
    p_lst = []
    for xyz in n_lst:
        p_lst.append('px%d_py%d_pz%d' %(xyz[0],xyz[1],xyz[2]))
    return p_lst

def p_simple_lst(n=4):
    r = range(-n,n+1)
    p_lst = []
    for p in r:
        p_lst.append('px%d_py0_pz0' %p)
        p_lst.append('px0_py%d_pz0' %p)
        p_lst.append('px0_py0_pz%d' %p)
    return p_lst
    
def time_reverse(corr,phase=1,time_axis=1):
    '''
    Performe time-reversal of correlation function accounting for BC in time
    phase     = +1 or -1
    time_axis = time_axis in array
    '''
    if len(corr.shape) > 1:
        if time_axis == 1:
            cr = phase * np.roll(corr[:,::-1],1,axis=time_axis)
            cr[:,0] = phase * cr[:,0]
        else:
            print('time_axis != 1 not supported at the moment')
            sys.exit()
    else:
        cr = phase * np.roll(corr[::-1],1)
        cr[0] = phase * cr[0]
    return cr

def mom_avg(h5_data,state,mom_lst,weights=False):
    '''
    perform a momentum average of a state from an open h5 file
    data file is assumed to be of shape [Nt,Nz,Ny,Nx,2] where 2 = [re,im]
    data_mom = h5_data[state][:,pz,py,px]
    '''
    d_lst = []
    w = []
    for mom in mom_lst:
        px,py,pz = mom['momentum']
        w.append(mom['weight'])
        #print(state)
        d_lst.append(h5_data[state][:,pz,py,px])
    d_lst = np.array(d_lst)
    w = np.array(w)
    if weights:
        for wi,we in enumerate(w):
            d_lst[wi] = we*d_lst[wi]
        d_avg = np.sum(d_lst,axis=0) / np.sum(w)
    else:
        d_avg = np.mean(d_lst,axis=0)
    return d_avg
