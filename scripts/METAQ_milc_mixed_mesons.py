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
params['METAQ_PROJECT'] = 'mixedmesons_'+ens_s

parser = argparse.ArgumentParser(description='make mixed meson tasks for cfg %s' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs',nargs='+',type=int,help='cfg[s] no to check: ni [nf dn]')
parser.add_argument('--src',type=str,help='pass a specific src if desired')
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('--mtype',default='gpu',help='specify metaq dir [%(default)s]')
parser.add_argument('--metaQ',default=True,action='store_const',const=False,\
    help='make metaQ files at submission time instead of running executable in run environment [%(default)s]')
parser.add_argument('-p',default=False,action='store_const',const=True,\
    help='put task.sh in priority queue? [%(default)s]')
parser.add_argument('--n_dir',default=True,action='store_const',const=False,\
    help='add tasks to n_dir eg. todo/8 [%(default)s]')
parser.add_argument('--si',type=int,default=0,help='default src for mixed mesons [%(default)s]')
parser.add_argument('--hisq',default=False,action='store_const',const=True,\
    help='create hisq_hisq spectrum? [%(default)s]')
args = parser.parse_args()
print('%s: Arguments passed' %sys.argv[0].split('/')[-1])
print(args)
print('')

if len(args.cfgs) not in [1,3]:
    print('improper usage!')
    os.system('python '+sys.argv[0]+' -h')
    sys.exit(-1)
ni = int(args.cfgs[0])
if len(args.cfgs) == 3:
    nf = int(args.cfgs[1])
    dn = int(args.cfgs[2])
else:
    nf = ni; dn = ni;
if ni > nf:
    print('improper usage:')
    os.system('python '+sys.argv[0]+' -h')
    sys.exit(-1)

cfgs = range(ni,nf+1,dn)

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
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,args.src,params)

if args.p:
    q = 'priority'
    params['PRIORITY'] = '-p'
else:
    q = 'todo'
    params['PRIORITY'] = ''

s_i = params['si']
s_f = params['sf']


params = area51.mpirun_params(c51.machine)
params['NODES']       = params['hisq_nodes']
params['METAQ_NODES'] = params['hisq_metaq_nodes']
params['METAQ_GPUS']  = params['hisq_gpus']
params['WALL_TIME']   = params['mixed_mesons_time']

params['ENS_DIR']     = c51.ens_dir % params
params['SCRIPT_DIR']  = c51.script_dir
params['MAXCUS']      = params['cpu_maxcus']
params['SOURCE_ENV']  = c51.env
params['SOURCE_ENV']  +='\nexport QUDA_RESOURCE_PATH="`pwd`/quda_resource_milc"\n'
params['SOURCE_ENV']  +='[[ -e $QUDA_RESOURCE_PATH ]] || mkdir $QUDA_RESOURCE_PATH'


params['PROG']        = '"$KS_HISQ_SPEC '+params['hisq_geom']+'"\n'
params['APP']         = 'APP='+c51.bind_dir+params['gpu_bind']
params['NRS']         = params['hisq_nrs']
params['RS_NODE']     = params['hisq_rs_node']
params['A_RS']        = params['hisq_a_rs']
params['G_RS']        = params['hisq_g_rs']
params['C_RS']        = params['hisq_c_rs']
params['L_GPU_CPU']   = params['hisq_latency']
params['IO_OUT']      = '$ini $stdout'
scheduler.mpirun['lassen']="jsrun "+params['NRS']+' '+params['RS_NODE']+' '+params['A_RS']+' '+params['G_RS']+ ' '+\
                           params['C_RS']+ ' '+ params['L_GPU_CPU']+ ' -b packed:smt:4 $PROG $geom $ini >> $stdout 2>&1'

mqList=[params['MV_L'],params['MV_S']]

smr='wv_w'+params['WF_S']+'_n'+params['WF_N']
params['SMR']=smr

ms_l = params['MS_L']
ms_s = params['MS_S']
mv_l = params['MV_L']
mv_s = params['MV_S']

debug=False

