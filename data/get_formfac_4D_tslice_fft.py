import os
import numpy as np
import tables as h5
from glob import glob
import sys
import random

mom_lst = []
for px in range(-2,3):
    for py in range(-2,3):
        for pz in range(-2,3):
            if px**2 + py**2 + pz**2 <= 5:
                mom_lst.append('px'+str(px)+'_py'+str(py)+'_pz'+str(pz))

particles = ['proton','proton_np']
flav_spin = ['UU_up_up','UU_dn_dn','DD_up_up','DD_dn_dn']
currents  = ['A3','V4','P','S','T34']
tseps     = [3,4,5]

f_tslice = h5.open_file('formfac_4D_tslice_src_avg/formfac_4D_tslice_src_avg_px0py0pz0_Nsnk1_src_avg_fft.h5','r')
fout = h5.open_file('formfac_src_avg/formfac_FROM_tslice_src_avg_px0py0pz0_Nsnk1_src_avg.h5','w')
for particle in particles:
    for fs in flav_spin:
        for curr in currents:
            for tsep in tseps:
                dt = str(tsep)
                if '_np' in particle:
                    dt = '-'+dt
                h5_path = '/pt/formfac/'+particle+'_'+fs+'_tsep_'+dt+'_sink_mom_px0_py0_pz0/'+curr+'/src_avg/4D_correlator/momentum_current'
                tslice_data = f_tslice.get_node(h5_path).read()
                for mom in mom_lst:
                    px = int(mom.split('_')[0].split('px')[1])
                    py = int(mom.split('_')[1].split('py')[1])
                    pz = int(mom.split('pz')[1])
                    print(particle,fs,curr,tsep,pz,py,px)
                    data = tslice_data[:,pz,py,px]

                    h5_avg_path = '/pt/formfac/'+particle+'_'+fs+'_tsep_'+dt+'_sink_mom_px0_py0_pz0/'+curr+'/src_avg'
                    fout.create_group(h5_avg_path,mom,createparents=True)
                    fout.create_array(h5_avg_path+'/'+mom,'local_current',data)
                    fout.flush()
fout.close()
f_tslice.close()
