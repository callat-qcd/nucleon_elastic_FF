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
parser = argparse.ArgumentParser(description='get fh spec data from h5 files')
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
}

curr_dict = {
    'proton'      :['A3_DD','A3_UU','V4_DD','V4_UU', 'S_UU', 'S_DD'],
    'lambda_z'    :['A3_DD','A3_UU','V4_DD','V4_UU', 'S_UU', 'S_DD'],
    'sigma_p'     :['A3_UU','V4_UU', 'S_UU'],
    'xi_z'        :['A3_UU','V4_UU', 'S_UU'],
    'delta_pp'    :['A3_UU','V4_UU', 'S_UU'],
    'sigma_star_p':['A3_UU','V4_UU', 'S_UU'],
    'xi_star_z'   :['A3_UU','V4_UU', 'S_UU'],
    'kplus'       :['V4_UU'],
    'kminus'      :['V4_DD'],
    'piplus'      :['V4_DD','V4_UU'],
    'piminus'     :['V4_DD','V4_UU'],
}

baryons  = ['proton', 'lambda_z', 'sigma_p', 'xi_z', 'delta_pp', 'sigma_star_p', 'xi_star_z']

for corr in baryons:
    spin_dict[corr+'_np'] = spin_dict[corr]
    curr_dict[corr+'_np'] = curr_dict[corr]

#print(spin_dict)
mesons = ['piminus','piplus','kplus']

baryons_np = [p+'_np' for p in baryons]
baryons = baryons + baryons_np
params['MQ'] = 'ml'+params['MV_L']+'_ms'+params['MV_S']

psq_lst    = list(range(0,args.psq_max+1,1))

for cfg in cfgs_run:
    no = str(cfg)
    params['CFG'] = no
    params = c51.ensemble(params)
    m_files = []
    b_files = []
    for src in srcs[cfg]:
        params['SRC'] = src
        # mesons
        spec_name = c51.names['fh_mesons'] % params
        spec_file =  params['fh_mesons']+'/'+spec_name +'.h5'
        utils.check_file(spec_file,params['fh_mesons_size'], params['file_time_delete'], params['corrupt'])
        if os.path.exists(spec_file):
            m_files.append(spec_file)
        # baryons
        spec_name = c51.names['fh_baryons'] % params
        spec_file =  params['fh_mesons']+'/'+spec_name +'.h5'
        utils.check_file(spec_file,params['fh_baryons_size'], params['file_time_delete'], params['corrupt'])
        if os.path.exists(spec_file):
            b_files.append(spec_file)

    for ftmp in m_files:
        src = ftmp.split('_')[-1].split('.')[0]
        src_split = sources.src_split(src)
        t_src = int(src.split('t')[1])
        mq = params['MQ'].replace('.','p')
        with h5.open_file(data_dir+'/'+ens_s+'_'+no+'_fh_srcs'+src_ext+'.h5','a') as f5:
            mq_dir = '/'+val_p+'/fh/'+mq
            for corr in mesons:
                for curr in curr_dict[corr]:
                    try:
                        f5.create_group(mq_dir,corr+"_"+curr,createparents=True)
                        f5.flush()
                    except:
                        pass
            # we can make baryon base dirs even in meson loop
            for corr in baryons:
                for curr in curr_dict[corr]:
                    for s in spin_dict[corr]:
                        try:
                            f5.create_group(mq_dir+'/'+corr+"_"+curr,s,createparents=True)
                            f5.flush()
                        except:
                            pass

            # PSEUDO SCALAR MESONS
            for corr in mesons:
                for curr in curr_dict[corr]:
                    spec_dir = mq_dir +'/'+ corr + "_"+curr
                    get_data = False
                    if src not in f5.get_node(spec_dir) or (args.o and src in f5.get_node(spec_dir)):
                        get_data = True

                    if get_data:
                        with h5.open_file(ftmp, 'r') as fin:
                            # For mesons currents comes first
                            # for curr in curr_dict[corr]:
                            pt = fin.get_node('/PS/'+curr+'/'+corr+'/'+src_split+'/px0_py0_pz0').read()
                            sh = fin.get_node('/SS/'+curr+'/'+corr+'/'+src_split+'/px0_py0_pz0').read()
                            nt = len(pt)
                            data = np.zeros([nt,2,1], dtype=dtype)
                            data[:,0,0] = sh
                            data[:,1,0] = pt

                            if not np.any(np.isnan(data)):
                                if args.v:
                                    sys.stdout.write("%4s  %6s  %5s %s\r" %(no,corr,curr,src))
                                    sys.stdout.flush()
                                if src not in f5.get_node(spec_dir):
                                    f5.create_array(spec_dir,src,data, createparents=True)
                                elif src in f5.get_node(spec_dir) and args.o:
                                    f5.get_node(spec_dir+'/'+src)[:] = data
                                elif src in f5.get_node(spec_dir) and not args.o:
                                    print('  skipping %s: overwrite = False; %s %s' %(corr,no,src))
                            else:
                                print('  NAN',no,src)
    for ftmp in b_files:
        src = ftmp.split('_')[-1].split('.')[0]
        src_split = sources.src_split(src)
        t_src = int(src.split('t')[1])
        mq = params['MQ'].replace('.','p')
        with h5.open_file(data_dir+'/'+ens_s+'_'+no+'_fh_srcs'+src_ext+'.h5','a') as f5:
            mq_dir = '/'+val_p+'/fh/'+mq
            for corr in baryons:
                for curr in curr_dict[corr]:
                    spec_dir = mq_dir +'/'+ corr + "_"+curr
                    get_data = False
                    for s in spin_dict[corr]:
                        if src not in f5.get_node(spec_dir+'/'+s):
                            get_data = True
                        if args.o and (src in f5.get_node(spec_dir+'/'+s)):
                            get_data = True
                    if get_data:
                        with h5.open_file(ftmp, 'r') as fin:
                            for s in spin_dict[corr]:
                                spec_dir = mq_dir +'/'+ corr+"_"+curr+"/"+s
                                pt = fin.get_node('/PS/fh_'+corr+"_"+curr+'/'+s+'/'+src_split+"/px0_py0_pz0").read()
                                sh = fin.get_node('/SS/fh_'+corr+"_"+curr+'/'+s+'/'+src_split+"/px0_py0_pz0" ).read()
                                nt = len(pt)
                                data = np.zeros([nt,2,1],dtype=dtype)
                                data[:,0,0] = sh
                                data[:,1,0] = pt
                                if not np.any(np.isnan(data)):
                                    if args.v:
                                        sys.stdout.write("%4s  %6s  %5s %9s %s\r" %(no,corr,curr,s,src))
                                        sys.stdout.flush()
                                    if src not in f5.get_node(spec_dir):
                                        f5.create_array(spec_dir,src,data, createparents=True)
                                    elif src in f5.get_node(spec_dir) and args.o:
                                        f5.get_node(spec_dir+'/'+src)[:] = data
                                    elif src in f5.get_node(spec_dir) and not args.o:
                                        print('  skipping %s: overwrite = False: %s %s ' %(corr+"_"+curr+'/'+s,no,src))
                                else:
                                    print('  NAN',no,src)
