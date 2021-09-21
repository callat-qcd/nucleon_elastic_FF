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
parser = argparse.ArgumentParser(description='average phi_qq')
parser.add_argument('--cfgs',nargs='+',type=int,help='cfgs: ci [cf dc]')
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

mq = params['MV_L']

spin = ['spin_up','spin_dn']
par  = ['proton','proton_np']

corr = 'piplus'
p_lst = utils.p_lst(params['MESONS_PSQ_MAX'])
mqs = 'ml'+mq.replace('.','p')
for mom in p_lst:
    with h5.open_file(f_out,'r') as fout:
        if '/'+val_p+'/spec/'+mqs+'/'+corr+'/'+mom in fout.root:
            if args.o:
                avg_data = True
            else:
                avg_data = False
        else:
            avg_data = False
    if avg_data:
        cfgs_srcs = []
        spec = np.array([],dtype=dtype)
        first_data = True
        mqs = 'ml'+mq.replace('.','p')
        for cfg in cfgs:
            no = str(cfg)
            good_cfg = False
            f_open = False
            if args.srcs == None:
                file_in = data_dir+'/'+ens_s+'_'+no+'_srcs'+src_ext+'.h5'
            elif args.srcs == 'old':
                file_in = data_dir+'/'+ens_s+'_'+no+'.h5'
            else:
                file_in = data_dir+'/'+ens_s+'_'+no+'_'+args.srcs+'.h5'
            if os.path.exists(file_in):
                fin = h5.open_file(file_in,'r')
                f_open = True
                try:
                    srcs = fin.get_node('/'+val_p+'/spec/'+mqs+'/'+corr+'/'+mom)
                    if srcs._v_nchildren > 0:
                        good_cfg = True
                except:
                    print('ERROR reading ',data_dir+'/'+ens_s+'_'+no+'.h5')
            #    fin.close()
            if good_cfg:
                ns = 0
                tmp = []
                for src in srcs:
                    tmp.append(src.read())
                    ns += 1
                if args.v:
                    sys.stdout.write('%s %s %s %s Ns = %.2f\r' %(corr,mq,mom,no,ns))
                    sys.stdout.flush()
                    #print(corr,mq,mom,no,'Ns = ',ns)
                tmp = np.array(tmp)
                if first_data:
                    spec = np.zeros((1,)+tmp.mean(axis=0).shape,dtype=dtype)
                    spec[0] = tmp.mean(axis=0)
                    first_data = False
                else:
                    spec = np.append(spec,[tmp.mean(axis=0)],axis=0)
                cfgs_srcs.append([cfg,ns])
            if f_open:
                fin.close()
        cfgs_srcs = np.array(cfgs_srcs)
        nc = cfgs_srcs.shape[0]
        ns_avg = cfgs_srcs.mean(axis=0)[1]
        print(corr,mq,mom,'Nc=',nc,'Ns=',ns_avg,'\n')
        if nc > 0:
            fout = h5.open_file(f_out,'a')
            try:
                fout.create_group('/'+val_p+'/spec/'+mqs,corr,createparents=True)
            except:
                pass
            tmp_dir = '/'+val_p+'/spec/'+mqs+'/'+corr
            add_spec = True
            if mom in fout.get_node(tmp_dir) and not args.o:
                print(tmp_dir+'/'+mom+' exists: overwrite = False')
                add_spec = False
            elif mom in fout.get_node(tmp_dir) and args.o:
                fout.remove_node(tmp_dir,mom,recursive=True)
                fout.create_group(tmp_dir,mom)
            elif corr not in fout.get_node(tmp_dir):
                fout.create_group(tmp_dir,mom)
            if add_spec:
                fout.create_array(tmp_dir+'/'+mom,'corr',spec)
                fout.create_array(tmp_dir+'/'+mom,'cfgs_srcs',cfgs_srcs)
            fout.close()

for corr in par:
    print(corr)
    p_lst = utils.p_lst(params['BARYONS_PSQ_MAX'])
    ''' flip spin and momentum order in h5 dir structrure '''
    for mom in p_lst:
        with h5.open_file(f_out,'r') as fout:
            avg_data = False
            for s in spin:
                if '/'+val_p+'/spec/'+mqs+'/'+corr+'/'+mom+'/'+s not in fout.root:
                    avg_data = True
                else:
                    if args.o:
                        avg_data = True
        if avg_data:
            spin_data = dict()
            have_spin = False
            for s in spin:
                cfgs_srcs = []
                spec = np.array([],dtype=dtype)
                first_data = True
                mqs = 'ml'+mq.replace('.','p')
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
                            srcs = fin.get_node('/'+val_p+'/spec/'+mqs+'/'+corr+'/'+s+'/'+mom)
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
                        if args.v:
                            sys.stdout.write('%s %s %s %s %s Ns = %.2f\r' %(corr,s,mq,mom,no,ns))
                            sys.stdout.flush()
                            #print(corr,s,mq,no,mom,'Ns = ',ns)
                        tmp = np.array(tmp)
                        if first_data:
                            spec = np.zeros((1,)+tmp.mean(axis=0).shape,dtype=dtype)
                            spec[0] = tmp.mean(axis=0)
                            first_data = False
                        else:
                            spec = np.append(spec,[tmp.mean(axis=0)],axis=0)
                        cfgs_srcs.append([cfg,ns])
                    fin.close()
                cfgs_srcs = np.array(cfgs_srcs)
                ''' perform time-reversal on neg par correlators '''
                if '_np' in corr:
                    print('PERFORMING TIME_REVERSAL:',corr)
                    spec = utils.time_reverse(spec,phase=-1,time_axis=1)
                spin_data[s] = spec
                if 'cfgs_srcs' not in spin_data:
                    spin_data['cfgs_srcs'] = cfgs_srcs
                else:
                    if not np.all(cfgs_srcs == spin_data['cfgs_srcs']):
                        print('spin_data miss match')
                        sys.exit()
                if cfgs_srcs.shape[0] > 0:
                    have_spin = True
            if have_spin:
                fout = h5.open_file(f_out,'a')
                try:
                    fout.create_group('/'+val_p+'/spec/'+mqs,corr,createparents=True)
                except:
                    pass
                tmp_dir = '/'+val_p+'/spec/'+mqs+'/'+corr
                add_spec = True
                if mom in fout.get_node(tmp_dir) and not args.o:
                    print(tmp_dir+'/'+mom+' exists: overwrite = False')
                    add_spec = False
                elif mom in fout.get_node(tmp_dir) and args.o:
                    fout.remove_node(tmp_dir,mom,recursive=True)
                    fout.create_group(tmp_dir,mom)
                elif mom not in fout.get_node(tmp_dir):
                    fout.create_group(tmp_dir,mom)
                if add_spec:
                    c_dir = tmp_dir + '/' + mom
                    cfgs_srcs = spin_data['cfgs_srcs']
                    nc = cfgs_srcs.shape[0]
                    ns_avg = cfgs_srcs.mean(axis=0)[1]
                    print(corr,mq,mom,'Nc=',nc,'Ns=',ns_avg,'\n')
                    fout.create_array(c_dir,'cfgs_srcs',cfgs_srcs)
                    for s in spin:
                        fout.create_array(c_dir,s,spin_data[s])
                fout.close()
