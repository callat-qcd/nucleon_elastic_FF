import numpy as np
import tables as h5
import os, shutil, sys, time

import c51_mdwf_hisq as c51

def get_res_phi(params,h5_dsets,h5_file=None,collect=False):
    overwrite = params['overwrite']
    verbose   = params['verbose']
    no        = params['CFG']
    sub_corrs = ['midpoint_pseudo', 'pseudo_pseudo','phi_qq']
    path_key = {'midpoint_pseudo':'mres_path','pseudo_pseudo':'mres_path','phi_qq':'phi_qq_path'}
    # first check if corrs are in the h5_dsets
    have_corrs = True
    for src in params['srcs']:
        for mq_v in params['MQ_LST']:
            mq = mq_v.replace('.','p')
            for corr in sub_corrs:
                if corr == 'phi_qq':
                    h5_path = params[path_key[corr]]+'/mq'+mq+'/'+src
                else:
                    h5_path = params[path_key[corr]]+'/mq'+mq+'/'+corr+'/'+src
                if h5_path not in h5_dsets:
                    have_corrs = False
                    if params['debug']:
                        print("%7s %s" %(corr,h5_path))
    if params['debug']:
        print('verbose',verbose)
        print('have_corrs',have_corrs)
    if have_corrs and verbose and not overwrite:
        print('res phi %s: all collected' %no)
    # if collect=True, try to collect data
    if (not have_corrs and collect) or (overwrite and collect):
        # loop over srcs and masses
        f5 = h5.open_file(h5_file,'a')
        for src in params['srcs']:
            params['SRC'] = src
            t_src = int(src.split('t')[1])
            for mq_v in params['MQ_LST']:
                params['MQ'] = mq_v
                prop_name = c51.names['prop'] % params
                prop_xml = params['xml'] + '/' + prop_name+'.out.xml'
                mq = params['MQ'].replace('.','p')
                # check if src collected already
                get_data = False
                h5_paths = dict()
                for corr in sub_corrs:
                    if corr == 'phi_qq':
                        h5_paths[corr] = '/'+params[path_key[corr]]+'/mq'+mq
                    else:
                        h5_paths[corr] = '/'+params[path_key[corr]]+'/mq'+mq+'/'+corr
                    try:
                        tmp_path,tmp_group = h5_paths[corr].rsplit('/',1)
                        f5.create_group(tmp_path,tmp_group,createparents=True)
                        f5.flush()
                    except:
                        pass
                    if (src not in f5.get_node(h5_paths[corr])) or (src in f5.get_node(h5_paths[corr]) and overwrite):
                        get_data = True
                if get_data:
                    # check xml file is OK
                    f_good = False
                    if os.path.exists(prop_xml):
                        if os.path.getsize(prop_xml) > 0:
                            with open(prop_xml) as f:
                                data = f.readlines()
                                if data[-1] == '</propagator>':
                                    f_good = True
                                else:
                                    now = time.time()
                                    file_time = os.stat(prop_xml).st_mtime
                                    if (now-file_time)/60 > 180:# time in minutes
                                        if verbose:
                                            print('MOVING BAD FILE:',prop_xml)
                                        shutil.move(prop_xml,params['corrupt']+'/'+prop_xml.split('/')[-1])
                    if f_good:
                        # try to get data
                        dtype = np.float64
                        data = dict()
                        f = open(prop_xml).readlines()
                        have_data  = False
                        have_mres  = False
                        have_phiqq = False
                        l = 0
                        while not have_data:
                            if f[l].find('<DWF_MidPoint_Pseudo>') > 0 and f[l+3].find('<DWF_Psuedo_Pseudo>') > 0:
                                mp = f[l+1].split('<mesprop>')[1].split('</mesprop>')[0].split()
                                pp = f[l+4].split('<mesprop>')[1].split('</mesprop>')[0].split()
                                data['midpoint_pseudo'] = np.array([float(d) for d in mp],dtype=dtype)
                                data['pseudo_pseudo']   = np.array([float(d) for d in pp],dtype=dtype)
                                have_mres = True
                            elif f[l].find('<prop_corr>') > 0:
                                corr = f[l].split('<prop_corr>')[1].split('</prop_corr>')[0].split()
                                phi_qq = np.array([float(d) for d in corr],dtype=dtype)
                                data['phi_qq'] = np.roll(phi_qq,-t_src)
                                have_phiqq = True
                            if have_mres and have_phiqq:
                                have_data = True
                            l += 1
                        good_data = True
                        for corr in sub_corrs:
                            if np.any(np.isnan(data[corr])):
                                good_data = False
                        if good_data:
                            if verbose:
                                print('    mres %3s %s %s' %(no, mq_v, src))
                            for corr in sub_corrs:
                                if src not in f5.get_node(h5_paths[corr]):
                                    f5.create_array(h5_paths[corr],src,data[corr])
                                elif src in f5.get_node(h5_paths[corr]) and overwrite:
                                    f5.get_node(h5_paths[corr]+'/'+src)[:] = data[corr]
                                elif src in f5.get_node(h5_paths[corr]) and not overwrite:
                                    print('        skipping %s: overwrite = False' %corr)
                            f5.flush()
                            have_corrs = True
                        else:
                            print('NAN in data',prop_xml)
                    else:
                        print('bad prop xml file',prop_xml)
        f5.close()            

    return have_corrs

