from __future__ import print_function
import os, sys, argparse
import numpy as np
np.set_printoptions(linewidth=180)
import tables as h5
import warnings
warnings.simplefilter('ignore', h5.NaturalNameWarning)
from glob import glob
import nucleon_elastic_ff.data.scripts.tslice as tslice

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
parser = argparse.ArgumentParser(description='average phi_qq')
parser.add_argument('data',type=str,help='what data type to average [spec formfac]?')
parser.add_argument('--cfgs',nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('-t','--tslice_fact',type=float,help='what time factor to cut by? [0.5 -> NT / 2]')
parser.add_argument('-o',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('-v',default=True,action='store_const',const=False,help='verbose? [%(default)s]')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')
if args.data not in ['spec','formfac']:
    print('unrecognized data type')
    print(args.data,' not in [ spec formfac ]')
    sys.exit()
if args.data == 'spec' and args.tslice_fact is None:
    print('tslicing spec must specify tslice_fact')
    sys.exit()

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
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,'',params)

src_ext = "%d-%d" %(params['si'],params['sf'])

for c in cfgs_run:
    no = str(c)
    params['CFG'] = no
    params = c51.ensemble(params)
    d_dir = params['prod']+'/'+args.data+'_4D/'+no
    if args.data == 'spec':
        tslice.tslice(
            root       = d_dir,
            name_input = "spec_4D",
            name_output= "spec_4D_tslice",
            overwrite  = args.o,
            tslice_fact= args.tslice_fact,
            dset_patterns=["4D_correlator/x[0-9]+_y[0-9]+_z[0-9]+_t[0-9]+"],
            boundary_sign_flip=True
        )
    elif args.data == 'formfac':
        tslice.tslice(
            root       = d_dir,
            name_input = "formfac_4D",
            name_output= "formfac_4D_tslice",
            overwrite  = args.o,
            boundary_sign_flip=False
        )
