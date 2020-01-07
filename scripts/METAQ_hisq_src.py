#!/usr/bin/env python
from __future__ import print_function
import os, sys
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
params['METAQ_PROJECT'] = 'spec_'+ens_s

parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs',nargs='+',type=int,help='cfg[s] no to check: ni [nf dn]')
parser.add_argument('--src',type=str,help='pass a specific src if desired')
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('--mtype',default='cpu',help='specify metaq dir [%(default)s]')
parser.add_argument('--metaQ',default=True,action='store_const',const=False,\
    help='make metaQ files at submission time instead of running executable in run environment [%(default)s]')
parser.add_argument('-p',default=False,action='store_const',const=True,\
    help='put task.sh in priority queue? [%(default)s]')
parser.add_argument('--n_dir',default=True,action='store_const',const=False,\
    help='add tasks to n_dir eg. todo/8 [%(default)s]')
parser.add_argument('--si',type=int,default=0,help='default src for mixed mesons [%(default)s]')
parser.add_argument('--pdel',default=False,action='store_const',const=True,\
    help='delete ddpairs props that are too small? [%(default)s]')
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
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,args.src,params)

if args.p:
    q = 'priority'
    params['PRIORITY'] = '-p'
else:
    q = 'todo'
    params['PRIORITY'] = ''

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

p_size = {
    'a06m310L':41708255696,
}
s_i = params['si']
s_f = params['sf']

#nn_srcs = ep.nn_srcs
#crnr_dl = ep.crnr_dl
params = area51.mpirun_params(c51.machine)
params['NODES']       = params['cpu_nodes']
params['METAQ_NODES'] = params['cpu_nodes']
params['METAQ_GPUS']  = params['cpu_gpus']
params['WALL_TIME']   = params['src_time']

params['ENS_DIR']     = c51.ens_dir % params
params['SCRIPT_DIR']  = c51.script_dir
params['MAXCUS']      = params['cpu_maxcus']
params['SOURCE_ENV']  = c51.env
params['PROG']        = '$LALIBE_CPU'
params['APP']         = 'APP='+c51.bind_dir+params['cpu_bind']
params['NRS']         = params['cpu_nrs']
params['RS_NODE']     = params['cpu_rs_node']
params['A_RS']        = params['cpu_a_rs']
params['G_RS']        = params['cpu_g_rs']
params['C_RS']        = params['cpu_c_rs']
params['L_GPU_CPU']   = params['cpu_latency']
params['IO_OUT']      = '-i $ini -o $out > $stdout 2>&1'

mqList=[params['MV_L'],params['MV_S']]
mqDict={'MS':params['MV_S'],'ML':params['MV_L']}

