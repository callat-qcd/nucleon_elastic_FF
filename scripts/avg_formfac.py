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
parser.add_argument('--cfgs',nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('-t','--t_sep',nargs='+',type=int,help='values of t_sep [default = all]')
parser.add_argument('-c','--current',type=str,nargs='+',help='pick a specific current or currents? [A3 V4 ...]')
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

params['MQ'] = params['MV_L']

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

h5_root_path = '/'+val_p+'/formfac/ml'+params['MV_L'].replace('.','p')

if args.t_sep == None:
    pass
else:
    params['t_seps'] = args.t_sep
print('getting t_sep values')
print(params['t_seps'])
if args.current != None:
    params['curr_0p'] = args.current
print('currents')
print('    ',params['curr_0p'])

for corr in params['particles']:
    for fs in flav_spin:
        for tsep in params['t_seps']:
            dt = str(tsep)
            if '_np' in corr:
                dt = '-'+dt
            h5_path = h5_root_path+'/'+corr+'_'+fs+'_tsep_'+dt+'_sink_mom_px0_py0_pz0'
            for curr in params['curr_0p']:
                f5_out = h5.open_file(f_out,'a')
                curr_dir = h5_path +'/'+curr
                try:
                    f5_out.create_group(h5_path,curr,createparents=True)
                    f5_out.flush()
                except:
                    pass
                p_lst = ['px0_py0_pz0']
                for mom in p_lst:
                    mom_dir = curr_dir+'/'+mom
                    print(mom_dir)
                    get_data = True
                    if mom in f5_out.get_node(curr_dir) and not args.o:
                        print('    data exists and overwrite=False')
                        get_data = False
                    if get_data:
                        cfgs_srcs = []
                        #data = np.array([],dtype=dtype)
                        first_data = True
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
                                    if mom_dir in fin.get_node('/'):
                                        srcs = fin.get_node(mom_dir)
                                        if srcs._v_nchildren > 0:
                                            good_cfg = True
                                    else:
                                        print('NOT COLLECTED:',cfg,mom_dir)
                                        good_cfg = False
                                except:
                                    print('ERROR reading ',file_in)
                            if good_cfg:
                                ns = 0
                                tmp = []
                                for src in srcs:
                                    tmp.append(src.read())
                                    ns += 1
                                sys.stdout.write('    cfg=%4d Ns = %d\r' %(cfg,ns))
                                sys.stdout.flush()
                                tmp = np.array(tmp)
                                if first_data:
                                    data = np.zeros((1,)+tmp.mean(axis=0).shape,dtype=dtype)
                                    data[0] = tmp.mean(axis=0)
                                    first_data = False
                                else:
                                    data = np.append(data,[tmp.mean(axis=0)],axis=0)
                                cfgs_srcs.append([cfg,ns])
                            fin.close()
                        if len(cfgs_srcs) > 0:
                            cfgs_srcs = np.array(cfgs_srcs)
                            ''' perform time-reversal on neg par correlators '''
                            if '_np' in corr:
                                print('PERFORMING TIME_REVERSAL:',corr)
                                # FORMFAC files already have -1 applied
                                data = utils.time_reverse(data,phase=1,time_axis=1)
                            print('    Nc=%4d, Ns=%.7f' %(cfgs_srcs.shape[0],cfgs_srcs.mean(axis=0)[1]))
                            data_slice = data[:,0:tsep+1]
                            if mom in f5_out.get_node(curr_dir):
                                f5_out.remove_node(curr_dir,mom,recursive=True)
                            f5_out.create_group(curr_dir,mom)
                            f5_out.create_array(mom_dir,'cfgs_srcs',cfgs_srcs)
                            f5_out.create_array(mom_dir,'local_curr',data_slice)
                            f5_out.flush()
                        else:
                            print('no data collected')
                f5_out.close()
