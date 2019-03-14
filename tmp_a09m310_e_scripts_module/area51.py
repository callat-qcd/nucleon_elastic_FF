import sources

params = dict()

''' a09m310
    l3296f211b630m0074m037m440
'''
params['a09m310'] = dict()
params['a09m310']['ENS_LONG'] = 'l3296f211b630m0074m037m440'
params['a09m310']['NL']   = '32'
params['a09m310']['NT']   = '96'
params['a09m310']['U0']   = '0.874164'
params['a09m310']['MS_L'] = '0.0074'
params['a09m310']['MS_S'] = '0.037'
params['a09m310']['MS_C'] = '0.440'

params['a09m310']['FLOW_TIME'] = '1.0'
params['a09m310']['FLOW_STEP'] = '40'
params['a09m310']['WF_S'] = '3.5'
params['a09m310']['WF_N'] = '45'

params['a09m310']['M5'] = '1.1'
params['a09m310']['L5'] = '6'
''' NOTE: b5-c5 = 1 for all our tuning '''
params['a09m310']['B5'] = '1.25'
params['a09m310']['C5'] = '0.25'
params['a09m310']['alpha5'] = '1.5'

params['a09m310']['MV_L'] = '0.00951'
params['a09m310']['MV_S'] = '0.0491'

params['a09m310']['MAX_ITER'] = '2000'
params['a09m310']['RSD_TARGET'] = '1.e-7'
params['a09m310']['Q_DELTA'] = '0.1'
params['a09m310']['RSD_TOL'] = '80'

params['a09m310']['SP_EXTENTION'] = 'lime'

params['a09m310']['seed'] = dict()
params['a09m310']['seed']['e'] = '1a' #this should have been 1e,
'''                               0, nt/2, nt/4, 3 nt/4 '''
params['a09m310']['t_shifts'] = [ 0, 48  , 24  , 72     ]
params['a09m310']['generator'] = sources.oa(int(params['a09m310']['NL']))
