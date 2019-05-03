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
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.complex64
data_dir = c51.data_dir % params
utils.ensure_dirExists(data_dir)

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

for cfg in cfgs_run:
    no = str(cfg)
    print(no)
    params['CFG'] = no
    params = c51.ensemble(params)
    for tsep in params['t_seps']:
        f5 = h5.open_file(data_dir+'/'+ens_s+'_'+no+'.h5','a')
        params['T_SEP'] = tsep
        files = []
        params['N_SEQ'] = len(srcs[cfg])
        for src in srcs[cfg]:
            params['SRC'] = src
            ff_name = c51.names['coherent_ff'] % params
            ff_file = params['formfac'] +'/'+ ff_name+'.h5'
            utils.check_file(ff_file,params['ff_size'],params['file_time_delete'],params['corrupt'])
            if os.path.exists(ff_file):
                files.append(ff_file)
        for ftmp in files:
            print(ftmp)
            f_in = h5.open_file(ftmp,'r')
            src = ftmp.split('_')[-2].split('.')[0]
            src_split = sources.src_split(src)
            t_src = src.split('t')[1]
            mq = params['MQ'].replace('.','p')
            ff_dir = '/'+val_p+'/formfac/ml'+mq
            for corr in params['particles']:
                dt = str(tsep)
                if '_np' in corr:
                    dt = '-'+dt
                for fs in flav_spin:
                    ff_in  = corr+'_'+fs+'_t0_'+t_src+'_tsep_'+dt+'_sink_mom_px0_py0_pz0'
                    ff_out = corr+'_'+fs+'_tsep_'+dt+'_sink_mom_px0_py0_pz0'
                    for curr in params['curr_0p']:
                        p_lst = ['px0_py0_pz0']
                        get_data = True
                        for mom in p_lst:
                            try:
                                f5.create_group(ff_dir+'/'+ff_out+'/'+curr,mom,createparents=True)
                                f5.flush()
                            except:
                                pass
                            mom_dir = ff_dir+'/'+ff_out+'/'+curr+'/'+mom
                            if src in f5.get_node(mom_dir) and not args.o:
                                get_data = False
                        if get_data:
                            for mom in p_lst:
                                d_path = '/'+ff_in+'/'+curr+'/'+src_split+'/'+mom+'/local_current'
                                mom_dir = ff_dir+'/'+ff_out+'/'+curr+'/'+mom
                                if args.v: print(no,ff_in,'%10s' %curr,mom,src)
                                '''
                                data = f_in.get_node(d_path).read()
                                if not np.any(np.isnan(data)):
                                    if src not in f5.get_node(mom_dir):
                                        f5.create_array(mom_dir,src,data)
                                        print('  fresh    ',ff,no,curr,mom,src)
                                    elif src in f5.get_node(mom_dir) and args.o:
                                        f5.get_node(mom_dir+'/'+src)[:] = data
                                        print('  replace  ',ff,no,curr,mom,src)
                                    elif src in f5.get_node(mom_dir) and not args.o:
                                        print('  skipping ',ff,': overwrite = False',no,curr,mom,src)
                                '''
                                utils.get_write_h5_ff_data(f_in,f5,d_path,mom_dir,src,overwrite=args.o)
                                f5.flush()
                        else:
                            print(ff_in,curr)
                            print('    data exists and overwrite=False')
            f_in.close()
            #print('I/O break: 1 second')
            #time.sleep(1)
        f5.close()
