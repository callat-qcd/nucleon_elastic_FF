import socket
import sources

hn = socket.gethostname()

params = dict()
#params['tuning_mq'] = False
#params['tuning_ms'] = False
#params['run_ff'] = True
#params['run_strange'] = True

# the params['si','sf','ds'] are now handled in the sources.py file - srcs here overide those defaults
# you must specify all three of these params to override the default
#params['si'] = 16
#params['sf'] = 23
#params['ds'] = 1

params['ENS_ABBR'] = 'a09m350'
params['ENS_LONG'] = 'l3264f211b630m00945m037m440'
params['NL']   = '32'
params['NT']   = '64'
params['U0']   = '0.874164'
params['MS_L'] = '0.00945'
params['MS_S'] = '0.037'
params['MS_C'] = '0.440'
params['NAIK'] = '-0.1201845'
params['cfg_i'] = 300
params['cfg_f'] = 6300
params['cfg_d'] = 5
params['NPBP_REPS_S']='64'
params['NPBP_REPS_C']='256'

#params['save_hisq_prop'] = False

params['FLOW_TIME'] = '1.0'
params['FLOW_STEP'] = '40'
params['WF_S'] = '3.5'
params['WF_N'] = '45'

params['M5'] = '1.1'
params['L5'] = '6'
''' NOTE: b5-c5 = 1 for all our tuning '''
params['B5']     = '1.25'
params['C5']     = '0.25'
params['alpha5'] = '1.0'

params['MV_L'] = '0.0121'
#params['MV_S'] = '0.0902'
#params['MV_S'] = '0.0946'
#params['MV_S'] = '0.0945'

#params['spec_size'] = 43000
#params['hyperspec_size'] = 383680
#params['ff_size']   = 429000
#params['spec_4D_tslice_fact'] = 0.5
#params['src_size']     = 8153728000
#params['prop_size']    = 8153729000
#params['prop_size_h5'] = 8153729000
#params['seqsrc_size']  = 8153734000
#params['seqprop_size'] = 8153736000


#params['MAX_ITER']   = '17000'
#params['RSD_TARGET'] = '1.e-7'
#params['Q_DELTA']    = '0.1'
#params['RSD_TOL']    = '80'

#params['SP_EXTENSION'] = 'lime'
'''
params['seed'] = dict()
if any(host in hn for host in ['lassen']):
    random_run = '1'
elif any(host in hn for host in ['login','batch']):
    random_run = '1'
for stream in ['a','b','c','d','e']:
    params['seed'][stream] = random_run + stream

# Lassen has done srcs 0 - 15, OA on [0 , 32, 16, 48, 8 , 40, 24, 56]
# Summit will do srcs 16 - 32, OA on [4 , 36, 20, 52, 12, 44, 28, 60]
# they have to be run in batches of 8 so that the t0 are spaced far enough apart to not interefere in the coherent sink
params['t_shifts'] = [ 0, 32, 16, 48,    8, 40, 24, 56,    4, 36, 20, 52,    12, 44, 28, 60 ]
params['generator'] = sources.oa(int(params['NL']))
#params['t_hisq']   = [0,  8, 16, 24, 32, 40, 48, 56]
'''

''' minutes after last file modification time when deletion of small files is OK '''
#params['file_time_delete'] = 10

#params['MESONS_PSQ_MAX']  = 5
#params['BARYONS_PSQ_MAX'] = 5
#params['MESONS_PSQ_MAX']  = 0
#params['BARYONS_PSQ_MAX'] = 0

#params['run_3pt'] = True
#params['t_seps']  = [3,4,5,6,7,8,9]
#params['flavs']   = ['UU','DD']
#params['spins']   = ['up_up','dn_dn']
#params['snk_mom'] = ['0 0 0']
#params['SS_PS']   = 'SS'
#params['particles'] = ['proton','proton_np']
#params['curr_4d'] = ['A3','V4','A1','A2','A4','V1','V2','V3','P','S']
#params['curr_0p'] = ['A3','V4','A1','A2','A4','V1','V2','V3','P','S','T34','T12','CHROMO_MAG']

''' SCHEDULING PARAMETERS '''

params['queue'] = 'metaq'

params['OMP_NUM_THREADS'] = '4'

