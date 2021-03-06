from __future__ import print_function
import os, sys, time
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
# tape utils from Evan's hpss module
import hpss.hsi as hsi
# to check disk
from lattedb_ff_disk_tape_functions import check_tape

ens,stream = c51.ens_base()
ens_s = ens+'_'+stream

tape_dir = c51.tape+'/'+ens_s

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
parser.add_argument('cfgs'           , nargs='+',type=int,help='start [stop] cfg numbers')
parser.add_argument('-s','--src'     , type=str)
parser.add_argument('--src_set'      , nargs=3,type=int,help='specify si sf ds')
parser.add_argument('-o'             , default=False,action='store_const',const=True,\
                    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('--mtype',default='gpu',help='specify metaq dir [%(default)s]')
parser.add_argument('-p'             , default=False,action='store_const',const=True,\
                    help='put task.sh in priority queue? [%(default)s]')
parser.add_argument('-v','--verbose' , default=True,action='store_const',const=False,\
                    help='run with verbose output? [%(default)s]')
parser.add_argument('--force'        , default=False,action='store_const',const=True,\
                    help='force create props? [%(default)s]')
parser.add_argument('--tape'         , default=False,action='store_const',const=True,\
                    help='push/pull props to/from tape? [%(default)s]')
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
src_set = "%d-%d" %(params['si'],params['sf'])

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
print('srcs:',src_set)
#time.sleep(1)

smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
''' for now - just doing the light quark '''
params['MQ'] = params['MV_L']

params = area51.mpirun_params(c51.machine)
params['NODES']       = params['gpu_nodes']
params['METAQ_NODES'] = params['gpu_metaq_nodes']
params['METAQ_GPUS']  = params['gpu_gpus']
params['WALL_TIME']   = params['prop_time']
params['ENS_DIR']     = c51.ens_dir % params
params['SCRIPT_DIR']  = c51.script_dir
params['MAXCUS']      = params['gpu_maxcus']
params['SOURCE_ENV']  = c51.env
params['PROG']        = '"$LALIBE_GPU '+params['gpu_geom']+'"\n'
params['PROG']       += 'export QUDA_RESOURCE_PATH='+c51.quda_resource_dir+'\n'
params['PROG']       += 'export QUDA_ENABLE_DSLASH_POLICY="0,1,6,7"\n'
params['APP']         = 'APP='+c51.bind_dir+params['gpu_bind']
params['NRS']         = params['gpu_nrs']
params['RS_NODE']     = params['gpu_rs_node']
params['A_RS']        = params['gpu_a_rs']
params['G_RS']        = params['gpu_g_rs']
params['C_RS']        = params['gpu_c_rs']
params['L_GPU_CPU']   = params['gpu_latency']
params['IO_OUT']      = '-i $ini -o $out > $stdout 2>&1'

props_to_pull_tape = []

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
        for s0 in srcs[c]:
            params['SRC'] = s0
            if args.verbose:
                print(c,s0)
            ''' check if spectrum exists '''
            spec_name    = c51.names['spec'] % params
            spec_file    = params['spec'] +'/'+ spec_name+'.h5'
            spec_file_4D = spec_file.replace('spec_','spec_4D_').replace('/spec/','/spec_4D/')
            spec_exists  = os.path.exists(spec_file) and os.path.exists(spec_file_4D)
            if not spec_exists or (args.force or args.tape):
                prop_name = c51.names['prop'] % params
                prop_file = params['prop'] + '/' + prop_name+'.'+params['SP_EXTENSION']
                ''' make sure prop is correct size '''
                try:
                    file_size = params['prop_size']
                except:
                    print('PROP_SIZE not defined in area51 file: using crude default')
                    file_size = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
                utils.check_file(prop_file,file_size,params['file_time_delete'],params['corrupt'])
                prop_exists = os.path.exists(prop_file)
                # check on tape
                t_dict = dict()
                t_dict['exists'] = False
                t_dict_h5 = dict()
                t_dict_h5['exists'] = False
                if not prop_exists:
                    t_dict = check_tape(tape_dir+'/prop/'+no, prop_name+'.'+params['SP_EXTENSION'])
                    if t_dict['exists'] and not prop_exists and args.tape:
                        hsi.cget(params['prop'], tape_dir+'/prop/'+no, prop_name+'.'+params['SP_EXTENSION'])
                        prop_exists = os.path.exists(prop_file)
                    elif t_dict['exists'] and not prop_exists and not args.tape:
                        props_to_pull_tape.append(no+'/'+prop_name+'.'+params['SP_EXTENSION'])
                elif prop_exists and args.tape:
                    hsi.cput(prop_file, tape_dir+'/prop/'+no+'/'+prop_name+'.'+params['SP_EXTENSION'])
                # a12m130 used h5 props
                if ens in ['a12m130','a15m135XL'] and (not prop_exists and not t_dict['exists']):
                    prop_file = params['prop'] + '/' + prop_name+'.h5'
                    try:
                        file_size = params['prop_size_h5']
                    except:
                        print('PROP_SIZE not defined in area51 file: using crude default')
                        file_size = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
                    utils.check_file(prop_file,file_size,params['file_time_delete'],params['corrupt'])
                    prop_exists = os.path.exists(prop_file)
                    if not prop_exists:
                        # check on tape
                        t_dict_h5 = check_tape(tape_dir+'/prop/'+no, prop_name+'.h5')
                        if t_dict_h5['exists'] and not prop_exists and args.tape:
                            hsi.cget(params['prop'], tape_dir+'/prop/'+no, prop_name+'.h5')
                            prop_exists = os.path.exists(prop_file)
                        elif  t_dict_h5['exists'] and not prop_exists and not args.tape:
                            props_to_pull_tape.append(no+'/'+prop_name+'.h5')
                    elif prop_exists and args.tape:
                        hsi.cput(prop_file, tape_dir+'/prop/'+no+'/'+prop_name+'.h5')
                if (not prop_exists and not (t_dict['exists'] or t_dict_h5['exists']) and not spec_exists) or args.force:
                    # restore prop extension to params['SP_EXTENSION'] in case we looked for h5 props
                    prop_file = params['prop'] + '/' + prop_name+'.'+params['SP_EXTENSION']
                    src_name = c51.names['src'] % params
                    src_file = params['src']+'/'+src_name+'.'+params['SP_EXTENSION']
                    try:
                        file_size = params['src_size']
                    except:
                        print('SRC_SIZE not defined in area51 file: using crude default')
                        file_size = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
                    utils.check_file(src_file,file_size,params['file_time_delete'],params['corrupt'])
                    if os.path.exists(src_file):
                        print('  making ',prop_file)
                        metaq = prop_name+'.sh'
                        t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
                        try:
                            if params['metaq_split']:
                                t_e2,t_w2 = scheduler.check_task(metaq,args.mtype+'_'+str(params['gpu_nodes']),params,folder=q,overwrite=args.o)
                                t_w = t_w or t_w2
                                t_e = t_e or t_e2
                        except:
                            pass
                        if not t_e or (args.o and not t_w):
                            xmlini = params['xml'] +'/'+(c51.names['prop_xml'] %params)+'.ini.xml'
                            fin = open(xmlini,'w')
                            fin.write(xml_input.head)
                            ''' read src '''
                            params['OBJ_ID']    = src_name
                            params['OBJ_TYPE']  = 'LatticePropagator'
                            params['LIME_FILE'] = src_file
                            fin.write(xml_input.qio_read % params)

                            ''' solve prop '''
                            params['SRC_NAME'] = src_name
                            params['PROP_NAME'] = prop_name
                            params['QUARK_SPIN'] = 'FULL'
                            ''' this xml file contains mres info and is distinct from the chroma .out.xml '''
                            params['PROP_XML']  = '<xml_file>'
                            params['PROP_XML'] += prop_file.replace('/prop/','/xml/').replace(params['SP_EXTENSION'],'out.xml')
                            params['PROP_XML'] += '</xml_file>'
                            fin.write(xml_input.quda_nef % params)

                            ''' write prop to disk '''
                            params['OBJ_ID']    = prop_name
                            params['OBJ_TYPE']  = 'LatticePropagatorF'
                            params['LIME_FILE'] = prop_file
                            fin.write(xml_input.qio_write % params)

                            ''' end xml file '''
                            fin.write(xml_input.tail % params)
                            fin.close()

                            ''' Make METAQ task '''
                            params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')
                            params['INI']       = xmlini
                            params['OUT']       = xmlini.replace('.ini.xml','.out.xml')
                            params['STDOUT']    = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                            if not params['tuning_mq']:
                                params['CLEANUP']   = 'if [ "$cleanup" -eq 0 ]; then\n'
                                params['CLEANUP']  += '    cd '+params['ENS_DIR']+'\n'
                                params['CLEANUP']  += '    python '+params['SCRIPT_DIR']+'/METAQ_spec.py '
                                params['CLEANUP']  += params['CFG']+' -s '+s0+' '+src_args+' '+params['PRIORITY']+'\n'
                                if params['run_ff']:
                                    params['CLEANUP'] += '    python '+params['SCRIPT_DIR']+'/METAQ_seqsource.py '
                                    params['CLEANUP'] += params['CFG']+' -s '+s0+' '+src_args+' '+params['PRIORITY']+'\n'
                                params['CLEANUP']  += '    sleep 5\n'
                                params['CLEANUP']  += 'else\n'
                                params['CLEANUP']  += '    echo "mpirun failed"\n'
                                params['CLEANUP']  += 'fi\n'
                            else:
                                params['CLEANUP']  = ''
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
                        if args.verbose:
                            print('    src missing',src_file)
                        print('python METAQ_src.py %s -s %s %s %s -v' %(c,s0,src_args,params['PRIORITY']))
                        os.system(c51.python+' %s/METAQ_src.py %s -s %s %s %s -v' \
                            %(params['SCRIPT_DIR'], c, s0, src_args, params['PRIORITY']))
                else:
                    if args.verbose:
                        if prop_exists:
                            print('    prop exists',prop_file)
                        elif not prop_exists and (t_dict['exists'] or t_dict_h5['exists']):
                            print('    prop on tape', prop_file)
            elif os.path.exists(spec_file) and not args.force:
                print('    spec exists and force make prop = False',spec_file.split('/')[-1])
    else:
        print('  flowed cfg missing',cfg_file)

if props_to_pull_tape:
    p_list = 'props_to_pull_Srcs'+src_set+'.lst'
    if os.path.exists(p_list):
        pull_list = open(p_list).readlines()
    else:
        pull_list = []
    pull_list = [prop.strip() for prop in pull_list]
    pull_list = pull_list + [prop for prop in props_to_pull_tape if prop not in pull_list]
    prop_pull = open(p_list,'w')
    for prop in pull_list:
        prop_pull.write(prop+'\n')
    prop_pull.close()
