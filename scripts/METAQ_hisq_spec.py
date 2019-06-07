from __future__ import print_function
import os, sys
from glob import glob
import argparse

'''
    NUCLEON_ELASTIC_FF IMPORTS
'''
# test change
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
params['METAQ_PROJECT'] = 'prop_'+ens_s

'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs',nargs='+',type=int,help='start [stop] cfg numbers')
parser.add_argument('-s','--src',type=str)
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('--mtype',default='gpu',help='specify metaq dir [%(default)s]')
parser.add_argument('-p',default=False,action='store_const',const=True,\
    help='put task.sh in priority queue? [%(default)s]')
parser.add_argument('-v','--verbose',default=True,action='store_const',const=False,\
    help='run with verbose output? [%(default)s]')
parser.add_argument('--force',default=False,action='store_const',const=True,\
    help='force create props? [%(default)s]')
args = parser.parse_args()
print('%s: Arguments passed' %sys.argv[0].split('/')[-1])
print(args)
print('')

'''
    RUN PARAMETER SET UP
'''
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,args.src,params)

if args.p:
    q = 'priority'
    params['PRIORITY'] = '-p'
else:
    q = 'todo'
    params['PRIORITY'] = ''

nt = int(params['NT'])
nl = int(params['NL'])

print('running ',cfgs_run[0],'-->',cfgs_run[-1])

smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
''' for now - just doing the light quark '''
params['MQ'] = params['MV_L']

save_prop=True

params = area51.mpirun_params(c51.machine)
params['NODES']       = params['gpu_nodes']
params['METAQ_NODES'] = params['gpu_metaq_nodes']
params['METAQ_GPUS']  = params['gpu_gpus']
params['WALL_TIME']   = params['prop_time']
params['ENS_DIR']     = c51.ens_dir % params
params['SCRIPT_DIR']  = c51.script_dir
params['MAXCUS']      = params['gpu_maxcus']
params['SOURCE_ENV']  = c51.env
params['PROG']        = '/usr/workspace/coldqcd/software/lassen_smpi/install/lattice_milc_qcd/ks_spectrum_hisq'
params['PROG']       += ' -qmp'+ params['gpu_geom_milc']+' -qmp-logic-map 3 2 1 0 -qmp-alloc-map 3 2 1 0\n'
params['APP']         = 'APP='+c51.bind_dir+params['gpu_bind']
params['NRS']         = params['gpu_nrs']
params['RS_NODE']     = params['gpu_rs_node']
params['A_RS']        = params['gpu_a_rs']
params['G_RS']        = params['gpu_g_rs']
params['C_RS']        = params['gpu_c_rs']
params['L_GPU_CPU']   = params['gpu_latency']
beta = '600'
u0 = params['U0'] 
ml = params['MS_L']
ms = params['MS_S']  
mc = params['MS_C']
params['ML'] = params['MS_L']
params['MS'] = params['MS_S']

#t_srcs = [0,8,16,24,32,40,48,56]
t_srcs = params['t_shifts']

