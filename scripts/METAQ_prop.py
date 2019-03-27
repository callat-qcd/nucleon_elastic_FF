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
params['METAQ_PROJECT'] = 'cfg_flow_'+ens_s

'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs',nargs='+',type=int,help='start [stop] cfg numbers')
parser.add_argument('-s','--src',type=str)
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('--mtype',default='cpu',help='specify metaq dir [%(default)s]')
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
params['NODES']       = params['cpu_nodes']
params['METAQ_NODES'] = params['cpu_nodes']
params['METAQ_GPUS']  = params['cpu_gpus']
params['WALL_TIME']   = params['gflow_time']
params['ENS_DIR']     = c51.ens_dir % params
params['SCRIPT_DIR']  = c51.script_dir
params['MAXCUS']      = params['cpu_maxcus']
params['SOURCE_ENV']  = c51.env
params['PROG']        = '$LALIBE_CPU'
params['APP']         = 'APP='+c51.bind_dir+c51.bind_c_36
params['NRS']         = params['cpu_nrs']
params['RS_NODE']     = params['cpu_rs_node']
params['A_RS']        = params['cpu_a_rs']
params['G_RS']        = params['cpu_g_rs']
params['C_RS']        = params['cpu_c_rs']
params['L_GPU_CPU']   = params['cpu_latency']

for c in cfgs_run:
    no = str(c)
    params['CFG'] = c
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
            if not spec_exists or args.force:
                prop_name = c51.names['prop'] % params
                prop_file = params['prop'] + '/' + prop_name+'.'+params['SP_EXTENSION']
                ''' make sure prop is correct size '''
                file_size = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
                utils.check_file(prop_file,file_size,params['file_time_delete'],params['corrupt'])
                if not os.path.exists(prop_file):
                    src_name = c51.names['src'] % params
                    src_file = params['src']+'/'+src_name+'.'+params['SP_EXTENSION']
                    utils.check_file(src_file,file_size,params['file_time_delete'],params['corrupt'])
                    if os.path.exists(src_file):
                        print('  making ',prop_file)
                        metaq = prop_name+'.sh'
                        t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
                        if not t_e or (args.o and not t_w):
                            xmlini = params['xml'] +'/'+(prop_xml_base %params)+'.ini.xml'
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
                            params['PROP_XML'] += prop_file.replace('/prop/','/xml/').replace(sp_ext,'out.xml')
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
                                params['CLEANUP']   = 'cd '+params['ENS_DIR']+'\n'
                                params['CLEANUP']  += 'python '+params['SCRIPT_DIR']+'/METAQ_spec.py '
                                params['CLEANUP']  += params['CFG']+' -s '+s0+' '+params['PRIORITY']+'\n'
                                if params['run_ff']:
                                    params['CLEANUP'] += 'python '+params['SCRIPT_DIR']+'/METAQ_seqsource.py '
                                    params['CLEANUP'] += params['CFG']+' -s '+s0+' '+params['PRIORITY']+'\n'
                                params['CLEANUP']  += 'sleep 5'
                            scheduler.make_task(metaq,args.mtype,params,folder=q)
                        else:
                            if args.verbose:
                                print('    task is in use or overwrite is false')
                    else:
                        if args.verbose:
                            print('    src missing',src_file)
                        print('python METAQ_src.py %s -s %s %s -v' %(c,s0,priority))
                        os.system('python %s/METAQ_src.py %s -s %s %s -v' %(params['SCRIPT_DIR'],c,s0,priority))
                else:
                    if args.verbose:
                        print('    prop exists',prop_file)
            elif os.path.exists(spec_file) and not args.force:
                print('    spec exists and force make prop = False',spec_file.split('/')[-1])
    else:
        print('  flowed cfg missing',cfg_file)
