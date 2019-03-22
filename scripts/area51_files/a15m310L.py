import sources

params = dict()
params['ENS_ABBR'] = 'a15m310L'
params['ENS_LONG'] = 'l2448f211b580m013m065m838'
params['NL']   = '24'
params['NT']   = '48'
params['U0']   = '0.85535'
params['MS_L'] = '0.013'
params['MS_S'] = '0.065'
params['MS_C'] = '0.838'

params['FLOW_TIME'] = '1.0'
params['FLOW_STEP'] = '40'
params['WF_S'] = '3.0'
params['WF_N'] = '30'

params['M5'] = '1.3'
params['L5'] = '12'
''' NOTE: b5-c5 = 1 for all our tuning '''
params['B5']     = '1.5'
params['C5']     = '0.5'
params['alpha5'] = '1.5'

params['MV_L'] = '0.0158'
params['MV_S'] = '0.0902'

params['MAX_ITER']   = '2000'
params['RSD_TARGET'] = '1.e-7'
params['Q_DELTA']    = '0.1'
params['RSD_TOL']    = '80'

params['SP_EXTENSION'] = 'lime'

params['seed'] = dict()
params['seed']['a'] = '1a'
'''                    0, nt/2, nt/4, 3 nt/4 '''
params['t_shifts'] = [ 0, 24  , 12  , 36     ]
params['generator'] = sources.oa(int(params['NL']))
params['N_SEQ'] = 2*len(params['t_shifts']) #2 * t_shifts

''' minutes after last file modification time when deletion of small files is OK '''
params['prop_time_delete'] = 10

params['MESONS_PSQ_MAX']  = 5
params['BARYONS_PSQ_MAX'] = 5

params['t_seps']  = [2,3,4,5,6,7,8,9,10]
params['flavs']   = ['UU','DD']
params['spins']   = ['up_up','dn_dn']
params['snk_mom'] = ['0 0 0']
params['SS_PS']   = 'SS'
params['particles'] = ['proton','proton_np']
params['curr_4d'] = ['A3','V4','A1','A2','A4','V2','V2','V3','P']
params['curr_p']  = ['A3','V4','A1','A2','A4','V2','V2','V3','P','S']
params['curr_0p'] = ['T34','T12','CHROMO_MAG']

params['cpu_nodes'] = 1
params['cpu_gpus']  = 0
params['gflow_time']  = 15
params['src_time']  = 5
params['spec_time'] = 10

params['gpu_nodes'] = 0
params['gpu_gpus']  = 6
params['prop_time'] = 10
