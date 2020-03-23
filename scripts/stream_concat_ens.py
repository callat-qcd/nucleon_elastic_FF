import tables as h5
import numpy as np
import sys

ens = sys.argv[1]
data_dir = sys.argv[2]

cs_offset = {
    'a06m310L':10000,
    'a09m135' :4000,
}
srcs = {
    'a06m310L':'0-7',
    'a09m135' :'0-15',
}
n_s = int(srcs[ens].split('-')[1]) + 1
streams = {
    'a06m310L':['b','c'],
    'a09m135' :['a','b'],
}
val = {
    'a06m310L':'gf1p0_w3p5_n45_M51p0_L56_a1p5',
    'a09m135' :'gf1p0_w3p5_n45_M51p1_L512_a2p0',
}
dwf_jmu = {
    'a06m310L':['mq0p00617','mq0p0309'],
    'a09m135' :['mq0p00152','mq0p04735'],
}
phi_qq = dwf_jmu
spec = {
    'a06m310L':'ml0p00617',
    'a09m135' :'ml0p00152',
}
hspec = {
    'a06m310L':'ml0p00617_ms0p0309',
    'a09m135' :'ml0p00152_ms0p04735',
}
mspec = {
    'a06m310L':'val_ml0p00617_ms0p0309_sea_ml0p0048_ms0p024',
    'a09m135' :'val_ml0p00152_ms0p04735_sea_ml0p001326_ms0p03636',
}

octet = ['proton','lambda_z','sigma_p','xi_z']
decuplet = ['delta_pp','omega_m','sigma_star_p','xi_star_z']
phi_mixed = {
    'phi_ju':['phi_ju','phi_uj'],
    'phi_js':['phi_js','phi_sj'],
    'phi_ru':['phi_ru','phi_ur'],
    'phi_rs':['phi_rs','phi_sr']
    }


f_out = h5.open_file(ens+'_s_avg_srcs'+srcs[ens]+'.h5','w')

# dwf_jmu
print('dwf_jmu')
for mq in dwf_jmu[ens]:
    print(mq)
    for i_s,s in enumerate(streams[ens]):
        f_in = h5.open_file(ens+'_'+s+'/'+data_dir+'/avg/'+ens+'_'+s+'_avg_srcs'+srcs[ens]+'.h5')
        if s == streams[ens][0]:
            mp = f_in.get_node('/'+val[ens]+'/dwf_jmu/'+mq+'/midpoint_pseudo').read()
            pp = f_in.get_node('/'+val[ens]+'/dwf_jmu/'+mq+'/pseudo_pseudo').read()
            cs = f_in.get_node('/'+val[ens]+'/dwf_jmu/'+mq+'/cfgs_srcs').read()
        else:
            tmp_mp = f_in.get_node('/'+val[ens]+'/dwf_jmu/'+mq+'/midpoint_pseudo').read()
            tmp_pp = f_in.get_node('/'+val[ens]+'/dwf_jmu/'+mq+'/pseudo_pseudo').read()
            tmp_cs = f_in.get_node('/'+val[ens]+'/dwf_jmu/'+mq+'/cfgs_srcs').read()
            tmp_cs[:,0] += i_s * cs_offset[ens]
            mp = np.concatenate((mp,tmp_mp),axis=0)
            pp = np.concatenate((pp,tmp_pp),axis=0)
            cs = np.concatenate((cs,tmp_cs),axis=0)
        f_in.close()
    cs[:,1] = n_s
    f_out.create_array('/'+val[ens]+'/dwf_jmu/'+mq,'midpoint_pseudo',mp,createparents=True)
    f_out.create_array('/'+val[ens]+'/dwf_jmu/'+mq,'pseudo_pseudo',  pp,createparents=True)
    f_out.create_array('/'+val[ens]+'/dwf_jmu/'+mq,'cfgs_srcs',      cs,createparents=True)
    f_out.flush()
print('phi_qq')
for mq in dwf_jmu[ens]:
    print(mq)
    for i_s,s in enumerate(streams[ens]):
        f_in = h5.open_file(ens+'_'+s+'/'+data_dir+'/avg/'+ens+'_'+s+'_avg_srcs'+srcs[ens]+'.h5')
        if s == streams[ens][0]:
            phi = f_in.get_node('/'+val[ens]+'/phi_qq/'+mq+'/corr').read()
            cs  = f_in.get_node('/'+val[ens]+'/phi_qq/'+mq+'/cfgs_srcs').read()
        else:
            tmp_phi = f_in.get_node('/'+val[ens]+'/phi_qq/'+mq+'/corr').read()
            tmp_cs  = f_in.get_node('/'+val[ens]+'/phi_qq/'+mq+'/cfgs_srcs').read()
            tmp_cs[:,0] += i_s * cs_offset[ens]
            phi = np.concatenate((phi,tmp_mp),axis=0)
            cs  = np.concatenate((cs,tmp_cs),axis=0)
        f_in.close()
    cs[:,1] = n_s
    f_out.create_array('/'+val[ens]+'/phi_qq/'+mq,'corr',     phi,createparents=True)
    f_out.create_array('/'+val[ens]+'/phi_qq/'+mq,'cfgs_srcs',cs, createparents=True)
    f_out.flush()
