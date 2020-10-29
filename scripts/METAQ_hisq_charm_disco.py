#!/usr/bin/env python
from __future__ import print_function
import os, shutil, sys, time
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
parser.add_argument('--cfgType',type=str,default='MILC',help='cfg type: MILC or SCIDAC')
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

params['machine']       = c51.machine
params['ENS_LONG']      = c51.ens_long[ens]
params['ENS_S']         = ens_s
params['STREAM']        = stream
params['METAQ_PROJECT'] = 'charm_pbp_'+ens_s
params['PROJECT']       = params['METAQ_PROJECT']

params = area51.mpirun_params(c51.machine)
params['NODES']       = params['charm_pbp_nodes']
params['METAQ_NODES'] = params['charm_pbp_meta_nodes']
params['METAQ_GPUS']  = params['charm_pbp_gpus']
params['WALL_TIME']   = params['charm_pbp_time']

params['ENS_DIR']     = c51.ens_dir % params

params['SCRIPT_DIR']  = c51.script_dir

params['MAXCUS']      = params['hisq_maxcus']
params['SOURCE_ENV']  = c51.env
params['SOURCE_ENV']  +='\nexport QUDA_RESOURCE_PATH="`pwd`/quda_resource_milc"\n'
params['SOURCE_ENV']  +='[[ -e $QUDA_RESOURCE_PATH ]] || mkdir $QUDA_RESOURCE_PATH'

#params['PROG']        = '"$KS_HISQ_SPEC '+params['hisq_geom']+'"\n'
#params['PROG']        = "/usr/workspace/coldqcd/software/lassen_smpi_RR/install/lattice_milc_qcd/ks_measure_hisq"
params['PROG']      = c51.milc_dir+'/ks_measure_hisq_no_t\n'
params['PROG']     +='geom="'+params['hisq_geom']+'"'

params['APP']         = 'APP='+c51.bind_dir+params['gpu_bind']
params['NRS']         = params['charm_pbp_nrs']
params['RS_NODE']     = params['hisq_rs_node']
params['A_RS']        = params['hisq_a_rs']
params['G_RS']        = params['hisq_g_rs']
params['C_RS']        = params['hisq_c_rs']
params['L_GPU_CPU']   = params['hisq_latency']
params['IO_OUT']      = '$ini > $stdout 2>&1'
params['CLEANUP']  = ''
mtype = 'gpu'

params = sources.src_start_stop(params,ens,stream)
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,None,params)

if args.p:
    q = 'priority'
    params['PRIORITY'] = '-p'
else:
    q = 'todo'
    params['PRIORITY'] = ''

phys_ensList={'a15':'a15m135XL','a12':'a12m135XL','a09':'a09m135XL','a06':'a06m135'}

if ens.split('m')[0] not in phys_ensList.keys():
    sys.exit('Missing physical ensemble info for '+ens.split('m')[0])

phys_ens=phys_ensList[ens.split('m')[0]]

naikcPhys={'a15m135XL':'-0.358919895451143','a12m135XL':'-0.230929816582185','a09m135XL':'-0.115856476703343','a06m135':'-0.0436217059345379'}

if phys_ens not in naikcPhys.keys():
    sys.exit('Missing physical naik value for '+phys_ens)

if 'NAIK' not in params.keys():
    sys.exit('Missing naik value')

head='''prompt 0
nx %(NL)s
ny %(NL)s
nz %(NL)s
nt %(NT)s
iseed %(SEED)s
job_id charm_reweight

######################################################################
# source time 0
######################################################################

# Gauge field description

reload_parallel %(CFG_FILE)s
u0 %(U0)s
forget
staple_weight 0
ape_iter 0
coordinate_origin 0 0 0 0
time_bc antiperiodic

max_number_of_eigenpairs 0

# Chiral condensate and related measurements

number_of_sets %(N_CHARM_SETS)s

'''

pbp_meas='''# Parameters common to all members of set %(SET)s

npbp_reps %(N_PBP)s
max_cg_iterations %(MC_MAX_ITER)s
max_cg_restarts 5
prec_pbp 2

# Number of masses in this set
number_of_pbp_masses 1

mass %(MASS)s
naik_term_epsilon %(NAIK)s
error_for_propagator %(MC_PROP_ERROR)s
rel_error_for_propagator %(MC_REL_PROP_ERROR)s

'''

for c in cfgs:
    no = str(c)
    params['CFG'] = str(no)
    params = c51.ensemble(params)
    cfg_scidac = params['prod']+'/cfgs_scidac/'+params['ENS_LONG']+stream+'.'+no+'.scidac'
    if os.path.exists(cfg_scidac):
        params['CFG_FILE'] = cfg_scidac
        params['RUN_DIR']       = params['prod']
        pbp_dir = params['prod']+'/pbp/'+no
        if not os.path.exists(pbp_dir):
            os.makedirs(pbp_dir)
        for mc in params['MC_reweight']:
            mass = str(mc)
            name = 'charm_pbp_'+ens_s+'_cfg_'+no+'_'+mass
            pbp  = name +'.stdout'
            pbp_file = pbp_dir+'/'+pbp
            if os.path.exists(pbp_file):
                std_content = open(pbp_file).read()
                if 'RUNNING COMPLETED' not in std_content:
                    now = time.time()
                    file_time = os.stat(pbp_file).st_mtime
                    if (now-file_time)/60 > 10:# if older than 10 minutes, delete
                        print('  OLD, incomplete, deleting',pbp_file)
                        shutil.move(pbp_file, params['corrupt']+'/'+pbp_file.split('/')[-1])
            if not os.path.exists(pbp_file):
                random.seed(ens_s+'.'+params['CFG']+'_'+mass)
                params['SEED']   = random.randint(0,10**6)
                params['JOBID']  = name
                params['INI']    = params['xml']+'/'+name+'.ini'
                params['OUT']    = ''
                params['STDOUT'] = pbp_file
                params['N_CHARM_SETS'] = 1
                params['SET']    = 0
                params['N_PBP']  = 1
                params['MASS']   = mass

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
                    in_file.write(head % params)
                    in_file.write(pbp_meas % params)
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
                print('Exists:',pbp_file)
    else:
        print('missing cfg',cfg_scidac)
