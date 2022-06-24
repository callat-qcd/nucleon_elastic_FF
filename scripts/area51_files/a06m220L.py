import sources

params = dict()
params['tuning_mq']   = False
params['tuning_ms']   = False
params['run_ff']      = False
params['run_strange'] = True
params['run_pipi']    = True
params['run_fh']      = True

# the params['si','sf','ds'] are now handled in the sources.py file - srcs here overide those defaults
# you must specify all three of these params to override the default
#params['si'] = 0
#params['sf'] = 7
#params['ds'] = 1

params['cfg_i'] = 750
params['cfg_f'] = 3744
params['cfg_d'] = 6

params['ENS_ABBR'] = 'a06m220L'
params['ENS_LONG'] = 'l72128f211b672m0024m02186m2579'
params['NL']   = '72'
params['NT']   = '128'
params['U0']   = '0.885773'
params['MS_L'] = '0.0024'
params['MS_S'] = '0.02186'
params['MS_C'] = '0.2579'
params['NAIK'] = '-0.04362170'

params['MC_reweight'] = {}
params['MC_reweight'][20] = [
    0.284595, 0.28319 , 0.281785, 0.28038 , 0.278975, 0.27757 , 0.276165, 0.27476 , 0.273355, 0.27195 ,
    0.270545, 0.26914 , 0.267735, 0.26633 , 0.264925, 0.26352 , 0.262115, 0.26071 , 0.259305, 0.2579
    ]
params['MC_reweight'][10] = [
    0.28319 , 0.28038 , 0.27757 , 0.27476 , 0.27195 ,
    0.26914 , 0.26633 , 0.26352 , 0.26071 , 0.2579
    ]
params['MC_MAX_ITER']       = 500
params['CC_Nnoise']         = 128
params['MC_PROP_ERROR']     = '5.e-16'
params['MC_REL_PROP_ERROR'] = '0'

params['FLOW_TIME'] = '1.0'
params['FLOW_STEP'] = '40'
params['WF_S'] = '3.5'
params['WF_N'] = '45'

params['M5'] = '1.0'
params['L5'] = '6'
''' NOTE: b5-c5 = 1 for all our tuning '''
params['B5']     = '1.25'
params['C5']     = '0.25'
params['alpha5'] = '%.1f' %(float(params['B5']) + float(params['C5']))

#MV_L = 0.00300, MV_S = 0.0300
#params['MV_L'] = '0.00306'
#params['MV_S'] = '0.0281'
params['MV_L'] = '0.00309'
params['MV_S'] = '0.0282'

params['spec_size']      = 824448
params['ff_size']        = 1
params['hyperspec_size'] = 8337216
params['pik_size']       = 3863760
params['fh_size']        = 1
params['mixed_size']     = 48000
params['src_size']       = 55037659100
params['prop_size']      = 55037660500
params['hisq_spec_size'] = 26000
params['save_hisq_prop'] = False
#params['seqsrc_size']  = 28991036000
#params['seqprop_size'] = 28991036000

params['spec_4D_tslice_fact'] = .3

params['MAX_ITER']   = '10000'
params['RSD_TARGET'] = '5.e-8'
params['Q_DELTA']    = '0.1'
params['RSD_TOL']    = '80'

params['SP_EXTENSION'] = 'lime'

params['seed'] = dict()
params['seed']['a'] = '1a'
params['seed']['b'] = '1b'
params['seed']['c'] = '1c'
'''                    0, nt/2, nt/4, 3 nt/4 '''
params['t_shifts'] = [ 0, 64  , 32  , 96 ,   16,  80, 48, 112 ]
params['generator'] = sources.oa(int(params['NL']))
params['t_hisq']   = [ 0, 15, 32, 48, 64, 80, 96, 112 ]

''' minutes after last file modification time when deletion of small files is OK '''
params['file_time_delete'] = 10


params['MESONS_PSQ_MAX']  = 4
params['BARYONS_PSQ_MAX'] = 4
params['MM_REL_MOM']      = 2
params['MM_TOT_MOM']      = 4

