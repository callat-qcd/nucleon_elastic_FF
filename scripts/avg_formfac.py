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
parser.add_argument('-o',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('-v',default=True,action='store_const',const=False,help='verbose? [%(default)s]')
parser.add_argument('--fout',type=str,help='name of output file')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.complex64
data_dir = c51.data_dir % params
utils.ensure_dirExists(data_dir)
data_avg_dir = data_dir+'/avg'
utils.ensure_dirExists(data_avg_dir)

if args.fout == None:
    f_out = data_avg_dir+'/'+ens_s+'_avg.h5'
else:
    f_out = args.fout

fin_files = glob(data_dir+'/'+ens_s+'_*.h5')
if args.cfgs == None:
    cfgs = []
    for f in fin_files:
        cfg = f.split('_')[-1].split('.')[0]
        cfgs.append(int(cfg))
    cfgs.sort()
else:
    cfgs = utils.parse_cfg_argument(args.cfgs,params)

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

for corr in params['particles']:
    for fs in flav_spin:
        for tsep in params['t_seps']:
            dt = str(tsep)
            if '_np' in corr:
                dt = '-'+dt
            h5_path = h5_root_path+'/'+corr+'_'+fs+'_tsep_'+dt+'_sink_mom_px0_py0_pz0'
            for curr in params['curr_p'] + params['curr_0p']:
                f5_out = h5.open_file(f_out,'a')
                curr_dir = h5_path +'/'+curr
                try:
                    f5_out.create_group(h5_path,curr,createparents=True)
                    f5_out.flush()
                except:
                    pass
                if curr in params['curr_0p']:
                    p_lst = ['px0_py0_pz0']
                else:
                    p_lst = utils.p_simple_lst(n=4)
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
                            if os.path.exists(data_dir+'/'+ens_s+'_'+no+'.h5'):
                                fin = h5.open_file(data_dir+'/'+ens_s+'_'+no+'.h5','r')
                                try:
                                    srcs = fin.get_node(mom_dir)
                                    if srcs._v_nchildren > 0:
                                        good_cfg = True
                                except:
                                    print('ERROR reading ',data_dir+'/'+ens_s+'_'+no+'.h5')
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
                        cfgs_srcs = np.array(cfgs_srcs)
                        ''' perform time-reversal on neg par correlators '''
                        if '_np' in corr:
                            print('PERFORMING TIME_REVERSAL:',corr)
                            data = utils.time_reverse(data,phase=-1,time_axis=1)
                        print('    Nc=%4d, Ns=%.7f' %(cfgs_srcs.shape[0],cfgs_srcs.mean(axis=0)[1]))
                        if mom in f5_out.get_node(curr_dir):
                            f5_out.remove_node(curr_dir,mom,recursive=True)
                        f5_out.create_group(curr_dir,mom)
                        f5_out.create_array(mom_dir,'cfgs_srcs',cfgs_srcs)
                        f5_out.create_array(mom_dir,'local_curr',data)
                        f5_out.flush()
                f5_out.close()

"""
for cfg in cfgs_run:
    no = str(cfg)
    print(no)
    params['CFG'] = no
    params = c51.ensemble(params)
    for tsep in params['t_seps']:
        f5 = h5.open_file(data_dir+'/'+ens_s+'_'+no+'.h5','a')
        params['T_SEP'] = tsep
        files = []
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
                            except:
                                pass
                            mom_dir = ff_dir+'/'+ff+'/'+curr+'/'+mom
                            if src in f5.get_node(mom_dir) and not args.o:
                                get_data = False
                        if get_data:
                            for mom in p_lst:
                                d_path = '/'+ff+'/'+curr+'/'+src_split+'/'+mom+'/local_current'
                                mom_dir = ff_dir+'/'+ff+'/'+curr+'/'+mom
                                if args.v: print(no,ff,curr,mom,src)
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
                                utils.get_write_h5_data(f_in,f5,d_path,mom_dir,src,overwrite=args.o)
                                f5.flush()
                        else:
                            print(ff,curr)
                            print('    data exists and overwrite=False')
            f_in.close()
            print('I/O break: 1 second')
            time.sleep(1)
        f5.close()
"""