for c in cfgs_run:
    no = str(c)
    params['CFG'] = no
    ''' set up ensemble and make sure all dirs exist '''
    params = c51.ensemble(params)
    params['RUN_DIR']     = params['prod']
    t0 = str(t_srcs[0])
    if save_prop:
        params.update({
            'PROP_L':'save_parallel_scidac_ksprop '+params['prop']+'/hisq_prop_mq'+ml+'_t'+t0,
            'PROP_S':'save_parallel_scidac_ksprop '+params['prop']+'/hisq_prop_mq'+ms+'_t'+t0,
            'PROP_C':'save_parallel_scidac_ksprop '+params['prop']+'/hisq_prop_mq'+mc+'_t'+t0
            })
    else:
        params.update({'PROP_L':'forget_ksprop','PROP_S':'forget_ksprop','PROP_C':'forget_ksprop'})



    ''' check if flowed cfg exists and make if not '''
    coul_cfg = params['prod']+'/cfgs_coul/'+params['ENS_LONG']+'.'+no+'.coulomb'
    cfg_flow   = params['ENS_LONG']+stream+'.'+no+'_wflow'+params['FLOW_TIME']
    cfg_file   = params['milc_cfg']


    params['SRC'] = 'x0y0z0t'+str(t0)
    hisq_spec_name    = c51.names['hisq_spec'] % params
    hisq_spec_file    = params['hisq_spec'] +'/'+ hisq_spec_name
    V3 = int(nl)**3
    params.update({'HISQ_CORR_FILE':hisq_spec_file,'V_INV':1./V3,
            'NL':nl,'NT':nt,'JOB_ID':ens+'_'+no+'_hisq',
            'T0':t0,'MAX_CG_ITER':7000,'MAX_CG_RESTART':5,
            'M_L':ml,'M_S':ms,'M_C':mc,'NAIK_c':-0.358919895,
            'ERR_L':1.e-7,'REL_ERR_L':0,
            })

    if not os.path.exists(coul_cfg ):
        cfg_in = '''
reload_parallel %s
u0 %s
coulomb_gauge_fix
save_parallel %s
        ''' %(cfg_file,u0,coul_cfg)
    else:
        cfg_in = '''
reload_parallel %s
u0 %s
no_gauge_fix
forget
        ''' %(coul_cfg,u0)
    params.update({'CFG_INPUT':cfg_in})

    if not os.path.exists(hisq_spec_file) and os.path.exists(cfg_file):
        hisq_spec_name    = c51.names['hisq_spec'] % params
        metaq  = hisq_spec_name+'.sh'
        print('  making ',hisq_spec_name)
        metaq = hisq_spec_name+'.sh'

        t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
        if not t_e or (args.o and not t_w):
            in_file = params['xml']+'/'+hisq_spec_name+'.in'
            '''make hisq input file'''
            fin = open(in_file,'w')
            in_tmp = open('hisq_spec.in').read()
            fin.write(in_tmp % params)
            fin.close()    

            ''' make METAQ task '''
            params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')
            params['INI']       = in_file
            params['OUT']       = in_file.replace('.in','.out')
            params['STDOUT']    = in_file.replace('.in','.stdout').replace('/xml/','/stdout/')
            params['CLEANUP']   = ''
            scheduler.make_task(metaq,args.mtype,params,folder=q)
        else:
            print('  task exists:',metaq)
    elif os.path.exists(hisq_spec_file):
        print('hisq_spec exists',hisq_spec_file.split('/')[-1])

    if os.path.exists(coul_cfg):
        for t in t_srcs:
            t0=str(t)	
            if save_prop:
               params.update({
                  'PROP_L':'save_parallel_scidac_ksprop '+params['prop']+'/hisq_prop_mq'+ml+'_t'+t0,
                  'PROP_S':'save_parallel_scidac_ksprop '+params['prop']+'/hisq_prop_mq'+ms+'_t'+t0,
                  'PROP_C':'save_parallel_scidac_ksprop '+params['prop']+'/hisq_prop_mq'+mc+'_t'+t0
                  })
            else:
               params.update({'PROP_L':'forget_ksprop','PROP_S':'forget_ksprop','PROP_C':'forget_ksprop'})
		
            params['SRC'] = 'x0y0z0t'+str(t0)
            if args.verbose:
                print(c,t0)
            hisq_spec_name    = c51.names['hisq_spec'] % params
            hisq_spec_file    = params['hisq_spec'] +'/'+ hisq_spec_name

            if not os.path.exists(hisq_spec_file):
                params.update({'T0':t0,'HISQ_CORR_FILE':hisq_spec_file})

                metaq  = hisq_spec_name+'.sh'
                print('  making ',hisq_spec_name)
                metaq = spec_name+'.sh'
                t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
                if not t_e or (args.o and not t_w):
                    in_file = params['xml']+'/'+hisq_spec_name+'.in'
                    ''' make hisq input file '''
                    fin = open(in_file,'w')
                    in_tmp = open('hisq_spec.in').read()
                    fin.write(in_tmp % params)
                    fin.close()        

                    ''' make METAQ task '''
                    params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')
                    params['INI']       = in_file
                    params['OUT']       = in_file.replace('.in','.out')
                    params['STDOUT']    = in_file.replace('.in','.stdout').replace('/xml/','/stdout/')
                    params['CLEANUP']   = ''
                    scheduler.make_task(metaq,args.mtype,params,folder=q)

                else:
                    print('  task exists:',metaq)


