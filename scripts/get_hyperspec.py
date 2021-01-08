from __future__ import print_function
import os, sys, argparse, shutil, datetime, time
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
parser.add_argument('cfgs',       nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('-s','--src', type=str,help='src [xXyYzZtT] None=All')
parser.add_argument('-o',         default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('--move',     default=False,action='store_const',const=True,help='move bad files? [%(default)s]')
parser.add_argument('-v',         default=True,action='store_const',const=False,help='verbose? [%(default)s]')
parser.add_argument('--src_index',nargs=3,type=int,help='specify si sf ds')
parser.add_argument('--psq_max',  type=int,default=0,
                    help=         'specify Psq max value [%(default)s]')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.complex64
data_dir = c51.data_dir % params
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
if args.src_index:# override src index in sources and area51 files for collection
    params['si'] = args.src_index[0]
    params['sf'] = args.src_index[1]
    params['ds'] = args.src_index[2]
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,args.src,params)
src_ext = "%d-%d" %(params['si'],params['sf'])
smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
val_p = val.replace('.','p')

print('MINING SPEC')

ps   = ['sh','pt']
spin_dict = {
    'proton'      :['spin_up','spin_dn'],
    'lambda_z'    :['spin_up','spin_dn'],
    'sigma_p'     :['spin_up','spin_dn'],
    'xi_z'        :['spin_up','spin_dn'],
    'delta_pp'    :['spin_upup','spin_up','spin_dn','spin_dndn'],
    'sigma_star_p':['spin_upup','spin_up','spin_dn','spin_dndn'],
    'xi_star_z'   :['spin_upup','spin_up','spin_dn','spin_dndn'],
    'omega_m'     :['spin_upup','spin_up','spin_dn','spin_dndn'],
}
par  = ['proton', 'lambda_z', 'sigma_p', 'xi_z', 'delta_pp', 'sigma_star_p', 'xi_star_z', 'omega_m']
for corr in par:
    spin_dict[corr+'_np'] = spin_dict[corr]
#print(spin_dict)
mesons = ['piplus','kplus','kminus']
par_np = [p+'_np' for p in par]
par = par + par_np
params['MQ'] = 'ml'+params['MV_L']+'_ms'+params['MV_S']

psq_lst    = list(range(0,args.psq_max+1,1))

for cfg in cfgs_run:
    no = str(cfg)
    print(no)
    params['CFG'] = no
    params = c51.ensemble(params)
    files = []
    for src in srcs[cfg]:
        params['SRC'] = src
        spec_name = c51.names['hyperspec'] % params
        spec_file = params['hyperspec'] +'/'+ spec_name+'.h5'
        utils.check_file(spec_file,params['spec_size'],params['file_time_delete'],params['corrupt'])
        if os.path.exists(spec_file):
            files.append(spec_file)
    for ftmp in files:
        src = ftmp.split('_')[-1].split('.')[0]
        src_split = sources.src_split(src)
        t_src = int(src.split('t')[1])
        f5 = h5.open_file(data_dir+'/'+ens_s+'_'+no+'_srcs'+src_ext+'.h5','a')
        mq = params['MQ'].replace('.','p')
        mq_dir = '/'+val_p+'/spec/'+mq
        for corr in mesons:
            try:
                f5.create_group(mq_dir,corr,createparents=True)
                f5.flush()
            except:
                pass
        for corr in par:
            for s in spin_dict[corr]:
                try:
                    f5.create_group(mq_dir+'/'+corr,s,createparents=True)
                    f5.flush()
                except:
                    pass
        # PSEUDO SCALAR MESONS
        psq_dict = utils.psq_dict(params['MESONS_PSQ_MAX'])
        for corr in mesons:
            spec_dir = mq_dir +'/'+ corr
            for nsq in [k for k in psq_lst if k <= max(psq_dict)]:
                try:
                    f5.create_group(spec_dir, 'psq_%d' %nsq, createparents=True)
                    f5.flush()
                except:
                    pass
                psq_dir   = spec_dir +'/psq_%d' %nsq
                get_data = False
                if src not in f5.get_node(psq_dir) or (args.o and src in f5.get_node(psq_dir)):
                    get_data = True
                    
                if get_data:
                    fin = h5.open_file(ftmp,'r')
                    psq_data = []
                    for mom in psq_dict[nsq]:                        
                        pt = fin.get_node('/pt/'+corr+'/'+src_split+'/'+mom).read()
                        sh = fin.get_node('/sh/'+corr+'/'+src_split+'/'+mom).read()
                        nt = len(pt)
                        data = np.zeros([nt,2,1],dtype=dtype)
                        data[:,0,0] = sh
                        data[:,1,0] = pt
                        psq_data.append(data)
                    psq_data = np.array(psq_data)
                    if not np.any(np.isnan(psq_data)):
                        if args.v: print("%4s  %6s  %13s  psq_%d" %(no,corr,src,nsq))
                        if src not in f5.get_node(psq_dir):
                            f5.create_array(psq_dir,src,psq_data.mean(axis=0))
                        elif src in f5.get_node(psq_dir) and args.o:
                            f5.get_node(psq_dir+'/'+src)[:] = psq_data.mean(axis=0)
                        elif src in f5.get_node(psq_dir) and not args.o:
                            print('  skipping %s: overwrite = False; %s %s psq_%d' %(corr,no,src,nsq))
                    else:
                        print('  NAN',no,src,'psq_%d' %nsq)
                    fin.close()
        # BARYONS
        psq_dict = utils.psq_dict(params['BARYONS_PSQ_MAX'])
        for corr in par:
            spec_dir = mq_dir +'/'+ corr
            for nsq in [k for k in psq_lst if k <= max(psq_dict)]:
                get_data = False
                for s in spin_dict[corr]:
                    try:
                        f5.create_group(spec_dir+'/'+ s, 'psq_%d' %nsq, createparents=True)
                        f5.flush()
                    except:
                        pass
                    psq_dir   = spec_dir +'/'+ s +'/psq_%d' %nsq
                    if src not in f5.get_node(psq_dir) or (args.o and src in f5.get_node(psq_dir)):
                        get_data = True
                if get_data:
                    fin = h5.open_file(ftmp,'r')
                    for s in spin_dict[corr]:
                        psq_dir  = spec_dir +'/'+ s +'/psq_%d' %nsq
                        psq_data = []
                        for mom in psq_dict[nsq]:
                            pt = fin.get_node('/pt/'+corr+'/'+s+'/'+src_split+'/'+mom).read()
                            sh = fin.get_node('/sh/'+corr+'/'+s+'/'+src_split+'/'+mom).read()
                            nt = len(pt)
                            data = np.zeros([nt,2,1],dtype=dtype)
                            data[:,0,0] = sh
                            data[:,1,0] = pt
                            psq_data.append(data)
                        psq_data = np.array(psq_data)
                        if not np.any(np.isnan(psq_data)):
                            if args.v:
                                print("%4s  %15s  %9s %13s  psq_%d" %(no,corr,s,src,nsq))
                            if src not in f5.get_node(psq_dir):
                                f5.create_array(psq_dir,src,psq_data.mean(axis=0))
                            elif src in f5.get_node(psq_dir) and args.o:
                                f5.get_node(psq_dir+'/'+src)[:] = psq_data.mean(axis=0)
                            elif src in f5.get_node(psq_dir) and not args.o:
                                print('  skipping %s: overwrite = False: %s %s psq_%d' %(corr,no,src,nsq))
                        else:
                            print('  NAN',no,src)
                    fin.close()
        f5.close()
