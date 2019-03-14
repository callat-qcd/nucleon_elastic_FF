import sources

params = dict()
params['ENS_ABBR'] = 'a09m310'
params['ENS_LONG'] = 'l3296f211b630m0074m037m440'
params['NL']   = '32'
params['NT']   = '96'
params['U0']   = '0.874164'
params['MS_L'] = '0.0074'
params['MS_S'] = '0.037'
params['MS_C'] = '0.440'

params['FLOW_TIME'] = '1.0'
params['FLOW_STEP'] = '40'
params['WF_S'] = '3.5'
params['WF_N'] = '45'

params['M5'] = '1.1'
params['L5'] = '6'
''' NOTE: b5-c5 = 1 for all our tuning '''
params['B5']     = '1.25'
params['C5']     = '0.25'
params['alpha5'] = '1.5'

params['MV_L'] = '0.00951'
params['MV_S'] = '0.0491'

params['MAX_ITER']   = '2000'
params['RSD_TARGET'] = '1.e-7'
params['Q_DELTA']    = '0.1'
params['RSD_TOL']    = '80'

params['SP_EXTENSION'] = 'lime'

params['seed'] = dict()
params['seed']['e'] = '1a' #this should have been 1e,
'''                               0, nt/2, nt/4, 3 nt/4 '''
params['t_shifts'] = [ 0, 48  , 24  , 72     ]
params['generator'] = sources.oa(int(params['NL']))