for c in cfgs:
    no = str(c)
    params['CFG'] = str(no)
    ''' set up ensemble and make sure all dirs exist '''
    params = c51.ensemble(params)
    params['RUN_DIR']     = params['prod']
    mixed_dir = params['prod']+'/mixed/'+params['CFG']

    src = srcs[c][args.si] #For now - only make mixed with 1 (first) source
    x0 = src.split('x')[1].split('y')[0]
    y0 = src.split('y')[1].split('z')[0]
    z0 = src.split('z')[1].split('t')[0]
    t0 = src.split('t')[1]
    params['SRC']=src
    
    hisq_file = 'hisq_hisq_spec_'+ens_s+'_cfg_%s_srcx0y0z0t0_ml%s_ms%s.corr' \
        %(no,ms_l,ms_s)

    hisq_id =hisq_file.replace('.corr','')# 'hisq_hisq_spec_'+ens_s+'_cfg_'str(no)#no
    prop_l = c51.names['prop'].replace('MQ','MV_L')%params +'_ddpairs'
    prop_s = c51.names['prop'].replace('MQ','MV_S')%params +'_ddpairs'

    params.update({
        'V_INV':'%.7e' %(1./float(params['NL'])**3),
        'MAX_CG_ITER':10000,'MAX_CG_RESTART':5,
        'PROP_PREC':2,'ERR_L':5.e-9,'REL_ERR_L':0,'ERR_S':1.e-9,'REL_ERR_S':0,
        'M_L':ms_l,'M_S':ms_s,
        'PROP_DIR':params['prop'],
        'PROP_DIR_STRANGE':params['prop_strange'],
        'X0':x0,'Y0':y0,'Z0':z0,'T0':t0,
        'SRC_DIR':params['prod']+'/src','SRC_HISQ':'src_'+str(no)+'_'+src+'_'+smr+'_hisq'
        })

    
    """
    # HISQ-HISQ SPEC
    if args.hisq and not os.path.exists(mixed_dir+'/'+hisq_file):
        hisq_spectrum = c51.milc_dir+'/ks_spectrum_hisq'
        milc_in = params['xml']+'/'+hisq_id+'.in'
        milc_out = params['xml']+'/'+hisq_id+'.out'
        milc_stdout = params['stdout']+'/'+hisq_id+'.stdout'
        meta_base = 'hisq_spec_'+ens+'_'+str(no)
        params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+hisq_id+'.log'
        
        params.update({
            'JOB_ID':hisq_id,
            'HISQ_CORR_FILE':mixed_dir+'/'+hisq_file,
            'MILC_EXE':hisq_spectrum,
            'MILC_IN':milc_in,'MILC_OUT':milc_out,'MILC_STDOUT':milc_stdout,
            })
        #check if task exists
        metaq = meta_base+'.sh'
    
        t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
        try:
            if params['metaq_split']:
                t_e2,t_w2 = scheduler.check_task(metaq,args.mtype+'_'+str(params['gpu_nodes']),params,folder=q,overwrite=args.o)
                t_w = t_w or t_w2
                t_e = t_e or t_e2
        except:
            pass
    
        if not t_e and not t_w:
            # make ks_spectrum input file
            sample_in = open(params['SCRIPT_DIR']+'/hisq_hisq.in').read()
            spec_in = open(milc_in,'w')
            spec_in.write(sample_in % params)
            spec_in.close()
                
            # make metaQ task file
            ''' Make METAQ task '''
            params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')
            params['INI']       = milc_in
            params['OUT']       = params['INI'].replace('.in','.out')
            params['STDOUT']    = params['INI'].replace('.in','.stdout').replace('/xml/','/stdout/')
            params['CLEANUP']  = ''
            mtype = args.mtype
            try:
                if params['metaq_split']:
                    mtype = mtype + '_'+str(params[mtype+'_nodes'])
            except:
                  pass
            scheduler.make_task(metaq,mtype,params,folder=q)
        else:
            print('task exists: %s' %metaq)
    """
    # DWF-HISQ SPEC
    # first - do a check on all props to see if they can be deleted
    mqList=[mv_l,mv_s]
    pq_del = dict()
    for mq in mqList:
        pq_del[mq] = True
    for mql in [mv_l]:
        for mqs in [mv_s]:
            params['MQ_L'],params['MQ_S']=mql,mqs
            mixed_corr = c51.names['mixed_corr']%params
            if not os.path.exists(mixed_dir+'/'+mixed_corr):
                print('mqs '+mixed_dir+'/'+mixed_corr)
                pq_del[mql],pq_del[mqs] = False,False

    p_del = []
    p_get = []
    
    if os.path.exists('props_del_%s.lst' %ens_s):
        f_del = open('props_del_%s.lst' %ens_s).readlines()
        for p in f_del:
            if p.strip() not in p_del:
                p_del.append(p.strip())
    if os.path.exists('props_get_%s.lst' %ens_s):
        f_get = open('props_get_%s.lst' %ens_s).readlines()
        for p in f_get:
            if p.strip() not in p_get:
                p_get.append(p.strip())
    
    for mq in pq_del:
        params['MQ']=mq
        prop = c51.names['prop']%params +'_ddpairs'

        if pq_del[mq]:
            for pdir in [params['PROP_DIR'], params['PROP_DIR_STRANGE']]:
                p_file = pdir+'/'+prop
                if p_file not in p_del and os.path.exists(p_file):
                    p_del.append(p_file)
        else:
            for pdir in [params['PROP_DIR'], params['PROP_DIR_STRANGE']]:
                p_file = pdir+'/'+prop
                if p_file not in p_get and not os.path.exists(p_file):
                    p_get.append(p_file)

    p_get.sort()
    p_del.sort()
    f_del = open('props_del_%s.lst' %ens_s,'w')
    for p in p_del:
         print(p, file=f_del)
    f_del.close()
    f_get = open('props_get_%s.lst' %ens_s,'w')
    for p in p_get:
        print(p, file=f_get)
    f_get.close()

    # add loop over pq_ml and pq_ms
    for mql in [mv_l]:
        params['MQL']=mql
        prop_l = c51.names['prop'].replace('MQ','MQL')%params +'_ddpairs'
        for mqs in [mv_s]:
            params['MQS']=mqs
            prop_s = c51.names['prop'].replace('MQ','MQS')%params%params +'_ddpairs'

            params['MQ_L'],params['MQ_S']=mql,mqs
            mixed_corr = c51.names['mixed_corr']%params

            if os.path.exists(params['milc_cfg']) and os.path.exists(params['PROP_DIR']+'/'+prop_l)\
                                               and os.path.exists(params['PROP_DIR_STRANGE']+'/'+prop_s) \
                                               and not os.path.exists(mixed_dir+'/'+mixed_corr):
                params.update({'PROP_L':prop_l,'PROP_S':prop_s,'MV_L':mql,'MV_S':mqs,})
                mixed_id = 'dwf_hisq_spec_'+str(no)+'_ml'+mql+'_ms'+mqs
                milc_in = params['xml']+'/'+mixed_id+'.in'
                milc_out = params['xml']+'/'+mixed_id+'.out'
                milc_stdout = params['stdout']+'/'+mixed_id+'.stdout'
                meta_base = ens_s+'_'+str(no)+'_dwf_hisq_ml'+mql+'_ms'+mqs
                params.update({
                    'JOB_ID':mixed_id,
                    'HISQ_CORR_FILE':mixed_dir+'/'+mixed_corr,
                    'MILC_IN':milc_in,'MILC_OUT':milc_out,'MILC_STDOUT':milc_stdout,
                    })

                # check if task exists
                metaq = 'mixedmesons_'+meta_base+'.sh'

                t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
                try:
                    if params['metaq_split']:
                        t_e2,t_w2 = scheduler.check_task(metaq,args.mtype+'_'+str(params['gpu_nodes']),params,folder=q,overwrite=args.o)
                        t_w = t_w or t_w2
                        t_e = t_e or t_e2
                except:
                    pass
                if not t_e or (args.o and not t_w):
                    # make ks_spectrum input file
                    sample_in = open(params['SCRIPT_DIR']+'/dwf_hisq.in').read()
                    spec_in = open(milc_in,'w')
                    spec_in.write(sample_in % params)
                    spec_in.close()

                    # make metaQ task file
                    ''' Make METAQ task '''

                    #NEED TO CHANGE TO  clov_spectrum 
                    params['PROG']      = hisq_spectrum = c51.milc_dir+'/su3_clov_hisq\n'
                    params['PROG']     +='geom="'+params['hisq_geom']+'"'

                    params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')
                    params['INI']       = milc_in
                    params['OUT']       = params['INI'].replace('.in','.out')
                    params['STDOUT']    = params['INI'].replace('.in','.stdout').replace('/xml/','/stdout/')
                    params['CLEANUP']  = ''
                    mtype = 'gpu'
                   
                    try:
                        if params['metaq_split']:
                            mtype = mtype + '_'+str(params[mtype+'_nodes'])
                    except:
                        pass
                    scheduler.make_task(metaq,mtype,params,folder=q)
                else:
                    print('task exists: %s' %metaq)
            else:
                if not os.path.exists( params['milc_cfg']):
                    print('DOES NOT EXIST:\n'+ params['milc_cfg'])
                if not os.path.exists(params['PROP_DIR']+'/'+prop_l):
                    print('DOES NOT EXIST:\n'+params['PROP_DIR']+'/'+prop_l)        
                if not os.path.exists(params['PROP_DIR_STRANGE']+'/'+prop_s):
                    print('DOES NOT EXIST:\n'+params['PROP_DIR_STRANGE']+'/'+prop_s)
                if os.path.exists(mixed_dir+'/'+mixed_corr):
                    print('EXISTS!\n'+mixed_corr)
