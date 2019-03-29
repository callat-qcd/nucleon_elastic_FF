#!/sw/summit/python/3.7/anaconda3/5.3.0/bin/python
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
    f_out = data_avg_dir+'/'+base+'_avg.h5'
else:
    f_out = args.fout

fin_files = glob(data_dir+'/'+ens+'_*.h5')
if args.cfg == None:
    cfgs = []
    for f in fin_files:
        cfg = f.split('_')[-1].split('.')[0]
        cfgs.append(int(cfg))
    cfgs.sort()
else:
    cfgs = utils.parse_cfg_argument(args.cfgs)

smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
val_p = val.replace('.','p')

mv_l = params['MV_L']


mq_list = [params['MV_L']]
mq = mq_list[0]

spin = ['spin_up','spin_dn']
par  = ['proton','proton_np']

corr = 'piplus'
p_lst = utils.p_lst(params['MESONS_PSQ_MAX'])
for mom in p_lst:
    cfgs_srcs = []
    spec = np.array([],dtype=dtype)
    first_data = True
    mqs = 'ml'+mq.replace('.','p')
    for cfg in cfgs:
        no = str(cfg)
        good_cfg = False
        if os.path.exists(data_dir+'/'+ens+'_'+no+'.h5'):
            fin = h5.open_file(data_dir+'/'+ens+'_'+no+'.h5','r')
            try:
                srcs = fin.get_node('/'+val_p+'/spec/'+mqs+'/'+corr+'/'+mom)
                if srcs._v_nchildren > 0:
                    good_cfg = True
            except:
                print('ERROR reading ',data_dir+'/'+ens+'_'+no+'.h5')
        #    fin.close()
        if good_cfg:
            ns = 0
            tmp = []
            for src in srcs:
                tmp.append(src.read())
                ns += 1
            if args.v:
                print(corr,mq,no,'Ns = ',ns)
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
    nc = cfgs_srcs.shape[0]
    ns_avg = cfgs_srcs.mean(axis=0)[1]
    print(corr,mq,mom,'Nc=',nc,'Ns=',ns_avg)
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
sys.exit()


for corr in par:
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
            if os.path.exists(data_dir+'/'+ens+'_'+no+'.h5'):
                fin = h5.open_file(data_dir+'/'+ens+'_'+no+'.h5')
                try:
                    srcs = fin.get_node('/'+val_p+'/spectrum/'+mqs+'/'+corr+'/'+s)
                    if srcs._v_nchildren > 0:
                        good_cfg = True
                except:
                    print('ERROR reading ',data_dir+'/'+ens+'_'+no+'.h5')
            if good_cfg:
                ns = 0
                tmp = []
                for src in srcs:
                    tmp.append(src.read())
                    ns += 1
                if args.v:
                    print(corr,s,mq,no,'Ns = ',ns)
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
        tmp_dir = '/'+val_p+'/spectrum/'+mqs
        add_spec = True
        if corr in fout.get_node(tmp_dir) and not args.o:
            print(tmp_dir+'/'+corr+' exists: overwrite = False')
            add_spec = False
        elif corr in fout.get_node(tmp_dir) and args.o:
            fout.remove_node(tmp_dir,corr,recursive=True)
            fout.create_group(tmp_dir,corr)
        elif corr not in fout.get_node(tmp_dir):
            fout.create_group(tmp_dir,corr)
        if add_spec:
            c_dir = tmp_dir + '/' + corr
            cfgs_srcs = spin_data['cfgs_srcs']
            nc = cfgs_srcs.shape[0]
            ns_avg = cfgs_srcs.mean(axis=0)[1]
            print(corr,mq,'Nc=',nc,'Ns=',ns_avg)
            fout.create_array(c_dir,'cfgs_srcs',cfgs_srcs)
            for s in spin:
                fout.create_array(c_dir,s,spin_data[s])
        fout.close()
