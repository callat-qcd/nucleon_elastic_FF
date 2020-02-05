import os, sys, time, shutil
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

def check_file(f_name,f_size,time_delete,bad_file_dir,debug=False):
    if os.path.exists(f_name) and os.path.getsize(f_name) < f_size:
        now = time.time()
        file_time = os.stat(f_name).st_mtime
        ''' check last update of file in minutes '''
        if (now-file_time)/60 > time_delete:
            if debug:
                print('DEBUG: DELETING BAD FILE',os.path.getsize(f_name),f_name.split('/')[-1])
                print('now',now,'file_time',file_time)
            else:
                print('DELETING BAD FILE',os.path.getsize(f_name),f_name.split('/')[-1])
                shutil.move(f_name,bad_file_dir+'/'+f_name.split('/')[-1])
    return os.path.exists(f_name)

def parse_cfg_argument(cfg_arg, params):
    allowed_cfgs = range(params['cfg_i'],params['cfg_f']+1,params['cfg_d'])
    if not cfg_arg:
        ci = params['cfg_i']
        cf = params['cfg_f']
        dc = params['cfg_d']
    else:
        if int(cfg_arg[0]) not in allowed_cfgs:
            sys.exit('you selected configs not allowed for %s: allowed_cfgs = range(%d, %d, %d)' %(params['ENS_S'],params['cfg_i'], params['cfg_f'], params['cfg_d']))
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

def parse_cfg_src_argument(cfg_arg,src_arg,params,src_type=[]):
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
            if 'si' in params and 'sf' in params and 'ds' in params:
                src_check = src_check[params['si']:params['sf']+params['ds']:params['ds']]
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
                for s_type, src in src_gen:
                    if len(src_type) > 0:
                        if s_type in src_type:
                            srcs[c].append(sources.xXyYzZtT(src))
                    else:
                        srcs[c].append(sources.xXyYzZtT(src))
            if 'si' in params and 'sf' in params and 'ds' in params:
                srcs[c] = srcs[c][params['si']:params['sf']+params['ds']:params['ds']]
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
    r = [i for j in (range(-n,0), range(1,n+1)) for i in j]
    p_lst = []
    p_lst.append('px0_py0_pz0')
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

def get_write_h5_ff_data(f_in,f_out,p_in,p_out,d_name,overwrite=False,verbose=False):
    data = f_in.get_node(p_in).read()
    if not np.any(np.isnan(data)):
        if d_name not in f_out.get_node(p_out):
            f_out.create_array(p_out,d_name,data)
            if verbose: print('    fresh collect')
        elif d_name in f_out.get_node(p_out) and overwrite:
            f_out.get_node(p_out+'/'+d_name)[:] = data
            if verbose: print('    replace collect')
        elif d_name in f_out.get_node(p_out) and not overwrite:
            if verbose: print('    skipping, overwrite = False')

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

'''
Function to obtained tslice values from the stdout output file for quark loops computed with the milc code
The lines format is
  PBP: mass 6.730000e-02     tslice 14 1.754393e-03  1.786215e-03  -2.306500e-05  -1.151786e-04 ( 6 of 200 )
'''
def getLineInfo(l):
    line=l.split()
    tsum=None
    if 'PBP:' and 'tslice' in line:
        mass,tslice,valEven,valOdd,valEvenIm,valOddIm,npbp=float(line[2]),int(line[4]),\
                                          float(line[5]),float(line[6]),float(line[7]),float(line[8]),int(line[-4])
    else:
        mass,tslice,valEven,valOdd,valEvenIm,valOddIm,npbp=None,None,None,None,None,None,None
        if 'PBP:' in line:
            mass,tsum,npbp=float(line[2]),[float(line[3]),float(line[4])],int(line[-4])
    return mass,tslice,valEven,valOdd,valEvenIm,valOddIm,tsum,npbp


'''

Function get the quark loop data sets from the stdout output file for quark loops computed with the milc code
The lines format is
  PBP: mass 6.730000e-02     tslice 14 1.754393e-03  1.786215e-03  -2.306500e-05  -1.151786e-04 ( 6 of 200 )
'''
def getLoopDataTextFromFile(fname):
    text=open(fname).read()

    newSetLine='Turning ON boundary phases 0 0 0 0 to FN links r0 0 0 0 0'
    npbpEndLine='new npbp or new mass'
    
    #Split the text in measurement sets for each quark mass
    setSplitText=text.split(newSetLine)[1::]
    dataSets,set_npbp=[],[]
    for i,iset in enumerate(setSplitText):
        tempText=''
        for x in iset.split('\n'):
            if 'PBP: mass ' in x:
                tempText+=x+'\n'
            if 'FACTION: mass =' in x:
                tempText+=npbpEndLine+'\n'
        tempSet=tempText.split(npbpEndLine)[0:-1]
        set_npbp.append(int(tempSet[0].split()[-2]))

        '''
         If there are more than one set for a given quark mass with different naik values,
         the sets must be split in the following if block.
        ''' 
        if len(tempSet) != set_npbp[i]:
            inds=[]
            for j in range(int(len(tempSet)/set_npbp[i])):
                inds.append(np.arange(0+j,int(len(tempSet)),int(len(tempSet)/set_npbp[i])))
                dataSets.append(np.array(tempSet)[inds[j]])
        else:
            dataSets.append(np.array(tempSet))

    return dataSets,set_npbp

'''
Construct arrays with quark loops data sets
'''
def getLoopData(dataSets,NT):
    data,dataSum=[],[]
    for i in range(len(dataSets)):
        data.append(np.zeros(shape=(dataSets[i].shape[0],NT,4)))
        dataSum.append(np.zeros(shape=(dataSets[i].shape[0],2)))
        for nTex in dataSets[i]:
            for k,l in enumerate(nTex.split('\n')):
               lmass,tsl,valEven,valOdd,valEvenIm,valOddIm,ltsum,npbp=getLineInfo(l)
               if tsl is not None:
                   data[i][npbp-1][tsl]=np.array([valEven,valOdd,valEvenIm,valOddIm])
               else:
                   if l!='':
                       dataSum[i][npbp-1]=np.array(ltsum)
    return data,dataSum
