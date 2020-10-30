import os, sys, argparse
import numpy as np
import tables as h5
import subprocess
from glob import glob
import warnings
warnings.simplefilter('ignore', h5.NaturalNameWarning)
warnings.simplefilter('ignore', np.ComplexWarning)

'''
    NUCLEON_ELASTIC_FF IMPORTS
'''
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
import importlib
import c51_mdwf_hisq as c51
import utils
import sources
ens,stream = os.getcwd().split('/')[-1].split('_')
ens_s = ens+'_'+stream
print(ens,stream)

area51 = importlib.import_module(ens)
params = area51.params
params['machine'] = c51.machine
params['ENS_LONG'] = c51.ens_long[ens]
params['ENS_S']    = ens_s
params['STREAM']   = stream

print('ENSEMBLE:',ens_s)

parser = argparse.ArgumentParser(description='collect charm PBP results and put in h5 files')
parser.add_argument('cfgs',            nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('-o','--overwrite',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('-d','--debug',    default=False,action='store_const',const=True,help='debug? [%(default)s]')
parser.add_argument('--fout',          type=str,help='name of output file')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.complex128
data_dir = c51.data_dir % params
utils.ensure_dirExists(data_dir)
utils.ensure_dirExists(data_dir+'/avg')

cfgs = utils.parse_cfg_argument(args.cfgs, params)
print('concatenating from cfgs %d - %d' %(cfgs[0],cfgs[-1]))

if args.fout == None:
    f_out = data_dir +'/avg/charm_PBP_'+ens_s+'_avg.h5'
else:
    f_out = args.fout
print('collecting data to')
print(f_out)

for mc in params['MC_reweight']:
    print('mc =',mc)
    mc_s = str(mc).replace('.','p')
    f_out = data_dir +'/avg/charm_PBP_'+ens_s+'_avg.h5'
    # did we already collect the data?
    if os.path.exists(f_out):
        with h5.open_file(f_out, 'a') as a5:
            have_data = 'mc_'+mc_s in a5.get_node('/')
            if have_data:
                if args.overwrite:
                    a5.remove_node('/mc_'+mc_s, recursive=True)
                    have_data = False
                else:
                    print('data exists and overwrite = ',args.overwrite)
    else:
        have_data = False
    if not have_data:
        cfgs_srcs  = []
        first_data = True
        for cfg in cfgs:
            no = str(cfg)
            sys.stdout.write('    %4s\r' %(no))
            sys.stdout.flush()
            d_file = data_dir +'/charm_PBP_'+ens_s+'_'+no+'.h5'
            if os.path.exists(d_file):
                with h5.open_file(d_file, 'r') as f5:
                    if 'mc_'+mc_s in f5.get_node('/'):
                        tmp = f5.get_node('/mc_'+mc_s).read()
                        cfgs_srcs.append([cfg, tmp.shape[0]])
                        if first_data:
                            pbp = np.zeros((1,)+tmp.shape, dtype=dtype)
                            pbp[0] = tmp
                            first_data = False
                        else:
                            pbp = np.append(pbp, [tmp], axis=0)
        cfgs_srcs = np.array(cfgs_srcs)
        nc        = cfgs_srcs.shape[0]
        print('   N_cfg = %d' %(nc))
        if nc > 0:
            with h5.open_file(f_out, 'a') as a5:
                a5.create_group('/','mc_'+mc_s)
                a5.create_array('/mc_'+mc_s,'pbp',pbp)
                a5.create_array('/mc_'+mc_s,'cfgs_srcs',cfgs_srcs)
            print('   cc = %.17f +- %.17f' %(pbp.mean(), pbp.std()/np.sqrt(nc)))
