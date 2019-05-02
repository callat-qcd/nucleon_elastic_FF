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

f_tslice = h5.open_file('spec_4D_tslice_avg/spec_4D_tslice_avg_px0py0pz0_Nsnk1_src_avg_fft.h5','r')
fout = h5.open_file('spec_src_avg/spec_FROM_tslice_src_avg_px0py0pz0_Nsnk1_src_avg.h5','w')
for particle in particles:
    h5_path = '/pt/spec/'+particle+'/spin_avg/4D_correlator/src_avg'
    tslice_data = f_tslice.get_node(h5_path).read()
    for mom in mom_lst:
        px = int(mom.split('_')[0].split('px')[1])
        py = int(mom.split('_')[1].split('py')[1])
        pz = int(mom.split('pz')[1])
        print(particle,pz,py,px)
        data = tslice_data[:,pz,py,px]

        h5_avg_path = '/pt/spec/'+particle+'/spin_avg'
        fout.create_group(h5_avg_path,mom,createparents=True)
        fout.create_array(h5_avg_path+'/'+mom,'src_avg',data)
        fout.flush()
fout.close()
f_tslice.close()
