from __future__ import print_function
import os, sys
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

params = area51.mpirun_params(c51.machine)
save_prop             = params['save_hisq_prop']
params['NODES']       = params['hisq_nodes']
params['METAQ_NODES'] = params['hisq_metaq_nodes']
params['METAQ_GPUS']  = params['hisq_gpus']
params['WALL_TIME']   = params['hisq_coul_spec']
params['ENS_DIR']     = c51.ens_dir % params
params['SCRIPT_DIR']  = c51.script_dir
params['MAXCUS']      = params['hisq_maxcus']
params['SOURCE_ENV']  = c51.env
params['PROG']        = '"$KS_HISQ_SPEC '+params['hisq_geom']+'"\n'
params['PROG']       += 'export QUDA_RESOURCE_PATH='+(c51.base_dir %params)+'/quda_resource_hisq\n'
params['PROG']       += '[[ -d $QUDA_RESOURCE_PATH ]] || mkdir $QUDA_RESOURCE_PATH \n'
params['APP']         = 'APP='+c51.bind_dir+params['gpu_bind']
params['NRS']         = params['hisq_nrs']
params['RS_NODE']     = params['hisq_rs_node']
params['A_RS']        = params['hisq_a_rs']
params['G_RS']        = params['hisq_g_rs']
params['C_RS']        = params['hisq_c_rs']
params['L_GPU_CPU']   = params['hisq_latency']
params['IO_OUT']      = '$ini >> $stdout'

u0 = params['U0']
ml = params['MS_L']
ms = params['MS_S']
mc = params['MS_C']
params['ML'] = params['MS_L']
params['MS'] = params['MS_S']

#t_srcs = [0,8,16,24,32,40,48,56]
t_srcs = params['t_hisq']

