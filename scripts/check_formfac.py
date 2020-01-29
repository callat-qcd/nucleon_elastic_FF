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
parser.add_argument('cfgs',        nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('-t','--t_sep',nargs='+',type=int,help='values of t_sep [default = all]')
parser.add_argument('--src_set',   nargs=3,type=int,help='specify si sf ds')
parser.add_argument('-s','--src',  type=str,help='src [xXyYzZtT] None=All')
parser.add_argument('-o',          default=False,action='store_const',const=True, help='overwrite? [%(default)s]')
parser.add_argument('--move',      default=False,action='store_const',const=True, help='move bad files? [%(default)s]')
parser.add_argument('-v',          default=True, action='store_const',const=False,help='verbose? [%(default)s]')
parser.add_argument('--collect',   default=False,action='store_const',const=True, help='try collecting from ff_4D files? [%(default)s]')
parser.add_argument('--curr_4D',   default=False,action='store_const',const=True, help='use 4D current selection? [%(default)s]')
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
if args.src_set:# override src index in sources and area51 files for collection
    params['si'] = args.src_set[0]
    params['sf'] = args.src_set[1]
    params['ds'] = args.src_set[2]
src_ext = "%d-%d" %(params['si'],params['sf'])
params['SRC_SET'] = src_ext
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,args.src,params)
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

if args.t_sep == None:
    pass
else:
    params['t_seps'] = args.t_sep
print('getting t_sep values')
print(params['t_seps'])

# If 0-mom files are missing, we can reconstruct from the 4D files
# but missing the T12, T34 and CHROMO_MAG operators
if args.collect and not args.curr_4D:
    sys.exit('to collect from 4D files, we must restrict the currents with --curr_4D')
if args.curr_4D:
    currents = params['curr_4d']
else:
    currents = params['curr_0p']

missing_ff_files = []
collect_files    = []
for cfg in cfgs_run:
    no = str(cfg)
    print(no)
    try:
        f5 = h5.open_file(data_dir+'/'+ens_s+'_'+no+'_srcs'+src_ext+'.h5','r')
        have_data_cfg = True
    except:
        have_data_cfg = False
    params['CFG'] = no
    params = c51.ensemble(params)
    for tsep in params['t_seps']:
        params['T_SEP'] = tsep
        params['N_SEQ'] = len(srcs[cfg])
        if ens_s == 'a15m310Lindvdl_a':
            params['N_SEQ'] = 1
        for src in srcs[cfg]:
            params['SRC'] = src
            src_split = sources.src_split(src)
            t_src = src.split('t')[1]
            ff_name = c51.names['formfac'] % params
            ff_file = params['formfac'] +'/'+ ff_name+'.h5'
            if not have_data_cfg:
                if os.path.exists(ff_file):
                    collect_files.append(ff_file)
                else:
                    missing_ff_files.append(ff_file)
            else:
                mq = params['MQ'].replace('.','p')
                ff_dir = '/'+val_p+'/formfac/ml'+mq
                for corr in params['particles']:
                    dt = str(tsep)
                    if '_np' in corr:
                        dt = '-'+dt
                    for fs in flav_spin:
                        ff_out = corr+'_'+fs+'_tsep_'+dt+'_sink_mom_px0_py0_pz0'
                        for curr in currents:
                            p_lst = ['px0_py0_pz0']
                            for mom in p_lst:
                                h5_data = ff_dir+'/'+ff_out+'/'+curr+'/'+mom+'/'+src
                                if h5_data not in f5.get_node('/'):
                                    if os.path.exists(ff_file) and ff_file not in collect_files:
                                        collect_files.append(ff_file)
                                    elif not os.path.exists(ff_file) and ff_file not in missing_ff_files:
                                        missing_ff_files.append(ff_file)
                                    elif not os.path.exists(ff_file) and ff_file in missing_ff_files:
                                        pass
                                    elif os.path.exists(ff_file) and ff_file in collect_files:
                                        pass
                                    else:
                                        print('CONFUSED')
                                        print(os.path.exists(ff_file),ff_file.split('/')[-1])
    if have_data_cfg: 
        f5.close()
    else:
        print('missing ',data_dir+'/'+ens_s+'_'+no+'_srcs'+src_ext+'.h5')

if len(missing_ff_files) > 0:
    print('missing %d formfac files' %(len(missing_ff_files)))
    tmp = open('missing_check_formfac_Srcs'+src_ext+'.lst','w')
    for f in missing_ff_files:
        no,ff = f.split('/')[-2],f.split('/')[-1]
        tmp.write(no+'/'+ff+'\n')
    tmp.close()

if len(collect_files) > 0:
    print('collect %d data sets' %(len(collect_files)))
    time.sleep(2)
    tmp = open('collect_formfac_Srcs'+src_ext+'.lst','w')
    for f in collect_files:
        no,ff = f.split('/')[-2],f.split('/')[-1]
        #print(no,ff)
        tmp.write(no+'/'+ff+'\n')
    tmp.close()

''' turn off for now as we may also be missing spec files
if args.collect:
    for ff in missing_ff_files:
        ff_4D = ff.replace('formfac','formfac_4D')
        ff_4D_tslice = ff.replace('formfac','formfac_4D_tslice')
        if os.path.exists(ff_4D) or os.path.exists(ff_4D_tslice):
            no = ff_4D.split(ens_s)[2].split('_')[1]
            src = ff_4D.split('_')[-2]
            src_split = sources.src_split(src)
            x0,y0,z0,t0 = sources.xyzt(src)
            tsep = ff_4D.split('_dt')[1].split('_')[0]
            mq = params['MQ'].replace('.','p')
            ff_dir = '/'+val_p+'/formfac/ml'+mq
            for corr in params['particles']:
                dt = str(tsep)
                if '_np' in corr:
                    dt = '-'+dt
                for fs in flav_spin:
                    ff_out = corr+'_'+fs+'_tsep_'+dt+'_sink_mom_px0_py0_pz0'
                    for curr in currents:
                        ff_4D_dir = '/'+corr+'_'+fs+'_t0_'+t0+'_tsep_'+dt+'_sink_mom_px0_py0_pz0/'+curr+'/'+src_split+'/4D_correlator/local_current'
                        if os.path.exists(ff_4D):
                            file_4D = h5.open_file(ff_4D,'r')
                            data_4D = file_4D.get_node(ff_4D_dir)
                            print(no,src,curr,dt,data_4D.shape)
                            file_4D.close()
'''