# make xml file to gauge-fix, flow
c51.names['prop']=c51.names['prop'].replace('%(CFG)s','%(NCFG)s')
for cfg in cfgs_run:
    no = str(cfg)

    params['NCFG'] = no
    params['CFG'] = no
    ''' set up ensemble and make sure all dirs exist '''
    params = c51.ensemble(params)
    params['RUN_DIR']     = params['prod']

    # make directories
    ''' check if flowed cfg exists and make if not '''
    job_name = '%(NL)s%(NT)s_w%(FLOW_TIME)s_src_%(CFG)s'%params
    # create xml ini file
    cfg_in = params['ENS_LONG'] + stream +'.'+no+'.scidac'
    
    params.update({
        'CFG_FILE':params['prod']+'/cfgs_scidac/'+cfg_in,'CFG_TYPE':'SCIDAC',
        })
    cfg_exist = os.path.exists(params['CFG_FILE'])
    print('CFG_EXISTS: %s' %cfg_exist)

    # make SRCS
    if args.src == None:
        srcs_cfg = [srcs[cfg][args.si]]#hardwire mixed_mesons to be only specified src
    else:
        srcs_cfg = [args.src]

    for src in srcs_cfg:
        print( no, src)
        task_base = 'hisq_src'
        xmlin  = task_base+'_'+ens_s+'_src'+src+'.ini.xml'
        xmlout = task_base+'_'+ens_s+'_src'+src+'.out.xml'
        stdout = task_base+'_'+ens_s+'_src'+src+'.stdout'
        xml_in = open(params['prod']+'/xml/'+no+'/'+xmlin,'w')
        xml_in.write(xml_input.head)
        x0 = src.split('x')[1].split('y')[0]
        y0 = src.split('y')[1].split('z')[0]
        z0 = src.split('z')[1].split('t')[0]
        t0 = src.split('t')[1]
        params.update({'X0':x0,'Y0':y0,'Z0':z0,'T0':t0,'SRC':src})
        src_id = 'src_'+no+'_'+src+'_'+'wv_w'+params['WF_S']+'_n'+params['WF_N']+'_hisq'
        params.update({'SRC_ID':src_id,'GAUGE_FIELD':'default_gauge_field'
                      })
        make_task = False

        if not os.path.exists(params['prod']+'/src'+'/'+src_id):
            print('making src %s' %src)
            # make and write source
            xml_in.write(xml_input.src_sh_stag % params)
            params.update({
                'OBJ_ID':src_id,'PARALLEL_IO':'true',
                'FILE_DIR':params['prod']+'/src','FILE_NAME':src_id,
                })
            xml_in.write(xml_input.stag_src_write % params)
            make_task = True
        # look for and delete ddpairs that are not too small
        if args.pdel:
            #pq_ml = [mv_l]   pq_ms = [mv_s]				
            for mqn in mqDict:
                mq=mqDict[mqn]
                prop_dir=params['prod'] + '/prop/'
                if mqn=='MS':
                    prop_dir=params['prod'] + '/prop_strange/'
                params['MQ']=mq

                prop = c51.names['prop']%params+'.lime'

                prop_dd = prop.replace('.lime','') + '_ddpairs'
                utils.check_file(prop_dir+no+'/'+prop_dd,p_size[ens],params['file_time_delete'],params['corrupt'])
                '''
                if os.path.exists(prop_dir+no+'/'+prop_dd) and os.path.getsize(prop_dir+no+'/'+prop_dd) < p_size[ens]:
                    print('DELETING')
                    print(prop_dd)
                    os.remove(prop_dir + '/'+prop_dd)
                '''
        # make USQCD_DD_PAIRS props
        for mqn in mqDict:
            mq=mqDict[mqn]
            params['MQ']=mq
            prop_dir=params['prod'] + '/prop/'
            if mqn=='MS':
                prop_dir=params['prod'] + '/prop_strange/'
            
            prop = c51.names['prop']%params+'.lime'
            prop_dd = prop.replace('.lime','') + '_ddpairs'
            
            if not os.path.exists(prop_dir+no+'/'+prop_dd):
                if not os.path.exists(prop_dir+no+'/'+prop):
                    print('DOES NOT EXIST: '+prop_dir+no+'/'+prop)
                else:
                    # read prop
                    print('Writing: %s' %prop)
                    params.update({'OBJ_ID':prop,'OBJ_TYPE':'LatticePropagator',
                        'LIME_FILE':prop_dir+no+'/'+prop})
                    xml_in.write(xml_input.qio_read % params)
                    # write ddpairs
                    params.update({'PROP_DIR':prop_dir+no,'PROP_ID_DD':prop_dd,'PROP_ID':prop})
                    xml_in.write(xml_input.dd_pairs % params)
                    make_task = True
        # close xml file
        xml_in.write(xml_input.tail % params)
        xml_in.close()

        # make TASK.sh
        if args.metaQ and make_task:
           metaq = task_base +'_'+ens_s+'_'+no+'_'+src+'_wv_w'+params['WF_S']+'_n'+params['WF_N']+'.sh'

           t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
           try:
                if params['metaq_split']:
                    t_e2,t_w2 = scheduler.check_task(metaq,args.mtype+'_'+str(params['gpu_nodes']),params,folder=q,overwrite=args.o)
                    t_w = t_w or t_w2
                    t_e = t_e or t_e2
           except:
                pass
           if not t_e or (args.o and not t_w):
                ''' make METAQ task '''
                params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')
                params['INI']       = params['prod']+'/xml/'+no+'/'+xmlin
                params['OUT']       = params['INI'].replace('.ini','.out')
                params['STDOUT']    = params['INI'].replace('.ini','').replace('xml','stdout')
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

        elif args.metaQ and not make_task:
            print('  done')
        else:
            print('not backwards compatible without metaQ')
