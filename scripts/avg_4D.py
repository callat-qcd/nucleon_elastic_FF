from __future__ import print_function
import os, sys, argparse
import numpy as np
np.set_printoptions(linewidth=180)
import tables as h5
import warnings
warnings.simplefilter('ignore', h5.NaturalNameWarning)
from glob import glob
# nucleon_elastic_ff utils
import nucleon_elastic_ff.data.scripts.average as average
import nucleon_elastic_ff.data.scripts.tslice as tslice

'''
    NUCLEON_ELASTIC_FF IMPORTS
'''
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
import importlib
import c51_mdwf_hisq as c51
import utils
import sources
ens,stream = c51.ens_base()
ens_s = ens+'_'+stream

area51 = importlib.import_module(ens)
params = area51.params
params['machine'] = c51.machine
params['ENS_LONG'] = c51.ens_long[ens]
params['ENS_S']    = ens_s
params['STREAM']   = stream

print('ENSEMBLE:',ens_s)

'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='average phi_qq')
parser.add_argument('data',type=str,help='what data type to average [spec formfac]?')
parser.add_argument('--cfgs',nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('-o',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('-v',default=True,action='store_const',const=False,help='verbose? [%(default)s]')
parser.add_argument('--src_set',nargs=3,type=int,help='specify si sf ds')
parser.add_argument('-t','--t_sep',nargs='+',type=int,help='values of t_sep [default = all]')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')
if args.data not in ['spec','formfac']:
    print('unrecognized data type')
    print(args.data,' not in [ spec formfac spec_full ]')
    sys.exit()

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
src_ext = "%d-%d" %(params['si'],params['sf'])
params['SRC_SET'] = src_ext

cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,'',params)

# modify logging info and location
import logging
from nucleon_elastic_ff.utilities import set_up_logger
LOGGER = set_up_logger("nucleon_elastic_ff") # get the logger for the module
fh = [h for h in LOGGER.handlers if isinstance(h, logging.FileHandler)][0] # get the file logger
LOGGER.removeHandler(fh) # remove the file logger
new_fh = logging.FileHandler(c51.scratch+'/production/'+ens_s+'/nucleon_elastic_ff_'+args.data+'_avg.log')
new_fh.setLevel(logging.INFO)
new_fh.setFormatter(fh.formatter)
LOGGER.addHandler(new_fh)


params['MQ'] = params['MV_L']
if args.t_sep == None:
    t_seps  = params['t_seps']
else:
    t_seps = args.t_sep

def check_ff_tslice(params,c51,srcs):
    all_files = True
    all_sizes = []
    for s0 in srcs:
        params['SRC'] = s0
        file_4D = params['formfac_4D_tslice'] +'/'+ (c51.names['formfac_4D_tslice'] % params)+'.h5'
        if not os.path.exists(file_4D):
            all_files = False
        else:
            all_sizes.append(os.path.getsize(file_4D))
    if not all(size == all_sizes[0] for size in all_sizes):
        print('BAD FORMFAC_4D_TSLICE FILE SIZE(s)')
        all_files = False
    return all_files

def check_ff(params,c51,srcs):
    all_files = True
    all_sizes = []
    for s0 in srcs:
        params['SRC'] = s0
        formfac_4D = params['formfac_4D'] +'/'+ (c51.names['formfac_4D'] % params)+'.h5'
        if not os.path.exists(formfac_4D):
            all_files = False
        else:
            all_sizes.append(os.path.getsize(formfac_4D))
    if not all(size == all_sizes[0] for size in all_sizes):
        print('BAD FORMFAC_4D FILE SIZE(s)')
        all_files = False
    return all_files

def tslice_ff(params,c51,srcs):
    if not os.path.exists(params['formfac_4D_tslice']): os.makedirs(params['formfac_4D_tslice'])
    for s0 in srcs:
        params['SRC'] = s0
        formfac_4D = params['formfac_4D'] +'/'+ (c51.names['formfac_4D'] % params)+'.h5'
        formfac_4D_tslice = params['formfac_4D_tslice'] +'/'+ (c51.names['formfac_4D_tslice'] % params)+'.h5'
        tslice.slice_file(
            formfac_4D,
            formfac_4D_tslice,
            overwrite=args.o,
            #tslice_fact=None - we don't want to tslice for ff files
            dset_patterns=("local_current",),
            boundary_sign_flip=False
            )

def check_spec_4D_tslice(params,c51,srcs):
    all_files = True
    all_sizes = []
    for s0 in srcs:
        params['SRC'] = s0
        file_4D = params['spec_4D_tslice'] +'/'+ (c51.names['spec_4D_tslice'] % params)+'.h5'
        if not os.path.exists(file_4D):
            all_files = False
        else:
            all_sizes.append(os.path.getsize(file_4D))
    if not all(size == all_sizes[0] for size in all_sizes):
        print('BAD SPEC_4D_TSLICE FILE SIZE(s)')
        all_files = False
    return all_files

def check_spec_4D(params,c51,srcs):
    all_files = True
    all_sizes = []
    for s0 in srcs:
        params['SRC'] = s0
        spec_file = params['spec_4D'] +'/'+ (c51.names['spec_4D'] % params)+'.h5'
        if not os.path.exists(spec_file):
            all_files = False
        else:
            all_sizes.append(os.path.getsize(spec_file))
    if not all(size == all_sizes[0] for size in all_sizes):
        print('BAD SPEC_4D FILE SIZE(s)')
        all_files = False
    return all_files

def tslice_spec(params,c51,srcs):
    if not os.path.exists(params['spec_4D_tslice']): os.makedirs(params['spec_4D_tslice'])
    for s0 in srcs:
        params['SRC'] = s0
        spec_file = params['spec_4D'] +'/'+ (c51.names['spec_4D'] % params)+'.h5'
        spec_file_tslice = params['spec_4D_tslice'] +'/'+ (c51.names['spec_4D_tslice'] % params)+'.h5'
        tslice.slice_file(
            spec_file,
            spec_file_tslice,
            overwrite=args.o,
            tslice_fact=params['spec_4D_tslice_fact'],
            dset_patterns=["4D_correlator/x[0-9]+_y[0-9]+_z[0-9]+_t[0-9]+"],
            boundary_sign_flip=True
            )        

missing_srcs = []

curr_dir = os.getcwd()
os.chdir(c51.base_dir %params)
for c in cfgs_run:
    no = str(c)
    params['CFG'] = no
    params = c51.ensemble(params)
    if args.data == 'spec':
        # does avg file exist already?
        params['SRC']    = 'src_avg'+src_ext
        spec_name        = c51.names['spec'] % params
        spec_file        = params['spec'] +'/'+ spec_name+'.h5'
        spec_file_4D_avg = params['spec_4D_tslice_avg'] +'/'+ (c51.names['spec_4D_tslice_avg'] % params)+'.h5'
        do_avg = True
        if os.path.exists(spec_file_4D_avg) and not args.o:
            do_avg = False
        if do_avg:
            run_avg = check_spec_4D_tslice(params,c51,srcs[c])
            if not run_avg:
                have_spec = check_spec_4D(params,c51,srcs[c])
                if have_spec:
                    print('  have all spec_4D files cfg=%d, trying to tslice' %(c))
                    tslice_spec(params,c51,srcs[c])
                    #os.system(c51.python+' %s/tslice_4D.py spec --cfgs %d' %(c51.script_dir, c))
                    run_avg = check_spec_4D_tslice(params,c51,srcs[c])
            if run_avg:
                d_dir = params['spec_4D_tslice']
                average.spec_average(root=d_dir, overwrite=args.o, expected_sources=srcs[c], file_name_addition=src_ext)
            else:
                print('missing srcs on cfg = %d' %c)
                if c not in missing_srcs: missing_srcs.append(c)
            # for spec_4D - we have to ensure all srcs exist
            '''
            avg_files = True
            for s0 in srcs[c]:
                params['SRC'] = s0
                spec_name    = c51.names['spec'] % params
                spec_file    = params['spec'] +'/'+ spec_name+'.h5'
                spec_file_4D = spec_file.replace('spec_','spec_4D_tslice_').replace('/spec/','/spec_4D_tslice/')
                if not os.path.exists(spec_file_4D):
                    avg_files = False
                    if c not in missing_srcs: missing_srcs.append(c)
            if avg_files:
                d_dir = params['prod']+'/'+args.data+'_4D_tslice/'+no
                average.spec_average(root=d_dir, overwrite=args.o, expected_sources=srcs[c], file_name_addition=src_ext)
            else:
                print('missing srcs on cfg = %d' %c)
            '''
        else:
            print('overwrite =',args.o,' and exists:',args.o,spec_file_4D_avg)
    elif args.data == 'formfac':
        snk_mom = params['snk_mom'][0]
        m0,m1,m2 = snk_mom.split()
        params['M0']=m0
        params['M1']=m1
        params['M2']=m2
        params['MOM'] = 'px%spy%spz%s' %(m0,m1,m2)
        params['N_SEQ'] = len(srcs[c])
        # loop over tseps
        for t in t_seps:
            # does avg file exist?
            print("printing t:", t)
            params['T_SEP'] = str(t)
            params['SRC'] = 'src_avg'
            formfac_name = c51.names['formfac'] % params
            formfac_file = params['formfac'] +'/'+ formfac_name+'.h5'
            formfac_file_4D_avg = params['formfac_4D_tslice_src_avg'] +'/'+ (c51.names['formfac_4D_tslice_src_avg'] % params)+'.h5'
            do_avg = True
            print(formfac_file_4D_avg,os.path.exists(formfac_file_4D_avg))
            sys.exit()
            if os.path.exists(formfac_file_4D_avg) and not args.o:
                do_avg = False
            if do_avg:
                run_avg = check_ff_tslice(params,c51,srcs[c])
                if not run_avg:
                    have_ff = check_ff(params,c51,srcs[c])
                    if have_ff:
                        print('  have all formfac_4D files - trying to tslice')
                        tslice_ff(params,c51,srcs[c])
                        #os.system(c51.python+' %s/tslice_4D.py formfac --cfgs %s' %(c51.script_dir, no))
                        run_avg = check_ff_tslice(params,c51,srcs[c])
                if run_avg:
                    #d_dir = params['prod']+'/'+args.data+'_4D_tslice/'+no
                    d_dir = params['formfac_4D_tslice']
                    #average.source_average(root=d_dir, overwrite=args.o, expected_sources=srcs[c], file_name_addition=src_ext, additional_file_patterns='dt'+str(t)+'_')
                    average.source_average(root=d_dir, overwrite=args.o, expected_sources=srcs[c], additional_file_patterns='dt'+str(t)+'_')
                else:
                    print('missing srcs for cfg %d t_sep %d' %(c,t))
                    if c not in missing_srcs: missing_srcs.append(c)
                '''
                avg_files = True
                for s0 in srcs[c]:
                    params['SRC'] = s0
                    formfac_name = c51.names['formfac'] % params
                    formfac_file = params['formfac'] +'/'+ formfac_name+'.h5'
                    formfac_file_4D = params['formfac_4D_tslice'] +'/'+ (c51.names['formfac_4D_tslice'] % params)+'.h5'
                    if not os.path.exists(formfac_file_4D):
                        avg_files = False
                        if c not in missing_srcs: missing_srcs.append(c)
                if avg_files:
                    d_dir = params['prod']+'/'+args.data+'_4D_tslice/'+no
                    average.source_average(root=d_dir, overwrite=args.o, expected_sources=srcs[c], file_name_addition=src_ext, additional_file_patterns='dt'+str(t)+'_')
                else:
                    # should try tslice and then check again and update two lists
                    print('missing srcs on cfg = %d' %c)
                    os.system(c51.python+' %s/tslice_4D.py formfac --cfgs %s' %(c51.script_dir, no))
                '''
            else:
                print('overwrite =',args.o,' and exists:',args.o,formfac_file_4D_avg.split('/')[-1])
    if args.data == 'spec_full':
        # does avg file exist already?
        params['SRC'] = 'src_avg'+src_ext
        spec_name    = c51.names['spec'] % params
        spec_file    = params['spec'] +'/'+ spec_name+'.h5'
        spec_file_4D_avg = spec_file.replace('spec_','spec_4D_avg_').replace('/spec/','/spec_4D_avg/')
        do_avg = True
        if os.path.exists(spec_file_4D_avg) and not args.o:
            do_avg = False
        if do_avg:
            # for spec_4D - we have to ensure all srcs exist
            avg_files = True
            for s0 in srcs[c]:
                params['SRC'] = s0
                spec_name    = c51.names['spec'] % params
                spec_file    = params['spec'] +'/'+ spec_name+'.h5'
                spec_file_4D = spec_file.replace('spec_','spec_4D_').replace('/spec/','/spec_4D/')
                if not os.path.exists(spec_file_4D):
                    avg_files = False
                    if c not in missing_srcs: missing_srcs.append(c)
            if avg_files:
                d_dir = params['prod']+'/'+args.data+'_4D/'+no
                average.spec_average(root=d_dir, overwrite=args.o, expected_sources=srcs[c], file_name_addition=src_ext)
            else:
                print('missing srcs on cfg = %d' %c)
        else:
            print('overwrite =',args.o,' and exists:',args.o,spec_file_4D_avg)

os.chdir(curr_dir)

if len(missing_srcs) > 0:
    f = open('missing_srcs_'+args.data+'.lst','w')
    for c in missing_srcs:
        f.write('%d\n' %c)
    f.close()
