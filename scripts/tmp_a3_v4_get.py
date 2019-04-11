import numpy as np
import tables as h5
import sys

ens_s = sys.argv[1]

t_seps = [3,4,5,6,7,8,9,10]

f_out = h5.open_file('tmp_a3_v4.h5','a')
f_in  = h5.open_file('/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/'+ens_s+'/ff4D_data/avg/formfac_'+ens_s+'_avg.h5','r')

try:
    f_out.create_group('/'+ens_s,'A3',createparents=True)
    f_out.create_group('/'+ens_s,'V4',createparents=True)
except:
    pass
path = '/gf1p0_w3p0_n30_M51p3_L512_a1p5/formfac_4D/ml0p0158/%(CORR)s_%(FS)s_tsep_%(DT)s_sink_mom_px0_py0_pz0/%(CURR)s/local_current'
for dt in t_seps:
    tmp_path = path % {'CORR':'proton','FS':'UU_up_up','DT':dt,'CURR':'A3'}
    if tmp_path in f_in.get_node('/'):
        print(ens_s,'A3',dt)
        # get pos parity
        a3  = f_in.get_node(path % {'CORR':'proton','FS':'UU_up_up','DT':dt,'CURR':'A3'}).read()
        a3 -= f_in.get_node(path % {'CORR':'proton','FS':'UU_dn_dn','DT':dt,'CURR':'A3'}).read()
        a3 -= f_in.get_node(path % {'CORR':'proton','FS':'DD_up_up','DT':dt,'CURR':'A3'}).read()
        a3 += f_in.get_node(path % {'CORR':'proton','FS':'DD_dn_dn','DT':dt,'CURR':'A3'}).read()
        # get neg parity
        a3 += f_in.get_node(path % {'CORR':'proton_np','FS':'UU_up_up','DT':-dt,'CURR':'A3'}).read()
        a3 -= f_in.get_node(path % {'CORR':'proton_np','FS':'UU_dn_dn','DT':-dt,'CURR':'A3'}).read()
        a3 -= f_in.get_node(path % {'CORR':'proton_np','FS':'DD_up_up','DT':-dt,'CURR':'A3'}).read()
        a3 += f_in.get_node(path % {'CORR':'proton_np','FS':'DD_dn_dn','DT':-dt,'CURR':'A3'}).read()
        a3 = np.sum(a3,axis=4)
        a3 = np.sum(a3,axis=3)
        a3 = np.sum(a3,axis=2)
        a3 = 0.5 * a3
        f_out.create_array('/'+ens_s+'/A3','tsep_'+str(dt),a3)
        print(a3.shape)
        f_out.flush()

        print(ens_s,'V4',dt)
        # get pos parity
        v4  = f_in.get_node(path % {'CORR':'proton','FS':'UU_up_up','DT':dt,'CURR':'V4'}).read()
        v4 += f_in.get_node(path % {'CORR':'proton','FS':'UU_dn_dn','DT':dt,'CURR':'V4'}).read()
        v4 -= f_in.get_node(path % {'CORR':'proton','FS':'DD_up_up','DT':dt,'CURR':'V4'}).read()
        v4 -= f_in.get_node(path % {'CORR':'proton','FS':'DD_dn_dn','DT':dt,'CURR':'V4'}).read()
        # get neg parity
        v4 += f_in.get_node(path % {'CORR':'proton_np','FS':'UU_up_up','DT':-dt,'CURR':'V4'}).read()
        v4 += f_in.get_node(path % {'CORR':'proton_np','FS':'UU_dn_dn','DT':-dt,'CURR':'V4'}).read()
        v4 -= f_in.get_node(path % {'CORR':'proton_np','FS':'DD_up_up','DT':-dt,'CURR':'V4'}).read()
        v4 -= f_in.get_node(path % {'CORR':'proton_np','FS':'DD_dn_dn','DT':-dt,'CURR':'V4'}).read()
        v4 = np.sum(v4,axis=4)
        v4 = np.sum(v4,axis=3)
        v4 = np.sum(v4,axis=2)
        v4 = 0.5 * v4
        f_out.create_array('/'+ens_s+'/V4','tsep_'+str(dt),v4)
        print(v4.shape)
        f_out.flush()

f_in.close()
f_out.close()
