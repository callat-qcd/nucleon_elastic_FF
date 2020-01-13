#!/usr/local/bin/python


from __future__ import print_function
import os, sys, argparse, shutil, datetime, time
import numpy as np
np.set_printoptions(linewidth=180)
import tables as h5
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
import time

ens,stream = c51.ens_base()
ens_s = ens+'_'+stream

area51 = importlib.import_module(ens)
params = area51.params
params['machine'] = c51.machine
params['ENS_LONG'] = c51.ens_long[ens]
params['ENS_S']    = ens_s
params['STREAM']   = stream


np.set_printoptions(linewidth=180)
parser = argparse.ArgumentParser(description='avg mres data from h5 file')
parser.add_argument('cfgs',nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('--ml',type=str,help='quark mass [%(default)s]')
parser.add_argument('--ms',type=str,help='quark mass [%(default)s]')
parser.add_argument('--ns',type=int,help='number of srcs/cfg [%(default)s]')
parser.add_argument('-o',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('--fin',type=str,help='directory to input (which is get script output), need to end with /, leave empty for production')
parser.add_argument('--fout',type=str,help='directory to output, need to end with /, leave empty for production')
parser.add_argument('--complete',default='avg_meson_complete.txt',type=str,help='avg_meson ml, ms, cfg complete text file')
parser.add_argument('--mfix',default=False,action='store_const',const=True,help='mixed-fix? [%(default)s]')
parser.add_argument('--abs',default=False,action='store_const',const=True,help='mixed-abs? [%(default)s]')

args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.complex64
data_dir = c51.data_dir % params
utils.ensure_dirExists(data_dir)

params = sources.src_start_stop(params,ens,stream)
args.src=None
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,args.src,params)
src_ext = "%d-%d" %(params['si'],params['sf'])
smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
val_p = val.replace('.','p')

mv_l = params['MV_L']
mv_s = params['MV_S']
ms_l = params['MS_L']
ms_s = params['MS_S']


data_dir = c51.data_dir % params

bd_name = 'bad_mes_'+ens_s+'.lst'
tmp_name = ens_s
cwd = os.getcwd()

dtype = np.float32


smr='wv_w'+params['WF_S']+'_n'+params['WF_N']
params['SMR']=smr

print ('ml:', mv_l)
print ('ms:', mv_s)

# input dir
fin_dir = data_dir
# output dir
if not args.fout:
    f_out = data_dir+'/avg/mixed_'+ens_s+'_avg.h5'
else:
    f_out = args.fout

print('input:\t'+fin_dir)
print('output:\t'+f_out)

proceed = input('do you want to proceed?\t')
if proceed not in ['y','yes']:
    os.system('python '+sys.argv[0]+' -h')
    sys.exit()


completeFile = open('./'+args.complete,'a')
completeFile.write(time.strftime("%a, %d %b %Y %H:%M:%S",time.localtime())+'\n')

fout = h5.open_file(f_out,'a')

fin_files = [fn for fn in glob(fin_dir+'mixed_'+ens_s+'_*.h5')]
print( 'no cfgs = %d' %len(cfgs_run))

# MIXED STATES
mixed_states = [#'phi_uu','phi_us','phi_ss',#THESE come from the regular spectrum
    'phi_ju','phi_jj_5',#the mixed (ju) and sea (jj) pions
    'phi_js','phi_ur','phi_jr_5',#the mixed (js, ur) and sea (jr) kaon
    'phi_rs','phi_rr_5'# the mixed (sr) and sea (rr) ssbar
    ]

ml = ms_l
ms = ms_s
mls = 'ml'+ms_l.replace('.','p')
mss = 'ms'+ms_s.replace('.','p')

vs = 'val_ml'+mv_l.replace('.','p')+'_ms'+mv_s.replace('.','p')+'_sea_'+mls+'_'+mss


# MIXED SPECTRUM
states = mixed_states
for state in states:
    first_data = True
    cfgs_srcs = []
    all_cfgs = True
    for cfg in cfgs_run:
        no = str(cfg)
        try:
            fin = h5.open_file(fin_dir+'/mixed_'+ens_s+'_'+no+'.h5')
            f5dir = '/'+val_p
            srcs = fin.get_node(f5dir+'/mixed_spec/'+vs+'/'+state)
            if srcs._v_nchildren > 0:
                good_cfg = True
                if srcs._v_nchildren != 1:
                    print('%s: more than 1 source found'%(no))
            fin.close()
        except Exception as e:
            print(e)
            all_cfgs = False
            
    if not all_cfgs:
        sys.exit('missing some configs')
    else:
        for cfg in cfgs_run:
            no = str(cfg)    
            fin = h5.open_file(fin_dir+'/mixed_'+ens_s+'_'+no+'.h5')
            f5dir = '/'+val_p
            srcs = fin.get_node(f5dir+'/mixed_spec/'+vs+'/'+state)
            ns = 0
            tmp = []
            for src in srcs:
                tmp.append(src.read())
                ns += 1
            if ns != 1:
                print('cfg %d: Ns = %d: %s %s' %(cfg,ns,val,state))
            tmp = np.array(tmp)
            if first_data:
                data = np.zeros((1,)+tmp.mean(axis=0).shape,dtype=dtype)
                #print data.shape
                data[0] = tmp.mean(axis=0)
                #print data.shape
                first_data = False
            else:
                data = np.append(data,[tmp.mean(axis=0)],axis=0)
            cfgs_srcs.append([cfg,ns])
            fin.close()

        cfgs_srcs = np.array(cfgs_srcs)
        #print 'cfgs_srcs:', cfgs_srcs
        nc = cfgs_srcs.shape[0]
        #ns_avg = cfgs_srcs.mean(axis=0)[1]
        if nc > 0:
            print ('concatenated %s ml=%s ms=%s: Ncfg = %d' %(state,ml,ms,nc))
            group = val_p+'/'+'mixed_spec/'+vs
            sdir = ''
            for i,gi in enumerate(group.split('/')):
                if gi not in fout.get_node('/'+sdir):
                    fout.create_group('/'+sdir,gi)
                sdir += '/'+gi
            if state not in fout.get_node(sdir):
                fout.create_group(sdir,state)
                fout.create_array(sdir+'/'+state,'corr',data)
                fout.create_array(sdir+'/'+state,'cfgs_srcs',cfgs_srcs)
            elif state in fout.get_node(sdir) and args.o:
                fout.remove_node(sdir+'/'+state+'/corr')
                fout.create_array(sdir+'/'+state,'corr',data)
                fout.remove_node(sdir+'/'+state+'/cfgs_srcs')
                fout.create_array(sdir+'/'+state,'cfgs_srcs',cfgs_srcs)
            elif state in fout.get_node(sdir) and not args.o:
                print(state+' exists: overwrite = False')
            fout.flush()
            completeFile.write('ml: '+str(ml)+'ms: '+str(ms)+'cfg: '+str(cfg)+'\n')        
fout.close()

