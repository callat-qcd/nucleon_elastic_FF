import numpy as np
import tables as h5
import os, shutil, sys, time

import c51_mdwf_hisq as c51
import sources
import utils

def create_group(f5,h5_path):
    tmp_path,tmp_group = h5_path.rsplit('/',1)
    try:
        f5.create_group(tmp_path,tmp_group,createparents=True)
        f5.flush()
    except:
        pass

mres_corrs = ['midpoint_pseudo', 'pseudo_pseudo']
phi_qq_corrs = ['phi_qq']
res_phi_corrs = {
    'mres_ll':['midpoint_pseudo', 'pseudo_pseudo'],
    'mres_ss':['midpoint_pseudo', 'pseudo_pseudo'],
    'phi_ll' :['phi_ll'],
    'phi_ss' :['phi_ss'],
}
res_phi_path  = {
    'mres_ll':'mres_path', 'mres_ss':'mres_path',
    'midpoint_pseudo':'mres_path','pseudo_pseudo':'mres_path',
    'phi_ll':'phi_qq_path', 'phi_ss':'phi_qq_path',
}
def res_phi_dset(params,full_path=True):
    if '_ll' in params['corr']:
        params['MQ'] = params['MV_L']
    elif '_ss' in params['corr']:
        params['MQ'] = params['MV_S']
    mq   = params['MQ'].replace('.','p')
    src  = params['SRC']
    corr = params['corr']
    if 'phi' in params['corr']:
        h5_path = params[res_phi_path[corr]]+'/mq'+mq
    else:
        h5_path = params[res_phi_path[corr]]+'/mq'+mq+'/%(CORR)s'
    if full_path:
        h5_path += '/'+src
    return h5_path


def spec_dset(params,corr,full_path=True):
    #params['core'] controls the master group while corr is the specific dset of interest
    b_octet    = ['proton','proton_np','lambda_z','lambda_z_np','sigma_p','sigma_p_np','xi_z','xi_z_np']
    b_decuplet = ['delta_pp','delta_pp_np','omega_m','omega_m_np','sigma_star_p','sigma_star_p_np','xi_star_z','xi_star_z_np']
    spec = params['corr']
    if spec == 'spec':
        params['MQ'] = 'ml'+params['MV_L']
    elif spec in ['hyperspec', 'h_spec']:
        params['MQ'] = 'ml'+params['MV_L']+'_ms'+params['MV_S']
    mq = params['MQ'].replace('.','p')
    if corr in ['spec','h_spec']:
        h5_path = params['h5_spec_path']+'/'+mq+'/%(CORR)s/%(SPIN)s/%(MOM)s'
    elif corr in ['piplus','kminus','kplus']:
        h5_path = params['h5_spec_path']+'/'+mq+'/'+corr+'/%(MOM)s'
    elif corr in b_octet + b_decuplet:
        h5_path = params['h5_spec_path']+'/'+mq+'/'+corr+'/%(SPIN)s/%(MOM)s'
    else:
        sys.exit('unrecognized spec type %s' %spec)
    if full_path:
        h5_path += '/'+params['SRC']
    return h5_path

def ff_dset(params, full_path=True):
    params['MQ'] = 'ml'+params['MV_L']
    mq = params['MQ'].replace('.','p')
    h5_path = params['ff_path'] +'/'+mq+'/%(PARTICLE)s_%(FLAV_SPIN)s_tsep_%(T_SEP)s_sink_mom_px0_py0_pz0/%(CURRENT)s/px0_py0_pz0'
    if full_path:
        h5_path += '/'+params['SRC']
    return h5_path

def make_corr_dict(params):
    meta_dict = dict()
    meta_dict['correlator']    = params['corr']
    meta_dict['ensemble']      = params['ENS_S'].split('_')[0]
    meta_dict['stream']        = params['STREAM']
    meta_dict['configuration'] = int(params['CFG'])
    meta_dict['source_set']    = params['SRC_SET']
    meta_dict['source']        = params['SRC']

def make_corr_td_dict(params):
    td_dict = dict()
    

