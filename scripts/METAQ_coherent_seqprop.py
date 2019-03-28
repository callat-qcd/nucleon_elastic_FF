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
params['METAQ_PROJECT'] = 'cfg_flow_'+ens_s

'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs',nargs='+',type=int,help='start [stop] run cfg number')
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('--mtype',default='gpu',help='specify metaq dir [%(default)s]')
parser.add_argument('-t','--t_sep',nargs='+',type=int,help='values of t_sep [default = all]')
parser.add_argument('-d','--debug',default=False,action='store_const',const=True,\
    help='run DEBUG? [%(default)s]')
parser.add_argument('-p','--priority',default=False,action='store_const',const=True,help='put task in priority? [%(default)s]')
parser.add_argument('-v','--verbose',default=True,action='store_const',const=False,\
    help='run with verbose output? [%(default)s]')
args = parser.parse_args()
print('%s: Arguments passed' %sys.argv[0].split('/')[-1])
print(args)
print('')

'''
    RUN PARAMETER SET UP
'''
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,args.src,params)

if args.priority:
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
params['MQ'] = params['MV_L']

smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
''' for now - just doing the light quark '''
params['MQ'] = params['MV_L']

if args.t_sep == None:
    t_seps  = params['t_seps']
else:
    t_seps = args.t_sep
flav_spin = []
for f in params['flavs']:
    for s in params['spins']:
        flav_spin.append(f+'_'+s)
