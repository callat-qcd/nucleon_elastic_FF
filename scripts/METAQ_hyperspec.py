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
params['METAQ_PROJECT'] = 'spec_'+ens_s

'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs',           nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-s','--src',     type=str)
parser.add_argument('-o',             default=False,action='store_true',
                    help=             'overwrite xml and metaq files? [%(default)s]')
parser.add_argument('--mtype',        default='cpu',help='specify metaq dir [%(default)s]')
parser.add_argument('--gpu_l',        default='gpu', help='specify metaq dir for prop jobs [%(default)s]')
parser.add_argument('--gpu_s',        default='gpu', help='specify metaq dir for strange prop jobs [%(default)s]')
parser.add_argument('-p',             default=False,action='store_true',
                    help=             'put task.sh in priority queue? [%(default)s]')
parser.add_argument('-v','--verbose', default=True,action='store_false',
                    help=             'run with verbose output? [%(default)s]')
parser.add_argument('-d','--debug',   default=False,action='store_true',
                    help=             'print DEBUG statements? [%(default)s]')
parser.add_argument('--src_set',      nargs=3,type=int,help='specify si sf ds')
parser.add_argument('--clean',        default=False,action='store_true',
                    help=             'delete used src and strange prop files? [%(default)s]')
parser.add_argument('--vast',         default=False,action='store_true',\
                    help=             'write src and strange prop files to vast instead of gpfs [%(default)s]')
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

params = area51.mpirun_params(c51.machine)
params['NODES']       = params['cpu_nodes']
params['METAQ_NODES'] = params['cpu_nodes']
params['METAQ_GPUS']  = params['cpu_gpus']
params['WALL_TIME']   = params['spec_time']
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

