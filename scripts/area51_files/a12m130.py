import sources

params = dict()
params['tuning_mq'] = False
params['tuning_ms'] = False
params['run_ff'] = False
params['run_strange'] = True
params['run_pipi'] = False

# the params['si','sf','ds'] are now handled in the sources.py file - srcs here overide those defaults
# you must specify all three of these params to override the default
#params['si'] = 8; params['sf'] = 15; params['ds'] = 1

params['cfg_i'] = 300
params['cfg_f'] = 5295
params['cfg_d'] = 5

params['ENS_ABBR'] = 'a12m130'
params['NL']   = '48'
params['NT']   = '64'
params['U0']   = '0.86372'
params['MS_L'] = '0.00184'
params['MS_S'] = '0.0507'
params['MS_C'] = '0.628'
params['NAIK'] = '-0.2248'

params['MC_reweight'] = {}
params['MC_reweight'][2] = [0.6331, 0.6382]
params['MC_MAX_ITER']       = 500
params['CC_Nnoise']         = 128
params['MC_PROP_ERROR']     = '5.e-16'
params['MC_REL_PROP_ERROR'] = '0'


params['FLOW_TIME'] = '1.0'
params['FLOW_STEP'] = '40'
params['WF_S'] = '3.0'
params['WF_N'] = '30'

params['M5'] = '1.2'
params['L5'] = '20'
''' NOTE: b5-c5 = 1 for all our tuning '''
params['B5']     = '2.0'
params['C5']     = '1.0'
params['alpha5'] = '3.0'

params['MV_L'] = '0.00195'
params['MV_S'] = '0.0693'

params['spec_size']      = 43120
params['hyperspec_size'] = 383680
params['ff_size']        = 386408
params['spec_4D_tslice_fact'] = 1

params['MAX_ITER']   = '15000'
params['RSD_TARGET'] = '1.e-7'
params['Q_DELTA']    = '0.1'
params['RSD_TOL']    = '80'

params['SP_EXTENSION'] = 'lime'

params['seed'] = dict()
params['seed']['a'] = '1a'
'''                    0, nt/2, nt/4, 3 nt/4 '''
params['t_shifts'] = [ 0, 32  , 16  , 48,    8, 24, 40, 56,    4, 36, 20, 52,    12, 28, 44, 60     ]
params['generator'] = sources.oa(int(params['NL']))

''' minutes after last file modification time when deletion of small files is OK '''
params['file_time_delete'] = 10.

params['MESONS_PSQ_MAX']  = 0
params['BARYONS_PSQ_MAX'] = 0

params['run_3pt'] = True
params['t_seps']  = [3,4,5,6,7,8,9,10,11]
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
        params['metaq_split'] = False
        params['cpu_nodes']   = 4
        params['cpu_gpus']    = 0
        params['cpu_maxcus']  = 1
        params['gflow_time']  = 15
        params['src_time']    = 1
        params['spec_time']   = 4

        params['cpu_nrs']     = '--nrs 8'
        params['cpu_rs_node'] = '-r2'
        params['cpu_a_rs']    = '-a16'
        params['cpu_g_rs']    = ''
        params['cpu_c_rs']    = '-c16'
        params['cpu_latency'] = '-l cpu-cpu'
        params['cpu_bind']    = 'lassen_bind_cpu.N32.sh'

        params['gpu_nodes']   = 4
        params['gpu_metaq_nodes'] = 0
        params['gpu_gpus']    = 12
        params['gpu_maxcus']  = 1
        params['prop_time']   = 120
        params['seqprop_time']   = 58
        params['strange_prop_time'] = 15

        params['gpu_nrs']     = '--nrs 4'
        params['gpu_rs_node'] = '-r1'
        params['gpu_a_rs']    = '-a4'
        params['gpu_g_rs']    = '-g4'
        params['gpu_c_rs']    = '-c4'
        params['gpu_latency'] = '-l gpu-cpu'
        params['gpu_geom']    = ' -geom 1 1 1 16'
        params['gpu_bind']    = 'lassen_bind_gpu.omp4.sh'

        params['hisq_maxcus'] = 1
        params['charm_pbp_nodes'] = 1
        params['charm_pbp_meta_nodes'] = 0
        params['charm_pbp_gpus']  = 4
        params['charm_pbp_time']  = 20
        params['charm_pbp_nrs']   = '--nrs 1'

        params['hisq_rs_node'] = '-r1'
        params['hisq_a_rs']    = '-a4'
        params['hisq_g_rs']    = '-g4'
        params['hisq_c_rs']    = '-c4'
        params['hisq_latency'] = '-l gpu-cpu'
        params['hisq_geom']    = '-qmp-geom 1 1 1 4 -qmp-alloc-map 3 2 1 0 -qmp-logic-map  3 2 1 0'

    if machine == 'lassen_3node':
        params['metaq_split'] = False
        params['cpu_nodes']   = 3
        params['cpu_gpus']    = 0
        params['cpu_maxcus']  = 1
        params['gflow_time']  = 15
        params['src_time']    = 1
        params['spec_time']   = 4

        params['cpu_nrs']     = '--nrs 6'
        params['cpu_rs_node'] = '-r2'
        params['cpu_a_rs']    = '-a16'
        params['cpu_g_rs']    = ''
        params['cpu_c_rs']    = '-c16'
        params['cpu_latency'] = '-l cpu-cpu'
        params['cpu_bind']    = 'lassen_bind_cpu.N32.sh'

        params['gpu_nodes']   = 3
        params['gpu_metaq_nodes'] = 0
        params['gpu_gpus']    = 12
        params['gpu_maxcus']  = 1
        params['prop_time']   = 120
        params['seqprop_time']   = 58
        params['strange_prop_time'] = 15

        params['gpu_nrs']     = '--nrs 3'
        params['gpu_rs_node'] = '-r1'
        params['gpu_a_rs']    = '-a4'
        params['gpu_g_rs']    = '-g4'
        params['gpu_c_rs']    = '-c4'
        params['gpu_latency'] = '-l gpu-cpu'
        params['gpu_geom']    = ' -geom 1 1 3 4'
        params['gpu_bind']    = 'lassen_bind_gpu.omp4.sh'

    if machine == 'summit':
        params['metaq_split'] = True
        params['cpu_nodes']   = 2
        params['cpu_gpus']    = 0
        params['cpu_maxcus']  = 1
        params['gflow_time']  = 15
        params['src_time']    = 1
        params['spec_time']   = 4

        params['cpu_nrs']     = '--nrs 4'
        params['cpu_rs_node'] = '-r2'
        params['cpu_a_rs']    = '-a16'
        params['cpu_g_rs']    = ''
        params['cpu_c_rs']    = '-c16'
        params['cpu_latency'] = '-l cpu-cpu'
        params['cpu_bind']    = ''

        params['gpu_nodes']         = 2
        params['gpu_metaq_nodes']   = 0
        params['gpu_gpus']          = 12
        params['gpu_maxcus']        = 1
        params['prop_time']         = 145
        params['seqprop_time']      = 58
        params['strange_prop_time'] = 15

        params['gpu_nrs']     = '--nrs 2'
        params['gpu_rs_node'] = '-r1'
        params['gpu_a_rs']    = '-a6'
        params['gpu_g_rs']    = '-g6'
        params['gpu_c_rs']    = '-c6'
        params['gpu_latency'] = '-l gpu-cpu'
        params['gpu_geom']    = ' -geom 1 1 3 4'
        params['gpu_bind']    = ''

    return params
