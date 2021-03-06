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
parser.add_argument('--src_type',nargs='+',type=str,default=[])
parser.add_argument('--debug',default=False,action='store_const',const=True)
parser.add_argument('--n_seq',type=int)
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.complex64
ff_data_dir = c51.ff_data_dir % params
utils.ensure_dirExists(ff_data_dir)

# give empty '' to in place of args.src to generate all srcs/cfg
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,'',params,src_type=args.src_type)
if args.n_seq:
    params['N_SEQ'] = args.n_seq
else:
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

h5_root_path = '/'+val_p+'/formfac/ml'+params['MV_L'].replace('.','p')

'''
for cfg in cfgs:
    for tsep in tseps:
        make sure all files exist (all srcs)
        for particle in particles:
            for fs in flav_spin:
                for curr in currents:
'''
for cfg in cfgs_run:
    no = str(cfg)
    params['CFG'] = no
    params = c51.ensemble(params)
    for tsep in params['t_seps']:
        dt = str(tsep)
        params['T_SEP'] = dt
        ''' check to make sure all files exist '''
        all_files = True
        for src in srcs[cfg]:
            params['SRC'] = src
            ff_name = (c51.names['formfac'] % params).replace('formfac_','formfac_4D_tslice_')
            ff_file = params['formfac_4D_tslice'] +'/'+ ff_name+'.h5'
            n_curr = len(params['curr_4d'])
            n_flav = len(params['flavs'])
            n_spin = len(params['spins'])
            n_par  = len(params['particles'])
            ff_slice_size = int(params['NL'])**3 * tsep * n_curr * n_flav * n_spin * n_par * 2 * 8
            utils.check_file(ff_file,ff_slice_size,params['file_time_delete'],params['corrupt'])
            if not os.path.exists(ff_file):
                all_files = False
                print('missing ',ff_file)
        if all_files:
            ''' open out file '''
            f5_out = h5.open_file(ff_data_dir+'/formfac_'+ens_s+'_'+no+'.h5','a')
            for corr in params['particles']:
                if '_np' in corr:
                    dt = '-'+dt
                for fs in flav_spin:
                    for curr in params['curr_4d']:
                        print(corr,cfg,dt,fs,curr)
                        data = []
                        for src in srcs[cfg]:
                            if args.debug:
                                print('    %s' %src)
                            else:
                                sys.stdout.write('    %s\r' %src)
                                sys.stdout.flush()
                            params['SRC'] = src
                            ff_name = (c51.names['formfac'] % params).replace('formfac_','formfac_4D_tslice_')
                            ff_file = params['formfac_4D_tslice'] +'/'+ ff_name+'.h5'
                            f_in = h5.open_file(ff_file,'r')
                            s_split = sources.src_split(src)
                            t0 = src.split('t')[1]
                            hin_path  = '/'+corr+'_'+fs+'_t0_'+t0+'_tsep_'+dt+'_sink_mom_px0_py0_pz0/'
                            hin_path += curr+'/'+s_split+'/4D_correlator/local_current'
                            data.append(f_in.get_node(hin_path).read())
                            f_in.close()
                        hout_path  = '/'+corr+'_'+fs+'_tsep_'+dt+'_sink_mom_px0_py0_pz0/'
                        hout_path += curr+'/src_avg'
                        data = np.array(data)
                        try:
                            f5_out.create_group(hout_path,'4D_correlator',createparents=True)
                        except:
                            pass
                        print(data.shape)
                        if 'local_current' not in f5_out.get_node(hout_path+'/4D_correlator'):
                            f5_out.create_array(hout_path+'/4D_correlator','local_current',data.mean(axis=0))
                        elif 'local_current' in f5_out.get_node(hout_path+'/4D_correlator') and args.o:
                            f5_out.get_node(hout_path+'/4D_correlator/local_current')[:] = data.mean(axis=0)
                        elif 'local_current' in f5_out.get_node(hout_path+'/4D_correlator') and not args.o:
                            print('    SKIPPING: data exists and overwrite = False')
            f5_out.close()
        else:
            print(no,dt,'missing srcs')
