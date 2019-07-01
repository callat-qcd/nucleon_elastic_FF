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

dtype = np.float64
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
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,args.src,params)
src_ext = "%d-%d" %(params['si'],params['sf'])
smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
val_p = val.replace('.','p')

mv_l = params['MV_L']

print('MINING MRES and PHI_QQ')
print('ens_stream = ',ens_s)
params['MQ'] = params['MV_L']

for cfg in cfgs_run:
    no = str(cfg)
    print(no)
    params['CFG'] = no
    params = c51.ensemble(params)
    files = []
    for src in srcs[cfg]:
        params['SRC'] = src
        prop_name = c51.names['prop'] % params
        prop_xml = params['xml'] + '/' + prop_name+'.out.xml'
        t_src = int(src.split('t')[1])
        mq = params['MQ'].replace('.','p')
        f_good = False
        if os.path.exists(prop_xml):
            if os.path.getsize(prop_xml) > 0:
                with open(prop_xml) as f:
                    data = f.readlines()
                    if data[-1] == '</propagator>':
                        f_good = True
                    else:
                        shutil.move(prop_xml,params['corrupt']+'/'+prop_xml.split('/')[-1])
        else:
            f_good = False
        if not f_good:
            print('    corrupt:',prop_xml)
        else:
            f5 = h5.open_file(data_dir+'/'+ens_s+'_'+no+'_srcs'+src_ext+'.h5','a')
            mpdir   = '/'+val_p+'/dwf_jmu/mq'+mq+'/midpoint_pseudo'
            ppdir   = '/'+val_p+'/dwf_jmu/mq'+mq+'/pseudo_pseudo'
            phi_dir = '/'+val_p+'/phi_qq/mq'+mq
            try:
                f5.create_group('/'+val_p+'/dwf_jmu/mq'+mq,'midpoint_pseudo',createparents=True)
                f5.create_group('/'+val_p+'/dwf_jmu/mq'+mq,'pseudo_pseudo',createparents=True)
                f5.flush()
            except:
                pass
            try:
                f5.create_group('/'+val_p+'/phi_qq','mq'+mq,createparents=True)
                f5.flush()
            except:
                pass
            get_data = False
            if src not in f5.get_node(mpdir) or src not in f5.get_node(ppdir) or src not in f5.get_node(phi_dir):
                get_data = True
            if args.o and (src in f5.get_node(mpdir) or src in f5.get_node(ppdir) or src in f5.get_node(phi_dir)):
                get_data = True
            if get_data:
                with open(prop_xml) as file:
                    f = file.readlines()
                have_data = False; l = 0
                while not have_data:
                    if f[l].find('<DWF_MidPoint_Pseudo>') > 0 and f[l+3].find('<DWF_Psuedo_Pseudo>') > 0:
                        corr_mp = f[l+1].split('<mesprop>')[1].split('</mesprop>')[0].split()
                        corr_pp = f[l+4].split('<mesprop>')[1].split('</mesprop>')[0].split()
                        nt = len(corr_mp)
                        mp = np.array([float(d) for d in corr_mp],dtype=dtype)
                        pp = np.array([float(d) for d in corr_pp],dtype=dtype)
                        if not np.any(np.isnan(pp)) and not np.any(np.isnan(mp)):
                            if args.v:
                                print(no,'mq'+mq,src,'mres collected')
                            if src not in f5.get_node(mpdir):
                                f5.create_array(mpdir,src,mp)
                            elif src in f5.get_node(mpdir) and args.o:
                                f5.get_node(mpdir+'/'+src)[:] = mp
                            elif src in f5.get_node(mpdir) and not args.o:
                                print('  skipping midpoint_pseudo: overwrite = False')
                            if src not in f5.get_node(ppdir):
                                f5.create_array(ppdir,src,pp)
                            elif src in f5.get_node(ppdir) and args.o:
                                f5.get_node(ppdir+'/'+src)[:] = pp
                            elif src in f5.get_node(ppdir) and not args.o:
                                print('  skipping pseudo_pseudo: overwrite = False')
                        else:
                            print('  NAN')
                    # phi_qq
                    if f[l].find('<prop_corr>') > 0:
                        corr = f[l].split('<prop_corr>')[1].split('</prop_corr>')[0].split()
                        phi_qq = np.array([float(d) for d in corr],dtype=dtype)
                        phi_qq = np.roll(phi_qq,-t_src)
                        if not np.any(np.isnan(phi_qq)):
                            print(no,'mq'+mq,src,'phi_qq collected')
                            if src not in f5.get_node(phi_dir):
                                f5.create_array(phi_dir,src,phi_qq)
                            elif src in f5.get_node(phi_dir) and args.o:
                                f5.get_node(phi_dir+'/'+src)[:] = phi_qq
                            elif src in f5.get_node(phi_dir) and not args.o:
                                print('  skipping forward_prop: overwrite = False')
                        else:
                            print('  NAN')
                        have_data = True
                    else:
                        l += 1
            f5.close()
