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
params['METAQ_PROJECT'] = 'seqsource_'+ens_s

'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs',            nargs='+',type=int,help='start [stop] run cfg number')
parser.add_argument('-s','--src',      type=str)
parser.add_argument('-o',              default=False,action='store_const',const=True,\
                    help=              'overwrite xml and metaq files? [%(default)s]')
parser.add_argument('--mtype',         default='gpu',help='specify metaq dir [%(default)s]')
parser.add_argument('-d','--debug',    default=False,action='store_const',const=True,\
                    help=              'run DEBUG? [%(default)s]')
parser.add_argument('-p','--priority', default=False,action='store_const',const=True,\
                    help=              'put task in priority? [%(default)s]')
parser.add_argument('-v','--verbose',  default=True,action='store_const',const=False,\
                    help=              'run with verbose output? [%(default)s]')
parser.add_argument('--src_set',       nargs=3,type=int,help='specify si sf ds')
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
if args.src_set:# override src index in sources and area51 files for collection
    params['si'] = args.src_set[0]
    params['sf'] = args.src_set[1]
    params['ds'] = args.src_set[2]
    src_args = '--src_set %d %d %d ' %(args.src_set[0],args.src_set[1],args.src_set[2])
else:
    src_args = ''
src_ext = "%d-%d" %(params['si'],params['sf'])

cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,args.src,params)
'''
if args.src:
    params['N_SEQ'] = len(range(params['si'],params['sf']+params['ds'],params['ds']))
else:
    params['N_SEQ'] = len(srcs[cfgs_run[0]])
'''
params['SRC_LST'] = src_ext

if args.priority:
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
params['NODES']       = params['gpu_nodes']
params['METAQ_NODES'] = params['gpu_metaq_nodes']
params['METAQ_GPUS']  = params['gpu_gpus']
params['WALL_TIME']   = params['prop_time'] * 2 # 2 props
params['ENS_DIR']     = c51.ens_dir % params
params['SCRIPT_DIR']  = c51.script_dir
params['MAXCUS']      = params['gpu_maxcus']
params['SOURCE_ENV']  = c51.env
params['PROG']        = '"$LALIBE_GPU '+params['gpu_geom']+'"\n'
params['PROG']       += 'export QUDA_RESOURCE_PATH='+(c51.base_dir %params)+'/quda_resource\n'
params['APP']         = 'APP='+c51.bind_dir+params['gpu_bind']
params['NRS']         = params['gpu_nrs']
params['RS_NODE']     = params['gpu_rs_node']
params['A_RS']        = params['gpu_a_rs']
params['G_RS']        = params['gpu_g_rs']
params['C_RS']        = params['gpu_c_rs']
params['L_GPU_CPU']   = params['gpu_latency']
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
        print("checking FH props and spec for cfg: ",no)

        # loop over srcs
        for s0 in srcs[c]:
            params['SRC'] = s0
            ''' Do the FH spec files exist? '''
            fh_spec_name = c51.names['fh_spec'] % params
            fh_spec_file = params['fh_spec']+'/'+fh_spec_name +'.h5'
            utils.check_file(fh_spec_file,params['fh_size'],params['file_time_delete'],params['corrupt'])
            if not os.path.exists(fh_spec_file):
                ''' Do the FH prop files exist? '''
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
                ''' if we do not have FH props, make them '''
                if not have_fh_props and (have_prop or args.debug):
                    params.update({'CURR':'A3V4'})
                    fh_base = c51.names['fh_prop'] % params
                    metaq   = fh_base+'.sh'
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
                        xmlini = params['xml'] +'/'+ fh_base+'.ini.xml'
                        fin    = open(xmlini,'w')
                        fin.write(xml_input.head)
                        ''' read prop that will be used as source '''
                        params['OBJ_ID']    = prop_name
                        params['OBJ_TYPE']  = 'LatticePropagator'
                        params['LIME_FILE'] = prop_file
                        params['SRC_PROP']  = prop_name
                        fin.write(xml_input.qio_read % params)

                        ''' add FH props '''
                        currents = ''
                        fh_p     = ''
                        for fh in fh_props:
                            if not os.path.exists(fh_prop_files[fh]):
                                params.update({'CURR':fh})
                                currents += '\n    <elem>'+fh+'</elem>'
                                fh_p     += '\n    <elem>'+fh_props[fh]+'</elem>'
                        params.update({'CURRENTS':currents, 'FH_PROPS':fh_p})
                        fin.write(xml_input.fh_prop_ga % params)

                        ''' write FH props to disk '''
                        params['OBJ_TYPE']  = 'LatticePropagatorF'
                        for fh in fh_props:
                            if not os.path.exists(fh_prop_files[fh]):
                                params['OBJ_ID']    = fh_props[fh]
                                params['LIME_FILE'] = fh_prop_files[fh]
                                fin.write(xml_input.qio_write % params)
                            
                        ''' end xml file '''
                        fin.write(xml_input.tail % params)
                        fin.close()

                        ''' Make METAQ task '''
                        params['METAQ_LOG'] = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                        params['INI']       = xmlini
                        params['OUT']       = xmlini.replace('.ini.xml','.out.xml')
                        params['STDOUT']    = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                        params['CLEANUP']   = 'if [ "$cleanup" -eq 0 ]; then\n'
                        params['CLEANUP']  += '    cd '+params['ENS_DIR']+'\n'
                        params['CLEANUP']  += '    '+c51.python+' '+params['SCRIPT_DIR']+'/METAQ_fhspec.py '
                        params['CLEANUP']  += params['CFG']+' -s '+s0+' '+src_args+' '+params['PRIORITY']+'\n'
                        params['CLEANUP']  += '    sleep 5\n'
                        params['CLEANUP']  += 'else\n'
                        params['CLEANUP']  += '    echo "mpirun failed"\n'
                        params['CLEANUP']  += 'fi\n'
                        mtype = args.mtype
                        try:
                            if params['metaq_split']:
                                mtype = mtype + '_'+str(params['gpu_nodes'])
                        except:
                            pass
                        scheduler.make_task(metaq,mtype,params,folder=q)
                    else:
                        if args.verbose:
                            print('    task is in use or overwrite is false')
                else:
                    if have_prop:
                        print('    exists:')
                        print('           '+' '.join([fh_props[fh]+'\n' for fh in fh_props]))
                    else:
                        print('python METAQ_prop.py %s -s %s %s ' %(c, s0, src_args))
                        os.system(c51.python+ ' %s/METAQ_prop.py %s -s %s %s' %(params['SCRIPT_DIR'], c, s0, src_args))
            else:
                print('    exists:',fh_spec_name)

    else:
        if not os.path.exists(cfg_file):
            print('  flowed cfg missing',cfg_file)
