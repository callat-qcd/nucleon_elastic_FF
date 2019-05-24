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
ff_data_dir = c51.ff_data_dir % params
if not os.path.exists(ff_data_dir+'/avg'):
    os.makedirs(ff_data_dir+'/avg')
utils.ensure_dirExists(ff_data_dir)

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

flav_spin = []
for flav in params['flavs']:
    for spin in params['spins']:
        flav_spin.append(flav+'_'+spin)
''' ONLY doing snk_mom 0 0 0 now '''
snk_mom = params['snk_mom'][0]
m0,m1,m2 = snk_mom.split()
params['M0']=m0
params['M1']=m1
params['M2']=m2
params['MOM'] = 'px%spy%spz%s' %(m0,m1,m2)

h5_root_path = '/'+val_p+'/formfac_4D/ml'+params['MV_L'].replace('.','p')

'''

for particle in particles:
    for fs in flav_spin:
        for tsep in tseps:
            for curr in currents:
                for cfg in cfgs:
'''
if args.fout:
    fout_name = args.fout
else:
    fout_name = ff_data_dir+'/avg/formfac_'+ens_s+'_avg.h5'
f5_out = h5.open_file(fout_name,'a')
for corr in params['particles']:
    for fs in flav_spin:
        for tsep in params['t_seps']:
            dt = str(tsep)
            params['T_SEP'] = dt
            if '_np' in corr:
                dt = '-'+dt
            for curr in params['curr_4d']:
                print(corr,fs,dt,curr)
                h5_out_path =  h5_root_path+'/'+corr+'_'+fs+'_tsep_'+dt
                h5_out_path += '_sink_mom_px'+m0+'_py'+m1+'_pz'+m2
                fin_path =  corr+'_'+fs+'_tsep_'+dt+'_sink_mom_px'+m0+'_py'+m1+'_pz'+m2
                fin_path += '/'+curr+'/src_avg/4D_correlator/local_current'
                try:
                    f5_out.create_group(h5_out_path,curr,createparents=True)
                except:
                    pass
                h5_out_path = h5_out_path
                get_data = True
                if 'local_current' in f5_out.get_node(h5_out_path+'/'+curr) and not args.o:
                    get_data = False
                if get_data:
                    cfgs_srcs = []
                    first_data = True
                    for cfg in cfgs_run:
                        sys.stdout.write('    cfg=%4d\r' %(cfg))
                        sys.stdout.flush()
                        no = str(cfg)
                        if os.path.exists(ff_data_dir+'/formfac_'+ens_s+'_'+no+'.h5'):
                            fin = h5.open_file(ff_data_dir+'/formfac_'+ens_s+'_'+no+'.h5','r')
                            tmp = fin.get_node('/'+fin_path).read()
                            fin.close()
                            if first_data:
                                data = np.zeros((1,)+tmp.shape,dtype=tmp.dtype)
                                data[0] = tmp
                                first_data = False
                            else:
                                data = np.append(data,[tmp],axis=0)
                            cfgs_srcs.append([cfg,params['N_SEQ']])
                    cfgs_srcs = np.array(cfgs_srcs)
                    print('    Nc=%4d, Ns=%.7f' %(cfgs_srcs.shape[0],cfgs_srcs.mean(axis=0)[1]))
                    if curr in f5_out.get_node(h5_out_path):
                        f5_out.remove_node(h5_out_path,curr,recursive=True)
                    f5_out.create_group(h5_out_path,curr)
                    f5_out.create_array(h5_out_path+'/'+curr,'cfgs_srcs',cfgs_srcs)
                    f5_out.create_array(h5_out_path+'/'+curr,'local_current',data)
                    f5_out.flush()
                else:
                    print('data exists and overwrite = False')

f5_out.close()
