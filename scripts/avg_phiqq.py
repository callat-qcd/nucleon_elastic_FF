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
parser = argparse.ArgumentParser(description='average phi_qq')
parser.add_argument('--cfgs',nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('-m','--mq',type=str,help='specify quark mass [default = all]')
parser.add_argument('-o',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('-v',default=True,action='store_const',const=False,help='verbose? [%(default)s]')
parser.add_argument('--srcs',type=str,help='optional name extension when collecting data files, e.g. srcs0-7')
parser.add_argument('--fout',type=str,help='name of output file')
parser.add_argument('--src_index',nargs=3,type=int,help='specify si sf ds')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.complex64
data_dir = c51.data_dir % params
utils.ensure_dirExists(data_dir)
data_avg_dir = data_dir+'/avg'
utils.ensure_dirExists(data_avg_dir)

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
if args.src_index:# override src index in sources and area51 files for collection
    params['si'] = args.src_index[0]
    params['sf'] = args.src_index[1]
    params['ds'] = args.src_index[2]
src_ext = "%d-%d" %(params['si'],params['sf'])

if args.fout == None:
    if args.srcs == None:
        f_out = data_avg_dir+'/'+ens_s+'_avg_srcs'+src_ext+'.h5'
    elif args.srcs == 'old':
        f_out = data_avg_dir+'/'+ens_s+'_avg.h5'
    else:
        f_out = data_avg_dir+'/'+ens_s+'_avg_'+args.srcs+'.h5'
else:
    f_out = args.fout

if args.cfgs == None:
    cfgs = range(params['cfg_i'],params['cfg_f']+params['cfg_d'],params['cfg_d'])
else:
    cfgs = utils.parse_cfg_argument(args.cfgs,params)

smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
val_p = val.replace('.','p')

if args.mq == None:
    try:
        if params['run_strange']:
            mq_lst = [params['MV_L'], params['MV_S']]
        else:
            mq_lst = [params['MV_L']]
    except:
        mq_lst = [params['MV_L']]
else:
    mq_lst = [args.mq]

for mq in mq_lst:
    cfgs_srcs = []
    phiqq = np.array([],dtype=dtype)
    first_data = True
    mqs = 'mq'+mq.replace('.','p')
    for cfg in cfgs:
        no = str(cfg)
        good_cfg = False
        if args.srcs == None:
            file_in = data_dir+'/'+ens_s+'_'+no+'_srcs'+src_ext+'.h5'
        elif args.srcs == 'old':
            file_in = data_dir+'/'+ens_s+'_'+no+'.h5'
        else:
            file_in = data_dir+'/'+ens_s+'_'+no+'_'+args.srcs+'.h5'
        if os.path.exists(file_in):
            fin = h5.open_file(file_in,'r')
            try:
                phiqq_srcs = fin.get_node('/'+val_p+'/phi_qq/'+mqs)
                if phiqq_srcs._v_nchildren > 0:
                    good_cfg = True
            except:
                print('ERROR reading ',file_in)
        if good_cfg:
            ns = 0
            phiqq_tmp = []
            for src in phiqq_srcs:
                phiqq_tmp.append(src.read())
                ns += 1
            phiqq_tmp = np.array(phiqq_tmp)
            if args.v:
                sys.stdout.write('  mq = %s, cfg = %s, NS = %d\r' %(mq,no,ns))
                sys.stdout.flush()
            if first_data:
                phiqq = np.append(phiqq,phiqq_tmp.mean(axis=0))
                phiqq = np.reshape(phiqq,(1,phiqq.shape[0]))
                first_data = False
            else:
                phiqq = np.append(phiqq,[phiqq_tmp.mean(axis=0)],axis=0)
            cfgs_srcs.append([cfg,ns])
        fin.close()
    cfgs_srcs = np.array(cfgs_srcs)
    nc = cfgs_srcs.shape[0]
    if nc > 0:
        ns_avg = cfgs_srcs.mean(axis=0)[1]
        print('')
        print('  Nc = %d, Ns_avg=%.4f' %(nc,ns_avg))
        fout = h5.open_file(f_out,'a')
        if val_p not in fout.get_node('/'):
            fout.create_group('/',val_p)
        if 'phi_qq' not in fout.get_node('/'+val_p):
            fout.create_group('/'+val_p,'phi_qq')
        add_phiqq = True
        if mqs in fout.get_node('/'+val_p+'/phi_qq') and not args.o:
            print('phi_qq/'+mqs+' exists: overwrite = False')
            add_phiqq = False
        elif mqs in fout.get_node('/'+val_p+'/phi_qq') and args.o:
            fout.remove_node('/'+val_p+'/phi_qq',mqs,recursive=True)
            fout.create_group('/'+val_p+'/phi_qq',mqs)
        elif mqs not in fout.get_node('/'+val_p+'/phi_qq'):
            fout.create_group('/'+val_p+'/phi_qq',mqs)
        if add_phiqq:
            fout.create_array('/'+val_p+'/phi_qq/'+mqs,'corr',phiqq)
            fout.create_array('/'+val_p+'/phi_qq/'+mqs,'cfgs_srcs',cfgs_srcs)
        fout.close()