def mpirun_params(machine):
    if machine == 'lassen':
        '''
        params['cpu_nodes']   = 3
        params['cpu_gpus']    = 0
        params['cpu_maxcus']  = 1
        params['gflow_time']  = 25
        params['src_time']    = 5
        params['spec_time']   = 10

        params['cpu_nrs']     = '--nrs 8'
        params['cpu_rs_node'] = '-r2'
        params['cpu_a_rs']    = '-a18'
        params['cpu_g_rs']    = ''
        params['cpu_c_rs']    = '-c18'
        params['cpu_latency'] = '-l cpu-cpu'
        params['cpu_bind']    = 'lassen_bind_cpu.N36.sh'

        params['gpu_nodes']   = 3
        params['gpu_metaq_nodes'] = 0
        params['gpu_gpus']    = 12
        params['gpu_maxcus']  = 1
        params['prop_time']   = 150
        params['seqprop_time']    = 80
        params['strange_prop_time'] = 15

        params['gpu_nrs']     = '--nrs 4'
        params['gpu_rs_node'] = '-r1'
        params['gpu_a_rs']    = '-a4'
        params['gpu_g_rs']    = '-g4'
        params['gpu_c_rs']    = '-c4'
        params['gpu_latency'] = '-l gpu-cpu'
        params['gpu_geom']    = ' -geom 1 1 1 16 -qmp-geom 1 1 1 16 -qmp-alloc-map 3 2 1 0 -qmp-logic-map  3 2 1 0'
        params['gpu_bind']    = 'lassen_bind_gpu.omp4.sh'
        '''

        params['hisq_nodes']  = 1
        params['hisq_metaq_nodes'] = 0
        params['hisq_gpus']   = 4
        params['hisq_coul_spec'] = 16
        params['hisq_spec']   = 4
        params['hisq_maxcus'] = 1

        params['hisq_nrs']     = '--nrs 1'
        params['hisq_rs_node'] = '-r1'
        params['hisq_a_rs']    = '-a4'
        params['hisq_g_rs']    = '-g4'
        params['hisq_c_rs']    = '-c4'
        params['hisq_latency'] = '-l gpu-cpu'
        params['hisq_geom']    = ' -qmp-geom 1 1 1 4 -qmp-alloc-map 3 2 1 0 -qmp-logic-map  3 2 1 0'
        params['gpu_bind']    = 'lassen_bind_gpu.omp4.sh'
        params['strange_charm_loops_time']=60



    '''
    if machine == 'lassen_3node':
        params['cpu_nodes']   = 3
        params['cpu_gpus']    = 0
        params['cpu_maxcus']  = 1
        params['gflow_time']  = 25
        params['src_time']    = 5
        params['spec_time']   = 10

        params['cpu_nrs']     = '--nrs 6'
        params['cpu_rs_node'] = '-r2'
        params['cpu_a_rs']    = '-a18'
        params['cpu_g_rs']    = ''
        params['cpu_c_rs']    = '-c18'
        params['cpu_latency'] = '-l cpu-cpu'
        params['cpu_bind']    = 'lassen_bind_cpu.N36.sh'

        params['gpu_nodes']   = 3
        params['gpu_metaq_nodes'] = 0
        params['gpu_gpus']    = 12
        params['gpu_maxcus']  = 1
        params['prop_time']   = 150
        params['seqprop_time']    = 80
        params['strange_prop_time'] = 15

        params['gpu_nrs']     = '--nrs 3'
        params['gpu_rs_node'] = '-r1'
        params['gpu_a_rs']    = '-a4'
        params['gpu_g_rs']    = '-g4'
        params['gpu_c_rs']    = '-c4'
        params['gpu_latency'] = '-l gpu-cpu'
        params['gpu_geom']    = ' -geom 1 1 3 4 -qmp-geom 1 1 3 4 -qmp-alloc-map 3 2 1 0 -qmp-logic-map  3 2 1 0'
        params['gpu_bind']    = 'lassen_bind_gpu.omp4.sh'


        params['hisq_nodes']  = 3
        params['hisq_metaq_nodes'] = 0
        params['hisq_gpus']   = 12
        params['hisq_coul_spec'] = 16
        params['hisq_spec']   = 3
        params['hisq_maxcus'] = 1

        params['hisq_nrs']     = '--nrs 3'
        params['hisq_rs_node'] = '-r1'
        params['hisq_a_rs']    = '-a4'
        params['hisq_g_rs']    = '-g4'
        params['hisq_c_rs']    = '-c4'
        params['hisq_latency'] = '-l gpu-cpu'
        params['hisq_geom']    = ' -geom 1 1 3 4 -qmp-geom 1 1 3 4 -qmp-alloc-map 3 2 1 0 -qmp-logic-map  3 2 1 0'
        params['gpu_bind']    = 'lassen_bind_gpu.omp4.sh'

    if machine == 'summit':
        params['metaq_split'] = False
        params['cpu_nodes']   = 2
        params['cpu_gpus']    = 0
        params['cpu_maxcus']  = 1
        params['gflow_time']  = 20
        params['src_time']    = 2
        params['spec_time']   = 5

        params['cpu_nrs']     = '--nrs 4'
        params['cpu_rs_node'] = '-r2'
        params['cpu_a_rs']    = '-a16'
        params['cpu_g_rs']    = ''
        params['cpu_c_rs']    = '-c16'
        params['cpu_latency'] = '-l cpu-cpu'
        params['cpu_bind']    = ''

        params['gpu_nodes']       = 2
        params['gpu_metaq_nodes'] = 0
        params['gpu_gpus']        = 12
        params['gpu_maxcus']      = 1
        params['prop_time']       = 150
        params['seqprop_time']    = 80
        params['strange_prop_time'] = 15

        params['gpu_nrs']     = '--nrs 2'
        params['gpu_rs_node'] = '-r1'
        params['gpu_a_rs']    = '-a6'
        params['gpu_g_rs']    = '-g6'
        params['gpu_c_rs']    = '-c6'
        params['gpu_latency'] = '-l gpu-cpu'
        params['gpu_geom']    = ' -geom 1 1 3 4'
        params['gpu_bind']    = ''

        params['hisq_nodes']  = 2
        params['hisq_metaq_nodes'] = 0
        params['hisq_gpus']   = 12
        params['hisq_coul_spec'] = 16
        params['hisq_spec']   = 3
        params['hisq_maxcus'] = 1

        params['hisq_nrs']     = '--nrs 2'
        params['hisq_rs_node'] = '-r1'
        params['hisq_a_rs']    = '-a6'
        params['hisq_g_rs']    = '-g6'
        params['hisq_c_rs']    = '-c6'
        params['hisq_latency'] = '-l gpu-cpu'
        params['hisq_geom']    = ' -qmp-geom 1 1 3 4'
    '''
    return params
