#!/usr/bin/env python
from __future__ import print_function
import os, sys
import argparse

'''
    NUCLEON_ELASTIC_FF IMPORTS
'''
# test change
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
import importlib
import c51_mdwf_hisq as c51
from utils import *
import sources
import random
import numpy as np
import h5py as h5


'''
    COMMAND LINE ARG PARSER
'''
parser = argparse.ArgumentParser(description='Collect hisq charm loop data')
parser.add_argument('cfgs',nargs='+',type=int,help='cfg[s] no to check: ni [nf dn]')
parser.add_argument('-o',default=False,action='store_const',const=True,help='overwrite? [%(default)s]')
parser.add_argument('-v',default=True,action='store_const',const=False,help='verbose? [%(default)s]')
parser.add_argument('--fout',type=str,help='name of output file')
args = parser.parse_args()
print('Arguments passed')
print(args)
print('')

if len(args.cfgs) not in [1,3]:
    print('improper usage!')
    os.system(c51.python+' '+sys.argv[0]+' -h')
    sys.exit(-1)
ni = int(args.cfgs[0])
if len(args.cfgs) == 3:
    nf = int(args.cfgs[1])
    dn = int(args.cfgs[2])
else:
    nf = ni; dn = ni;
if ni > nf:
    print('improper usage:')
    os.system(c51.python+' '+sys.argv[0]+' -h')
    sys.exit(-1)

cfgs = range(ni,nf+1,dn)

ens,stream = c51.ens_base()
ens_s = ens+'_'+stream

area51 = importlib.import_module(ens)
params = area51.params


params['machine'] = c51.machine
params['ENS_LONG'] = c51.ens_long[ens]
params['ENS_S']    = ens_s
params['STREAM']   = stream
params['METAQ_PROJECT'] = 'strange_charm_loops_'+ens_s
params['PROJECT']=params['METAQ_PROJECT']

params = area51.mpirun_params(c51.machine)


phys_ensList={'a15':'a15m135XL','a12':'a12m135XL','a09':'a09m135XL'}
phys_ens=phys_ensList[ens.split('m')[0]]
ms_phys='0.'+c51.ens_long[phys_ens].split('m')[-2]
mc_phys='0.'+c51.ens_long[phys_ens].split('m')[-1]

hisq_name=c51.names['strange_charm_loops']+'.stdout'
hisq_name_ini=hisq_name.replace('.stdout','.ini')

seedDict={}

masses={'strange':ms_phys,'charm':mc_phys}
massesStr={'MS':ms_phys,'MC':mc_phys}
params.update(massesStr)

good,bad=[],[]

#pbp_tslice = {i:[] for i in masses}
#pbp = {i:[] for i in masses}
badFiles=[]


shapes={m:None for m in masses}
shapes['charm']=(params['NT'],params['NPBP_REPS_C'],2)
shapes['strange']=(params['NT'],params['NPBP_REPS_S'],2)

naikVals=[]
masses=[]

tslice,tsum = {},{}
Allmasses_naikVals=[]
for cfg in cfgs:
    masses,naikVals=[],[]
    params['CFG']=str(cfg)

    params=c51.ensemble(params)

    if os.path.exists(params['stdout']+'/'+hisq_name%params) and os.path.exists(params['xml']+'/'+hisq_name_ini%params):
        infile=open(params['xml']+'/'+hisq_name_ini%params)
        stdfile=open(params['stdout']+'/'+hisq_name%params)

        hisq_in_file=infile.read()
        stdText=stdfile.read()

        if 'RUNNING COMPLETED' in stdText:
            temp=stdText.split('Time to reload gauge configuration ')[0].split('\n')

            try:
                dataSets,set_npbp=getLoopDataTextFromFile(params['stdout']+'/'+hisq_name%params)
                seedDict[str(cfg)]=hisq_in_file.split('iseed ')[1].split('\n')[0]
                data,dataSum=getLoopData(dataSets,int(params['NT'])) 
             
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
                print(params['stdout']+'/'+hisq_name%params+ ' is a bad file')
                badFiles.append(params['stdout']+'/'+hisq_name%params)
        else:
            print(params['stdout']+'/'+hisq_name%params+ ' did not finished running')
            badFiles.append(params['stdout']+'/'+hisq_name%params)

        infile.close()
        stdfile.close()
    else:
        print(params['stdout']+'/'+hisq_name%params + ' does not exists')
        bad.append(int(cfg))
    for u,v in zip(masses,naikVals):
        if [u,v] not in Allmasses_naikVals:
            Allmasses_naikVals.append([u,v])

if args.fout is None:
	out_name='loops_avgdata_%(ENS_S)s_ms%(MS)s_n%(NPBP_REPS_S)s_mc%(MC)s_n%(NPBP_REPS_C)s_collected.h5'
else:
        out_name=args.fout

f=h5.File(params['prod']+'/'+out_name%params,'a')


good=[int(i) for i in good]
indsCfgsOrd=np.array(good).argsort()
print('collected cfgs:',np.array(good)[indsCfgsOrd])

for k in Allmasses_naikVals:
    j,n=k[0],k[1]
    nodeStr='mq'

    if  massesStr['MS']==j:
        nodeStr='ms'
    if  massesStr['MC']==j: 
        nodeStr='mc'  

    f['/'+nodeStr+'_'+j+'/naik_'+n+'/pbp_tslice']=np.array(tslice[j][n])[tuple([indsCfgsOrd])]
    f['/'+nodeStr+'_'+j+'/naik_'+n+'/pbp']=np.array(tsum[j][n])[tuple([indsCfgsOrd])]
f['/cfgs']=np.array(good)[tuple([indsCfgsOrd])]

seeds=[]
for cfg in np.array(good)[tuple([indsCfgsOrd])]:
	seeds.append(int(seedDict[str(cfg)]))

f['/seeds']=np.array(seeds)

#Write list of bad files to delete

out_bad='loops_badfiles_%(ENS_S)s_ms%(MS)s_n%(NPBP_REPS_S)s_mc%(MC)s_n%(NPBP_REPS_C)s.txt'%params
fbad=open(out_bad,'w')

for x in badFiles:
    fbad.write(x+'\n')
fbad.close()
