from __future__ import print_function
import os, sys, argparse, shutil, datetime, time, subprocess
import numpy as np
np.set_printoptions(linewidth=180)
import tables as h5
import warnings
warnings.simplefilter('ignore', h5.NaturalNameWarning)
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
parser.add_argument('cfgs',nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('-m','--mq', type=str,help='specify quark mass [default = all]')
parser.add_argument('-s','--src',type=str,help='src [xXyYzZtT] None=All')
parser.add_argument('-o',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('-q',default=True, action='store_const',const=False,help='collect stout Q measurement? [%(default)s]')
parser.add_argument('--qonly',default=False,action='store_const',const=True,help='only collect Q? [%(default)s]')
parser.add_argument('--rho',     type=str,default='0.068',help='specify rho parameter for stout smearing [%(default)s]')
parser.add_argument('--steps',   type=str,default='2000' ,help='specify Nsteps of stout [%(default)s]')
parser.add_argument('--move',default=False,action='store_const',const=True,help='move bad files? [%(default)s]')
parser.add_argument('-v',default=True,action='store_const',const=False,help='verbose? [%(default)s]')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.float64
data_dir = c51.data_dir % params
utils.ensure_dirExists(data_dir)

params = sources.src_start_stop(params,ens,stream)
cfgs_run = utils.parse_cfg_argument(args.cfgs,params)

print('MINING WFLOW and Q')
print('ens_stream = ',ens_s)

for cfg in cfgs_run:
    no = str(cfg)
    print(no)
    params['CFG'] = no
    params = c51.ensemble(params)
    wflow_file = params['prod']+'/gauge/'+params['ENS_LONG']+params['STREAM']+'.gflow.'+no
    q_file     = params['prod']+'/gauge/'+params['ENS_LONG']+params['STREAM']+'.stout.rho'+args.rho+'.step'+args.steps+'.'+no
    # get flow data
    if os.path.exists(wflow_file) and not args.qonly:
        t_gf = []
        plaq = []
        E    = []
        Q    = []
        wflow_grep = subprocess.check_output('grep performWFlownStep %s' %wflow_file, shell=True).decode('ascii')
        for l in wflow_grep.split('\n'):
            try:
                float(l.split()[1])
                t_gf.append(float(l.split()[1]))
                plaq.append(float(l.split()[2]))
                E_tmp = [float(l.split()[i]) for i in [3,4,5]]
                E.append(np.array(E_tmp))
                Q.append(float(l.split()[6]))
            except:
                pass
        t_gf = np.array(t_gf)
        plaq = np.array(plaq)
        E    = np.array(E)
        Q    = np.array(Q)
        f5 = h5.open_file(data_dir+'/'+ens_s+'_'+no+'_gauge_params'+'.h5','w')
        f5.create_array('/','t_gf',t_gf)
        f5.create_array('/','plaq',plaq)
        f5.create_array('/','E',E)
        f5.create_array('/','Q_wflow',Q)
        f5.close()
    if args.q:
        if os.path.exists(q_file):
            f5 = h5.open_file(data_dir+'/'+ens_s+'_'+no+'_gauge_params'+'.h5','a')
            collect=True
            if 'Q_stout' in f5.root and not args.o:
                collect=False
            if 'Q_stout' in f5.root and args.o:
                f5.remove_node('/Q_stout')
            if collect:
                Q_stout = []
                stout_grep = subprocess.check_output('grep "Q charge at step" %s' %q_file, shell=True).decode('ascii')
                for l in stout_grep.split('\n'):
                    try:
                        Q_stout.append(float(l.split()[6]))
                    except:
                        pass
                Q_stout = np.array(Q_stout)
                f5.create_array('/','Q_stout',Q_stout)
            f5.close()
        