''' ONLY doing snk_mom 0 0 0 now '''
snk_mom = params['snk_mom'][0]
m0,m1,m2 = snk_mom.split()
params['M0']=m0
params['M1']=m1
params['M2']=m2
params['MOM'] = 'px%spy%spz%s' %(m0,m1,m2)

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
        print("Making coherent sources and seqprops for cfg: ",c)

        have_seqsrc = True
        have_all_3pts = True
        for dt_int in t_seps:
            dt = str(dt_int)
            params['T_SEP'] = dt
            ''' Do the 3pt files exist? '''
            have_3pts = True
            for s0 in srcs[c]:
                params['SRC'] = s0
                coherent_formfac_name  = c51.names['coherent_ff'] % params
                coherent_formfac_file  = params['formfac'] +'/'+coherent_formfac_name + '.h5'
                coherent_formfac_file_4D = coherent_formfac_file.replace('formfac_','formfac_4D_')
                if not os.path.exists(coherent_formfac_file) and not os.path.exists(coherent_formfac_file_4D):
                    have_3pts = False
                    have_all_3pts = False
            if not have_3pts:
                for fs in flav_spin:
                    flav,snk_spin,src_spin=fs.split('_')
                    params['FLAV']=flav
                    params['SOURCE_SPIN']=snk_spin
                    params['SINK_SPIN']=src_spin
                    spin = snk_spin+'_'+src_spin
                    params['FLAV_SPIN']=fs
                    for particle in particles:
                        params['PARTICLE'] = particle
                        if '_np' in particle:
                            params['QUARK_SPIN'] = 'LOWER'
                            params['T_SEP'] = '-'+dt
                        else:
                            params['QUARK_SPIN'] = 'UPPER'
                            params['T_SEP'] = dt
                        seqprop_name  = c51.names['seqprop'] %params
                        seqprop_file  = params['seqprop']+'/'+seqprop_name+'.'+params['SP_EXTENSION']
                        ''' check SEQPROP file size
                            delete if small and older than time_delete
                        '''
                        seqprop_size      = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
                        utils.check_file(seqprop_file,seqprop_size,params['file_time_delete'],params['corrupt'])
                        if not os.path.exists(seqprop_file):
                            ''' make sure all seqsource files exists '''
                            have_seqsrc_t = True
                            for s0 in srcs[c]:
                                params['SRC'] = s0
                                seqsrc_name = c51.names['seqsrc'] %params
                                seqsrc_file = params['seqsrc']+'/'+seqsrc_name+'.'+params['SP_EXTENSION']
                                if not os.path.exists(seqsrc_file):
                                    if args.verbose:
                                        print('    missing sink',seqsrc_file)
                                    have_seqsrc_t = False
                                    have_seqsrc   = False
                            if have_seqsrc_t:
                                metaq  = seqprop_name+'.sh'
                                t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
                                if not t_e or (args.o and not t_w):
                                    xmlini = seqprop_file.replace('seqprop/','xml/').replace('.'+sp_ext,'.ini.xml')
                                    fin = open(xmlini,'w')
                                    fin.write(xml_input.head)

                                    ''' read all seqsources '''
                                    for si,s0 in enumerate(srcs[c]):
                                        params['SRC'] = s0
                                        seqsrc_name = c51.names['seqsrc'] %params
                                        seqsrc_file = params['seqsrc']+'/'+seqsrc_name+'.'+params['SP_EXTENSION']
                                        params['OBJ_ID']    = seqsrc_name
                                        params['OBJ_TYPE']  = 'LatticePropagator'
                                        params['LIME_FILE'] = seqsrc_file
                                        fin.write(xml_input.qio_read % params)
                                        params['SEQSOURCE_'+str(si)] = seqsrc_name
                                    ''' make coherent_seqsource '''
                                    coherent_seqsrc_name = c51.names['coherent_seqsrc'] % params
                                    params['COHERENT_SEQSOURCE'] = coherent_seqsrc_name
                                    fin.write(xml_input.coherent_seqsrc % params)

                                    ''' solve seqprop '''
                                    params['SRC_NAME']  = coherent_seqsrc_name
                                    params['PROP_NAME'] = seqprop_name
                                    params['PROP_XML']  = ''
                                    fin.write(xml_input.quda_nef % params)

                                    ''' save seqprop '''
                                    params['OBJ_ID']      = seqprop_name
                                    params['OBJ_TYPE']    = 'LatticePropagatorF'
                                    params['LIME_FILE']   = seqprop_file
                                    '''
                                    params['H5_FILE']     = seqprop_file
                                    params['H5_PATH']     = ''
                                    params['H5_OBJ_NAME'] = 'propagator'
                                    '''
                                    fin.write(xml_input.qio_write % params)

                                    fin.write(xml_input.tail % params)
                                    fin.close()

                                    ''' Make METAQ task '''
                                    params['METAQ_LOG'] = params['METAQ_DIR']+'/log/'+metaq.replace('.sh','.log')
                                    params['INI']       = xmlini
                                    params['OUT']       = xmlini.replace('.ini.xml','.out.xml')
                                    params['STDOUT']    = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                                    params['CLEANUP']   = 'cd '+params['ENS_DIR']+'\n'
                                    params['CLEANUP']  += 'python '+params['SCRIPT_DIR']+'/METAQ_coherent_formfac.py '
                                    params['CLEANUP']  += params['CFG']+' -t'+params['T_SEP']+' -s '+s0+' '+params['PRIORITY']
                                    params['CLEANUP']  += 'sleep 5'
                                    scheduler.make_task(metaq,args.mtype,params,folder=q)
                                else:
                                    if not args.verbose:
                                        print('    task is in use or overwrite is false')
                        else:
                            print('seqprop exists',seqprop_file)
            else:
                if args.verbose:
                    print('    3pt corr exists:',coherent_formfac_file)
        if not have_seqsrc and not have_all_3pts:
            print('python METAQ_seqsource.py %s -v' %(c))
            os.system('python %s/METAQ_seqsource.py %s %s -v' %(params['SCRIPT_DIR'],c,params['PRIORITY']))

    else:
        if not os.path.exists(cfg_file):
            print('  flowed cfg missing',cfg_file)
        elif not all_srcs:
            print('missing srcs [8]')
            print(c,srcs[c])
