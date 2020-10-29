import os, sys, argparse
import numpy as np
import tables as h5
import subprocess
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
ens,stream = os.getcwd().split('/')[-1].split('_')
ens_s = ens+'_'+stream
print(ens,stream)

area51 = importlib.import_module(ens)
params = area51.params
params['machine'] = c51.machine
params['ENS_LONG'] = c51.ens_long[ens]
params['ENS_S']    = ens_s
params['STREAM']   = stream

print('ENSEMBLE:',ens_s)

parser = argparse.ArgumentParser(description='collect charm PBP results and put in h5 files')
parser.add_argument('cfgs',            nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('-o','--overwrite',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('-d','--debug',    default=False,action='store_const',const=True,help='debug? [%(default)s]')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

dtype = np.complex64
data_dir = c51.data_dir % params
utils.ensure_dirExists(data_dir)

cfgs = utils.parse_cfg_argument(args.cfgs, params)
print('collecting from cfgs %d - %d' %(cfgs[0],cfgs[-1]))

for cfg in cfgs:
    no = str(cfg)
    params['CFG'] = no
    params = c51.ensemble(params)
    pbp_dir = params['prod']+'/pbp/'+no
    sys.stdout.write('    %4s\r' %(no))
    sys.stdout.flush()
    d_file = data_dir +'/charm_PBP_'+ens_s+'_'+no+'.h5'
    for mc in params['MC_reweight']:
        mc_s = str(mc).replace('.','p')
        # did we already collect the data?
        if os.path.exists(d_file):
            with h5.open_file(d_file,'r') as f5:
                have_data = 'mc_'+mc_s in f5.get_node('/')
                if have_data and args.overwrite:
                    have_data = False
        else:
            have_data = False
        if not have_data:
            # is the data file healthy?
            pbp_file = pbp_dir + '/charm_pbp_'+ens_s+'_cfg_'+no+'_'+str(mc)+'.stdout'
            if os.path.exists(pbp_file):
                std_content = open(pbp_file).read()
                get_data = 'RUNNING COMPLETED' in std_content
                if not get_data:
                    now = time.time()
                    file_time = os.stat(pbp_file).st_mtime
                    if (now-file_time)/60 > 10:# if older than 10 minutes, delete
                        print('  OLD, incomplete, deleting',pbp_file)
                        shutil.move(pbp_file, params['corrupt']+'/'+pbp_file.split('/')[-1])
            else:
                get_data = False
            if get_data:
                pbp_grep = subprocess.check_output('grep "PBP: mass" %s' %pbp_file, shell=True).decode('ascii').split('\n')
                pbp = []
                for n in range(params['CC_Nnoise']):
                    tmp = pbp_grep[n].split()
                    if int(tmp[-2]) != params['CC_Nnoise']:
                        sys.exit('%s has Nnoise = %d but area51 file has CC_Nnoise = %d' %(pbp_file.split('/')[-1], int(tmp[-2]), params['CC_Nnoise']))
                    m = float(tmp[2])
                    if m != mc:
                        sys.exit('charm mass does not match: name %f, in file %f' %(mc, m))
                    pbp.append([ float(tmp[3]) +1j*float(tmp[5]), float(tmp[4]) +1j*float(tmp[6])])
                pbp = np.array(pbp)
                with h5.open_file(d_file, 'a') as f5:
                    if 'mc_'+mc_s in f5.get_node('/'):
                        if args.overwrite:
                            f5.get_node('/mc_'+mc_s)[:] = pbp
                        else:
                            sys.exit('data exists and overwrite = %s' %args.overwrite)
                    else:
                        f5.create_array('/','mc_'+mc_s,pbp)
