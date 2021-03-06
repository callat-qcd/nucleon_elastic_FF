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
parser.add_argument('-t','--t_sep',nargs='+',type=int,help='values of t_sep [default = all]')
parser.add_argument('-c','--current',type=str,nargs='+',help='pick a specific current or currents? [A3 V4 ...]')
parser.add_argument('-o',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('-v',default=True,action='store_const',const=False,help='verbose? [%(default)s]')
parser.add_argument('-f','--force',default=False,action='store_const',const=True,help='concat even if cfgs missing? [%(default)s]')
parser.add_argument('--fout',type=str,help='name of output file')
parser.add_argument('--src_index',nargs=3,type=int,help='specify si sf ds')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.complex64
ff_data_dir = c51.data_dir_4d % params
utils.ensure_dirExists(ff_data_dir)

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

print('beginning concatenation:')
print('    srcs:',src_ext)
print('    ',params['particles'],flav_spin)
if args.current != None:
    params['curr_4d'] = args.current
print('    ',params['curr_4d'])
cfgs_set = "%d-%d" %(cfgs_run[0],cfgs_run[-1])
print('    cfgs:',cfgs_set)
if args.t_sep != None:
    params['t_seps'] = args.t_sep

for corr in params['particles']:
    for fs in flav_spin:
        for curr in params['curr_4d']:
            if args.fout:
                fout_name = args.fout
            else:
                fout_name = ff_data_dir+'/formfac_4D_'+ens_s+'_'+corr+'_'+fs+'_'+curr+'_cfgs_'+cfgs_set+'_srcs_'+src_ext+'.h5'
            for tsep in params['t_seps']:
                dt = str(tsep)
                params['T_SEP'] = dt
                if '_np' in corr:
                    dt = '-'+dt
                print(corr,fs,'tsep=%s' %dt,curr)
                f5_out = h5.open_file(fout_name,'a')
                try:
                    f5_out.create_group(h5_root_path,corr+'_'+fs+'_tsep_'+dt+'_sink_mom_px'+m0+'_py'+m1+'_pz'+m2,createparents=True)
                except:
                    pass
                h5_out_path  = h5_root_path +'/'+corr+'_'+fs+'_tsep_'+dt
                h5_out_path += '_sink_mom_px'+m0+'_py'+m1+'_pz'+m2
                fin_path =  corr+'_'+fs+'_tsep_'+dt+'_sink_mom_px'+m0+'_py'+m1+'_pz'+m2
                fin_path += '/'+curr+'/src_avg/4D_correlator/local_current'
                get_data = True
                if curr in f5_out.get_node(h5_out_path) and not args.o:
                    get_data = False
                if curr in f5_out.get_node(h5_out_path) and args.o:
                    f5_out.remove_node(h5_out_path,curr,recursive=True)
                f5_out.close()
                if get_data:
                    cfgs_srcs = []
                    first_data = True
                    # make sure all configs exist
                    if not args.force:
                        print('    checking for all files')
                        concat = True
                        for cfg in cfgs_run:
                            no = str(cfg)
                            fin_file = ff_data_dir+'/../formfac_4D_tslice_src_avg/'+no+'/formfac_4D_tslice_src_avg_'+ens_s+'_'+no+'_'+val+'_mq'+mv_l+'_px0py0pz0_dt'+str(tsep)+'_Srcs'+src_ext+'_src_avg_SS.h5'
                            if not os.path.exists(fin_file):
                                print('    MISSING cfg=%d' %cfg)
                                concat = False
                    else:
                        concat = True
                    if concat:
                        print('    concatenating files!')
                        for cfg in cfgs_run:
                            sys.stdout.write('    cfg=%4d\r' %(cfg))
                            sys.stdout.flush()
                            no = str(cfg)
                            fin_file = ff_data_dir+'/../formfac_4D_tslice_src_avg/'+no+'/formfac_4D_tslice_src_avg_'+ens_s+'_'+no+'_'+val+'_mq'+mv_l+'_px0py0pz0_dt'+str(tsep)+'_Srcs'+src_ext+'_src_avg_SS.h5'
                            if os.path.exists(fin_file):
                                fin = h5.open_file(fin_file,'r')
                                tmp = fin.get_node('/'+fin_path).read()
                                fin.close()
                                f5_out = h5.open_file(fout_name,'a')
                                if first_data:
                                    shape = (0,)+tmp.shape
                                    data = np.zeros((1,)+tmp.shape,dtype=tmp.dtype)
                                    data[0] = tmp
                                    f5_out.create_earray(h5_out_path+'/'+curr,'local_current',shape=shape,createparents=True,obj=data,expectedrows=len(cfgs_run))
                                    first_data = False
                                else:
                                    data = f5_out.get_node(h5_out_path+'/'+curr+'/local_current')
                                    data.append(np.array([tmp]))
                                f5_out.close()
                                cfgs_srcs.append([cfg,params['N_SEQ']])
                            else:
                                print('missing',fin_file)
                        #print(cfgs_srcs)
                        cfgs_srcs = np.array(cfgs_srcs)
                        print('    Nc=%4d, Ns=%.7f' %(cfgs_srcs.shape[0],cfgs_srcs.mean(axis=0)[1]))
                else:
                    print('data exists and overwrite = False')