def collect_res_phi(params,h5_file):
    overwrite  = params['overwrite']
    verbose    = params['verbose']
    debug      = params['debug']
    no         = params['CFG']
    mq         = params['MQ'].replace('.','p')
    src        = params['SRC']
    t_src      = int(src.split('t')[1])
    get_data   = False
    h5_paths   = dict()
    corrs = res_phi_corrs[params['corr']]
    have_corrs = False
    # check if data is collected in h5 already
    f5 = h5.open_file(h5_file,'a')
    for corr in corrs:
        h5_paths[corr] = '/'+res_phi_dset(params,full_path=False) %{'CORR':corr}
        create_group(f5,h5_paths[corr])
        if (src not in f5.get_node(h5_paths[corr])) or (src in f5.get_node(h5_paths[corr]) and overwrite):
            get_data = True
    # if not in h5
    if get_data:
        prop_name = c51.names['prop'] % params
        prop_xml = params['xml'] + '/' + prop_name+'.out.xml'
        mq = params['MQ'].replace('.','p')
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
                        if (now-file_time)/60 > 240:# time in minutes
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
                if 'mres' in params['corr']:
                    if f[l].find('<DWF_MidPoint_Pseudo>') > 0 and f[l+3].find('<DWF_Psuedo_Pseudo>') > 0:
                        mp = f[l+1].split('<mesprop>')[1].split('</mesprop>')[0].split()
                        pp = f[l+4].split('<mesprop>')[1].split('</mesprop>')[0].split()
                        data['midpoint_pseudo'] = np.array([float(d) for d in mp],dtype=dtype)
                        data['pseudo_pseudo']   = np.array([float(d) for d in pp],dtype=dtype)
                        have_data = True
                else:
                    if f[l].find('<prop_corr>') > 0:
                        corr = f[l].split('<prop_corr>')[1].split('</prop_corr>')[0].split()
                        phi_qq = np.array([float(d) for d in corr],dtype=dtype)
                        data[params['corr']] = np.roll(phi_qq,-t_src)
                        have_data = True
                #if have_mres and have_phiqq:
                #    have_data = True
                l += 1
            good_data = True
            for corr in corrs:
                if np.any(np.isnan(data[corr])):
                    good_data = False
            if good_data:
                if verbose:
                    print('    %s %3s %s %s' %(params['corr'],params['CFG'], params['MQ'], params['SRC']))
                for corr in corrs:
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

def get_res_phi(params_in,h5_dsets,h5_file=None,collect=False):
    params    = dict(params_in)
    overwrite = params['overwrite']
    verbose   = params['verbose']
    debug     = params['debug']
    no        = params['CFG']
    if '_ll' in params['corr']:
        params['MQ'] = params['MV_L']
    elif '_ss' in params['corr']:
        params['MQ'] = params['MV_S']
    # first check if corrs are in the h5_dsets
    corrs = res_phi_corrs[params['corr']]
    have_corrs = True
    for src in params['srcs']:
        mq = params['MQ'].replace('.','p')
        params['SRC'] = src
        for corr in corrs:
            h5_path = res_phi_dset(params,full_path=True) %{'CORR':corr}
            if h5_path not in h5_dsets:
                have_corrs = False
                if debug:
                    print("%7s %s" %(corr,h5_path))
    if debug:
        print('verbose',verbose)
        print('have_corrs',have_corrs)
    if have_corrs and verbose and not overwrite:
        print('%s %s: all collected' %(params['corr'],no))
    # if collect=True, try to collect data
    if (not have_corrs and collect) or (overwrite and collect):
        # loop over srcs and masses
        for src in params['srcs']:
            params['SRC'] = src
            # check lattedb for collection status
            lattedb_have_res_phi = False # this will be replaced by a function call
            if not lattedb_have_res_phi:
                # make list of dictionary entries for lattedb
                res_phi_lst = []
                # update param dict for collecting
                prop_name = c51.names['prop'] % params
                prop_xml = params['xml'] + '/' + prop_name+'.out.xml'
                mq = params['MQ'].replace('.','p')
                # try and collect corrs if not in h5 file already
                have_corrs = collect_res_phi(params,h5_file)
                # make dict entry for lattedb
                # res_phi_lst.append(res_phi_element) 

    return have_corrs

