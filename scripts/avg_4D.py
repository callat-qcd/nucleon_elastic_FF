from __future__ import print_function
import os, sys, argparse
import numpy as np
np.set_printoptions(linewidth=180)
import tables as h5
import warnings
warnings.simplefilter('ignore', h5.NaturalNameWarning)
from glob import glob
import nucleon_elastic_ff.data.scripts.average as average

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

cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,'',params)

src_ext = "%d-%d" %(params['si'],params['sf'])

for c in cfgs_run:
    no = str(c)
    params['CFG'] = no
    params = c51.ensemble(params)
    d_dir = params['prod']+'/'+args.data+'_4D_tslice/'+no
    if args.data == 'spec':
        average.spec_average(root=d_dir, overwrite=args.o, expected_sources=srcs[c], file_name_addition=src_ext)
    elif args.data == 'formfac':
        average.source_average(root=d_dir, overwrite=args.o, expected_sources=srcs[c], file_name_addition=src_ext)
