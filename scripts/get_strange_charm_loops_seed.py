import sys,os,argparse
import numpy as np
import h5py as h5
import importlib
import loop_params as loop_par
from milc_output_reader import *
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
sys.path.append(os.path.join(os.path.dirname(__file__),\
               '/usr/workspace/coldqcd/c51/x_files/project_2/production/nucleon_elastic_FF/scripts'))

'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='Collect hisq charm loop data')
parser.add_argument('--ens',type=str,help='Ensemble name')
parser.add_argument('--cnpbp',type=int,help='Charm npbp')
parser.add_argument('--snpbp',type=int,help='Strange npbp')
parser.add_argument('-o',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('-v',default=True,action='store_const',const=False,help='verbose? [%(default)s]')
parser.add_argument('--fout',type=str,help='name of output file')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')


c51=importlib.import_module('c51_mdwf_hisq')
ens,stream = c51.ens_base()
args.ens=ens+'_'+stream

phys_ensList={'a15':'a15m135XL','a12':'a12m135XL','a09':'a09m135XL'}
c51.ens_long['a12m135XL']='l7296f211b600m001907m05252m6382'
c51.ens_long['a09m135XL']='l96128f211b630m001326m03636m4313'

phys_ens=phys_ensList[ens.split('m')[0]]
ms_phys='0.'+c51.ens_long[phys_ens].split('m')[-2]
mc_phys='0.'+c51.ens_long[phys_ens].split('m')[-1]

#ens,stream = c51.ens_base()
#ens_s = ens+'_'+stream

#area51 = importlib.import_module(ens)
#params = area51.params

NT=int(loop_par.sizes[args.ens.split('_')[0]]['NT'])

prod_dir='/p/gpfs1/walkloud/c51/x_files/project_2/production/'
std_dir=prod_dir+args.ens+'/stdout/'
xml_dir=prod_dir+args.ens+'/xml/'
out_dir=prod_dir+args.ens+'/'

hisq_name='strange_charm_loops_hisq_%(ENS)s_ms%(MS)s_n%(NPBP_REPS_S)s_mc%(MC)s_n%(NPBP_REPS_C)s_%(CFG)s.stdout'
hisq_name_ini=hisq_name.replace('.stdout','.ini')


seedDict={}


#hisq_name='strange_charm_loops_hisq_%(ENS)s_ms%(MS)s_n%(NPBP_REPS_S)s_mc%(MC)s_n%(NPBP_REPS_C)s_'%params+args.cfg'


if args.fout is None:
	out_name='loops_data_%(ENS)s_ms%(MS)s_mc%(MC)s.h5'
else:
	out_name=args.fout
masses = {'strange':'6.730000e-02','charm':'8.447000e-01'}
masses={'strange':ms_phys,'charm':mc_phys}
massesStr={'MS':ms_phys,'MC':mc_phys}
params={'ENS':args.ens,'CFG':None,'NPBP_REPS_S':loop_par.NPBP_REPS_S,'NPBP_REPS_C':loop_par.NPBP_REPS_C}
params.update(massesStr)


good,bad=[],[]
cfgs=os.listdir(std_dir)
#cfgs=[str(i) for i in range(300,5300,5)]


#pbp_tslice = {i:[] for i in masses}
#pbp = {i:[] for i in masses}
badFiles=[]


shapes={m:None for m in masses}
if args.cnpbp is not None:
    shapes['charm']=(NT,loop_par.NPBP_REPS_C,2)
if args.snpbp is not None:
    shapes['strange']=(NT,loop_par.NPBP_REPS_S,2)

naikVals=[]
masses=[]

tslice,tsum = {},{}
Allmasses_naikVals=[]
for cfg in cfgs:
    masses,naikVals=[],[]
    params['CFG']=cfg
	
    #print std_dir+cfg+'/'+hisq_name%params
    if os.path.exists(std_dir+cfg+'/'+hisq_name%params):
        #print std_dir+cfg+'/'+hisq_name%params #print hisq_name%params
        try:
            try:
                dataSets,set_npbp=getLoopDataTextFromFile(std_dir+cfg+'/'+hisq_name%params)
                hisq_in_file=open(xml_dir+cfg+'/'+hisq_name_ini%params).read()
                seedDict[cfg]=hisq_in_file.split('iseed ')[1].split('\n')[0]
                data,dataSum=getLoopData(dataSets,NT) 
 		print 'here'
	        temp=open(std_dir+cfg+'/'+hisq_name%params).read().split('Time to reload gauge configuration ')[0].split('\n')
		#print temp
                #tslice,tsum = {},{}
		for k in temp:
                        tempM,tempN='',''
                        if 'mass ' in k:
                                masses.append(k.split('mass ')[1])
                                
               	        if 'naik_term_epsilon ' in k:
                                naikVals.append(k.split('naik_term_epsilon ')[1])
                for k,m in enumerate(masses):
                    n=naikVals[k]
                    if m not in tslice:
                        tslice[m],tsum[m]={},{}
                    if n not in tslice[m]:
                        tslice[m][n],tsum[m][n]=[],[]

                    tslice[m][n].append(np.array(data[k]))
                    tsum[m][n].append(np.array(dataSum[k]))
                    
                good.append(cfg)
            except:
                print std_dir+cfg+'/'+hisq_name%params+ ' is a bad file'
                badFiles.append(std_dir+cfg+'/'+hisq_name%params)
                int('c')  
        
        except:
            print(std_dir+cfg+'/'+hisq_name%params + ' does not exists')
            bad.append(int(cfg))
    else:
        print(std_dir+cfg+'/'+hisq_name%params + ' does not exists')
        bad.append(int(cfg))
    for u,v in zip(masses,naikVals):
        if [u,v] not in Allmasses_naikVals:
            Allmasses_naikVals.append([u,v])

if args.fout is None:
	out_name='loops_avgdata_%(ENS)s_ms%(MS)s_n%(NPBP_REPS_S)s_mc%(MC)s_n%(NPBP_REPS_C)s_All.h5'

f=h5.File(out_dir+out_name%params,'a')


good=[int(i) for i in good]
indsCfgsOrd=np.array(good).argsort()
print np.array(good)[indsCfgsOrd]

for k in Allmasses_naikVals:
	j,n=k[0],k[1]
	nodeStr='mq'
	if  massesStr['MS']==j:
		nodeStr='ms'
        if  massesStr['MC']==j: 
                nodeStr='mc'  
	
	f['/'+nodeStr+'_'+j+'/naik_'+n+'/pbp_tslice']=np.array(tslice[j][n])[tuple([indsCfgsOrd])]#pbp_tslice[j][n]
	f['/'+nodeStr+'_'+j+'/naik_'+n+'/pbp']=np.array(tsum[j][n])[tuple([indsCfgsOrd])]#pbp[j][n]
f['/cfgs']=np.array(good)[tuple([indsCfgsOrd])]

seeds=[]
for cfg in np.array(good)[tuple([indsCfgsOrd])]:
	seeds.append(seedDict[str(cfg)])

f['/seeds']=np.array(seeds)


'''ADDITIONAL CODE TO CHECK SEEDS
   seedDict[ens] should match f['/seeds']
'''
'''
sys.path.insert(0,'/usr/workspace/coldqcd/c51/x_files/project_2/production/nucleon_elastic_FF/')
import c51_mdwf_hisq as c51
import random
import numpy as np

ens_long=c51.ens_long[ens]
seedDict={ens:[]}

for cfg in f['cfgs'][()]:
		random.seed(ens_long+'.'+str(cfg))
		mySeed  = random.randint(0,5682304)
		np.random.seed(mySeed)
		cfg_seed=str(np.random.randint(10**7,10**8,1)[0])
		seedDict[ens].append(cfg_seed)
'''









