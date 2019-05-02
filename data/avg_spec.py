import os
import numpy as np
import tables as h5
from glob import glob
import sys
import random

def time_reverse(corr,phase=1,time_axis=1):
    '''
    Performe time-reversal of correlation function accounting for BC in time
    phase     = +1 or -1
    time_axis = time_axis in array
    '''
    if len(corr.shape) > 1:
        if time_axis in [0,1]:
            #cr = phase * np.roll(corr[:,::-1],1,axis=time_axis)
            cr = phase * np.roll(np.flip(corr,axis=time_axis),1,axis=time_axis)
            if time_axis == 0:
                cr[0] = phase * cr[0]
            elif time_axis == 1:
                cr[:,0] = phase * cr[:,0]
            else:
                pass
        else:
            print('time_axis != 0,1 not supported at the moment')
            sys.exit()
    else:
        cr = phase * np.roll(np.flip(corr,axis=0),1)
        cr[0] = phase * cr[0]
    return cr

def src_split(src):
    x0 = src.split('x')[1].split('y')[0]
    y0 = src.split('y')[1].split('z')[0]
    z0 = src.split('z')[1].split('t')[0]
    t0 = src.split('t')[1]
    return 'x%s_y%s_z%s_t%s' %(x0,y0,z0,t0)

def xyzt(src):
    x = src.split('x')[1].split('y')[0]
    y = src.split('y')[1].split('z')[0]
    z = src.split('z')[1].split('t')[0]
    t = src.split('t')[1]
    return x,y,z,t

mom_lst = []
for px in range(-2,3):
    for py in range(-2,3):
        for pz in range(-2,3):
            if px**2 + py**2 + pz**2 <= 5:
                mom_lst.append('px'+str(px)+'_py'+str(py)+'_pz'+str(pz))

particles = ['proton','proton_np']

files = glob('spec/*.h5')
srcs = []
for f in files:
    srcs.append(f.split('_')[-1].split('.')[0])
random.shuffle(srcs)
print(srcs)
if not os.path.exists('spec_src_avg'):
    os.makedirs('spec_src_avg')
fout = h5.open_file('spec_src_avg/spec_tslice_src_avg_px0py0pz0_Nsnk1_src_avg.h5','w')
for particle in particles:
    for mom in mom_lst:
        print(particle,mom)
        data = []
        for src in srcs:
            x0,y0,z0,t0 = xyzt(src)
            fin = h5.open_file('spec/spec_px0py0pz0_Nsnk1_'+src+'.h5','r')
            for spin in ['spin_up','spin_dn']:
                h5_path = '/pt/spec/'+particle+'/'+spin+'/'+src_split(src)+'/'+mom
                src_data = fin.get_node(h5_path).read()
                data.append(src_data)
            fin.close()
            #src_data = np.roll(src_data,-int(t0))
        data = np.array(data)
        data_avg = data.mean(axis=0)
        if '_np' in particle:
            print('    time_reversing')
            print('        spec needs time flip')
            data_avg = time_reverse(data_avg,phase=-1,time_axis=0)
        data_slice = data_avg[0:5]
        h5_avg_path = '/pt/spec/'+particle+'/spin_avg'
        fout.create_group(h5_avg_path,mom,createparents=True)
        fout.create_array(h5_avg_path+'/'+mom,'src_avg',data_slice)
        fout.flush()
fout.close()
