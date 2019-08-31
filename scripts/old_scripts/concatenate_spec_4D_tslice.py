from __future__ import print_function
from __future__ import print_function
import os, sys, argparse
import numpy as np
np.set_printoptions(linewidth=180)
import tables as h5
import warnings
warnings.simplefilter('ignore', h5.NaturalNameWarning)
from glob import glob

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
parser.add_argument('-o',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('-v',default=True,action='store_const',const=False,help='verbose? [%(default)s]')
parser.add_argument('--fout',type=str,help='name of output file')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.complex64
data_dir = c51.data_dir % params
if not os.path.exists(data_dir+'/avg'):
    os.makedirs(data_dir+'/avg')
utils.ensure_dirExists(data_dir)

# give empty '' to in place of args.src to generate all srcs/cfg
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,'',params)
if 'indvdl' in ens:
    params['N_SEQ'] = 1
else:
    params['N_SEQ'] = len(srcs[cfgs_run[0]])

smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
val_p = val.replace('.','p')

mv_l = params['MV_L']
params['MQ'] = mv_l

h5_root_path = '/'+val_p+'/spec_4D/ml'+mv_l.replace('.','p')

par = ['proton','proton_np']

if args.fout:
    fout_name = args.fout
else:
    fout_name = data_dir+'/avg/spec_4D_'+ens_s+'_avg.h5'
f5_out = h5.open_file(fout_name,'a')
for corr in params['particles']:
    print(corr)
    try:
        f5_out.create_group(h5_root_path,corr,createparents=True)
    except:
        pass
    h5_out_path = h5_root_path+'/'+corr
    fin_path = '/sh/'+corr+'/spin_avg/4D_correlator/src_avg'
    get_data = True
    if '4D_correlator' in f5_out.get_node(h5_out_path) and not args.o:
        get_data = False
    if get_data:
        cfgs_srcs = []
        first_data = True
        for cfg in cfgs_run:
            sys.stdout.write('    cfg=%4d\r' %(cfg))
            sys.stdout.flush()
            no = str(cfg)
            cfg_file = data_dir+'/../spec_4D_tslice_avg/'+no+'/spec_4D_tslice_avg_'+ens_s+'_'+no+'_'+val+'_mq'+mv_l+'_src_avg.h5'
            if os.path.exists(cfg_file):
                fin = h5.open_file(cfg_file,'r')
                tmp = fin.get_node('/'+fin_path).read()
                n_srcs = len(fin.get_node('/'+fin_path)._v_attrs['meta'].split('\n')) / 2
                fin.close()
                if first_data:
                    data = np.zeros((1,)+tmp.shape,dtype=tmp.dtype)
                    data[0] = tmp
                    first_data = False
                else:
                    data = np.append(data,[tmp],axis=0)
                cfgs_srcs.append([cfg,int(n_srcs)])
        cfgs_srcs = np.array(cfgs_srcs)
        print('    Nc=%4d, Ns=%.7f' %(cfgs_srcs.shape[0],cfgs_srcs.mean(axis=0)[1]))
        if '4D_correlators' in f5_out.get_node(h5_out_path):
            f5_out.remove_node(h5_out_path,'4D_correlator',recursive=True)
        f5_out.create_group(h5_out_path,'4D_correlator')
        #f5_out.create_array(h5_out_path+'/'+'4D_correlator','cfgs_srcs',cfgs_srcs)
        f5_out.create_array(h5_out_path+'/'+'4D_correlator','spin_avg',data)
        f5_out.flush()
    else:
        print('data exists and overwrite = False')

f5_out.close()
