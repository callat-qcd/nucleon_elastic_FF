from __future__ import print_function
import os, sys, argparse, shutil, datetime, time
import numpy as np
np.set_printoptions(linewidth=180)
import tables as h5
import warnings
warnings.simplefilter('ignore', h5.NaturalNameWarning)
from glob import glob
'''
    NUCLEON_ELASTIC_FF IMPORTS
'''
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
import importlib
import c51_mdwf_hisq as c51
import utils
import sources

message = {
    'res_phi':'MRES and PHI_QQ',
    'spec'   :'PIONS and PROTONS',
    'formfac':'PROTON FORMFAC',
}

def get_data(params,d_type):
    # switch for data types to define h5 path
    if d_type == 'res_phi':
        prop_name = c51.names['prop'] % params




def put_data(params,d_type,data=None,overwrite=False,db_info=False):
    # switch for data types to define h5 path
    if d_type == 'res_phi':    
        # data file
        data_file = params['data_dir']+'/'+params['ens_s']+'_'+params['CFG']+'_srcs'+src_ext+'.h5'
        # define h5 directories
        mp_dir  = '/'+params['val_p']+'/dwf_jmu/mq'+params['MQ'].replace('.','p')+'/midpoint_pseudo'
        pp_dir  = '/'+params['val_p']+'/dwf_jmu/mq'+params['MQ'].replace('.','p')+'/pseudo_pseudo'
        phi_dir = '/'+params['val_p']+'/phi_qq/mq'+params['MQ'].replace('.','p')
        # if db_info, just print information
        if db_info:
            for corr in [mp_dir,pp_dir]:
                print('data key  : mres')
                print('data file : %s' %data_file)
                print('h5 path   : %s' %(corr+'/'+params['SRC']))
        # else, actually put the data in the h5 file
        else:
            print('putting data not supported yet')

if __name__ == "__main__":
    fmt = '%Y-%m-%d %H:%M:%S'

    ens,stream = c51.ens_base()
    ens_s = ens+'_'+stream

    area51 = importlib.import_module(ens)
    params = area51.params
    params['ens_s'] = ens_s

    params['machine'] = c51.machine
    params['ENS_LONG'] = c51.ens_long[ens]
    params['ENS_S']    = ens_s
    params['STREAM']   = stream

    print('ENSEMBLE:',ens_s)

    '''
        COMMAND LINE ARG PARSER
    '''
    parser = argparse.ArgumentParser(description='get data and put in h5 files')
    parser.add_argument('data_type',type=str,help='[res_phi spec formfac]')
    parser.add_argument('--cfgs',nargs='+',type=int,help='cfgs: ci [cf dc]')
    parser.add_argument('-s','--src',type=str,help='src [xXyYzZtT] None=All')
    parser.add_argument('-o',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
    parser.add_argument('--move',default=False,action='store_const',const=True,help='move bad files? [%(default)s]')
    parser.add_argument('-v',default=True,action='store_const',const=False,help='verbose? [%(default)s]')
    parser.add_argument('-d','--db_info',default=False,action='store_const',const=True,\
        help='print DB info and not collect? [%(default)s]')
    args = parser.parse_args()
    print('Arguments passed')
    print(args)
    print('')

    dtype = np.float64
    # make sure the h5 data directory exists
    data_dir = c51.data_dir % params
    utils.ensure_dirExists(data_dir)
    params['data_dir'] = data_dir

    # if we read si, sf, ds from area51 file, user is over-riding default
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

    # Get cfg and src list, create source extension for name
    cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,args.src,params)
    src_ext = "%d-%d" %(params['si'],params['sf'])
    params['src_ext'] = src_ext

    # get the valence information
    smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
    val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
    val_p = val.replace('.','p')
    params['val']   = val
    params['val_p'] = val_p

    # for now, we are ONLY doing the light quark
    mv_l = params['MV_L']
    params['MQ'] = params['MV_L']

    print('MINING %s' %(message[args.data_type]))
    print('ens_stream = %s' %(ens_s))
    if len(cfgs_run) == 1:
        dc = 1
    else:
        dc = cfgs_run[1]-cfgs_run[0]
    print('cfgs_i : cfg_f : dc = %d : %d : %d' %(cfgs_run[0],cfgs_run[-1],dc))
    print('si - sf x ds        = %d - %d x %d\n' %(params['si'],params['sf'],params['ds']))
    time.sleep(2)

    # if db_info, we are just printing the h5 file path, h5 dir info and key
    if args.db_info:
        print('printing info for the database')
        for cfg in cfgs_run:
            no = str(cfg)
            params['CFG'] = no
            params = c51.ensemble(params)
            for src in srcs[cfg]:
                params['SRC'] = src
                put_data(params=params,d_type=args.data_type,overwrite=args.o,db_info=args.db_info)


    # else, collect data and put it in the h5 files
    else:
        print('collecting data')
        for cfg in cfgs_run:
            no = str(cfg)
            sys.stdout.write('  cfg=%4d\r' %(cfg))
            sys.stdout.flush()
