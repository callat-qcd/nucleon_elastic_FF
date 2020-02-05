#!/usr/bin/env python
from __future__ import print_function
import os, sys
import argparse

'''
    NUCLEON_ELASTIC_FF IMPORTS
'''
# test change
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
import importlib
import c51_mdwf_hisq as c51
import utils
import scheduler
import sources
import random
import numpy as np

parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs',nargs='+',type=int,help='cfg[s] no to check: ni [nf dn]')
parser.add_argument('--cfgType',type=str,help='cfg type: MILC or SCIDAC')
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('-p',default=False,action='store_const',const=True,\
    help='put task.sh in priority queue? [%(default)s]')
parser.add_argument('-v','--verbose',default=True,action='store_const',const=False,\
    help='run with verbose output? [%(default)s]')
args = parser.parse_args()
print('%s: Arguments passed' %sys.argv[0].split('/')[-1])
print(str(args))

if len(args.cfgs) not in [1,3]:
    print('improper usage!')
    os.system(c51.python+' '+sys.argv[0]+' -h')
    sys.exit(-1)
ni = int(args.cfgs[0])
if len(args.cfgs) == 3:
    nf = int(args.cfgs[1])
    dn = int(args.cfgs[2])
else:
    nf = ni; dn = ni;
if ni > nf:
    print('improper usage:')
    os.system(c51.python+' '+sys.argv[0]+' -h')
    sys.exit(-1)

cfgs = range(ni,nf+1,dn)



ens,stream = c51.ens_base()
ens_s = ens+'_'+stream

area51 = importlib.import_module(ens)
params = area51.params


params['machine'] = c51.machine
params['ENS_LONG'] = c51.ens_long[ens]
params['ENS_S']    = ens_s
params['STREAM']   = stream
params['METAQ_PROJECT'] = 'strange_charm_loops_'+ens_s
params['PROJECT']=params['METAQ_PROJECT']

params = area51.mpirun_params(c51.machine)
params['NODES']       = params['hisq_nodes']
params['METAQ_NODES'] = params['hisq_metaq_nodes']
params['METAQ_GPUS']  = params['hisq_gpus']
params['WALL_TIME']   = params['strange_charm_loops_time']

params['ENS_DIR']     = c51.ens_dir % params
#for testing script dir
params['SCRIPT_DIR']  = '/p/gpfs1/mcamacho/nucleon_elastic_FF_hisq_spec/scripts'#c51.script_dir
params['MAXCUS']      = params['hisq_maxcus']
params['SOURCE_ENV']  = c51.env
params['SOURCE_ENV']  +='\nexport QUDA_RESOURCE_PATH="`pwd`/quda_resource_milc"\n'
params['SOURCE_ENV']  +='[[ -e $QUDA_RESOURCE_PATH ]] || mkdir $QUDA_RESOURCE_PATH'


#params['PROG']        = '"$KS_HISQ_SPEC '+params['hisq_geom']+'"\n'
#params['PROG']        = "/usr/workspace/coldqcd/software/lassen_smpi_RR/install/lattice_milc_qcd/ks_measure_hisq"
params['PROG']      = hisq_spectrum = c51.milc_dir+'/ks_measure_hisq\n'
params['PROG']     +='geom="'+params['hisq_geom']+'"'

params['APP']         = 'APP='+c51.bind_dir+params['gpu_bind']
params['NRS']         = params['hisq_nrs']
params['RS_NODE']     = params['hisq_rs_node']
params['A_RS']        = params['hisq_a_rs']
params['G_RS']        = params['hisq_g_rs']
params['C_RS']        = params['hisq_c_rs']
params['L_GPU_CPU']   = params['hisq_latency']
params['IO_OUT']      = '$ini >> $stdout 2>&1'
params['CLEANUP']  = ''
mtype = 'gpu'

scheduler.mpirun['lassen']="jsrun "+params['NRS']+' '+params['RS_NODE']+' '+params['A_RS']+' '+params['G_RS']+ ' '+\
                           params['C_RS']+ ' '+ params['L_GPU_CPU']+ ' -b packed:smt:4 $APP $PROG $geom '+params['IO_OUT']

params = sources.src_start_stop(params,ens,stream)
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,None,params)

if args.p:
    q = 'priority'
    params['PRIORITY'] = '-p'
else:
    q = 'todo'
    params['PRIORITY'] = ''

phys_ensList={'a15':'a15m135XL','a12':'a12m135XL','a09':'a09m135XL'}

if ens.split('m')[0] not in phys_ensList.keys():
    sys.exit('Missing physical ensemble info for '+ens.split('m')[0])

phys_ens=phys_ensList[ens.split('m')[0]]

naikcPhys={'a15m135XL':'-0.358919895451143','a12m135XL':'-0.230929816582185','a09m135XL':'-0.115856476703343'}

if phys_ens not in naikcPhys.keys():
    sys.exit('Missing physical naik value for '+phys_ens)

if 'NAIK' not in params.keys():
    sys.exit('Missing naik value')
else:
    try:
        float(params['NAIK'])
    except:
        sys.exit('Wrong naik value '+phys_ens)

ms_phys='0.'+c51.ens_long[phys_ens].split('m')[-2]
mc_phys='0.'+c51.ens_long[phys_ens].split('m')[-1]


#Strange/Charm loop parameters
params.update({'MS':ms_phys,'MC':mc_phys,'NAIK_C':params['NAIK'],'NAIK_C_PHYS':naikcPhys[phys_ens]})

in_text=open(params['SCRIPT_DIR']+'/strange_charm_loops_hisq.in','r').read()
if args.cfgType=='SCIDAC':
    in_text=in_text.replace('milc_cfg','scidac_cfg')



for c in cfgs:
    no = str(c)
    params['CFG'] = str(no)
    params=c51.ensemble(params)
    random.seed(params['ENS_LONG']+'.'+params['CFG'])
    mySeed  = random.randint(0,5682304)
    np.random.seed(mySeed)
    cfg_seed=str(np.random.randint(10**7,10**8,1)[0])

    params['SEED']=cfg_seed
    name=c51.names['strange_charm_loops']%params
    params['JOBID']=name

    ''' set up ensemble and make sure all dirs exist '''
    params = c51.ensemble(params)
    params['RUN_DIR']     = params['prod']
    params['INI']=params['xml']+'/'+name+'.ini'
    params['STDOUT']=params['stdout']+'/'+name+'.stdout'
    params['OUT']=params['stdout']+'/'+name+'.stdout'

 
    if not os.path.exists(params['STDOUT']):
    
        # check if task exists
        metaq = name+'.sh'
        t_e,t_w = scheduler.check_task(metaq,mtype,params,folder=q,overwrite=args.o)
        try:
            if params['metaq_split']:
                t_e2,t_w2 = scheduler.check_task(metaq,mtype+'_'+str(params['gpu_nodes']),params,folder=q,overwrite=args.o)
                t_w = t_w or t_w2
                t_e = t_e or t_e2
        except:
            pass
        if not t_e or (args.o and not t_w):
            # make ks_spectrum input file   
            params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')

            in_file=open(params['INI'],'w')
            in_file.write(in_text%params)
            in_file.close()


            # make metaQ task file
            ''' Make METAQ task '''
            try:
                if params['metaq_split']:
                    mtype = mtype + '_'+str(params[mtype+'_nodes'])
            except:
                pass
            scheduler.make_task(metaq,mtype,params,folder=q)
        else:
            print('task exists: %s' %metaq)
    else:
        print(params['STDOUT']+ ' found')

