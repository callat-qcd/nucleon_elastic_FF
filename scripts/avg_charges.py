from __future__ import print_function
import os,sys
import tables as h5
import numpy as np
from glob import glob

verbose=True

sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
import importlib
import management
import sources
try:
    ens_s = os.getcwd().split('/')[-2]
except:
    ens_s,junk = os.getcwd().split('/')[-2]
ens,stream = ens_s.split('_')

sys.path.append('area51_files')
area51 = importlib.import_module(ens)
params = area51.params
ens_long=params['ENS_LONG']
params['ENS_S'] = ens_s


def time_reverse(corr,phase=1,time_axis=1):
    ''' assumes time index is second of array '''
    ''' assumes phase = +- 1 '''
    if len(corr.shape) > 1:
        cr = phase * np.roll(corr[:,::-1],1,axis=time_axis)
        cr[:,0] = phase * cr[:,0]
    else:
        cr = phase * np.roll(corr[::-1],1)
        cr[0] = phase * cr[0]
    return cr

nt = int(params['NT'])
nl = int(params['NL'])

h5_out = h5.open_file(ens_s+'_charges.h5','a')

base_dir = management.base_dir % params
state = dict()
state['pp'] = 'proton'
state['np'] = 'proton_np'
spins = ['up_up','dn_dn']

for charge in params['curr_p']:
    params['CURR'] = charge
    if charge not in h5_out.get_node('/'):
        h5_out.create_group('/',charge)
    for dt in params['t_seps']:
        tsep = str(dt)
        h5_path = '/'+charge+'/tsep_'+tsep
        if tsep not in h5_out.get_node('/'+charge):
            print(charge,tsep)
            params['T_SEP'] = tsep
            h5_out.create_group('/'+charge,'tsep_'+tsep)
            'charge_spin_parity'
            data = dict()
            data['up_up_pp'] = []
            data['up_up_np'] = []
            data['dn_dn_pp'] = []
            data['dn_dn_np'] = []
            for cfg in range(params['cfg_i'],params['cfg_f']+1,params['cfg_d']):
                no = str(cfg)
                params['CFG'] = no
                data_tmp = dict()
                data_tmp['up_up_pp'] = []
                data_tmp['up_up_np'] = []
                data_tmp['dn_dn_pp'] = []
                data_tmp['dn_dn_np'] = []
                srcs = []
                srcs_cfg = sources.make(no, nl=nl, nt=nt, t_shifts=params['t_shifts'],
                    generator=params['generator'], seed=params['seed'][stream])
                for origin in srcs_cfg:
                    try:
                        src_gen = srcs_cfg[origin].iteritems()
                    except AttributeError: # Python 3 automatically creates a generator
                        src_gen = srcs_cfg[origin].items()
                    for src_type, src in src_gen:
                        srcs.append(sources.xXyYzZtT(src))
                for s0 in srcs:
                    t0 = s0.split('t')[1]
                    params['SRC'] = s0
                    if args.verbose:
                        print(charge,tsep,no,src)
                    coherent_formfac_name = coherent_ff_base % params
                    coherent_formfac_file  = base_dir+'/formfac/'+no + '/'+coherent_formfac_name+'.h5'
                    src_h5 = h5.open_file(coherent_formfac_file,'r')
                    for par in ['pp','np']:
                        for spin in spins:
                            h5_path  = '/'+state[par]+'_%(FS)s_t0_'+t0+'_tsep_'+tsep+'_sink_mom_px0_py0_pz0/'
                            h5_path += charge+'/'+src_split(s0)+'/px0_py0_pz0/local_current'
                            try:
                                FS   = 'UU_'+spin
                                tmp  = src_h5.get_node(h5_path % FS).read()
                                FS   = 'DD_'+spin
                                tmp -= src_h5.get_node(h5_path % FS).read()
                                data_tmp[spin+'_'+par].append()
                            except:
                                print('bad data read')
                    src_h5.close()
                for par in ['pp','np']:
                    for spin in spins:
                        data[spin+'_'+par].append(np.mean(np.array(data_tmp[spin+'_'+par]),axis=0))
            for par in ['pp','np']:
                for spin in spins:
                    h5_out.create_array(h5_path,spin+'_'+par,np.array(data[spin+'_'+par]))
                    h5_out.flush()
h5_out.close()
