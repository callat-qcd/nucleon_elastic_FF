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
parser.add_argument('cfgs',nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('-s','--src',type=str,help='src [xXyYzZtT] None=All')
parser.add_argument('-o',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('--move',default=False,action='store_const',const=True,help='move bad files? [%(default)s]')
parser.add_argument('-v',default=True,action='store_const',const=False,help='verbose? [%(default)s]')
parser.add_argument('--src_set',nargs=3,type=int,help='specify si sf ds')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.complex64
tmp_data_dir = c51.tmp_data_dir % params
utils.ensure_dirExists(tmp_data_dir)

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
if args.src_set:# override src index in sources and area51 files for collection
    params['si'] = args.src_set[0]
    params['sf'] = args.src_set[1]
    params['ds'] = args.src_set[2]
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
        f5 = h5.open_file(tmp_data_dir+'/'+ens_s+'_'+no+'_srcs'+src_ext+'.h5','a')
        mq = params['MQ'].replace('.','p')
        spec_dir = '/'+val_p+'/spec/'+mq
        for corr in mesons:
            try:
                f5.create_group(spec_dir,corr,createparents=True)
                f5.flush()
            except:
                pass
        for corr in par:
            for s in spin_dict[corr]:
                try:
                    f5.create_group(spec_dir+'/'+corr,s,createparents=True)
                    f5.flush()
                except:
                    pass
        # PSEUDO SCALAR MESONS
        for corr in mesons:
            get_data = False
            if src not in f5.get_node(spec_dir+'/'+corr):
                get_data = True
            if args.o and src in f5.get_node(spec_dir+'/'+corr):
                get_data = True
            if get_data:
                fin = h5.open_file(ftmp,'r')
                tmp_dir = spec_dir+'/'+corr
                p_lst = utils.p_lst(params['MESONS_PSQ_MAX'])
                for mom in p_lst:
                    if mom not in f5.get_node(tmp_dir):
                        f5.create_group(tmp_dir,mom)
                    mom_dir = tmp_dir + '/'+mom
                    pt = fin.get_node('/pt/'+corr+'/'+src_split+'/'+mom).read()
                    sh = fin.get_node('/sh/'+corr+'/'+src_split+'/'+mom).read()
                    nt = len(pt)
                    data = np.zeros([nt,2,1],dtype=dtype)
                    data[:,0,0] = sh
                    data[:,1,0] = pt
                    if not np.any(np.isnan(data)):
                        if args.v: print(no,corr,src,mom)
                        if src not in f5.get_node(mom_dir):
                            f5.create_array(mom_dir,src,data)
                        elif src in f5.get_node(mom_dir) and args.o:
                            f5.get_node(mom_dir+'/'+src)[:] = data
                        elif src in f5.get_node(mom_dir) and not args.o:
                            print('  skipping %s: overwrite = False; %s %s' %(corr,no,src))
                    else:
                        print('  NAN',no,src)
                fin.close()
        # BARYONS
        for corr in par:
            get_data = False
            for s in spin_dict[corr]:
                if src not in f5.get_node(spec_dir+'/'+corr+'/'+s):
                    get_data = True
                if args.o and src in f5.get_node(spec_dir+'/'+corr+'/'+s):
                    get_data = True
            if get_data:
                fin = h5.open_file(ftmp,'r')
                for s in spin_dict[corr]:
                    tmp_dir = spec_dir+'/'+corr+'/'+s
                    p_lst = utils.p_lst(params['BARYONS_PSQ_MAX'])
                    for mom in p_lst:
                        if mom not in f5.get_node(tmp_dir):
                            f5.create_group(tmp_dir,mom)
                        mom_dir = tmp_dir + '/'+mom
                        pt = fin.get_node('/pt/'+corr+'/'+s+'/'+src_split+'/'+mom).read()
                        sh = fin.get_node('/sh/'+corr+'/'+s+'/'+src_split+'/'+mom).read()
                        nt = len(pt)
                        data = np.zeros([nt,2,1],dtype=dtype)
                        data[:,0,0] = sh
                        data[:,1,0] = pt
                        if not np.any(np.isnan(data)):
                            if args.v:
                                print(no,corr,s,src,mom)
                            if src not in f5.get_node(mom_dir):
                                f5.create_array(mom_dir,src,data)
                            elif src in f5.get_node(mom_dir) and args.o:
                                f5.get_node(mom_dir+'/'+src)[:] = data
                            elif src in f5.get_node(mom_dir) and not args.o:
                                print('  skipping %s: overwrite = False: %s %s' %(corr,no,src))
                        else:
                            print('  NAN',no,src)
                fin.close()
        f5.close()
