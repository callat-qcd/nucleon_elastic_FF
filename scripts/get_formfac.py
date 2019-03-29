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

flav_spin = []
for flav in params['flavs']:
    for spin in params['spins']:
        flav_spin.append(flav+'_'+spin)

'''
gf1p0_w3p0_n30_M51p3_L512_a1p5
    formfac
        ml0p0158
            proton_UU_up_up_t0_31_tsep_10_sink_mom_px0_py0_pz0
                A3, curr_p and curr_0p
                    SRC
                        MOM
                            local_current
'''

for cfg in cfgs_run:
    no = str(cfg)
    print(no)
    params['CFG'] = no
    params = c51.ensemble(params)
    files = []
    for src in srcs[cfg]:
        params['SRC'] = src
        ff_name = c51.names['coherent_ff'] % params
        ff_file = params['formfac'] +'/'+ ff_name+'.h5'
        utils.check_file(ff_file,params['ff_size'],params['file_time_delete'],params['corrupt'])
        if os.path.exists(ff_file):
            files.append(ff_file)
    for ftmp in files:
        f_in = h5.open_file(f_in,'r')
        src = ftmp.split('_')[-1].split('.')[0]
        src_split = sources.src_split(src)
        t_src = src.split('t')[1]
        mq = params['MQ'].replace('.','p')
        f5 = h5.open_file(data_dir+'/'+ens_s+'_'+no+'.h5','a')
        ff_dir = '/'+val_p+'/formfac/ml'+mq
        for corr in params['particles']:
            for fs in flav_spin:
                for tsep in params['t_seps']:
                    dt = tsep
                    if '_np' in corr:
                        dt = '-'+dt
                    ff = corr+'_'+fs+'_t0_'+t_src+'_tsep_'+dt+'_sink_mom_px0_py0_pz0'
                    for curr in params['curr_p'] + params['curr_0p']:
                        if curr in params['curr_0p']:
                            p_lst = ['px0_py0_pz0']
                        else:
                            p_lst = utils.p_simple_lst(n=4)
                        get_data = True
                        for mom in p_lst:
                            try:
                                f5.create_group(ff_dir+'/'+ff+'/'+curr,mom,createparents=True)
                                f5.flush()
                            mom_dir = ff_dir+'/'+ff+'/'+curr+'/'+mom
                            if src in f5.get_node(mom_dir) and not args.o:
                                get_data = False
                        if get_data:
                            for mom in p_lst:
                                d_path = '/'+ff+'/'+curr+'/'+src_split+'/'+mom+'/local_current'
                                data = f_in.get_node(d_path)
                                mom_dir = ff_dir+'/'+ff+'/'+curr+'/'+mom
                                if not np.any(np.isnan(data)):
                                    if args.v: print(no,ff,curr,mom,src)
                                    if src not in f5.get_node(mom_dir):
                                        f5.create_array(mom_dir,src,data)
                                    elif src in f5.get_node(mom_dir) and args.o:
                                        f5.get_node(mom_dir+'/'+src)[:] = data
                                    elif src in f5.get_node(mom_dir) and not args.o:
                                        print('  skipping ',ff,': overwrite = False',no,curr,mom,src)
                        else:
                            print(ff,curr)
                            print('    data exists and overwrite=False')
        f5.close()
        f_in.close()