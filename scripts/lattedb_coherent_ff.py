from __future__ import print_function
import os, sys, shutil, time
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

import collect_corr_utils as collect_utils

import lattedb_ff_disk_tape_functions as lattedb_ff
from lattedb.project.formfac.models import (
    TSlicedSAveragedFormFactor4DFile,
    DiskTSlicedSAveragedFormFactor4DFile,
    TapeTSlicedSAveragedFormFactor4DFile,
    CorrelatorMeta,
    TapeCorrelatorH5Dset
)

ens,stream = c51.ens_base()
ens_s = ens+'_'+stream

area51 = importlib.import_module(ens)
params = area51.params
params['machine'] = c51.machine
params['ENS_LONG'] = c51.ens_long[ens]
params['ENS_S']    = ens_s
params['STREAM']   = stream
params['METAQ_PROJECT'] = 'formfac_'+ens_s

'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs'            , nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-s','--src'      , type=str)
parser.add_argument('--mtype'         , default='cpu',help='specify metaq dir [%(default)s]')
parser.add_argument('-t','--t_sep'    , nargs='+',type=int,help='values of t_sep [default = all]')
parser.add_argument('--src_set'       , nargs=3,type=int,help='specify si sf ds')
parser.add_argument('-r','--rtol'     , type=float, default=1.e-8, help='relative tolerance used to compare h5 files [%(default)s]')
parser.add_argument('-a','--atol'     , type=float, default=0., help='absolute tolerance used to compare h5 files [%(default)s]')
parser.add_argument('-o'              , default=False,action='store_const',const=True, \
                    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('--redo'          , default=False,action='store_const',const=True, \
                    help='remake even if 4D_tslice or 4D_tslice_src_avg exists? [%(default)s]')
parser.add_argument('-d','--debug'    , default=False,action='store_const',const=True, \
                    help='run DEBUG? [%(default)s]')
parser.add_argument('-p','--priority' , default=False,action='store_const',const=True, \
                    help='put task in priority? [%(default)s]')
parser.add_argument('-v','--verbose'  , default=True, action='store_const',const=False,\
                    help='run with verbose output? [%(default)s]')
parser.add_argument('--make_tasks'    , default=True, action='store_const', const=False,\
                    help='make tasks? [%(default)s]')
parser.add_argument('--collect'       , default=False, action='store_const', const=True,\
                    help='collect data? [%(default)s]')
parser.add_argument('--dbl_check'     , default=False, action='store_const', const=True,\
                    help='double check tape entries? [%(default)s]')
args = parser.parse_args()
print('%s: Arguments passed' %sys.argv[0].split('/')[-1])
print(args)
print('')

''' DATA collection directories '''
data_dir     = c51.data_dir % params
tmp_data_dir = c51.tmp_data_dir % params
tape_dir     = c51.tape+'/'+ens_s+'/data'
# if we are collecting data - no need to push during data query for non-lattedb interface
tape_push    = not args.collect

''' RUN PARAMETER SET UP '''
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
params['SRC_SET'] = src_set

cfgs,srcs = utils.parse_cfg_src_argument(args.cfgs,args.src,params)
if args.src:
    params['N_SEQ'] = len(range(params['si'],params['sf']+params['ds'],params['ds']))
else:
    params['N_SEQ'] = len(srcs[cfgs[0]])

if args.priority:
    q = 'priority'
    params['PRIORITY'] = '-p'
else:
    q = 'todo'
    params['PRIORITY'] = ''

nt = int(params['NT'])
nl = int(params['NL'])

print('running ',cfgs[0],'-->',cfgs[-1])
print('srcs:',src_set)
#time.sleep(1)

smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
val_p = val.replace('.','p')

''' for now - just doing the light quark '''
params['MQ'] = params['MV_L']

params['ff_path'] = val_p+'/formfac'

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

n_curr = len(params['curr_4d'])
n_flav = len(params['flavs'])
n_spin = len(params['spins'])
n_par  = len(params['particles'])
coherent_ff_size_4d = n_curr * n_flav * n_spin * n_par *int(nt)*int(nl)**3 * 2*8

meta_entries = dict()
tape_entries = dict()

try:
    print('trying to querry Lattedb for ff_4D files')
    f_type = 'formfac_4D_tslice_src_avg'
    meta_entries[f_type] = lattedb_ff.get_or_create_ff4D_tsliced_savg(params, cfgs, ens, stream, src_set)
    tape_dir_4D = c51.tape+'/'+ens_s+'/'+f_type+'/%(CFG)s'
    tape_entries[f_type] = lattedb_ff.get_or_create_tape_entries(
        meta_entries = meta_entries[f_type], 
        tape_entries = TapeTSlicedSAveragedFormFactor4DFile,
        path         = tape_dir_4D,
        machine      = c51.machine,
        dbl_check    = args.dbl_check,
    )

    for dt in params['t_seps']:
        print('trying to querry Lattedb for ff files for dt = %d' %dt)
        corr = 'ff_tsep_'+str(dt)
        meta_entries[corr] = lattedb_ff.get_or_create_meta_entries(corr, cfgs, ens, stream, src_set, srcs)
        tape_entries[corr] = lattedb_ff.get_or_create_tape_entries(
            meta_entries = meta_entries[corr],
            tape_entries = TapeCorrelatorH5Dset,
            path         = c51.tape+'/'+ens_s+'/data',
            machine      = c51.machine,
            name         = ens_s+'_%(CFG)s_srcs'+src_set+'.h5'
            )
    have_lattedb = True
except:
    print('not able to connect to lattedb - will directly access tape')
    have_lattedb = False


''' logic loop
for cfg in cfgs:
    for dt in t_seps:
        for src in srcs:
            does ff_src exist in tape?
            does ff_4D_src_avg exist in tape?
            if not:
                do files exist on disk?
                if not:
                    do seqprops and props exist?
                    if so - make task
'''

for c in cfgs:
    print('now checking tasks for cfg = %d' %c)
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
        print("Checking coherent formfactor for cfg: ",c)

        have_all_seqprops=True
        for dt_int in t_seps:
            ff_dict    = {'ensemble':ens, 'stream':stream, 'configuration':c, 'source_set':src_set}
            ff_4D_dict = {'ensemble':ens, 'stream':stream, 'configuration':c, 'source_set':src_set, 't_separation':dt_int}
            dt = str(dt_int)
            params['T_SEP'] = dt
            have_disk_all_src = True
            have_tape_all_src = True
            for s0 in srcs[c]:
                params['SRC']  = s0
                ff_name        = (c51.names['formfac'] % params) +'.h5'
                ff_file        = params['formfac'] +'/'+ff_name
                ff_4D_name     = (c51.names['formfac_4D'] % params) +'.h5'
                ff_4D_file     = params['formfac_4D'] +'/'+ ff_4D_name
                ff_4D_tslice   = params['formfac_4D_tslice'] +'/'+ (c51.names['formfac_4D_tslice'] % params) +'.h5'
                ff_4D_avg_name = (c51.names['formfac_4D_tslice_src_avg'] % params).replace(s0,'src_avg') +'.h5'
                ff_4D_avg_file = params['formfac_4D_tslice_src_avg'] +'/'+ ff_4D_avg_name
                #if False:
                if have_lattedb:
                    ff_dict.update({'source':s0, 'correlator':'ff_tsep_'+dt})
                    ff_4D_dict.update({'name':ff_4D_avg_name})
                    db_ff = meta_entries['ff_tsep_'+dt].filter(**ff_dict).first()
                    db_4D = meta_entries['formfac_4D_tslice_src_avg'].filter(**ff_4D_dict).first()
                    if hasattr(db_4D, 'tape') and hasattr(db_ff,'tape'):
                        have_tape = db_ff.tape.exists and db_4D.tape.exists
                    else:
                        have_tape = False
                else:
                    d_sets = []
                    for particle in params['particles']:
                        params['PARTICLE'] = particle
                        if '_np' in particle:
                            params['T_SEP'] = '-'+dt
                        else:
                            params['T_SEP'] = dt
                        for fs in flav_spin:
                            params['FLAV_SPIN'] = fs
                            for curr in params['curr_4d']:
                                params['CURRENT'] = curr
                                d_sets.append(collect_utils.ff_dset(params) % params)
                    ff_collect_name = ens_s+'_'+no+'_srcs'+src_set+'.h5'
                    have_ff = lattedb_ff.corr_compare_tape_disk(ff_collect_name, tape_dir, data_dir, tmp_data_dir, d_sets, 
                                                                args.atol, args.rtol, tape_push=tape_push)
                    db_4D_tape = lattedb_ff.check_tape(c51.tape+'/'+ens_s+'/formfac_4D_tslice_src_avg/'+no, ff_4D_avg_name)
                    have_tape = db_4D_tape['exists'] and have_ff
                # restore T_SEP for other file names
                params['T_SEP'] = dt
                #sys.exit()

                if not have_tape:
                    have_tape_all_src = False
                if not have_tape:
                    # do files exists on disk?
                    have_4D_processed = os.path.exists(ff_4D_tslice) or os.path.exists(ff_4D_avg_file)
                    # make sure files are correct size
                    utils.check_file(ff_4D_file,coherent_ff_size_4d,params['file_time_delete'],params['corrupt'],debug=args.debug)
                    utils.check_file(ff_file,   params['ff_size'],  params['file_time_delete'],params['corrupt'],debug=args.debug)
                    # if we have corr and not 4D or vice versa - problem
                    if os.path.exists(ff_file) and not os.path.exists(ff_4D_file):
                        utils.check_time_mv_file(ff_file, params['file_time_delete'], params['corrupt'])
                    if os.path.exists(ff_4D_file) and not os.path.exists(ff_file):
                        utils.check_time_mv_file(ff_4D_file, params['file_time_delete'], params['corrupt'])
                    # now check if files are still on disk
                    have_disk = os.path.exists(ff_file) or os.path.exists(ff_4D_file)
                    if not have_disk and not have_4D_processed:
                        print(ff_file)
                        print(ff_4D_file)
                        have_disk_all_src = False                
                        # check if seqprops and props exist
                        all_seqprops=True
                        seqprop_file_list = []
                        for fs in flav_spin:
                            flav,snk_spin,src_spin=fs.split('_')
                            params['FLAV']=flav
                            params['SOURCE_SPIN']=snk_spin
                            params['SINK_SPIN']=src_spin
                            spin = snk_spin+'_'+src_spin
                            params['FLAV_SPIN']=fs
                            for particle in params['particles']:
                                params['PARTICLE'] = particle
                                if '_np' in particle:
                                    params['T_SEP'] = '-'+dt
                                else:
                                    params['T_SEP'] = dt
                                seqprop_name = c51.names['seqprop'] %params
                                seqprop_file = params['seqprop']+'/'+seqprop_name+'.'+params['SP_EXTENSION']
                                try:
                                    seqprop_size = params['seqprop_size']
                                except:
                                    print('SEQPROP_SIZE not defined in area51 file: using crude default')
                                    seqprop_size = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
                                utils.check_file(seqprop_file,seqprop_size,params['file_time_delete'],params['corrupt'],debug=args.debug)
                                if not os.path.exists(seqprop_file):
                                    print('    missing:',seqprop_file)
                                    all_seqprops=False
                                    have_all_seqprops=False
                                else:
                                    seqprop_file_list.append(seqprop_file)
                        if all_seqprops:
                            # restore T_SEP for file name
                            params['T_SEP'] = dt
                            params['THREE_PT_FILE']    = ff_file
                            params['THREE_PT_FILE_4D'] = ff_4D_file
                            if os.path.exists(ff_file):
                                sys.exit('error - should not exist',ff_file)
                            if os.path.exists(ff_4D_file):
                                sys.exit('error - should not exist', ff_4D_file)
                            metaq  = ff_name+'.sh'
                            t_e,t_w = scheduler.check_task(metaq,args.mtype,params,folder=q,overwrite=args.o)
                            try:
                                if params['metaq_split']:
                                    cpu_n = args.mtype+'_'+str(params['cpu_nodes'])
                                    t_e2,t_w2 = scheduler.check_task(metaq,cpu_n,params,folder=q,overwrite=args.o)
                                    t_w = t_w or t_w2
                                    t_e = t_e or t_e2
                            except:
                                pass
                            if not t_e or (args.o and not t_w):
                                prop_name = c51.names['prop'] % params
                                prop_file = params['prop'] + '/' + prop_name+'.'+params['SP_EXTENSION']
                                prop_exists = os.path.exists(prop_file)
                                prop_h5 = False
                                if ens in ['a12m130', 'a15m135XL'] and not prop_exists:
                                    prop_file = params['prop'] + '/' + prop_name+'.h5'
                                    if os.path.exists(prop_file):
                                        prop_h5 = True
                                        prop_exists = True
                                if prop_exists:
                                    xmlini = ff_file.replace('/formfac/','/xml/').replace('.h5','.ini.xml')
                                    xml_input.make_coherent_ff_xml(xmlini, params, prop_name, prop_file, dt, flav_spin)
                                    ''' Make METAQ task '''
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
                                    scheduler.make_task(metaq, mtype, params, folder=q)
                                else:
                                    print('MISSING prop',prop_file)
                                    os.system(c51.python+' %s/METAQ_prop.py %s %s %s -v' \
                                        %(params['SCRIPT_DIR'], c, src_args, params['PRIORITY']))
                            else:
                                print('  task exists or running:',metaq)
                        else:# touch existing seqprops to keep them on disk
                            for seqprop in seqprop_file_list:
                                os.system('touch %s' %seqprop)
                    else:
                        if not (os.path.exists(ff_file) and os.path.exists(ff_4D_file)):
                            print('    exists',os.path.exists(ff_file), ff_file)
                            print('    exists',os.path.exists(ff_4D_file), ff_4D_file)
                else:
                    if args.verbose:
                        print("formfac: cfg = %4d  tsep = %2s  src = %13s  on_tape = %s" %(c,dt,s0,have_tape))
            if have_disk_all_src and not have_tape_all_src and args.collect:
                print('collect data')
                params['T_SEP'] = dt
                lattedb_ff.collect_spec_ff_4D_tslice_src_avg('formfac', params, meta_entries['formfac_4D_tslice_src_avg'])

        if not have_all_seqprops:
            print('    missing FLAV or SPIN seqprops')
            if args.t_sep:
                tsep = "".join("%d " %t for t in args.t_sep)
                tsep = "-t "+tsep
            else:
                tsep = ''
            os.system(c51.python+' %s/METAQ_coherent_seqprop.py %s %s %s %s -v' \
                %(params['SCRIPT_DIR'], c, src_args, params['PRIORITY'],tsep))

    else:
        print('  flowed cfg missing',cfg_file)
