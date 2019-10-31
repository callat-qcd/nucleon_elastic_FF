from __future__ import print_function
import os, sys, shutil, time
from glob import glob
import argparse

'''
    NUCLEON_ELASTIC_FF IMPORTS
'''
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
import xml_input
import metaq_input
import importlib
import c51_mdwf_hisq as c51
import sources
import utils
import scheduler

ens,stream = c51.ens_base()
ens_s = ens+'_'+stream

area51 = importlib.import_module(ens)
params = area51.params
params['machine'] = c51.machine
params['ENS_LONG'] = c51.ens_long[ens]
params['ENS_S']    = ens_s
params['STREAM']   = stream
params['METAQ_PROJECT'] = 'formfac_'+ens_s

'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('data',type=str,help='what data type to check? [spec spec_4D spec_4D_tslice formfac formfac_4D formfac_4D_tslice hyperspec]')
parser.add_argument('--cfgs',nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-v','--verbose',default=True,action='store_const',const=False,\
    help='run with verbose output? [%(default)s]')
parser.add_argument('--src_index',nargs=3,type=int,help='specify si sf ds')
args = parser.parse_args()
print('%s: Arguments passed' %sys.argv[0].split('/')[-1])
print(args)
print('')

'''
    RUN PARAMETER SET UP
'''
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
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,'',params)

nt = int(params['NT'])
nl = int(params['NL'])

print('checking ',cfgs_run[0],'-->',cfgs_run[-1])
print('    srcs: ',params['si'],'-', params['sf'])

smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
''' for now - just doing the light quark '''
params['MQ'] = params['MV_L']

''' ONLY doing snk_mom 0 0 0 now '''
snk_mom = params['snk_mom'][0]
m0,m1,m2 = snk_mom.split()
params['M0']=m0
params['M1']=m1
params['M2']=m2
params['MOM'] = 'px%spy%spz%s' %(m0,m1,m2)

if args.data in ['spec','spec_4D','spec_4D_tslice']:
    dtype = 'spec'
elif args.data in ['hyperspec']:
    dtype = 'hyperspec'
elif args.data in ['formfac','formfac_4D','formfac_4D_tslice']:
    dtype = 'formfac'
else:
    print('unrecognized data type,',args.data)
    print('recognized list: spec spec_4D spec_4D_tslice formfac formfac_4D formfac_4D_tslice')
    sys.exit()

missing = open('missing_'+args.data+'_srcs'+params['si']+'-'+params['sf']+'.lst','w')
for c in cfgs_run:
    no = str(c)
    sys.stdout.write('    cfg=%4d\r' %(c))
    sys.stdout.flush()
    params['CFG'] = no
    params['N_SEQ'] = str(len(srcs[c]))
    ''' set up ensemble and make sure all dirs exist '''
    params = c51.ensemble(params)
    params['RUN_DIR']     = params['prod']

    all_srcs = True
    for s0 in srcs[c]:
        params['SRC'] = s0
        if dtype == 'spec':
            s_file = (params['spec'] +'/' + (c51.names['spec'] %params) +'.h5').replace('spec',args.data)
            if not os.path.exists(s_file):
                if args.verbose: print('missing:',s_file)
                all_srcs = False
                missing.write(s_file+'\n')            
        elif dtype == 'hyperspec':
            s_file = (params['hyperspec'] +'/' + (c51.names['hyperspec'] %params) +'.h5')
            if not os.path.exists(s_file):
                if args.verbose: print('missing:',s_file)
                all_srcs = False
                missing.write(s_file+'\n')
        elif dtype == 'formfac':
            for t_sep in params['t_seps']:
                params['T_SEP'] = str(t_sep)
                coherent_formfac_name  = c51.names['coherent_ff'] % params
                coherent_formfac_file  = params['formfac'] +'/'+coherent_formfac_name + '.h5'
                s_file = coherent_formfac_file.replace('formfac',args.data)
                if not os.path.exists(s_file):
                    if args.verbose: print('missing:',s_file)
                    all_srcs = False
                    missing.write(s_file+'\n')            
missing.close()                
