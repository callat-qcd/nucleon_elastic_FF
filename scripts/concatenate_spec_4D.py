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
data_dir = c51.data_dir_4d % params
utils.ensure_dirExists(data_dir)

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
# give empty '' to in place of args.src to generate all srcs/cfg
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,'',params)
src_ext = "%d-%d" %(params['si'],params['sf'])
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
    fout_name = data_dir+'/spec_4D_'+ens_s+'_avg'+src_ext+'.h5'
print('out file')
print(fout_name)
for corr in params['particles']:
    print(corr)
    fin_path = '/sh/'+corr+'/spin_avg/4D_correlator/src_avg'
    f5_out = h5.open_file(fout_name,'a')
    try:
        f5_out.create_group(h5_root_path,corr,createparents=True)
    except:
        pass
    h5_out_path = h5_root_path+'/'+corr
    get_data = True
    if '4D_correlator' in f5_out.get_node(h5_out_path) and not args.o:
        get_data = False
    if '4D_correlator' in f5_out.get_node(h5_out_path) and args.o:
        f5_out.remove_node(h5_out_path,'4D_correlator',recursive=True)
    f5_out.close()
    if get_data:
        cfgs_srcs = []
        first_data = True
        for cfg in cfgs_run:
            sys.stdout.write('    cfg=%4d\r' %(cfg))
            sys.stdout.flush()
            no = str(cfg)
            cfg_file = data_dir+'/../spec_4D_tslice_avg/'+no+'/spec_4D_tslice_avg_'+ens_s+'_'+no+'_'+val+'_mq'+mv_l+'_src_avg'+src_ext+'.h5'
            cfg_file = data_dir+'/../spec_4D_avg/'+no+'/spec_4D_avg_'+ens_s+'_'+no+'_'+val+'_mq'+mv_l+'_src_avg'+src_ext+'.h5'
            if os.path.exists(cfg_file):
                fin = h5.open_file(cfg_file,'r')
                tmp = fin.get_node('/'+fin_path).read()
                n_srcs = len(fin.get_node('/'+fin_path)._v_attrs['meta'].split('\n')) / 2
                fin.close()
                f5_out = h5.open_file(fout_name,'a')
                if first_data:
                    shape = (0,)+tmp.shape
                    data = np.zeros((1,)+tmp.shape,dtype=tmp.dtype)
                    data[0] = tmp
                    f5_out.create_earray(h5_out_path+'/4D_correlator','spin_avg',shape=shape,createparents=True,obj=data,expectedrows=len(cfgs_run))
                    first_data = False
                else:
                    data = f5_out.get_node(h5_out_path+'/4D_correlator/spin_avg')
                    data.append(np.array([tmp]))
                f5_out.close()
                cfgs_srcs.append([cfg,int(n_srcs)])
        cfgs_srcs = np.array(cfgs_srcs)
        print('    Nc=%4d, Ns=%.7f' %(cfgs_srcs.shape[0],cfgs_srcs.mean(axis=0)[1]))
        #f5_out.create_group(h5_out_path,'4D_correlator')
        #f5_out.create_array(h5_out_path+'/'+'4D_correlator','cfgs_srcs',cfgs_srcs)
        #f5_out.create_array(h5_out_path+'/'+'4D_correlator','spin_avg',data)
        #f5_out.flush()
    else:
        print('data exists and overwrite = False')

