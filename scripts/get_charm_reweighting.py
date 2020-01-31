#Compute reweighting factors
import numpy as np
import h5py as h5
import os

ensembles=['a12m130_a','a12m180L_a','a12m180L_b','a12m180L_c','a12m180L_d','a12m180L_e','a09m220_a',\
           'a12m220XL_a','a12m220L_a','a12m220_a','a12m220S_a','a15m220XL_a','a15m220_a','a09m260_a',\
           'a12m260_a','a09m310_e','a12m310XL_a','a12m310L_a','a12m310_a','a15m310XL_a',\
           'a15m260_a','a15m310L_a','a15m310_a','a15m350_a','a15m400_a','a09m350_a','a12m350_a',\
           'a09m400_a','a12m400_a']


ensembles=['a12m130_a','a12m180L_a','a12m180L_b','a12m180L_c','a12m180L_d','a12m180L_e','a09m220_a',\
           'a12m220L_a','a12m220_a','a12m220S_a','a15m220XL_a','a15m220_a','a09m260_a',\
           'a12m260_a','a09m310_e','a12m310L_a','a12m310_a',\
           'a15m260_a','a15m310L_a','a15m310_a','a15m350_a','a15m400_a','a09m350_a','a12m350_a',\
           'a09m400_a','a12m400_a']

files={}
mcs={'a09':'0.4313','a12':'0.6382','a15':'0.8447'}
mss={'a09':'0.03636','a12':'0.05252','a15':'0.06730'}
cnpbp=float(256)
snpbp=64
fstring='loops_avgdata_%(ENS)s_ms%(MS)s_n%(SNPBP)s_mc%(MC)s_n%(CNPBP)s.h5'

mc,ms={ens:None for ens in ensembles},{ens:None for ens in ensembles}

mc={'a12m130_a':'0.628','a12m180L_a':'0.628','a12m180L_b':'0.628','a12m180L_c':'0.628','a12m180L_d':'0.628',
'a12m180L_e':'0.628','a12m220L_a':'0.628','a12m220_a':'0.628','a12m220S_a':'0.628','a15m220XL_a':'0.828',
'a15m220_a':'0.828','a09m260_a':'0.430','a12m260_a':'0.628','a15m260_a':'0.828','a09m310_e':'0.440','a12m310L_a':'0.635',
'a12m310_a':'0.635','a15m260_a':'0.828','a15m310L_a':'0.838','a15m310_a':'0.838','a15m350_a':'0.838','a15m400_a':'0.838',
'a09m350_a':'0.440','a12m350_a':'0.635','a12m400_a':'0.635','a09m400_a':'0.440','a09m220_a':'0.430'}


path='/p/gpfs1/walkloud/c51/x_files/project_2/production/'
fout=h5.File('charm_reweighting_factors.h5')

for ens in ensembles:
	#fname=fstring%{'ENS':ens,'MC':mc[ens],'MS':ms[ens],'SNPBP':snpbp,'CNPBP':cnpbp}
        fname=fstring%{'ENS':ens,'MC':mcs[ens.split('m')[0]],'MS':mss[ens.split('m')[0]],'SNPBP':snpbp,'CNPBP':int(cnpbp)}
	if  os.path.exists(path+ens+'/'+fname):
		#print path+ens+'/'+fname
		f=h5.File(path+ens+'/'+fname)
		cfgs,seeds=f['cfgs'][()],f['seeds'][()]
		#print 
		for naik in f['mc_'+mcs[ens.split('m')[0]]]:
		#	#loop shape [Ncfg,npbp,NT,VAL]
			loop=f['mc_'+mcs[ens.split('m')[0]]+'/'+naik+'/pbp_tslice'][()]
			ens_mc=mc[ens]
			dm=float(mcs[ens.split('m')[0]])-float(ens_mc)
			#print dm
			temp=np.exp(0.25*dm*loop)/cnpbp	
			fout[ens+'/'+naik]=temp.sum(axis=1)
		










