for c in cfgs_run:
    no = str(c)
    params['CFG'] = no
    ''' set up ensemble and make sure all dirs exist '''
    params = c51.ensemble(params)
    params['RUN_DIR']     = params['prod']

    ''' check if scidac cfg exists and make if not '''
    utils.ensure_dirExists(params['prod']+'/cfgs_coul')
    utils.ensure_dirExists(params['prod']+'/cfgs_scidac')
    cfg_milc   = params['prod']+'/cfgs/'+params['ENS_LONG']+stream+'.'+no
    cfg_coul   = params['prod']+'/cfgs_coul/'+params['ENS_LONG']+stream+'.'+no+'.coulomb'
    cfg_scidac = params['prod']+'/cfgs_scidac/'+params['ENS_LONG']+stream+'.'+no+'.scidac'
    cfg_flow   = params['ENS_LONG']+stream+'.'+no+'_wflow'+params['FLOW_TIME']
    milc_cfg   = params['milc_cfg']

    if os.path.exists(cfg_scidac):
        cfg_file = cfg_scidac
    else:
        cfg_file = milc_cfg

    if not os.path.exists(cfg_coul):
        params['CLEANUP']   = 'if [ "$cleanup" -eq 0 ]; then\n'
        params['CLEANUP']   = '    cd '+params['ENS_DIR']+'\n'
        params['CLEANUP']  += '    '+c51.python+' '+params['SCRIPT_DIR']+'/METAQ_hisq_spec.py '
        params['CLEANUP']  += params['CFG']+' '+params['PRIORITY']+'\n'
        params['CLEANUP']  += 'else\n'
        params['CLEANUP']  += '    echo "mpirun failed"\n'
        params['CLEANUP']  += 'fi\n'
        if not os.path.exists(cfg_scidac):
            cfg_in = '''
reload_parallel %s
u0 %s
no_gauge_fix
save_parallel_scidac %s
staple_weight 0
ape_iter 0
coordinate_origin 0 0 0 0
time_bc antiperiodic

max_number_of_eigenpairs 0
number_of_pbp_masses 0
number_of_base_sources 0
number_of_modified_sources 0
number_of_sets 0
number_of_quarks 0
number_of_mesons 0
number_of_baryons 0

continue

u0 %s
coulomb_gauge_fix
save_parallel %s
''' %(milc_cfg, u0, cfg_scidac, u0, cfg_coul)
        else:
            cfg_in = '''
reload_parallel %s
u0 %s
coulomb_gauge_fix
save_parallel %s
''' %(cfg_file, u0, cfg_coul)

        t0_lst = [t_srcs[0]]

    else:
        params['WALL_TIME'] = params['hisq_spec']
        params['CLEANUP']   = ''
        cfg_in = '''
reload_parallel %s
u0 %s
no_gauge_fix
forget
        ''' %(cfg_coul,u0)

        t0_lst = t_srcs

    params.update({'CFG_INPUT':cfg_in})

    #for t in t_srcs:
    for t in t0_lst:
        t0 = str(t)
        if save_prop:
            params.update({
                'PROP_L':'save_parallel_scidac_ksprop '+params['prop']+'/hisq_prop_mq'+ml+'_t'+t0,
                'PROP_S':'save_parallel_scidac_ksprop '+params['prop']+'/hisq_prop_mq'+ms+'_t'+t0,
                'PROP_C':'save_parallel_scidac_ksprop '+params['prop']+'/hisq_prop_mq'+mc+'_t'+t0
                })
        else:
            params.update({'PROP_L':'forget_ksprop','PROP_S':'forget_ksprop','PROP_C':'forget_ksprop'})

        params['SRC'] = 'x0y0z0t'+str(t0)
        hisq_spec_name    = c51.names['hisq_spec'] % params
        hisq_spec_file    = params['hisq_spec'] +'/'+ hisq_spec_name
        V3 = int(nl)**3
        params.update({'HISQ_CORR_FILE':hisq_spec_file,'V_INV':1./V3,
                'NL':nl,'NT':nt,'JOB_ID':ens+'_'+no+'_hisq',
                'T0':t0,'MAX_CG_ITER':7000,'MAX_CG_RESTART':5,
                'M_L':ml,'M_S':ms,'M_C':mc,'NAIK_c':params['NAIK'],
                'ERR_L':1.e-7,'REL_ERR_L':0,
                })

        utils.check_file(hisq_spec_file,params['hisq_spec_size'],params['file_time_delete'],params['corrupt'])
        if not os.path.exists(hisq_spec_file) and (os.path.exists(cfg_file) or os.path.exists(cfg_coul)):
            hisq_spec_name    = c51.names['hisq_spec'] % params
            metaq  = hisq_spec_name+'.sh'
            print('  making ',hisq_spec_name)
            metaq = hisq_spec_name+'.sh'

            t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
            try:
                if params['metaq_split']:
                    t_e2,t_w2 = scheduler.check_task(metaq,args.mtype+'_'+str(params['gpu_nodes']),params,folder=q,overwrite=args.o)
                    t_w = t_w or t_w2
                    t_e = t_e or t_e2
            except:
                pass
            if not t_e or (args.o and not t_w):
                in_file = params['xml']+'/'+hisq_spec_name+'.in'
                '''make hisq input file'''
                fin = open(in_file,'w')
                if ml == ms:
                    in_tmp = open(c51.script_dir + '/hisq_spec_su3.in').read()
                else:
                    in_tmp = open(c51.script_dir + '/hisq_spec.in').read()
                fin.write(in_tmp % params)
                fin.close()

                ''' make METAQ task '''
                params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')
                params['INI']       = in_file
                params['OUT']       = in_file.replace('.in','.out')
                params['STDOUT']    = in_file.replace('.in','.stdout').replace('/xml/','/stdout/')
                #params['CLEANUP']   = ''
                mtype = args.mtype
                try:
                    if params['metaq_split']:
                        mtype = mtype + '_'+str(params['gpu_nodes'])
                except:
                    pass
                scheduler.make_task(metaq,mtype,params,folder=q)
            else:
                print('  task exists:',metaq)

        elif os.path.exists(hisq_spec_file):
            if not os.path.exists(cfg_scidac):
                metaq = 'milc_to_scidac_'+no+'.sh'
                print('  making',metaq)
                t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
                try:
                    if params['metaq_split']:
                        t_e2,t_w2 = scheduler.check_task(metaq,args.mtype+'_'+str(params['gpu_nodes']),params,folder=q,overwrite=args.o)
                        t_w = t_w or t_w2
                        t_e = t_e or t_e2
                except:
                    pass
                if not t_e or (args.o and not t_w):
                    in_file = params['xml']+'/'+metaq.replace('.sh','.in')
                    fin = open(in_file,'w')
                    in_tmp = open(c51.script_dir + '/milc_to_scidac.in').read()
                    in_tmp = in_tmp.replace('CFG',no)
                    in_tmp = in_tmp.replace('NL', str(params['NL']))
                    in_tmp = in_tmp.replace('NT', str(params['NT']))
                    in_tmp = in_tmp.replace('TADPOLE',u0)
                    in_tmp = in_tmp.replace('ENSSTREAM',params['ENS_LONG']+stream)
                    fin.write(in_tmp)
                    fin.close()

                    ''' make METAQ task '''
                    params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')
                    params['INI']       = in_file
                    params['OUT']       = in_file.replace('.in','.out')
                    params['STDOUT']    = in_file.replace('.in','.stdout').replace('/xml/','/stdout/')
                    params['CLEANUP']   = ''
                    mtype = args.mtype
                    try:
                        if params['metaq_split']:
                            mtype = mtype + '_'+str(params['gpu_nodes'])
                    except:
                        pass
                    scheduler.make_task(metaq,mtype,params,folder=q)
                else:
                    print('  task exists:',metaq)
            else:
                print('hisq_spec exists',hisq_spec_file.split('/')[-1])
        else:
            print('hisq_spec_file',hisq_spec_file)
            print(os.path.exists(hisq_spec_file))
            print('cfg_file',cfg_file)
            print(os.path.exists(cfg_file))
            print('cfg_coul',cfg_coul)
            print(os.path.exists(cfg_coul))
"""
    if os.path.exists(cfg_coul):
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
                metaq = hisq_spec_name+'.sh'
                t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
                if not t_e or (args.o and not t_w):
                    in_file = params['xml']+'/'+hisq_spec_name+'.in'
                    ''' make hisq input file '''
                    fin = open(in_file,'w')
                    in_tmp = open(c51.script_dir + '/hisq_spec.in').read()
                    fin.write(in_tmp % params)
                    fin.close()

                    ''' make METAQ task '''
                    params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')
                    params['INI']       = in_file
                    params['OUT']       = in_file.replace('.in','.out')
                    params['STDOUT']    = in_file.replace('.in','.stdout').replace('/xml/','/stdout/')
                    #params['CLEANUP']   = ''
                    scheduler.make_task(metaq,args.mtype,params,folder=q)

                else:
                    print('  task exists:',metaq)


"""
