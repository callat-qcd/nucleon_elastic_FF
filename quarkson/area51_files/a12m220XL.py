import sources

params = dict()
params['tuning_mq'] = False
params['run_ff'] = True

params['si'] = 0
params['sf'] = 7
params['ds'] = 1

params['ENS_ABBR'] = 'a12m220XL'
params['NL']   = '48'
params['NT']   = '64'
params['U0']   = '0.86372'
params['MS_L'] = '0.00507'
params['MS_S'] = '0.0507'
params['MS_C'] = '0.628'
params['cfg_i'] = 200
params['cfg_f'] = 5195
params['cfg_d'] = 5

params['FLOW_TIME'] = '1.0'
params['FLOW_STEP'] = '40'
params['WF_S'] = '3.0'
params['WF_N'] = '30'

params['M5'] = '1.2'
params['L5'] = '12'
''' NOTE: b5-c5 = 1 for all our tuning '''
params['B5']     = '1.5'
params['C5']     = '0.5'
params['alpha5'] = '1.5'

params['MV_L'] = '0.00600'
params['MV_S'] = '0.0693'

params['spec_size'] = 200100
params['ff_size']   = 386400

params['MAX_ITER']   = '8000'
params['RSD_TARGET'] = '1.e-7'
params['Q_DELTA']    = '0.1'
params['RSD_TOL']    = '80'

params['SP_EXTENSION'] = 'lime'

params['seed'] = dict()
params['seed']['a'] = '1a'
'''                    0, nt/2, nt/4, 3 nt/4 '''
params['t_shifts'] = [ 0, 32  , 16  , 48     ]
params['generator'] = sources.oa(int(params['NL']))

''' minutes after last file modification time when deletion of small files is OK '''
params['file_time_delete'] = 10.

params['MESONS_PSQ_MAX']  = 5
params['BARYONS_PSQ_MAX'] = 0

params['run_3pt'] = True
params['t_seps']  = [3,4,5,6,7,8,9,10,11,12]
params['flavs']   = ['UU','DD']
params['spins']   = ['up_up','dn_dn']
params['snk_mom'] = ['0 0 0']
params['SS_PS']   = 'SS'
params['particles'] = ['proton','proton_np']
params['curr_4d'] = ['A3','V4','A1','A2','A4','V1','V2','V3','P','S']
params['curr_0p'] = ['A3','V4','A1','A2','A4','V1','V2','V3','S','T34','T12','CHROMO_MAG']

''' SCHEDULING PARAMETERS '''

params['queue'] = 'metaq'

params['OMP_NUM_THREADS'] = '4'

def mpirun_params(machine):
    if machine == 'lassen':
        params['metaq_split'] = True
        params['cpu_nodes']   = 1
        params['cpu_gpus']    = 0
        params['cpu_maxcus']  = 1
        params['gflow_time']  = 15
        params['src_time']    = 5
        params['spec_time']   = 13

        params['cpu_nrs']     = '--nrs 2'
        params['cpu_rs_node'] = '-r2'
        params['cpu_a_rs']    = '-a16'
        params['cpu_g_rs']    = ''
        params['cpu_c_rs']    = '-c16'
        params['cpu_latency'] = '-l cpu-cpu'
        params['cpu_bind']    = 'lassen_bind_cpu.N32.sh'

        params['gpu_nodes']   = 1
        params['gpu_metaq_nodes'] = 0
        params['gpu_gpus']    = 4
        params['gpu_maxcus']  = 1
        params['prop_time']   = 10
        params['seqprop_time']   = 10

        params['gpu_nrs']     = '--nrs 1'
        params['gpu_rs_node'] = '-r1'
        params['gpu_a_rs']    = '-a4'
        params['gpu_g_rs']    = '-g4'
        params['gpu_c_rs']    = '-c4'
        params['gpu_latency'] = '-l gpu-cpu'
        params['gpu_geom']    = ' -geom 1 1 1 4'
        params['gpu_bind']    = 'lassen_bind_gpu.omp4.sh'

    if machine == 'summit':
        # split tasks to todo/cgpu_n where n = nodes?
        params['metaq_split'] = True
        # other params
        params['cpu_nodes']   = 1
        params['cpu_gpus']    = 0
        params['cpu_maxcus']  = 1
        params['gflow_time']  = 9
        params['src_time']    = 5
        params['spec_time']   = 10

        params['cpu_nrs']     = '--nrs 2'
        params['cpu_rs_node'] = '-r2'
        params['cpu_a_rs']    = '-a16'
        params['cpu_g_rs']    = ''
        params['cpu_c_rs']    = '-c16'
        params['cpu_latency'] = '-l cpu-cpu'
        params['cpu_bind']    = ''

        params['gpu_nodes']   = 1
        params['gpu_metaq_nodes'] = 0
        params['gpu_gpus']    = 6
        params['gpu_maxcus']  = 1
        params['prop_time']   = 33
        params['seqprop_time']   = 20

        params['gpu_nrs']     = '--nrs 1'
        params['gpu_rs_node'] = '-r1'
        params['gpu_a_rs']    = '-a6'
        params['gpu_g_rs']    = '-g6'
        params['gpu_c_rs']    = '-c6'
        params['gpu_latency'] = '-l gpu-cpu'
        params['gpu_geom']    = ' -geom 1 1 3 2'
        params['gpu_bind']    = ''

    return params