from __future__ import print_function
import os, sys, argparse, shutil, datetime, time
import numpy as np
np.set_printoptions(linewidth=180)
import tables as h5
from glob import glob
fmt = '%Y-%m-%d %H:%M:%S'

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
#params['machine'] = c51.machine
params['ENS_LONG'] = c51.ens_long[ens]
params['ENS_S']    = ens_s
params['STREAM']   = stream

print('ENSEMBLE:',ens_s)

'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='get hisq and mixed data and put in h5 file')


parser.add_argument('cfgs',       nargs='+',type=int,help='cfgs: ci [cf dc]')
parser.add_argument('-s','--src', type=str,help='src [xXyYzZtT] None=All')
parser.add_argument('-o',         default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('--force',    default=False,action='store_const',const=True,\
                    help=         'run without prompting user? [%(default)s]')
parser.add_argument('--move',     default=False,action='store_true',help='move bad files? [%(default)s]')
parser.add_argument('-v',         default=True,action='store_false',help='verbose? [%(default)s]')
parser.add_argument('--fout',     type=str,help='directory to output, need to end with /, leave empty for production')
 
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

def read_milc(f,i,nt):
    #print('reading correlator', f[i], nt)
    data = np.zeros([int(nt)],dtype=np.complex64)
    for t in range(data.shape[0]):
        data[t] = float(f[i+5+t].split()[1]) +1.j*float(f[i+5+t].split()[2])
    return data

######################################################################
######################################################################

dtype = np.complex64
data_dir = c51.data_dir % params
utils.ensure_dirExists(data_dir)
out_path = data_dir

params = sources.src_start_stop(params,ens,stream)
args.src=None
cfgs_run,srcs = utils.parse_cfg_src_argument(args.cfgs,args.src,params)

bd_name = 'bad_mes_'+ens_s+'.lst'
tmp_name = ens_s
cwd = os.getcwd()

# sea quark masses
ms_l = params['MS_L']
ms_s = params['MS_S']
# TASTE_5,I SPECTRUM
if ms_l == ms_s:
    mesons = {
        'PION_5':'phi_jj_5','PION_I':'phi_jj_I',
    }
else:
    mesons = {
        'PION_5':'phi_jj_5','PION_I':'phi_jj_I',
        'KAON_5':'phi_jr_5','KAON_I':'phi_jr_I',
        'SS_5':'phi_rr_5','SS_I':'phi_rr_I',
    }

print('looking for data in: '+ c51.ens_dir % params+'/hisq_spec'+'\n')
print('Saving output file to:'+out_path)

print('  ml = %s, ms = %s' %(ms_l,ms_s))

if not args.force:
    proceed = input('would you like to proceed?\t')
    if proceed not in ['y','yes']:
        os.system('python '+sys.argv[0]+' -h')
        sys.exit()

bad_lst = open(cwd+'/'+bd_name,'a')
for cfg in cfgs_run:
    no = str(cfg)
    params['CFG'] = str(no)
    ''' set up ensemble and make sure all dirs exist '''
    params = c51.ensemble(params)

    for t in params['t_hisq']:
        t0 = str(t)
        params['SRC']='x0y0z0t'+t0

        ftmp = params['hisq_spec']+'/'+c51.names['hisq_corr']%params
        if os.path.exists(ftmp):
            f5 = h5.open_file(out_path+'/hisq_spec_'+ ens_s+'_'+no+'.h5','a')
            mls = 'ml'+ms_l.replace('.','p')
            mss = 'ms'+ms_s.replace('.','p')
            cdir = '/'
            group=(params['ENS_LONG']+'/hisq_spec/'+mls+'_'+mss).split('/')
            for g_i in range(len(group)):
                if group[g_i] not in f5.get_node(cdir):
                    f5.create_group(cdir,group[g_i])
                if g_i == 0:
                    cdir += group[g_i]
                else:
                    cdir += '/'+group[g_i]

            corr_input = open(ftmp).readlines()
            for i,l in enumerate(corr_input):
                if 'correlator:' in l:
                    corr_name = l.split()[1]
                    state = mesons[corr_name]
                    print (no, params['SRC'], state, corr_name)
                    data = read_milc(corr_input,i,params['NT'])

                    if state not in f5.get_node(cdir):
                        f5.create_group(cdir,state)
                    sdir = cdir+'/'+state
                    if not np.any(np.isnan(data)):
                        if sdir+'/'+params['SRC'] not in f5.get_node(sdir):
                            f5.create_array(sdir,params['SRC'],data)
                        elif sdir+'/'+params['SRC'] in f5 and args.o:
                                tmp = f5.get_node(sdir+'/'+params['SRC'])
                                tmp[:] = data
                        elif sdir+'/'+params['SRC'] in f5 and not args.o:
                            pass
                            print('  skipping %s: overwrite = False' %state)
                    else:
                        print('  NAN')
                        bad_lst.write('%s %s %s NAN' %(no,state,params['SRC']))
                        bad_lst.flush()
            f5.close()
        else:
            print('missing ',ftmp)
bad_lst.close()
print ("DONE")