def get_spec(params,h5_dsets,h5_file=None,collect=False,spec='spec'):
    overwrite = params['overwrite']
    verbose   = params['verbose']
    no        = params['CFG']
    if spec == 'spec':
        mesons    = ['piplus']
        octet     = ['proton','proton_np']
        decuplet  = []
    elif spec == 'hyperspec':
        mesons    = ['piplus','kminus','kplus']
        octet     = ['proton','proton_np','lambda_z','lambda_z_np','sigma_p','sigma_p_np','xi_z','xi_z_np']
        decuplet  = ['delta_pp','delta_pp_np','omega_m','omega_m_np','sigma_star_p','sigma_star_p_np','xi_star_z','xi_star_z_np']
    spin_dict = {
        'proton'      :['spin_up','spin_dn'],
        'lambda_z'    :['spin_up','spin_dn'],
        'sigma_p'     :['spin_up','spin_dn'],
        'xi_z'        :['spin_up','spin_dn'],
        'delta_pp'    :['spin_upup','spin_up','spin_dn','spin_dndn'],
        'sigma_star_p':['spin_upup','spin_up','spin_dn','spin_dndn'],
        'xi_star_z'   :['spin_upup','spin_up','spin_dn','spin_dndn'],
        'omega_m'     :['spin_upup','spin_up','spin_dn','spin_dndn'],
    }
    for corr in octet + decuplet:
        spin_dict[corr+'_np'] = spin_dict[corr]
    # params['MQ'] is assigned as ml or ml_ms depending on spec or hyperspec
    mq = params['MQ'].replace('.','p')
    # first check if corrs are in the h5_dsets
    have_corrs = True
    for src in params['srcs']:
        for corr in mesons:
            h5_path = params['spec']+'/'+mq+'/'+corr+'/px0_py0_pz0/'+src
            if h5_path not in h5_dsets:
                have_corrs = False
                if params['debug']:
                    print("%15s %s" %(corr,h5_path))
        for corr in octet + decuplet:
            for spin in spin_dict[corr]:
                h5_path = params['spec']+'/'+mq+'/'+corr+'/'+spin+'/px0_py0_pz0/'+src
                if h5_path not in h5_dsets:
                    have_corrs = False
                    if params['debug']:
                        print("%15s %s" %(corr,h5_path))
    if params['debug']:
        print('have_corrs',have_corrs)
    if have_corrs and verbose and not overwrite:
        print('%s %s: all collected' %(spec,no))