# spec
print('spec')
for corr in ['piplus','kplus','kminus']:
    print(corr)
    for i_s,s in enumerate(streams[ens]):
        f_in = h5.open_file(ens+'_'+s+'/'+data_dir+'/avg/'+ens+'_'+s+'_avg_srcs'+srcs[ens]+'.h5')
        if s == streams[ens][0]:
            data = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+'/px0_py0_pz0/corr').read()
            cs   = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+'/px0_py0_pz0/cfgs_srcs').read()
        else:
            tmp_data = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+'/px0_py0_pz0/corr').read()
            tmp_cs   = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+'/px0_py0_pz0/cfgs_srcs').read()
            tmp_cs[:,0] += i_s * cs_offset[ens]
            data = np.concatenate((data,tmp_data),axis=0)
            cs   = np.concatenate((cs,tmp_cs),axis=0)
        f_in.close()
    cs[:,1] = n_s
    f_out.create_array('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr,'corr',     data,createparents=True)
    f_out.create_array('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr,'cfgs_srcs',cs)
    f_out.flush()
for corr in ['piplus']:
    print(corr)
    for i_s,s in enumerate(streams[ens]):
        f_in = h5.open_file(ens+'_'+s+'/'+data_dir+'/avg/'+ens+'_'+s+'_avg_srcs'+srcs[ens]+'.h5')
        if s == streams[ens][0]:
            data = f_in.get_node('/'+val[ens]+'/spec/'+spec[ens]+'/'+corr+'/px0_py0_pz0/corr').read()
            cs   = f_in.get_node('/'+val[ens]+'/spec/'+spec[ens]+'/'+corr+'/px0_py0_pz0/cfgs_srcs').read()
        else:
            tmp_data = f_in.get_node('/'+val[ens]+'/spec/'+spec[ens]+'/'+corr+'/px0_py0_pz0/corr').read()
            tmp_cs   = f_in.get_node('/'+val[ens]+'/spec/'+spec[ens]+'/'+corr+'/px0_py0_pz0/cfgs_srcs').read()
            tmp_cs[:,0] += i_s * cs_offset[ens]
            data = np.concatenate((data,tmp_data),axis=0)
            cs   = np.concatenate((cs,tmp_cs),axis=0)
        f_in.close()
    cs[:,1] = n_s
    f_out.create_array('/'+val[ens]+'/spec/'+spec[ens]+'/'+corr,'corr',     data,createparents=True)
    f_out.create_array('/'+val[ens]+'/spec/'+spec[ens]+'/'+corr,'cfgs_srcs',cs)
    f_out.flush()
for corr in ['proton']:
    for parity in ['','_np']:
        print(corr,parity)
        for i_s,s in enumerate(streams[ens]):
            f_in = h5.open_file(ens+'_'+s+'/'+data_dir+'/avg/'+ens+'_'+s+'_avg_srcs'+srcs[ens]+'.h5')
            if s == streams[ens][0]:
                su = f_in.get_node('/'+val[ens]+'/spec/'+spec[ens]+'/'+corr+parity+'/px0_py0_pz0/spin_up').read()
                sd = f_in.get_node('/'+val[ens]+'/spec/'+spec[ens]+'/'+corr+parity+'/px0_py0_pz0/spin_dn').read()
                cs = f_in.get_node('/'+val[ens]+'/spec/'+spec[ens]+'/'+corr+parity+'/px0_py0_pz0/cfgs_srcs').read()
            else:
                tmp_su = f_in.get_node('/'+val[ens]+'/spec/'+spec[ens]+'/'+corr+parity+'/px0_py0_pz0/spin_up').read()
                tmp_sd = f_in.get_node('/'+val[ens]+'/spec/'+spec[ens]+'/'+corr+parity+'/px0_py0_pz0/spin_dn').read()
                tmp_cs = f_in.get_node('/'+val[ens]+'/spec/'+spec[ens]+'/'+corr+parity+'/px0_py0_pz0/cfgs_srcs').read()
                tmp_cs[:,0] += i_s * cs_offset[ens]
                su = np.concatenate((su,tmp_su),axis=0)
                sd = np.concatenate((sd,tmp_sd),axis=0)
                cs = np.concatenate((cs,tmp_cs),axis=0)
            f_in.close()
        cs[:,1] = n_s
        f_out.create_array('/'+val[ens]+'/spec/'+spec[ens]+'/'+corr+parity+'/px0_py0_pz0','spin_up',su,createparents=True)
        f_out.create_array('/'+val[ens]+'/spec/'+spec[ens]+'/'+corr+parity+'/px0_py0_pz0','spin_dn',sd)
        f_out.create_array('/'+val[ens]+'/spec/'+spec[ens]+'/'+corr+parity+'/px0_py0_pz0','cfgs_srcs',cs)
        f_out.flush()
for corr in octet:
    for parity in ['','_np']:
        print(corr,parity)
        for i_s,s in enumerate(streams[ens]):
            f_in = h5.open_file(ens+'_'+s+'/'+data_dir+'/avg/'+ens+'_'+s+'_avg_srcs'+srcs[ens]+'.h5')
            if s == streams[ens][0]:
                su = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0/spin_up').read()
                sd = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0/spin_dn').read()
                cs = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0/cfgs_srcs').read()
            else:
                tmp_su = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0/spin_up').read()
                tmp_sd = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0/spin_dn').read()
                tmp_cs = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0/cfgs_srcs').read()
                tmp_cs[:,0] += i_s * cs_offset[ens]
                su = np.concatenate((su,tmp_su),axis=0)
                sd = np.concatenate((sd,tmp_sd),axis=0)
                cs = np.concatenate((cs,tmp_cs),axis=0)
            f_in.close()
        cs[:,1] = n_s
        f_out.create_array('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0','spin_up',su,createparents=True)
        f_out.create_array('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0','spin_dn',sd)
        f_out.create_array('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0','cfgs_srcs',cs)
        f_out.flush()
for corr in decuplet:
    for parity in ['','_np']:
        print(corr,parity)
        for i_s,s in enumerate(streams[ens]):
            f_in = h5.open_file(ens+'_'+s+'/'+data_dir+'/avg/'+ens+'_'+s+'_avg_srcs'+srcs[ens]+'.h5')
            if s == streams[ens][0]:
                suu = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0/spin_upup').read()
                su  = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0/spin_up').read()
                sd  = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0/spin_dn').read()
                sdd = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0/spin_dndn').read()
                cs = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0/cfgs_srcs').read()
            else:
                tmp_suu = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0/spin_upup').read()
                tmp_su  = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0/spin_up').read()
                tmp_sd  = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0/spin_dn').read()
                tmp_sdd = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0/spin_dndn').read()
                tmp_cs = f_in.get_node('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0/cfgs_srcs').read()
                tmp_cs[:,0] += i_s * cs_offset[ens]
                suu = np.concatenate((suu,tmp_suu),axis=0)
                su  = np.concatenate((su, tmp_su), axis=0)
                sd  = np.concatenate((sd, tmp_sd), axis=0)
                sdf = np.concatenate((sdd,tmp_sdd),axis=0)
                cs = np.concatenate((cs,tmp_cs),axis=0)
            f_in.close()
        cs[:,1] = n_s
        f_out.create_array('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0','spin_upup',suu,createparents=True)
        f_out.create_array('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0','spin_up',  su)
        f_out.create_array('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0','spin_dn',  sd)
        f_out.create_array('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0','spin_dndn',sdd)
        f_out.create_array('/'+val[ens]+'/spec/'+hspec[ens]+'/'+corr+parity+'/px0_py0_pz0','cfgs_srcs',cs)
        f_out.flush()
# mixed spec
for phi in phi_mixed:
    print(phi)
    for i_s,s in enumerate(streams[ens]):
        f_in = h5.open_file(ens+'_'+s+'/'+data_dir+'/avg/mixed_'+ens+'_'+s+'_avg.h5','r')
        if s == streams[ens][0]:
            d0 = f_in.get_node('/'+val[ens]+'/mixed_spec/'+mspec[ens]+'/'+phi_mixed[phi][0]+'/corr').read()
            d1 = f_in.get_node('/'+val[ens]+'/mixed_spec/'+mspec[ens]+'/'+phi_mixed[phi][1]+'/corr').read()
            cs = f_in.get_node('/'+val[ens]+'/mixed_spec/'+mspec[ens]+'/'+phi_mixed[phi][0]+'/cfgs_srcs').read()
            d  = 0.5*(d0 + d1)
            #d  = d0
        else:
            tmp0   = f_in.get_node('/'+val[ens]+'/mixed_spec/'+mspec[ens]+'/'+phi_mixed[phi][0]+'/corr').read()
            tmp1   = f_in.get_node('/'+val[ens]+'/mixed_spec/'+mspec[ens]+'/'+phi_mixed[phi][1]+'/corr').read()
            tmp_cs = f_in.get_node('/'+val[ens]+'/mixed_spec/'+mspec[ens]+'/'+phi_mixed[phi][0]+'/cfgs_srcs').read()
            tmp_cs[:,0] += i_s * 1750
            d  = np.concatenate((d, 0.5*(tmp0+tmp1)), axis=0)
            #d  = np.concatenate((d, tmp0), axis=0)
            cs = np.concatenate((cs,tmp_cs),axis=0)
        f_in.close()
    f_out.create_array('/'+val[ens]+'/mixed_spec/'+mspec[ens]+'/'+phi,'corr',d,createparents=True)
    f_out.create_array('/'+val[ens]+'/mixed_spec/'+mspec[ens]+'/'+phi,'cfgs_srcs',cs,createparents=True)
f_out.close()
'''
f_out.close()
'''
