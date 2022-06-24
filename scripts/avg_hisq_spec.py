#!/usr/local/bin/python
from __future__ import print_function
import os, sys, argparse, shutil, datetime, time
import numpy as np
np.set_printoptions(linewidth=180)
import tables as h5
from glob import glob
fmt = '%Y-%m-%d %H:%M:%S'

'''
    NUCLEON_ELASTIC_FF IMPORTS
'''
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
import importlib
import c51_mdwf_hisq as c51
import utils
import sources
import time

ens,stream = c51.ens_base()
ens_s = ens+'_'+stream

area51 = importlib.import_module(ens)
params = area51.params
params['machine'] = c51.machine
params['ENS_LONG'] = c51.ens_long[ens]
params['ENS_S']    = ens_s
params['STREAM']   = stream


np.set_printoptions(linewidth=180)
parser = argparse.ArgumentParser(description='avg mres data from h5 file')
parser.add_argument('cfgs',  nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('--ns',  type=int,help='number of srcs/cfg [%(default)s]')
parser.add_argument('-o',    default=False,action='store_true',help='overwrite? [%(default)s]')
parser.add_argument('--fin', type=str,
                    help=    'directory to input (which is get script output), need to end with /, leave empty for production')
parser.add_argument('--fout',type=str,
                    help=    'directory to output, need to end with /, leave empty for production')

args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.complex64
data_dir = c51.data_dir % params
utils.ensure_dirExists(data_dir)

params = sources.src_start_stop(params,ens,stream)
args.src=None
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,args.src,params)

ms_l = params['MS_L']
ms_s = params['MS_S']

print ('ml:', ms_l)
print ('ms:', ms_s)

# input dir
fin_dir = data_dir
# output dir
if not args.fout:
    if not os.path.exists( data_dir+'/avg'): os.makedirs( data_dir+'/avg')
    f_out = data_dir+'/avg/hisq_spec_'+ens_s+'_avg.h5'
else:
    f_out = args.fout

print('input:\t'+fin_dir)
print('output:\t'+f_out)

proceed = input('do you want to proceed?\t')
if proceed not in ['y','yes']:
    os.system('python '+sys.argv[0]+' -h')
    sys.exit()

fin_files = [fn for fn in glob(fin_dir+'/hisq_spec_'+ens_s+'_*.h5')]
print( 'no cfgs = %d' %len(cfgs_run))

# HISQ HISQ mesons
if ms_l == ms_s:
    mixed_states = ['phi_jj_5', 'phi_jj_I']
else:
    mixed_states = ['phi_jj_5', 'phi_jr_5', 'phi_rr_5', 'phi_jj_I', 'phi_jr_I', 'phi_rr_I']

ml = ms_l
ms = ms_s
mls = 'ml'+ms_l.replace('.','p')
mss = 'ms'+ms_s.replace('.','p')

for state in mixed_states:
    first_data = True
    cfgs_srcs = []
    all_cfgs = True
    for cfg in cfgs_run:
        no = str(cfg)
        try:
            with h5.open_file(fin_dir+'/hisq_spec_'+ens_s+'_'+no+'.h5') as fin:
                f5dir = '/'+params['ENS_LONG']+'/hisq_spec/'+mls+'_'+mss
                srcs = fin.get_node(f5dir+'/'+state)
                if srcs._v_nchildren > 0:
                    good_cfg = True
        except Exception as e:
            print('checking cfg %s' %no)
            print(e)
            all_cfgs = False
            
    if not all_cfgs:
        sys.exit('missing some configs')
    else:
        for cfg in cfgs_run:
            no = str(cfg)    
            fin = h5.open_file(fin_dir+'/hisq_spec_'+ens_s+'_'+no+'.h5')
            f5dir = '/'+params['ENS_LONG']+'/hisq_spec/'+mls+'_'+mss
            srcs = fin.get_node(f5dir+'/'+state)
            ns = 0
            tmp = []
            for src in srcs:
                tmp.append(src.read())
                ns += 1
            sys.stdout.write('%4s  %d  %s\r' %(cfg,ns,state))
            sys.stdout.flush()
            tmp = np.array(tmp)
            if first_data:
                data = np.zeros((1,)+tmp.mean(axis=0).shape,dtype=dtype)
                #print data.shape
                data[0] = tmp.mean(axis=0)
                #print data.shape
                first_data = False
            else:
                data = np.append(data,[tmp.mean(axis=0)],axis=0)
            cfgs_srcs.append([cfg,ns])
            fin.close()

        cfgs_srcs = np.array(cfgs_srcs)
        #print 'cfgs_srcs:', cfgs_srcs
        nc = cfgs_srcs.shape[0]
        #ns_avg = cfgs_srcs.mean(axis=0)[1]
        if nc > 0:
            print ('concatenated %s ml=%s ms=%s: Ncfg = %d' %(state,ml,ms,nc))
            with h5.open_file(f_out,'a') as fout:
                group = params['ENS_LONG']+'/hisq_spec/'+mls+'_'+mss
                sdir = ''
                for i,gi in enumerate(group.split('/')):
                    if gi not in fout.get_node('/'+sdir):
                        fout.create_group('/'+sdir,gi)
                    sdir += '/'+gi
                if state not in fout.get_node(sdir):
                    fout.create_group(sdir,state)
                    fout.create_array(sdir+'/'+state,'corr',data)
                    fout.create_array(sdir+'/'+state,'cfgs_srcs',cfgs_srcs)
                elif state in fout.get_node(sdir) and args.o:
                    fout.remove_node(sdir+'/'+state+'/corr')
                    fout.create_array(sdir+'/'+state,'corr',data)
                    fout.remove_node(sdir+'/'+state+'/cfgs_srcs')
                    fout.create_array(sdir+'/'+state,'cfgs_srcs',cfgs_srcs)
                elif state in fout.get_node(sdir) and not args.o:
                    print(state+' exists: overwrite = False')
