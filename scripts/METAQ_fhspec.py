from __future__ import print_function
import os, sys, time, shutil
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
params['METAQ_PROJECT'] = 'fhspec_'+ens_s

'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs',           nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-s','--src',     type=str)
parser.add_argument('-o',             default=False,action='store_const',const=True,\
                    help=             'overwrite xml and metaq files? [%(default)s]')
parser.add_argument('--mtype',        default='cpu',help='specify metaq dir [%(default)s]')
parser.add_argument('--gpu_l',        default='gpu', help='specify metaq dir for prop jobs [%(default)s]')
parser.add_argument('--gpu_s',        default='gpu', help='specify metaq dir for strange prop jobs [%(default)s]')
parser.add_argument('-p',             default=False,action='store_const',const=True,\
                    help=             'put task.sh in priority queue? [%(default)s]')
parser.add_argument('-v','--verbose', default=True,action='store_const',const=False,\
                    help=             'run with verbose output? [%(default)s]')
parser.add_argument('-d','--debug',   default=False,action='store_const',const=True,\
                    help=             'print DEBUG statements? [%(default)s]')
parser.add_argument('--src_set',      nargs=3,type=int,help='specify si sf ds')
args = parser.parse_args()
print('%s: Arguments passed' %sys.argv[0].split('/')[-1])
print(args)
print('')

'''
    RUN PARAMETER SET UP
'''
if params['tuning_mq']:
    params['si'] = 0
    params['sf'] = 0
    params['ds'] = 1
else:
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
if args.src_set:# override src index in sources and area51 files for collection
    params['si'] = args.src_set[0]
    params['sf'] = args.src_set[1]
    params['ds'] = args.src_set[2]
    src_args = '--src_set %d %d %d ' %(args.src_set[0],args.src_set[1],args.src_set[2])
else:
    src_args = ''
src_ext = "%d-%d" %(params['si'],params['sf'])

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
print('srcs:',src_ext)
#time.sleep(1)

smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
''' for now - just doing the light quark '''
params['MQ'] = params['MV_L']

params = area51.mpirun_params(c51.machine)
params['NODES']       = params['cpu_nodes']
params['METAQ_NODES'] = params['cpu_nodes']
params['METAQ_GPUS']  = params['cpu_gpus']
params['WALL_TIME']   = params['gflow_time']
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