def get_spec(params_in, h5_dsets,h5_file=None,collect=False):
    params    = dict(params_in)
    overwrite = params['overwrite']
    verbose   = params['verbose']
    debug     = params['debug']
    no        = params['CFG']
    dtype     = np.complex64
    spec      = params['corr']
    if spec == 'spec':
        mesons    = ['piplus']
        octet     = ['proton','proton_np']
        decuplet  = []
        params['MQ'] = 'ml'+params['MV_L']
    elif spec in ['hyperspec','h_spec']:
        params['h_spec'] = params['hyperspec']
        mesons    = ['piplus','kminus','kplus']
        octet     = ['proton','proton_np','lambda_z','lambda_z_np','sigma_p','sigma_p_np','xi_z','xi_z_np']
        decuplet  = ['delta_pp','delta_pp_np','omega_m','omega_m_np','sigma_star_p','sigma_star_p_np','xi_star_z','xi_star_z_np']
        params['MQ'] = 'ml'+params['MV_L']+'_ms'+params['MV_S']
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
        params['SRC'] = src
        for corr in mesons:
            for mom in utils.p_lst(params['MESONS_PSQ_MAX']):
                h5_path = spec_dset(params,corr,full_path=True) %{'MOM':mom}
                #h5_path = params['h5_spec_path']+'/'+mq+'/'+corr+'/'+mom+'/'+src
                if h5_path not in h5_dsets:
                    have_corrs = False
                    if debug:
                        print("%15s %s" %(corr,h5_path))
        for corr in octet + decuplet:
            for spin in spin_dict[corr]:
                for mom in utils.p_lst(params['BARYONS_PSQ_MAX']):
                    h5_path = spec_dset(params, corr, full_path=True) %{'MOM':mom, 'SPIN':spin}
                    #h5_path = params['h5_spec_path']+'/'+mq+'/'+corr+'/'+spin+'/'+mom+'/'+src
                    if h5_path not in h5_dsets:
                        have_corrs = False
                        if debug:
                            print("%15s %s" %(corr,h5_path))
    if debug:
        print('have_corrs',have_corrs)
    if have_corrs and verbose and not overwrite:
        print('%s %s: all collected' %(spec,no))
    # if collect=True, try to collect data
    if (not have_corrs and collect) or (overwrite and collect):
        f5 = h5.open_file(h5_file,'a')
        corr_dicts = []
        for src in params['srcs']:
            params['SRC'] = src
            src_split = sources.src_split(src)
            # first check if src is already collected
            get_data = False
            for corr in mesons:
                for mom in utils.p_lst(params['MESONS_PSQ_MAX']):
                    h5_path = '/'+ spec_dset(params,corr,full_path=False) %{'MOM':mom}
                    create_group(f5,h5_path)
                    if (src not in f5.get_node(h5_path)) or (src in f5.get_node(h5_path) and overwrite):
                        get_data = True
            for corr in octet + decuplet:
                for spin in spin_dict[corr]:
                    for mom in utils.p_lst(params['BARYONS_PSQ_MAX']):
                        #h5_path = '/'+params['h5_spec_path']+'/'+mq+'/'+corr+'/'+spin+'/'+mom
                        h5_path = '/' + spec_dset(params,corr,full_path=False) %{'MOM':mom, 'SPIN':spin}
                        create_group(f5,h5_path)
                        if (src not in f5.get_node(h5_path)) or (src in f5.get_node(h5_path) and overwrite):
                            get_data = True
            if debug:
                print('get_spec: get_data',get_data)
            if get_data:
                spec_name = c51.names[spec] % params
                spec_file = params[spec] +'/'+ spec_name+'.h5'
                # make sure file exists and is the correct size
                if debug:
                    print(params['spec_size'], os.path.getsize(spec_file), spec_file)
                if os.path.exists(spec_file) and os.path.getsize(spec_file) > params['spec_size']:
                    fin = h5.open_file(spec_file,'r')
                    src_split = sources.src_split(src)
                    t_src = int(src.split('t')[1])
                    for corr in mesons:
                        for mom in utils.p_lst(params['MESONS_PSQ_MAX']):
                            h5_path = '/'+ spec_dset(params,corr,full_path=False) %{'MOM':mom} #params['h5_spec_path']+'/'+mq+'/'+corr+'/'+mom
                            nt = int(params['NT'])
                            data = np.zeros([nt,2,1],dtype=dtype)
                            data[:,0,0] = fin.get_node('/sh/'+corr+'/'+src_split+'/'+mom).read()
                            data[:,1,0] = fin.get_node('/pt/'+corr+'/'+src_split+'/'+mom).read()
                            if not np.any(np.isnan(data)):
                                if verbose:
                                    print("%4s %15s %13s %s" %(no,corr,src,mom))
                                if src not in f5.get_node(h5_path):
                                    f5.create_array(h5_path,src,data)
                                elif src in f5.get_node(h5_path) and overwrite:
                                    f5.get_node(h5_path+'/'+src)[:] = data
                                elif src in f5.get_node(h5_path) and not overwrite:
                                    print('  skipping %s: overwrite = False, %s, %s' %(corr,no,src))
                                f5.flush()
                            else:
                                print('  NAN: %s %s %s' %(corr,no,src))
                    for corr in octet+decuplet:
                        for spin in spin_dict[corr]:
                            for mom in utils.p_lst(params['BARYONS_PSQ_MAX']):
                                h5_path = '/'+ spec_dset(params,corr,full_path=False) %{'MOM':mom, 'SPIN':spin} #params['h5_spec_path']+'/'+mq+'/'+corr+'/'+spin+'/'+mom
                                nt = int(params['NT'])
                                data = np.zeros([nt,2,1],dtype=dtype)
                                data[:,0,0] = fin.get_node('/sh/'+corr+'/'+spin+'/'+src_split+'/'+mom).read()
                                data[:,1,0] = fin.get_node('/pt/'+corr+'/'+spin+'/'+src_split+'/'+mom).read()
                                if not np.any(np.isnan(data)):
                                    if verbose:
                                        print("%4s %15s %6s %13s %s" %(no,corr,spin,src,mom))
                                    if src not in f5.get_node(h5_path):
                                        f5.create_array(h5_path,src,data)
                                    elif src in f5.get_node(h5_path) and overwrite:
                                        f5.get_node(h5_path+'/'+src)[:] = data
                                    elif src in f5.get_node(h5_path) and not overwrite:
                                        print('  skipping %s: overwrite = False, %s %s %s' %(corr,spin,no,src))
                                    f5.flush()
                                else:
                                    print('  NAN: %s %s %s %s' %(corr,spin,no,src))
                    fin.close()
        f5.close()
    return have_corrs

