import sys
import tables as h5
import numpy as np
from glob import glob

#tsep = '10'

def src_split(src):
    x0 = src.split('x')[1].split('y')[0]
    y0 = src.split('y')[1].split('z')[0]
    z0 = src.split('z')[1].split('t')[0]
    t0 = src.split('t')[1]
    return 'x%s_y%s_z%s_t%s' %(x0,y0,z0,t0)
def time_reverse(corr,phase=1,time_axis=1):
    ''' assumes time index is second of array '''
    ''' assumes phase = +- 1 '''
    if len(corr.shape) > 1:
        cr = phase * np.roll(corr[:,::-1],1,axis=time_axis)
        cr[:,0] = phase * cr[:,0]
    else:
        cr = phase * np.roll(corr[::-1],1)
        cr[0] = phase * cr[0]
    return cr
h5_out = h5.open_file('avg_a3_v4_spin.h5','a')
#for dt in [3]:#,4,5,6,7,8,9,10,11,12,13,14]:
for dt in [4,5,6,7,8,9,10,11,12,13,14]:
    tsep = str(dt)
    a3_u = []
    v4_u = []
    a3_u_np = []
    v4_u_np = []
    a3_d = []
    v4_d = []
    a3_d_np = []
    v4_d_np = []
    for cfg in range(300,4999,6):
        no = str(cfg)
        a3_u_tmp = []
        v4_u_tmp = []
        a3_u_np_tmp = []
        v4_u_np_tmp = []
        a3_d_tmp = []
        v4_d_tmp = []
        a3_d_np_tmp = []
        v4_d_np_tmp = []
        for src in glob('/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/a09m310_e/formfac/'+no+'/formfac_*dt'+tsep+'_*.h5'):
            s0 = src.split('_')[-2]
            print(dt,no,s0)
            t0 = s0.split('t')[1]
            src_h5 = h5.open_file(src,'r')
            root = '/proton_%(FS)s_t0_'+t0+'_tsep_'+tsep+'_sink_mom_px0_py0_pz0/%(CURR)s/%(SRC)s/px0_py0_pz0/local_current'
            a3_data  = src_h5.get_node(root % {'FS':'UU_up_up','CURR':'A3','SRC':src_split(s0)}).read()
            a3_data -= src_h5.get_node(root % {'FS':'DD_up_up','CURR':'A3','SRC':src_split(s0)}).read()
            v4_data  = src_h5.get_node(root % {'FS':'UU_up_up','CURR':'V4','SRC':src_split(s0)}).read()
            v4_data -= src_h5.get_node(root % {'FS':'DD_up_up','CURR':'V4','SRC':src_split(s0)}).read()
            a3_u_tmp.append(a3_data)
            v4_u_tmp.append(v4_data)        

            a3_data  = src_h5.get_node(root % {'FS':'UU_dn_dn','CURR':'A3','SRC':src_split(s0)}).read()
            a3_data -= src_h5.get_node(root % {'FS':'DD_dn_dn','CURR':'A3','SRC':src_split(s0)}).read()
            v4_data  = src_h5.get_node(root % {'FS':'UU_dn_dn','CURR':'V4','SRC':src_split(s0)}).read()
            v4_data -= src_h5.get_node(root % {'FS':'DD_dn_dn','CURR':'V4','SRC':src_split(s0)}).read()
            a3_d_tmp.append(a3_data)
            v4_d_tmp.append(v4_data)        

            root = '/proton_np_%(FS)s_t0_'+t0+'_tsep_-'+tsep+'_sink_mom_px0_py0_pz0/%(CURR)s/%(SRC)s/px0_py0_pz0/local_current'
            a3_data  = time_reverse(src_h5.get_node(root % {'FS':'UU_up_up','CURR':'A3','SRC':src_split(s0)}).read(),phase=-1)
            a3_data -= time_reverse(src_h5.get_node(root % {'FS':'DD_up_up','CURR':'A3','SRC':src_split(s0)}).read(),phase=-1)
            v4_data  = time_reverse(src_h5.get_node(root % {'FS':'UU_up_up','CURR':'V4','SRC':src_split(s0)}).read(),phase=-1)
            v4_data -= time_reverse(src_h5.get_node(root % {'FS':'DD_up_up','CURR':'V4','SRC':src_split(s0)}).read(),phase=-1)
            a3_u_np_tmp.append(a3_data)
            v4_u_np_tmp.append(v4_data)        

            a3_data  = time_reverse(src_h5.get_node(root % {'FS':'UU_dn_dn','CURR':'A3','SRC':src_split(s0)}).read(),phase=-1)
            a3_data -= time_reverse(src_h5.get_node(root % {'FS':'DD_dn_dn','CURR':'A3','SRC':src_split(s0)}).read(),phase=-1)
            v4_data  = time_reverse(src_h5.get_node(root % {'FS':'UU_dn_dn','CURR':'V4','SRC':src_split(s0)}).read(),phase=-1)
            v4_data -= time_reverse(src_h5.get_node(root % {'FS':'DD_dn_dn','CURR':'V4','SRC':src_split(s0)}).read(),phase=-1)
            a3_d_np_tmp.append(a3_data)
            v4_d_np_tmp.append(v4_data)        

            src_h5.close()
        #print(np.array(a3_tmp).shape)
        #print(np.mean(np.array(a3_tmp),axis=0).shape)
        a3_u.append(np.mean(np.array(a3_u_tmp),axis=0))
        v4_u.append(np.mean(np.array(v4_u_tmp),axis=0))
        a3_u_np.append(np.mean(np.array(a3_u_np_tmp),axis=0))
        v4_u_np.append(np.mean(np.array(v4_u_np_tmp),axis=0))
        a3_d.append(np.mean(np.array(a3_d_tmp),axis=0))
        v4_d.append(np.mean(np.array(v4_d_tmp),axis=0))
        a3_d_np.append(np.mean(np.array(a3_d_np_tmp),axis=0))
        v4_d_np.append(np.mean(np.array(v4_d_np_tmp),axis=0))
    a3_u = np.array(a3_u)
    v4_u = np.array(v4_u)
    a3_u_np = np.array(a3_u_np)
    v4_u_np = np.array(v4_u_np)
    a3_d = np.array(a3_d)
    v4_d = np.array(v4_d)
    a3_d_np = np.array(a3_d_np)
    v4_d_np = np.array(v4_d_np)

    h5_out.create_group('/','tsep_'+tsep)
    h5_out.create_array('/tsep_'+tsep,'a3_u_pp',    np.imag(a3_u)        )
    h5_out.create_array('/tsep_'+tsep,'v4_u_pp',    np.real(v4_u)        )
    h5_out.create_array('/tsep_'+tsep,'a3_u_np',    np.imag(a3_u_np)     )
    h5_out.create_array('/tsep_'+tsep,'v4_u_np',    np.real(v4_u_np)     )
    h5_out.create_array('/tsep_'+tsep,'a3_d_pp',    np.imag(a3_d)        )
    h5_out.create_array('/tsep_'+tsep,'v4_d_pp',    np.real(v4_d)        )
    h5_out.create_array('/tsep_'+tsep,'a3_d_np',    np.imag(a3_d_np)     )
    h5_out.create_array('/tsep_'+tsep,'v4_d_np',    np.real(v4_d_np)     )
    
    h5_out.flush()
h5_out.close()
