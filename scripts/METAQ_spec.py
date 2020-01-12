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
            ''' check if spectrum exists '''
            spec_name    = c51.names['spec'] % params
            spec_file    = params['spec'] +'/'+ spec_name+'.h5'
            spec_file_4D = spec_file.replace('spec_','spec_4D_').replace('/spec/','/spec_4D/')
            '''
                NOTE: we need to enhance this to look for the t_sliced data file as well
            '''
            '''            spin*par* vol       * comp * dbl '''
            spec_size_4D = 2 * 2 * nt * nl**3 * 2 * 8
            utils.check_file(spec_file_4D,spec_size_4D,params['file_time_delete'],params['corrupt'])
            if os.path.exists(spec_file) and not os.path.exists(spec_file_4D):
                now = time.time()
                file_time = os.stat(spec_file).st_mtime
                if (now-file_time)/60 > params['file_time_delete']:
                    print('DELETING:',spec_file)
                    shutil.move(spec_file,params['corrupt']+'/'+spec_file.split('/')[-1])
            spec_exists = os.path.exists(spec_file) and os.path.exists(spec_file_4D)
            if not spec_exists:
                prop_name = c51.names['prop'] % params
                prop_file = params['prop'] + '/' + prop_name+'.'+params['SP_EXTENSION']
                ''' make sure prop is correct size '''
                file_size = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
                utils.check_file(prop_file,file_size,params['file_time_delete'],params['corrupt'])
                prop_exists = os.path.exists(prop_file)
                # a12m130 used h5 props
                if ens in ['a12m130','a15m135XL'] and not prop_exists:
                    prop_file = params['prop'] + '/' + prop_name+'.h5'
                    utils.check_file(prop_file,file_size,params['file_time_delete'],params['corrupt'])
                    prop_exists = os.path.exists(prop_file)
                if args.debug:
                    print('DEBUG: prop exists',prop_exists)
                if prop_exists:
                    print('  making ',spec_name)
                    metaq = spec_name+'.sh'
                    t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
                    try:
                        if params['metaq_split']:
                            t_e2,t_w2 = scheduler.check_task(metaq,args.mtype+'_'+str(params['cpu_nodes']),params,folder=q,overwrite=args.o)
                            t_w = t_w or t_w2
                            t_e = t_e or t_e2
                    except:
                        pass
                    if not t_e or (args.o and not t_w):
                        params['PROP_NAME'] = prop_name
                        params['SPEC_FILE'] = spec_file
                        xmlini = params['xml'] +'/'+spec_name+'.'+'ini.xml'
                        fin = open(xmlini,'w')
                        fin.write(xml_input.head)
                        ''' read prop '''
                        params['OBJ_ID']    = prop_name
                        params['OBJ_TYPE']  = 'LatticePropagator'
                        # we need to look for both lime and h5 prop
                        prop_file = params['prop'] + '/' + prop_name+'.'+params['SP_EXTENSION']
                        if os.path.exists(prop_file):
                            params['LIME_FILE'] = prop_file
                            fin.write(xml_input.qio_read % params)
                        else:
                            prop_file = params['prop'] + '/' + prop_name+'.h5'
                            params['H5_FILE'] = prop_file
                            if ens == 'a12m130':
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
                        ''' smear prop '''
                        params['SMEARED_PROP'] = prop_name+'_SS'
                        fin.write(xml_input.shell_smearing % params)
                        ''' PS '''
                        params['BARYON_MOM'] = '    <p2_max>'+str(params['BARYONS_PSQ_MAX'])+'</p2_max>'
                        params['H5_PATH'] = 'pt'
                        params['UP_QUARK'] = prop_name
                        params['DN_QUARK'] = prop_name
                        fin.write(xml_input.meson_spec % params)
                        fin.write(xml_input.baryon_spec % params)
                        ''' SS '''
                        params['H5_PATH'] = 'sh'
                        params['UP_QUARK'] = prop_name+'_SS'
                        params['DN_QUARK'] = prop_name+'_SS'
                        fin.write(xml_input.meson_spec % params)
                        fin.write(xml_input.baryon_spec % params)
                        ''' BARYONS 4D '''
                        params['BARYON_MOM'] = ''
                        params['SPEC_FILE'] = spec_file_4D
                        fin.write(xml_input.baryon_spec % params)
                        ''' end '''
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
                        print('missing prop',prop_file)
                    print('python METAQ_prop.py %s -s %s %s' %(c, s0, src_args))
                    os.system(c51.python+' %s/METAQ_prop.py %s -s %s %s %s' \
                        %(params['SCRIPT_DIR'], c, s0, src_args, params['PRIORITY']))
            else:
                if args.verbose:
                    print('spec exists',spec_file)
    else:
        print('  flowed cfg missing',cfg_file)
