import sources

params = dict()
params['tuning_mq']   = False
params['tuning_ms']   = False
params['run_ff']      = False
params['run_strange'] = True
params['run_mm']      = True

# the params['si','sf','ds'] are now handled in the sources.py file - srcs here overide those defaults
# you must specify all three of these params to override the default
#params['si'] = 0
#params['sf'] = 7
#params['ds'] = 1

params['cfg_i'] = 78
params['cfg_f'] = 3102
params['cfg_d'] = 6

params['ENS_ABBR'] = 'a09m135'
params['ENS_LONG'] = 'l6496f211b630m001326m03636m4313'
params['NL']   = '64'
params['NT']   = '96'
params['U0']   = '0.874164'
params['MS_L'] = '0.001326'
params['MS_S'] = '0.03636'
params['MS_C'] = '0.4313'
params['NAIK'] = '-0.1204'

params['FLOW_TIME'] = '1.0'
params['FLOW_STEP'] = '40'
params['WF_S'] = '3.5'
params['WF_N'] = '45'

params['M5'] = '1.1'
params['L5'] = '12'
''' NOTE: b5-c5 = 1 for all our tuning '''
params['B5']     = '1.5'
params['C5']     = '0.5'
params['alpha5'] = '2.0'

#params['MV_L'] = '0.00137'
params['MV_L'] = '0.00152'
#params['MV_S'] = '0.0491' # from a09m220
#params['MV_S'] = '0.0481' # estimated from MILC's phys pion mass a09m130 ensemble
params['MV_S'] = '0.04735' # after 100 cfgs tuning

params['spec_size'] = 51312
params['ff_size']   = 435560
params['hyperspec_size'] = 485800
params['mixed_size'] = 48200
params['spec_4D_tslice_fact'] = 0.33333333
params['src_size']     = 28991031000
params['prop_size']    = 28991032000
params['seqsrc_size']  = 28991036000
params['seqprop_size'] = 28991036000

params['MAX_ITER']   = '18000'
params['RSD_TARGET'] = '1.e-7'
params['Q_DELTA']    = '0.1'
params['RSD_TOL']    = '80'

params['SP_EXTENSION'] = 'lime'

params['seed'] = dict()
params['seed']['a'] = '1a'
params['seed']['b'] = '1b'
'''                    0, nt/2, nt/4, 3 nt/4 '''
params['t_shifts'] = [ 0, 48  , 24  , 72 ,   12,  60, 36, 84 ]
params['generator'] = sources.oa(int(params['NL']))

''' minutes after last file modification time when deletion of small files is OK '''
params['file_time_delete'] = 10


params['MESONS_PSQ_MAX']  = 0
params['BARYONS_PSQ_MAX'] = 0
params['MM_REL_MOM']      = 9
params['MM_TOT_MOM']      = 5

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
        params['cpu_nodes']   = 1
        params['cpu_gpus']    = 0
        params['cpu_maxcus']  = 1
        params['gflow_time']  = 15
        params['src_time']    = 5
        params['spec_time']   = 10

        params['cpu_nrs']     = '--nrs 2'
        params['cpu_rs_node'] = '-r2'
        params['cpu_a_rs']    = '-a18'
        params['cpu_g_rs']    = ''
        params['cpu_c_rs']    = '-c18'
        params['cpu_latency'] = '-l cpu-cpu'
        params['cpu_bind']    = 'lassen_bind_cpu.N36.sh'

        params['gpu_nodes']   = 0
        params['gpu_gpus']    = 4
        params['gpu_maxcus']  = 1
        params['prop_time']   = 10

        params['gpu_nrs']     = '--nrs 1'
        params['gpu_rs_node'] = '-r1'
        params['gpu_a_rs']    = '-a4'
        params['gpu_g_rs']    = '-g4'
        params['gpu_c_rs']    = '-c4'
        params['gpu_latency'] = '-l gpu-cpu'
        params['gpu_geom']    = ' -geom 1 1 1 4'

    if machine == 'summit':
        params['metaq_split'] = True
        params['cpu_nodes']   = 4
        params['cpu_gpus']    = 0
        params['cpu_maxcus']  = 1
        params['gflow_time']  = 15
        params['src_time']    = 5
        params['spec_time']   = 10

        params['cpu_nrs']     = '--nrs 8'
        params['cpu_rs_node'] = '-r2'
        params['cpu_a_rs']    = '-a16'
        params['cpu_g_rs']    = ''
        params['cpu_c_rs']    = '-c16'
        params['cpu_latency'] = '-l cpu-cpu'
        params['cpu_bind']    = ''

        params['gpu_nodes']   = 4
        params['gpu_metaq_nodes'] = 0
        params['gpu_gpus']    = 24
        params['gpu_maxcus']  = 1
        params['prop_time']   = 145
        params['seqprop_time'] = 75
        params['strange_prop_time'] = 37

        params['gpu_nrs']     = '--nrs 4'
        params['gpu_rs_node'] = '-r1'
        params['gpu_a_rs']    = '-a6'
        params['gpu_g_rs']    = '-g6'
        params['gpu_c_rs']    = '-c6'
        params['gpu_latency'] = '-l gpu-cpu'
        params['gpu_geom']    = ' -geom 1 1 2 12'
        params['gpu_bind']    = ''

        params['hisq_nodes']  = 4
        params['hisq_metaq_nodes'] = 0
        params['hisq_gpus']   = 24
        params['hisq_coul_spec'] = 16
        params['hisq_spec']   = 4
        params['hisq_maxcus'] = 1
        params['mixed_mesons_time'] = 20

        params['hisq_nrs']     = '--nrs 4'
        params['hisq_rs_node'] = '-r1'
        params['hisq_a_rs']    = '-a6'
        params['hisq_g_rs']    = '-g6'
        params['hisq_c_rs']    = '-c6'
        params['hisq_latency'] = '-l gpu-cpu'
        params['hisq_geom']    = ' -geom 1 1 2 12 -qmp-geom 1 1 2 12 -qmp-alloc-map 3 2 1 0 -qmp-logic-map  3 2 1 0'
        params['gpu_bind']    = ''

    return params
