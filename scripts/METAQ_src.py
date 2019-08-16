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

ens,stream = c51.ens_base()
ens_s = ens+'_'+stream

area51 = importlib.import_module(ens)
params = area51.params
params['machine'] = c51.machine
params['ENS_LONG'] = c51.ens_long[ens]
params['ENS_S']    = ens_s
params['STREAM']   = stream
params['METAQ_PROJECT'] = 'src_'+ens_s

'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs',nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-s','--src',type=str)
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('--mtype',default='cpu',help='specify metaq dir [%(default)s]')
parser.add_argument('-p',default=False,action='store_const',const=True,\
    help='put task.sh in priority queue? [%(default)s]')
parser.add_argument('-v','--verbose',default=True,action='store_const',const=False,\
    help='run with verbose output? [%(default)s]')
parser.add_argument('-f','--force',default=False,action='store_const',const=True,\
    help='force create props? [%(default)s]')
parser.add_argument('--strange',default=False,action='store_const',const=True,\
    help='submit METAQ_strange_prop when finished? [%(default)s]')
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
            ''' check if spectrum and props exist '''
            make_src = False
            prop_name = c51.names['prop'] % params
            prop_file = params['prop'] + '/' + prop_name+'.'+params['SP_EXTENSION']
            ''' make sure prop is correct size '''
            file_size = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
            utils.check_file(prop_file,file_size,params['file_time_delete'],params['corrupt'])
            prop_exists = os.path.exists(prop_file)
            # if a12m130, then check for h5 files
            if ens in ['a12m130'] and not prop_exists:
                prop_file = params['prop'] + '/' + prop_name+'.h5'
                utils.check_file(prop_file,file_size,params['file_time_delete'],params['corrupt'])
                prop_exists = os.path.exists(prop_file)


            if args.force:
                make_src = True
            else:
                spec_name    = c51.names['spec'] % params
                spec_file    = params['spec'] +'/'+ spec_name+'.h5'
                spec_file_4D = spec_file.replace('spec_','spec_4D_').replace('/spec/','/spec_4D/')
                spec_exists  = os.path.exists(spec_file) and os.path.exists(spec_file_4D)
                if not spec_exists and not prop_exists:
                    make_src = True

            if make_src:
                src_name = c51.names['src'] % params
                src_file = params['src']+'/'+src_name+'.'+params['SP_EXTENSION']
                utils.check_file(src_file,file_size,params['file_time_delete'],params['corrupt'])
                print('making src',src_name)
                if not os.path.exists(src_file):
                    metaq = src_name + '.sh'
                    t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
                    try:
                        if params['metaq_split']:
                            t_e2,t_w2 = scheduler.check_task(metaq,args.mtype+'_'+str(params['cpu_nodes']),params,folder=q,overwrite=args.o)
                            t_w = t_w or t_w2
                            t_e = t_e or t_e2
                    except:
                        pass
                    if not t_e or (args.o and not t_w):
                        xmlini = params['xml'] +'/'+src_name+'.'+'ini.xml'
                        fin = open(xmlini,'w')
                        fin.write(xml_input.head)
                        ''' create source '''
                        x0,y0,z0,t0 = sources.xyzt(s0)
                        params['X0'] = x0
                        params['Y0'] = y0
                        params['Z0'] = z0
                        params['T0'] = t0
                        params['SRC_NAME'] = src_name
                        fin.write(xml_input.shell_source % params)
                        ''' write source '''
                        params['OBJ_ID']    = src_name
                        params['OBJ_TYPE']  = 'LatticePropagatorF'
                        params['LIME_FILE'] = src_file
                        fin.write(xml_input.qio_write % params)
                        ''' close xml file '''
                        fin.write(xml_input.tail % params)
                        fin.close()

                        ''' Make METAQ task '''
                        params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')
                        params['INI']       = xmlini
                        params['OUT']       = xmlini.replace('.ini.xml','.out.xml')
                        params['STDOUT']    = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                        # check if props exists in case of forced running
                        prop_strange = prop_file.replace(params['MV_L'],params['MV_S'])
                        if prop_file.split('.')[-1] =='h5':
                            prop_strange = prop_strange.replace('.h5','.lime')
                        if not prop_exists or (args.strange and not os.path.exists(prop_strange)):
                            params['CLEANUP']   = 'if [ "$cleanup" -eq 0 ]; then\n'
                            params['CLEANUP']  += '    cd '+params['ENS_DIR']+'\n'
                            if not prop_exists:
                                params['CLEANUP']  += '    python '+params['SCRIPT_DIR']+'/METAQ_prop.py '+params['CFG']+' -s '+s0+' '+params['PRIORITY']+'\n'
                            if args.strange and not os.path.exists(prop_strange):
                                params['CLEANUP']  += '    python '+params['SCRIPT_DIR']+'/METAQ_strange_prop.py '+params['CFG']+' -s '+s0+' '+params['PRIORITY']+'\n'
                            params['CLEANUP']  += '    sleep 5\n'
                            params['CLEANUP']  += 'else\n'
                            params['CLEANUP']  += '    echo "mpirun failed"\n'
                            params['CLEANUP']  += 'fi\n'
                        else:
                            params['CLEANUP'] = ''
                        mtype = args.mtype
                        try:
                            if params['metaq_split']:
                                mtype = mtype + '_'+str(params['cpu_nodes'])
                        except:
                            pass
                        scheduler.make_task(metaq,mtype,params,folder=q)
                else:
                    if args.verbose:
                        print('src exists',src_file)

            else:
                if args.verbose and prop_exists:
                    print('prop exists',prop_file)
                elif args.verbose and spec_exists:
                    print('spec exists',spec_file)
    else:
        print('missing flowed config')
