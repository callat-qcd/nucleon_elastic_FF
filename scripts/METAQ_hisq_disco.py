from metaq_input_ks_measture_test import *
import os, sys
import argparse
import importlib
import random
import numpy as np
import loop_params as loop_par

#sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))

#sys.path.append(os.path.join(os.path.dirname(__file__),\
#               '/p/gpfs1/mcamacho/nucleon_elastic_FF/scripts/area51_files'))

script_path=os.path.dirname(__file__)+('/'*len(os.path.dirname(__file__)))[0:1]
#sys.path.append(os.path.join(os.path.dirname(__file__),\
#               '/usr/workspace/coldqcd/c51/x_files/project_2/production/nucleon_elastic_FF/scripts'))
sys.path.append(os.path.join(os.path.dirname(__file__),\
               '/p/gpfs1/mcamacho/nucleon_elastic_FF/scripts'))
#sys.path.append(os.path.join(os.path.dirname(__file__),\
#               '/usr/workspace/coldqcd/c51/x_files/project_2/production/nucleon_elastic_FF/scripts/area51_files'))

parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfg',type=str,help='cfg number')
parser.add_argument('--cfgType',type=str,help='cfg type: MILC or SCIDAC')
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('-p',default=False,action='store_const',const=True,\
    help='put task.sh in priority queue? [%(default)s]')
parser.add_argument('-v','--verbose',default=True,action='store_const',const=False,\
    help='run with verbose output? [%(default)s]')
args = parser.parse_args()
print('%s: Arguments passed' %sys.argv[0].split('/')[-1])
print(str(args)+'\n'+args.cfg)


c51=importlib.import_module('c51_mdwf_hisq')
ens,stream = c51.ens_base()
ens_s = ens+'_'+stream

area51 = importlib.import_module(ens)

params = area51.params
#params={'FLOW_TIME':''}
params['CFG']=args.cfg
try:
	params['ENS_LONG'] = c51.ens_long[ens]
except:
	if ens=='a12m180S':
		params['ENS_LONG'] = 'l3264f211b600m00339m0507m628'


params['ENS_S']    = ens_s
params['STREAM']   = stream
print params['NL'],params['NT'],loop_par.sizes[ens]['NL'],loop_par.sizes[ens]['NT']
#params['NL']=loop_par.sizes[ens]['NL']
#params['NT']=loop_par.sizes[ens]['NT']
#params['U0']=loop_par.U0[ens]

params=c51.ensemble(params)

phys_ensList={'a15':'a15m135XL','a12':'a12m135XL','a09':'a09m135XL'}
phys_ens=phys_ensList[ens.split('m')[0]]
c51.ens_long['a12m135XL']='l7296f211b600m001907m05252m6382'
c51.ens_long['a09m135XL']='l96128f211b630m001326m03636m4313'
#print c51.ens_long

ms_phys='0.'+c51.ens_long[phys_ens].split('m')[-2]
mc_phys='0.'+c51.ens_long[phys_ens].split('m')[-1]
naikc_phys=loop_par.naikc[phys_ens]
naikc=loop_par.naikc[ens]


random.seed(params['ENS_LONG']+'.'+params['CFG'])
mySeed  = random.randint(0,5682304)
np.random.seed(mySeed)
cfg_seed=str(np.random.randint(10**7,10**8,1)[0])


#Strange/Charm loop parameters
#params.update({'NPBP_REPS_S':'200','NPBP_REPS_C':'500','MS':'0.06730','MC':'0.8447','NAIK_C':'-0.358919895451143','SEED':cfg_seed,'ENS':ens_s})
params.update({'NPBP_REPS_S':loop_par.NPBP_REPS_S,'NPBP_REPS_C':loop_par.NPBP_REPS_C,'MS':ms_phys,'MC':mc_phys,'NAIK_C':naikc,
               'NAIK_C_PHYS':naikc_phys,'SEED':cfg_seed,'ENS':ens_s})

params['MS_STR']=ms_phys.replace('.','p')
params['MC_STR']=mc_phys.replace('.','p')
name='strange_charm_loops_hisq_%(ENS)s_ms%(MS)s_n%(NPBP_REPS_S)s_mc%(MC)s_n%(NPBP_REPS_C)s_'%params+args.cfg
params['JOBID']=name
params.update({'INI':params['xml']+'/'+name+'.ini','OUT':params['stdout']+'/'+name+'.stdout'})
params.update({'NODES':'0','GPUS':'4','WTIME':'30:00','BWTIME':'30','PROJECT':'nucleon_charm','LOG':params['METAQ_DIR']+'/log/'+name+'.log'})



if not os.path.exists(params['OUT']):
	in_text=open(script_path+'strange_charm_loops_hisq.in','r').read()
	if args.cfgType=='SCIDAC':
		in_text=in_text.replace('milc_cfg','scidac_cfg')

	in_file=open(params['INI'],'w')
	in_file.write(in_text%params)

	task=open(params['METAQ_DIR']+'/todo/gpu/a_'+name+'.sh','w')
	task.write(strange_charm_loops%params)
	os.chmod(params['METAQ_DIR']+'/todo/gpu/a_'+name+'.sh', 0o770)
	#print params,'  ',ens,stream
	print 'Making task: '+params['METAQ_DIR']+'/todo/gpu/a_'+name+'.sh'

	task.close()
	in_file.close()
else:
	print params['OUT']+ ' found'