for c in cfgs_run:
    no = str(c)
    params['CFG'] = no
    ''' set up ensemble and make sure all dirs exist '''
    params = c51.ensemble(params)
    params['RUN_DIR']     = params['prod']

    ''' check if flowed cfg exists and make if not '''
    scidac_cfg = params['scidac_cfg']
    cfg_flow   = params['ENS_LONG']+stream+'.'+no+'_wflow'+params['FLOW_TIME']
    cfg_file   = params['flowed_cfg']

    if os.path.exists(cfg_file):
        params['CFG_FILE'] = cfg_file
        print('Making %s for cfg: %d' %(sys.argv[0].split('/')[-1],c))
        if args.debug:
            print('srcs[%d] = %s' %(c,str(srcs[c])))

        for s0 in srcs[c]:
            if args.debug:
                print('DEBUG: src',s0)
            params['SRC'] = s0
            if args.verbose:
                print(c,s0)
            ''' check if FH spectrum exists '''
            fh_spec_name = c51.names['fh_spec'] % params
            fh_spec_file = params['fh_spec']+'/'+fh_spec_name +'.h5'
            utils.check_file(fh_spec_file,params['fh_size'],params['file_time_delete'],params['corrupt'])
            if not os.path.exists(fh_spec_file):
                ''' Do the FH_PROP and PROP files exist? '''
                have_fh_props = True
                fh_props = {}
                fh_prop_files = {}
                for fh in ['A3','V4']:
                    params.update({'CURR':fh})
                    fh_props[fh] = c51.names['fh_prop'] % params
                    fh_prop_files[fh] = params['fh_prop']+'/'+fh_props[fh]+'.lime'
                    utils.check_file(fh_prop_files[fh], params['prop_size'], params['file_time_delete'],params['corrupt'])
                    if not os.path.exists(fh_prop_files[fh]):
                        have_fh_props = False
                ''' does incoming prop exist? '''
                prop_name = c51.names['prop'] % params
                prop_file = params['prop'] +'/'+prop_name+'.'+params['SP_EXTENSION']
                utils.check_file(prop_file, params['prop_size'], params['file_time_delete'],params['corrupt'])
                have_prop = os.path.exists(prop_file)

                if have_fh_props and have_prop:
                    metaq = fh_spec_name +'.sh'
                    print('    making task:', metaq)
                    t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
                    try:
                        if params['metaq_split']:
                            t_e2,t_w2 = scheduler.check_task(metaq,args.mtype+'_'+str(params['gpu_nodes']),params,folder=q,overwrite=args.o)
                            t_w = t_w or t_w2
                            t_e = t_e or t_e2
                    except:
                        pass
                    if not t_e or (args.o and not t_w):
                        xmlini = params['xml'] +'/'+ fh_spec_name+'.ini.xml'
                        fin    = open(xmlini,'w')
                        fin.write(xml_input.head)
                        ''' read and sink smear prop and FH props '''
                        params['OBJ_ID']    = prop_name
                        params['OBJ_TYPE']  = 'LatticePropagator'
                        params['LIME_FILE'] = prop_file
                        fin.write(xml_input.qio_read % params)
                        params.update({'SMEARED_PROP':prop_name+'_SS', 'PROP_NAME':prop_name})
                        fin.write(xml_input.shell_smearing % params)
                        
                        for fh in fh_props:
                            params.update({'OBJ_ID':fh_props[fh], 'LIME_FILE':fh_prop_files[fh]})
                            fin.write(xml_input.qio_read % params)
                            params.update({'SMEARED_PROP':fh_props[fh]+'_SS', 'PROP_NAME':fh_props[fh]})
                            fin.write(xml_input.shell_smearing % params)

                        ''' make FH contractions '''
                        params.update({'UP_PROP':prop_name, 'DN_PROP':prop_name, 'FH_SPEC_FILE':fh_spec_file})
                        for FF in ['UU','DD']:
                            for fh in fh_props:
                                params.update({'CURR':fh, 'FLAVOR':FF, 'FH_PROP':fh_props[fh], 'H5_FH_PATH':'PS'})
                                fin.write(xml_input.fh_spec % params)
                        params.update({'UP_PROP':prop_name+'_SS', 'DN_PROP':prop_name+'_SS'})
                        for FF in ['UU','DD']:
                            for fh in fh_props:
                                params.update({'CURR':fh, 'FLAVOR':FF, 'FH_PROP':fh_props[fh]+'_SS', 'H5_FH_PATH':'SS'})
                                fin.write(xml_input.fh_spec % params)

                        ''' end xml file '''
                        fin.write(xml_input.tail % params)

                        fin.close()
                        
                        ''' make METAQ task '''
                        #params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')
                        params['METAQ_LOG'] = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                        params['INI']       = xmlini
                        params['OUT']       = xmlini.replace('.ini.xml','.out.xml')
                        params['STDOUT']    = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                        params['CLEANUP']   = 'sleep 30'
                        mtype = args.mtype
                        try:
                            if params['metaq_split']:
                                mtype = mtype + '_'+str(params['cpu_nodes'])
                        except:
                            pass
                        scheduler.make_task(metaq,mtype,params,folder=q)
                else:
                    if args.verbose:
                        print('missing prop',prop_file)
                    print('python METAQ_fhprop.py %s -s %s %s' %(c, s0, src_args))
                    os.system(c51.python+' %s/METAQ_fhprop.py %s -s %s %s %s' %(params['SCRIPT_DIR'], c, s0, src_args, params['PRIORITY']))
            else:
                if args.verbose:
                    print('fhspec exists',spec_file)
    else:
        print('  flowed cfg missing',cfg_file)