def get_formfac(params_in, h5_dsets,h5_file=None,collect=False):
    params    = dict(params_in)
    overwrite = params['overwrite']
    verbose   = params['verbose']
    debug     = params['debug']
    no        = params['CFG']
    dtype     = np.complex64
    tsep      = params['T_SEP']
    flav_spin = []
    for flav in params['flavs']:
        for spin in params['spins']:
            flav_spin.append(flav+'_'+spin)
    params['MQ']  = 'ml'+params['MV_L']
    mq            = params['MQ'].replace('.','p')
    params['MOM'] = 'px0py0pz0'
    have_corrs = True
    for src in params['srcs']:
        params['SRC'] = src
        t_src = src.split('t')[1]
        for corr in params['particles']:
            dt = str(tsep)
            if '_np' in corr:
                dt = '-'+dt
            for fs in flav_spin:
                for curr in params['curr_0p']:
                    path_replace = {'PARTICLE':corr, 'FLAV_SPIN':fs, 'T_SEP':dt, 'CURRENT':curr}
                    h5_path = ff_dset(params, full_path=True) %path_replace
                    if h5_path not in h5_dsets:
                        have_corrs = False
    if debug:
        print('have_corrs t_sep = ',dt,have_corrs)
    if have_corrs and verbose and not overwrite:
        print('%s %s: all collected' %(spec,no))


    return have_corrs
