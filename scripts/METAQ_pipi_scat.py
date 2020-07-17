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
parser.add_argument('cfgs',nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-s','--src',type=str)
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('--mtype',default='cpu',help='specify metaq dir [%(default)s]')
parser.add_argument('-p',default=False,action='store_const',const=True,\
    help='put task.sh in priority queue? [%(default)s]')
parser.add_argument('-v','--verbose',default=True,action='store_const',const=False,\
    help='run with verbose output? [%(default)s]')
parser.add_argument('-d','--debug',default=False,action='store_const',const=True,\
    help='print DEBUG statements? [%(default)s]')
parser.add_argument('--src_set',nargs=3,type=int,help='specify si sf ds')
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

#Find source pairs
src_pairs={cfg:{src.split('t')[1]:[] for src in srcs[cfg]} for cfg in srcs}
for cfg in srcs:
    for src in srcs[cfg]:
        tsrc=src.split('t')[1]
        src_pairs[cfg][tsrc].append(src)

#Check source pairs
for cfg in srcs:
    for tsrc in src_pairs[cfg]:
        if len(src_pairs[cfg][tsrc])<2:
            print('Less than two sources passed for t='+tsrc)
            src_pairs[cfg].pop(tsrc)
    if len(src_pairs[cfg])==0:
        sys.exit('Not enough sources passed.') 

print('running ',cfgs_run[0],'-->',cfgs_run[-1])
print('srcs:',src_ext)
#time.sleep(1)

smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
''' for now - just doing the light quark '''
params['MQ'] = params['MV_L']
if params['run_strange']:
    params['MV_LS'] = 'ml'+params['MV_L']+'_ms'+params['MV_S']
else:
    params['MV_LS'] = 'ml'+params['MV_L']

params = area51.mpirun_params(c51.machine)
params['NODES']       = params['cpu_nodes']
params['METAQ_NODES'] = params['cpu_nodes']
params['METAQ_GPUS']  = params['cpu_gpus']
params['WALL_TIME']   = params['gflow_time']
params['ENS_DIR']     = c51.ens_dir % params
params['SCRIPT_DIR']  = c51.script_dir
params['MAXCUS']      = params['cpu_maxcus']
params['SOURCE_ENV']  = c51.env
params['PROG']        = '$INSTALLDIR/lalibe_haobo_cpu/bin/lalibe'
params['APP']         = 'APP='+c51.bind_dir+params['cpu_bind']
params['NRS']         = params['cpu_nrs']
params['RS_NODE']     = params['cpu_rs_node']
params['A_RS']        = params['cpu_a_rs']
params['G_RS']        = params['cpu_g_rs']
params['C_RS']        = params['cpu_c_rs']
params['L_GPU_CPU']   = params['cpu_latency']
params['IO_OUT']      = '-i $ini -o $out > $stdout 2>&1'

if 'run_mm' not in params:
    sys.exit('You must set the run_mm switch on the area51 file')


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

        for ts0 in src_pairs[c]:
            if args.debug:
                print('DEBUG: srcs',src_pairs[c][ts0][0],src_pairs[c][ts0][1])
            if args.verbose:
                print(c,src_pairs[c][ts0][0],src_pairs[c][ts0][1])
            ''' check if pipi scat exists '''
            for s0 in src_pairs[c][ts0]:
                params['SRC']=s0
                pipi_scat_name    = c51.names['pipi_scat'] % params
                pipi_scat_file    = params['pipi_scat'] +'/'+ pipi_scat_name+'.h5'

                pipi_scat_exists = os.path.exists(pipi_scat_file)
                if not pipi_scat_exists:
                    ''' make sure prop is correct size '''
                    try:
                        file_size = params['prop_size']
                    except:
                        print('PROP_SIZE not defined in area51 file: using crude default')
                        file_size = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4

                    params['MQ'] = params['MV_L']
                    prop_l = c51.names['prop'] % params
                    prop_l_file = params['prop'] + '/' +prop_l +'.'+params['SP_EXTENSION']
                    utils.check_file(prop_l_file, file_size,params['file_time_delete'],params['corrupt'])
                    prop_l_exists = os.path.exists(prop_l_file)
                    if not prop_l_exists and ens in ['a12m130','a15m135XL']:
                        prop_file = prop_l_file.replace('.'+params['SP_EXTENSION'],'.h5')
                        try:
                            file_size_h5 = params['prop_size_h5']
                        except:
                            print('PROP_SIZE not defined in area51 file: using crude default')
                            file_size = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
                        utils.check_file(prop_file, file_size_h5, params['file_time_delete'],params['corrupt'])
                        if os.path.exists(prop_file):
                            prop_l_exists = True
                            prop_l_file = str(prop_file)
                    # if run_strange, also check strange prop
                    if params['run_strange']:
                        params['MQ'] = params['MV_S']
                        prop_s = c51.names['prop'] % params
                        prop_s_file = params['prop_strange'] + '/' +prop_s +'.'+params['SP_EXTENSION']
                        utils.check_file(prop_s_file, file_size,params['file_time_delete'],params['corrupt'])
                        prop_s_exists = os.path.exists(prop_s_file)
                        if not prop_s_exists and ens in ['a12m130','a15m135XL']:
                            prop_file = prop_s_file.replace('.'+params['SP_EXTENSION'],'.h5')
                            try:
                                file_size_h5 = params['prop_size_h5']
                            except:
                                print('PROP_SIZE not defined in area51 file: using crude default')
                                file_size = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
                            utils.check_file(prop_file, file_size_h5, params['file_time_delete'],params['corrupt'])
                            if os.path.exists(prop_file):
                                prop_s_exists = True
                                prop_s_file = str(prop_file)

                    # now create xml and metaq
                    if params['run_strange']:
                        proceed = prop_l_exists and prop_s_exists
                    else:
                        proceed = prop_l_exists
                    if proceed:
                        print('  making ',pipi_scat_name)
                        metaq = pipi_scat_name+'.sh'
                        t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
                        try:
                            if params['metaq_split']:
                                t_e2,t_w2 = scheduler.check_task(metaq,args.mtype+'_'+str(params['cpu_nodes']),params,folder=q,overwrite=args.o)
                                t_w = t_w or t_w2
                                t_e = t_e or t_e2
                        except:
                            pass

                        if not t_e or (args.o and not t_w):
                            xmlini = params['xml'] +'/'+pipi_scat_name+'.'+'ini.xml'
                            fin = open(xmlini,'w')
                            fin.write(xml_input.head)

                            # read prop(s)
                            params['OBJ_TYPE']  = 'LatticePropagator'
                            params['OBJ_ID']    = prop_l
                            params['PROP_NAME'] = prop_l_file
                            if prop_l_file.split('.')[-1] == 'lime':
                                params['LIME_FILE'] = prop_l_file
                                fin.write(xml_input.qio_read % params)
                            elif prop_l_file.split('.') == '.h5':
                                params['H5_FILE'] = prop_l_file
                                if ens == 'a12m130':
                                    if params['si'] in [0,8]:
                                        params['H5_OBJ_NAME'] = 'prop1'
                                        params['H5_PATH'] = '48_64'
                                    else:
                                        params['H5_PATH'] = ''
                                        params['H5_OBJ_NAME'] = 'prop'
                                else:
                                    params['H5_PATH'] = ''
                                    params['H5_OBJ_NAME'] = 'prop'
                                fin.write(xml_input.hdf5_read % params)
                            else:
                                print(prop_l_file)
                                sys.exit('unrecognized prop extension')
                            # read strange prop if we are doing run_strange
                            if params['run_strange']:
                                params['OBJ_ID']    = prop_s
                                params['PROP_NAME'] = prop_s_file
                                if prop_s_file.split('.')[-1] == 'lime':
                                    params['LIME_FILE'] = prop_s_file
                                    fin.write(xml_input.qio_read % params)
                                elif prop_s_file.split('.') == '.h5':
                                    params['H5_FILE'] = prop_s_file
                                    if ens == 'a12m130':
                                        if params['si'] in [0,8]:
                                            params['H5_OBJ_NAME'] = 'prop1'
                                            params['H5_PATH'] = '48_64'
                                        else:
                                            params['H5_PATH'] = ''
                                            params['H5_OBJ_NAME'] = 'prop'
                                    else:
                                        params['H5_PATH'] = ''
                                        params['H5_OBJ_NAME'] = 'prop'
                                    fin.write(xml_input.hdf5_read % params)
                                else:
                                    print(prop_s_file)
                                    sys.exit('unrecognized prop extension')
                            # sink smear props
                            params['PROP_NAME'] = prop_l
                            params['SMEARED_PROP'] = 'SS_'+prop_l
                            fin.write(xml_input.shell_smearing % params)
                            if params['run_strange']:
                                params['PROP_NAME'] = prop_s
                                params['SMEARED_PROP'] = 'SS_'+prop_s
                                fin.write(xml_input.shell_smearing % params)
                            # make pipi xml file
                            params['PIPI_SCAT_FILE']=pipi_scat_file
                            params['PROP_LIGHT'] = prop_l
                            if params['run_strange']:
                                params['PROP_STRANGE'] = prop_s
                                fin.write(xml_input.pik_spec % params)
                            else:
                                fin.write(xml_input.pipi_spec % params)

                            fin.write(xml_input.tail % params)
                            fin.close()

                            ''' make METAQ task '''
                            params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')
                            params['INI']       = xmlini
                            params['OUT']       = xmlini.replace('.ini.xml','.out.xml')
                            params['STDOUT']    = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                            params['CLEANUP']   = ''
                            mtype = args.mtype
                            try:
                                if params['metaq_split']:
                                    mtype = mtype + '_'+str(params['cpu_nodes'])
                            except:
                                pass
                            scheduler.make_task(metaq,mtype,params,folder=q)
                    else:
                        if args.verbose:
                            print('missing props')
                            print(prop_l_file)
                            if params['run_strange']:
                                print(prop_s_file)
                        print('python METAQ_prop.py %s -s %s %s' %(c, src_pairs[c][ts0][0], src_args))
                        print('python METAQ_prop.py %s -s %s %s' %(c,src_pairs[c][ts0][1], src_args))
                        os.system(c51.python+' %s/METAQ_prop.py %s -s %s %s %s' \
                            %(params['SCRIPT_DIR'], c,  src_pairs[c][ts0][0], src_args, params['PRIORITY']))
                        os.system(c51.python+' %s/METAQ_prop.py %s -s %s %s %s' \
                            %(params['SCRIPT_DIR'], c,  src_pairs[c][ts0][1], src_args, params['PRIORITY']))
                else:
                    if args.verbose:
                        print('pipi/kpi file exists',pipi_scat_file)
    else:
        print('  flowed cfg missing',cfg_file)
