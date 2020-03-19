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
parser.add_argument('--srcs',type=str,help='optional name extension when collecting data files, e.g. srcs0-7')
parser.add_argument('--fout',type=str,help='name of output file')
parser.add_argument('--src_index',nargs=3,type=int,help='specify si sf ds')
parser.add_argument('--ddir',             type=str,default='data',help='use data or tmp_data dir to collect from [%(default)s]')
parser.add_argument('-o',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('-v',default=True,action='store_const',const=False,help='verbose? [%(default)s]')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.complex64
if args.ddir == 'data':
    data_dir = c51.data_dir % params
elif args.ddir == 'tmp_data':
    data_dir = c51.tmp_data_dir % params
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
    mp = np.array([],dtype=dtype)
    pp = np.array([],dtype=dtype)
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
                mp_srcs = fin.get_node('/'+val_p+'/dwf_jmu/'+mqs+'/midpoint_pseudo')
                pp_srcs = fin.get_node('/'+val_p+'/dwf_jmu/'+mqs+'/pseudo_pseudo')
                if mp_srcs._v_nchildren > 0 and pp_srcs._v_nchildren > 0:
                    good_cfg = True
            except:
                print('ERROR reading ',file_in)
        if good_cfg:
            ns = 0
            mp_tmp = []
            pp_tmp = []
            for src in mp_srcs:
                if src._v_name in pp_srcs:
                    mp_tmp.append(src.read())
                    pp_tmp.append(pp_srcs[src._v_name])
                    ns += 1
                else:
                    print('BAD SRC',no,mq,src)
            mp_tmp = np.array(mp_tmp)
            pp_tmp = np.array(pp_tmp)
            if args.v:
                print(mq,no,'Ns = ',ns)
            if first_data:
                mp = np.append(mp,mp_tmp.mean(axis=0))
                mp = np.reshape(mp,(1,mp.shape[0]))
                pp = np.append(pp,pp_tmp.mean(axis=0))
                pp = np.reshape(pp,(1,pp.shape[0]))
                first_data = False
            else:
                mp = np.append(mp,[mp_tmp.mean(axis=0)],axis=0)
                pp = np.append(pp,[pp_tmp.mean(axis=0)],axis=0)
            cfgs_srcs.append([cfg,ns])
        fin.close()
    cfgs_srcs = np.array(cfgs_srcs)
    nc = cfgs_srcs.shape[0]
    ns_avg = cfgs_srcs.mean(axis=0)[1]
    print('mres',mq,'Nc=',nc,'Ns=',ns_avg)
    if nc > 0:
        fout = h5.open_file(f_out,'a')
        if val_p not in fout.get_node('/'):
            fout.create_group('/',val_p)
        if 'dwf_jmu' not in fout.get_node('/'+val_p):
            fout.create_group('/'+val_p,'dwf_jmu')
        add_phiqq = True
        if mqs in fout.get_node('/'+val_p+'/dwf_jmu') and not args.o:
            print('dwf_jmu/'+mqs+' exists: overwrite = False')
            add_phiqq = False
        elif mqs in fout.get_node('/'+val_p+'/dwf_jmu') and args.o:
            fout.remove_node('/'+val_p+'/dwf_jmu',mqs,recursive=True)
            fout.create_group('/'+val_p+'/dwf_jmu',mqs)
        elif mqs not in fout.get_node('/'+val_p+'/dwf_jmu'):
            fout.create_group('/'+val_p+'/dwf_jmu',mqs)
        if add_phiqq:
            fout.create_array('/'+val_p+'/dwf_jmu/'+mqs,'midpoint_pseudo',mp)
            fout.create_array('/'+val_p+'/dwf_jmu/'+mqs,'pseudo_pseudo',pp)
            fout.create_array('/'+val_p+'/dwf_jmu/'+mqs,'cfgs_srcs',cfgs_srcs)
        fout.close()
        print('  mres ~= ',(mp.mean(axis=0)/pp.mean(axis=0)).mean(),(mp.mean(axis=0)/pp.mean(axis=0)).std()/np.sqrt(nc))