''' PIPI '''
run_pipi = params['run_pipi'] and params['run_strange']

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
    if args.debug:
        print(cfg_file)
        sys.exit()

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
            ''' check if spectrum exists '''
            hyperspec_name = c51.names['hyperspec'] % params
            hyperspec_file = params['hyperspec'] +'/'+ hyperspec_name+'.h5'
            utils.check_file(hyperspec_file,params['hyperspec_size'],params['file_time_delete'],params['corrupt'])
            if run_pipi:
                pipi_name = c51.names['pik'] % params
                pipi_file = params['hyperspec'] +'/'+ pipi_name
                utils.check_file(pipi_file, params['pik_size'], params['file_time_delete'],params['corrupt'])
                pipi_exists = os.path.exists(pipi_file)
                params['PIPI_SCAT_FILE'] = pipi_file
            else:
                pipi_exists = True
            if not os.path.exists(hyperspec_file) or not pipi_exists:
                # light prop
                params['MQ'] = params['MV_L']
                light_prop_name = c51.names['prop'] % params
                light_prop_file = params['prop'] + '/' + light_prop_name+'.'+params['SP_EXTENSION']
                ''' make sure prop is correct size '''
                try:
                    file_size = params['prop_size']
                except:
                    print('PROP_SIZE not defined in area51 file: using crude default')
                    file_size = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
                utils.check_file(light_prop_file,file_size,params['file_time_delete'],params['corrupt'])
                light_prop_exists = os.path.exists(light_prop_file)
                # a12m130 used h5 props
                if ens in ['a15m135XL','a12m130'] and not light_prop_exists:
                    light_prop_file = params['prop'] + '/' + light_prop_name+'.h5'
                    try:
                        file_size = params['prop_size_h5']
                    except:
                        print('PROP_SIZE not defined in area51 file: using crude default')
                        file_size = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
                    utils.check_file(light_prop_file,file_size,params['file_time_delete'],params['corrupt'])
                    light_prop_exists = os.path.exists(light_prop_file)
                if args.debug:
                    print('DEBUG: light prop exists',light_prop_exists)
                # strange prop
                params['MQ'] = params['MV_S']
                strange_prop_name = c51.names['prop'] % params
                strange_prop_file = params['prop_strange'] + '/' + strange_prop_name+'.'+params['SP_EXTENSION']
                if args.vast:
                    strange_prop_file = strange_prop_file.replace('gpfs1/walkloud','vast1/coldqcd')
                try:
                    file_size = params['prop_size']
                except:
                    print('PROP_SIZE not defined in area51 file: using crude default')
                    file_size = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
                utils.check_file(strange_prop_file, file_size,params['file_time_delete'],params['corrupt'])
                strange_prop_exists = os.path.exists(strange_prop_file)
                if light_prop_exists and strange_prop_exists:
                    print('  making ',hyperspec_name)
                    metaq = hyperspec_name+'.sh'
                    t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
                    try:
                        if params['metaq_split']:
                            t_e2,t_w2 = scheduler.check_task(metaq,args.mtype+'_'+str(params['cpu_nodes']),params,folder=q,overwrite=args.o)
                            t_w = t_w or t_w2
                            t_e = t_e or t_e2
                    except:
                        pass
                    if not t_e or (args.o and not t_w):
                        params['HYPERSPEC_FILE'] = hyperspec_file
                        xmlini = params['xml'] +'/'+hyperspec_name+'.'+'ini.xml'
                        fin = open(xmlini,'w')
                        fin.write(xml_input.head)
                        ''' read prop '''
                        params['OBJ_ID']    = light_prop_name
                        params['OBJ_TYPE']  = 'LatticePropagator'
                        # we need to look for both lime and h5 prop
                        prop_file = params['prop'] + '/' + light_prop_name+'.'+params['SP_EXTENSION']
                        if os.path.exists(prop_file):
                            params['LIME_FILE'] = prop_file
                            fin.write(xml_input.qio_read % params)
                        else:
                            prop_file = params['prop'] + '/' + light_prop_name+'.h5'
                            params['H5_FILE'] = light_prop_file
                            if ens in ['a12m130']:
                                if params['si'] in [0,8]:
                                    params['H5_PATH'] = '48_64'
                                    params['H5_OBJ_NAME'] = 'prop1'
                                else:
                                    params['H5_PATH'] = ''
                                    params['H5_OBJ_NAME'] = 'prop'
                            else:
                                params['H5_PATH'] = ''
                                params['H5_OBJ_NAME'] = 'prop'
                            fin.write(xml_input.hdf5_read % params)
                        # strange prop
                        params['OBJ_ID']    = strange_prop_name
                        prop_file = params['prop_strange'] + '/' + strange_prop_name+'.'+params['SP_EXTENSION']
                        if args.vast:
                            prop_file = prop_file.replace('gpfs1/walkloud','vast1/coldqcd')
                        params['LIME_FILE'] = prop_file
                        fin.write(xml_input.qio_read % params)
                        ''' smear props '''
                        params['PROP_NAME']    = light_prop_name
                        params['SMEARED_PROP'] = light_prop_name+'_SS'
                        fin.write(xml_input.shell_smearing % params)
                        params['PROP_NAME']    = strange_prop_name
                        params['SMEARED_PROP'] = strange_prop_name+'_SS'
                        fin.write(xml_input.shell_smearing % params)
                        if not os.path.exists(hyperspec_file):
                            ''' PS '''
                            params['BARYON_MOM'] = '    <p2_max>'+str(params['BARYONS_PSQ_MAX'])+'</p2_max>'
                            params['H5_PATH'] = 'pt'
                            params['UP_QUARK'] = light_prop_name
                            params['DN_QUARK'] = light_prop_name
                            params['STRANGE_QUARK'] = strange_prop_name
                            fin.write(xml_input.pi_k_spec % params)
                            fin.write(xml_input.hyperon_spec % params)
                            ''' SS '''
                            params['H5_PATH'] = 'sh'
                            params['UP_QUARK'] = light_prop_name+'_SS'
                            params['DN_QUARK'] = light_prop_name+'_SS'
                            params['STRANGE_QUARK'] = strange_prop_name+'_SS'
                            fin.write(xml_input.pi_k_spec % params)
                            fin.write(xml_input.hyperon_spec % params)
                        if run_pipi and not os.path.exists(pipi_file):
                            ''' PS '''
                            params['H5_PATH'] = 'pt'
                            params['UP_QUARK'] = light_prop_name
                            params['STRANGE_QUARK'] = strange_prop_name
                            fin.write(xml_input.meson_meson % params)
                            ''' SS '''
                            params['H5_PATH'] = 'sh'
                            params['UP_QUARK'] = light_prop_name+'_SS'
                            params['STRANGE_QUARK'] = strange_prop_name+'_SS'
                            fin.write(xml_input.meson_meson % params)
                        ''' end '''
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
                        print('missing light or strange prop')
                        print(light_prop_file)
                        print(strange_prop_file)
                    print('python METAQ_strange_prop.py %s -s %s %s --mtype %s --gpu_l %s' %(c,s0, src_args, args.gpu_s, args.gpu_l))
                    os.system(c51.python+' %s/METAQ_prop.py %s -s %s %s %s --mtype %s --gpu_s %s' \
                              %(params['SCRIPT_DIR'],c,s0,src_args,params['PRIORITY'], args.gpu_l, args.gpu_s))
                    os.system(c51.python+' %s/METAQ_strange_prop.py %s -s %s %s %s --mtype %s --gpu_l %s' \
                              %(params['SCRIPT_DIR'],c,s0,src_args,params['PRIORITY'], args.gpu_s, args.gpu_l))
            else:
                if args.verbose:
                    print('hyperspec exists',hyperspec_file)
                if args.clean:
                    # light prop
                    params['MQ'] = params['MV_L']
                    light_prop_name = c51.names['prop'] % params
                    light_prop_file = params['prop'] + '/' + light_prop_name+'.'+params['SP_EXTENSION']
                    ''' make sure prop is correct size '''
                    try:
                        file_size = params['prop_size']
                    except:
                        print('PROP_SIZE not defined in area51 file: using crude default')
                        file_size = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
                    utils.check_file(light_prop_file,file_size,params['file_time_delete'],params['corrupt'])
                    light_prop_exists = os.path.exists(light_prop_file)
                    # strange prop
                    params['MQ'] = params['MV_S']
                    strange_prop_name = c51.names['prop'] % params
                    strange_prop_file = params['prop_strange'] + '/' + strange_prop_name+'.'+params['SP_EXTENSION']
                    if args.vast:
                        strange_prop_file = strange_prop_file.replace('gpfs1/walkloud','vast1/coldqcd')
                    utils.check_file(strange_prop_file, file_size,params['file_time_delete'],params['corrupt'])
                    strange_prop_exists = os.path.exists(strange_prop_file)
                    # delete source
                    if light_prop_exists and strange_prop_exists:
                        src_name = c51.names['src'] % params
                        src_file = params['src']+'/'+src_name+'.'+params['SP_EXTENSION']
                        if args.vast:
                            src_file = src_file.replace('gpfs1/walkloud','vast1/coldqcd')
                        if os.path.exists(src_file):
                            print('deleting %s' %src_name)
                            os.remove(src_file)
                    # delete strange prop
                    if os.path.exists(hyperspec_file) and os.path.exists(pipi_file) and params['hyperspec_size'] > 1 and params['pik_size'] > 1:
                        if os.path.exists(strange_prop_file):
                            print('deleting %s' %strange_prop_name)
                            os.remove(strange_prop_file)
                    elif params['hyperspec_size'] == 1 or params['pik_size'] == 1:
                        print('you must specify real size of hyperspec_size and pik_size to clean (delete) srcs and props')
                    
    else:
        print('  flowed cfg missing',cfg_file)
