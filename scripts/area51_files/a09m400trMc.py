import sources

params = dict()
params['tuning_mq']   = True
params['run_strange'] = False
params['run_pipi']    = False
params['run_ff']      = False
params['LIGHT_BARYONS'] = 'proton</elem> <elem>delta_pp'

# the params['si','sf','ds'] are now handled in the sources.py file - srcs here overide those defaults
# you must specify all three of these params to override the default

params['cfg_i'] = 600
params['cfg_f'] = 6594
params['cfg_d'] = 6

params['ENS_ABBR'] = 'a09m400trMc'
params['NL']   = '32'
params['NT']   = '96'
params['U0']   = '0.874164'
params['MS_L'] = '0.01300'
params['MS_S'] = '0.01300'
params['MS_C'] = '0.4313'
params['NAIK'] = '-0.1158565'

params['FLOW_TIME'] = '1.0'
params['FLOW_STEP'] = '40'
params['WF_S'] = '3.5'
params['WF_N'] = '45'

params['M5'] = '1.1'
params['L5'] = '6'
''' NOTE: b5-c5 = 1 for all our tuning '''
params['B5']     = '1.25'
params['C5']     = '0.25'
params['alpha5'] = '%.1f' %(float(params['B5']) + float(params['C5']))

mv_q = '0.0181'
params['MV_L'] = mv_q
params['MV_S'] = mv_q

params['spec_size'] = 1
params['hisq_spec_size'] = 6800
params['ff_size']   = 1



params['MAX_ITER']   = '4000'
params['RSD_TARGET'] = '1.e-7'
params['Q_DELTA']    = '0.1'
params['RSD_TOL']    = '80'

params['SP_EXTENSION'] = 'lime'
params['save_hisq_prop'] = False

params['seed'] = dict()
params['seed']['a'] = '1a' #this should have been 1e,
'''                               0, nt/2, nt/4, 3 nt/4 '''
params['t_shifts'] = [ 0, 48  , 24  , 72     ]
params['generator'] = sources.oa(int(params['NL']))

params['t_hisq'] = [0, 12, 24, 36, 48, 60, 72, 84]

''' minutes after last file modification time when deletion of small files is OK '''
params['file_time_delete'] = 10


params['MESONS_PSQ_MAX']  = 5
params['BARYONS_PSQ_MAX'] = 0

params['t_seps']  = [2,3,4,5,6,7,8,9,10,11,12,13,14]
params['flavs']   = ['UU','DD']
params['spins']   = ['up_up','dn_dn']
params['snk_mom'] = ['0 0 0']
params['SS_PS']   = 'SS'
params['particles'] = ['proton','proton_np']
params['curr_4d'] = ['A3','V4','A1','A2','A4','V1','V2','V3','P','S']
params['curr_0p'] = ['A3','V4','A1','A2','A4','V1','V2','V3','P','S','T34','T12','CHROMO_MAG']

''' SCHEDULING PARAMETERS '''

params['queue'] = 'metaq'

params['OMP_NUM_THREADS'] = '4'

def mpirun_params(machine):
    if machine == 'lassen':
        params['cpu_nodes']   = 1
        params['cpu_gpus']    = 0
        params['cpu_maxcus']  = 1
        params['gflow_time']  = 15
        params['src_time']    = 5
        params['spec_time']   = 10

        params['cpu_nrs']     = '--nrs 2'
        params['cpu_rs_node'] = '-r2'
        params['cpu_a_rs']    = '-a16'
        params['cpu_g_rs']    = ''
        params['cpu_c_rs']    = '-c16'
        params['cpu_latency'] = '-l cpu-cpu'
        params['cpu_bind']    = 'lassen_bind_cpu.N36.sh'

        params['gpu_nodes']   = 0
        params['gpu_gpus']    = 4
        params['gpu_maxcus']  = 1
        params['prop_time']   = 15

        params['gpu_nrs']     = '--nrs 1'
        params['gpu_rs_node'] = '-r1'
        params['gpu_a_rs']    = '-a4'
        params['gpu_g_rs']    = '-g4'
        params['gpu_c_rs']    = '-c4'
        params['gpu_latency'] = '-l gpu-cpu'
        params['gpu_geom']    = ' -geom 1 1 1 4'

        params['hisq_nodes']       = 1
        params['hisq_metaq_nodes'] = 0
        params['hisq_gpus']        = 4
        params['hisq_coul_spec']   = 10
        params['hisq_spec_time']   = 4
        params['hisq_maxcus']      = 1
        
        params['hisq_nrs']     = '--nrs 1'
        params['hisq_rs_node'] = '-r1'
        params['hisq_a_rs']    = '-a4'
        params['hisq_g_rs']    = '-g4'
        params['hisq_c_rs']    = '-c4'
        params['hisq_latency'] = '-l gpu-cpu'
        params['hisq_geom']    = '-qmp-geom 1 1 1 4 -qmp-alloc-map 3 2 1 0 -qmp-logic-map  3 2 1 0'
        params['gpu_bind']     = 'lassen_bind_gpu.omp4.sh'

    if machine == 'summit':
        params['cpu_nodes']   = 1
        params['cpu_gpus']    = 0
        params['cpu_maxcus']  = 1
        params['gflow_time']  = 15
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
        params['prop_time']   = 10

        params['gpu_nrs']     = '--nrs 1'
        params['gpu_rs_node'] = '-r1'
        params['gpu_a_rs']    = '-a6'
        params['gpu_g_rs']    = '-g6'
        params['gpu_c_rs']    = '-c6'
        params['gpu_latency'] = '-l gpu-cpu'
        params['gpu_geom']    = ' -geom 1 1 1 6'
        params['gpu_bind']    = ''

    return params