params['t_seps']  = [3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18]
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
    gpu_geom = {8:' -geom 1 1 2 16',16:' -geom 1 1 4 16'}
    nrs_cpu  = {8:'--nrs 16',16:'--nrs 32'}
    if machine == 'lassen':
        params['cpu_nodes']   = 8
        params['cpu_gpus']    = 0
        params['cpu_maxcus']  = 1
        params['gflow_time']  = 25
        params['landau_time'] = 60
        params['src_time']    = 15
        params['spec_time']   = 10

        params['cpu_nrs']     = nrs_cpu[params['cpu_nodes']]
        params['cpu_rs_node'] = '-r2'
        params['cpu_a_rs']    = '-a16'
        params['cpu_g_rs']    = ''
        params['cpu_c_rs']    = '-c16'
        params['cpu_latency'] = '-l cpu-cpu'
        params['cpu_bind']    = 'lassen_bind_cpu.N32.sh'

        params['gpu_nodes']   = 8
        params['gpu_metaq_nodes'] = params['gpu_nodes']
        params['gpu_gpus']    = 4*params['gpu_nodes']
        params['gpu_maxcus']  = 1
        params['prop_time']   = 55
        params['strange_prop_time'] = 15

        params['gpu_nrs']     = '--nrs '+str(params['gpu_nodes'])
        params['gpu_rs_node'] = '-r1'
        params['gpu_a_rs']    = '-a4'
        params['gpu_g_rs']    = '-g4'
        params['gpu_c_rs']    = '-c4'
        params['gpu_latency'] = '-l gpu-cpu'
        params['gpu_geom']    = gpu_geom[params['gpu_nodes']]
        params['gpu_bind']    = 'lassen_bind_gpu.omp4.sh'

        params['hisq_nodes']  = 8
        params['hisq_metaq_nodes'] = 8
        params['hisq_gpus']   = 32
        params['hisq_coul_spec'] = 16
        params['hisq_spec']   = 9
        params['hisq_maxcus'] = 1
        params['mixed_mesons_time']   = 30
        params['charm_pbp_nodes'] = 4
        params['charm_pbp_meta_nodes'] = 0
        params['charm_pbp_gpus']  = 16
        params['charm_pbp_time']  = 20
        params['charm_pbp_nrs']   = '--nrs 4'

        params['hisq_nrs']     = '--nrs 8'
        params['hisq_rs_node'] = '-r1'
        params['hisq_a_rs']    = '-a4'
        params['hisq_g_rs']    = '-g4'
        params['hisq_c_rs']    = '-c4'
        params['hisq_latency'] = '-l gpu-cpu'
        params['hisq_geom']    = '-qmp-geom 1 2 2 8 -qmp-alloc-map 3 2 1 0 -qmp-logic-map  3 2 1 0'
        params['gpu_bind']    = 'lassen_bind_gpu.omp4.sh'



    if machine == 'summit':
        params['metaq_split'] = True
        params['cpu_nodes']   = 6
        params['cpu_gpus']    = 0
        params['cpu_maxcus']  = 1
        params['gflow_time']  = 15
        params['src_time']    = 5
        params['spec_time']   = 10

        params['cpu_nrs']     = '--nrs 12'
        params['cpu_rs_node'] = '-r2'
        params['cpu_a_rs']    = '-a16'
        params['cpu_g_rs']    = ''
        params['cpu_c_rs']    = '-c16'
        params['cpu_latency'] = '-l cpu-cpu'
        params['cpu_bind']    = ''

        params['gpu_nodes']   = 6
        params['gpu_metaq_nodes'] = 0
        params['gpu_gpus']    = 36
        params['gpu_maxcus']  = 1
        params['prop_time']   = 140
        params['seqprop_time'] = 75

        params['gpu_nrs']     = '--nrs 6'
        params['gpu_rs_node'] = '-r1'
        params['gpu_a_rs']    = '-a6'
        params['gpu_g_rs']    = '-g6'
        params['gpu_c_rs']    = '-c6'
        params['gpu_latency'] = '-l gpu-cpu'
        params['gpu_geom']    = ' -geom 1 3 3 4'
        params['gpu_bind']    = ''

    return params
