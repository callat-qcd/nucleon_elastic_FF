import os,shutil
import time
import socket

''' NUCLEON_ELASTIC_FF import '''
import utils

def ens_base():
    ens,stream = os.getcwd().split('/')[-1].split('_')
    return ens,stream

hn = socket.gethostname()
if any(host in hn for host in ['oslic','pascal']):
    manage    = '/usr/workspace/coldqcd/c51/x_files/project_2'
    scratch   = '/p/lustre1/walkloud/c51/x_files/project_2'
    machine   = 'pascal'
    env       = ''
    bind_dir  = ''
elif any(host in hn for host in ['lassen']):
    manage    = '/usr/workspace/coldqcd/c51/x_files/project_2'
    scratch   = '/p/gpfs1/walkloud/c51/x_files/project_2'
    machine   = 'lassen'
    #env       = 'source /usr/workspace/coldqcd/software/lassen_smpi_RR/install/env.sh'
    env       = 'source /usr/workspace/coldqcd/software/lassen_smpi_RR2/install/env.sh'
    bind_dir  = '/usr/workspace/coldqcd/software/callat_build_scripts/binding_scripts/'
    milc_dir  = '/usr/workspace/coldqcd/software/lassen_smpi_RR/install/lattice_milc_qcd'
    python    = '/usr/workspace/coldqcd/software/python_venv-3.7.2.lassen/bin/python'
    jsrun_fail= '/p/gpfs1/walkloud/c51/x_files/project_2/production/failing_jsrun_jobids.txt'
elif any(host in hn for host in ['login','batch']):
    ''' TERRIBLE LOGIN NAME FOR SUMMIT '''
    manage   = '/ccs/proj/lgt100/c51/x_files/project_2'
    scratch  = '/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2'
    tape     = '/proj/lgt100/c51/x_files/project_2/production'
    machine  = 'summit'
    env      = 'source /ccs/proj/lgt100/c51/software/summit_smpi/install/env.sh'
    env     += '\nmodule load python/3.7.0-anaconda3-5.3.0'
    bind_dir = ''
    python   = 'python'
else:
    print("Host "+hn+" unknown, using default.")
    manage   = os.path.dirname(os.path.abspath(__file__))
    root     = os.path.dirname(os.path.abspath(__file__))+'/c51/x_files/project_2'
    machine  = 'default'
    env      = ''
    bind_dir = ''
    python   = 'python'
print("c51 manage dir is",manage)
print("c51 scratch dir is",scratch)

ens_long = {
    'a15m400trMc':'l2048f31b580m02405m02405m8447',
    'a12m400trMc':'l2464f31b600m01878m01878m6382',
    'a09m400trMc':'l3296f31b630m01300m01300m4313',
    'a15m400'  :'l1648f211b580m0217m065m838',
    'a15m350'  :'l1648f211b580m0166m065m838',
    'a15m310'  :'l1648f211b580m013m065m838',
    'a15m310L' :'l2448f211b580m013m065m838',
    'a15m310Lfaces' :'l2448f211b580m013m065m838',
    'a15m310Lcorners' :'l2448f211b580m013m065m838',
    'a15m310Lindvdl' :'l2448f211b580m013m065m838',
    'a15m310XL':'l4864f211b580m013m065m838',
    'a15m260'  :'l2448f211b580m00894m064m828',
    'a15m260XL':'',
    'a15m220'  :'l2448f211b580m0064m0640m828',
    'a15m220XL':'l4864f211b580m0064m0640m828',
    'a15m130'  :'l3248f211b580m00235m0647m831',
    'a15m135XL':'l4864f211b580m002426m06730m8447',
    'a12m400'  :'l2464f211b600m0170m0509m635',
    'a12m350'  :'l2464f211b600m0130m0509m635',
    'a12m310'  :'l2464f211b600m0102m0509m635',
    'a12m310L' :'l3264f211b600m0102m0509m635',
    'a12m310XL':'l4864f211b600m0102m0509m635',
    'a12m260'  :'l3264f211b600m00717m0507m628',
    'a12m220'  :'l3264f211b600m00507m0507m628',
    'a12m220ms':'l3264f211b600m00507m0304m628',
    'a12m220diff': 'l3264f31b600m00507m628',
    'a12m220lms':'l3264f211b600m00507m022815m628',
    'a12m220S' :'l2464f211b600m00507m0507m628',
    'a12m220L' :'l4064f211b600m00507m0507m628',
    'a12m220XL':'l4864f211b600m00507m0507m628',
    'a12m180S' :'l3264f211b600m00339m0507m628',
    'a12m180L' :'l4864f211b600m00339m0507m628',
    'a12m130'  :'l4864f211b600m00184m0507m628',
    'a12m135XL':'',
    'a09m400'  :'l3264f211b630m0124m037m440',
    'a09m350'  :'l3264f211b630m00945m037m440',
    'a09m310'  :'l3296f211b630m0074m037m440',
    'a09m260'  :'l4896f211b630m0052m0363m430',
    'a09m220'  :'l4896f211b630m00363m0363m430',
    'a09m130'  :'l6496f211b630m0012m0363m432',
    'a09m135'  :'l6496f211b630m001326m03636m4313',
    'a06m310'  :'l48144f211b672m0048m024m286',
    'a06m310L' :'l7296f211b672m0048m024m286',
    'a06m220L' :'l72128f211b672m0024m02186m2579',
    }

base_dir    = scratch+'/production/%(ENS_S)s'
ens_dir     = manage +'/production/%(ENS_S)s'
script_dir  = manage +'/production/nucleon_elastic_FF/scripts'
metaq_dir   = manage +'/metaq'
#data_dir   = manage +'/production/%(ENS_S)s/data'
data_dir    = scratch+'/production/%(ENS_S)s/data'
data_dir_4d = scratch+'/production/%(ENS_S)s/data_4D'
ff_data_dir = scratch+'/production/%(ENS_S)s/ff4D_data'

def ensemble(params):
    params['JSRUN_FAIL']  = jsrun_fail
    milc_cfg              = params['ENS_LONG']+params['STREAM']+'.'+params['CFG']
    params['prod']        = scratch + "/production/" + params['ENS_S']
    params['milc_cfg']    = params['prod']+'/cfgs/'+milc_cfg
    params['scidac_cfg']  = params['prod']+'/cfgs_scidac/'+milc_cfg+'.scidac'
    params['flowed_cfg']  = params['prod']+'/cfgs_flow/'+milc_cfg+'_wflow'+params['FLOW_TIME']+'.lime'

    ''' DIRECTORIES '''
    params['METAQ_DIR']   = metaq_dir
    dirs    = ['cfgs_flow','corrupt','src','quda_resource']
    dirs_no = ['xml','stdout','prop','spec','spec_4D','seqsrc','seqprop','formfac','formfac_4D','hisq_spec','prop_strange','hyperspec','mixed']
    for d in dirs:
        params[d] = params['prod']+'/'+d
    for d in dirs_no:
        params[d] = params['prod']+'/'+d+'/'+params['CFG']
    if 'run_fh' in params:
        if params['run_fh']:
            params['fh_prop'] = params['prod']+'/fh_prop/'+params['CFG']
            params['fh_spec'] = params['prod']+'/fh_spec/'+params['CFG']
            params['fh_baryons'] = params['prod']+'/fh_spec/'+params['CFG']
            params['fh_mesons'] = params['prod']+'/fh_spec/'+params['CFG']
            utils.ensure_dirExists(params['fh_prop'])
            utils.ensure_dirExists(params['fh_spec'])
            utils.ensure_dirExists(params['fh_baryons'])
            utils.ensure_dirExists(params['fh_mesons'])

    for d in dirs+dirs_no:
        utils.ensure_dirExists(params[d])
    params['spec_4D_avg']        = params['prod']+'/spec_4D_avg/'+params['CFG']
    params['spec_4D_tslice']     = params['prod']+'/spec_4D_tslice/'+params['CFG']
    params['spec_4D_tslice_avg'] = params['prod']+'/spec_4D_tslice_avg/'+params['CFG']
    params['formfac_4D_tslice']  = params['prod']+'/formfac_4D_tslice/'+params['CFG']
    params['formfac_4D_tslice_src_avg'] = params['prod']+'/formfac_4D_tslice_src_avg/'+params['CFG']

    return params

names = dict()
names['flow']             = 'cfg_flow_%(ENS_LONG)s%(STREAM)s_%(CFG)s_wflow%(FLOW_TIME)s'
names['src']              = 'src_%(ENS_S)s_%(CFG)s_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s_%(SRC)s'
names['prop']             = 'prop_%(ENS_S)s_%(CFG)s_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s'
names['prop']            += '_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s_%(SRC)s'
''' the xml generation may incluce multiple quark masses, so no mq info '''
names['prop_xml']         = 'prop_%(ENS_S)s_%(CFG)s_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s'
names['prop_xml']        += '_M5%(M5)s_L5%(L5)s_a%(alpha5)s_%(SRC)s'
names['spec']             = 'spec_%(ENS_S)s_%(CFG)s_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s'
names['spec']            += '_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s_%(SRC)s'
names['spec_4D']            = names['spec'].replace('spec_','spec_4D_')
names['spec_4D_tslice']     = names['spec'].replace('spec_','spec_4D_tslice_')
names['spec_4D_tslice_avg'] = names['spec'].replace('spec_','spec_4D_tslice_avg_')
names['hyperspec']        = 'hyperspec_%(ENS_S)s_%(CFG)s_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s'
names['hyperspec']       += '_M5%(M5)s_L5%(L5)s_a%(alpha5)s_ml%(MV_L)s_ms%(MV_S)s_%(SRC)s'
names['hisq_spec']        = 'hisq_spec_%(ENS_S)s_ml%(MS_L)s_ms%(MS_S)s_%(CFG)s_%(SRC)s'
names['seqsrc']           = 'seqsrc_%(ENS_S)s_%(CFG)s_%(PARTICLE)s_%(FLAV_SPIN)s'
names['seqsrc']          += '_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s'
names['seqsrc']          += '_%(MOM)s_%(SRC)s_%(SS_PS)s'
names['coherent_seqsrc']  = 'seqsrc_%(ENS_S)s_%(CFG)s_%(PARTICLE)s_%(FLAV_SPIN)s'
names['coherent_seqsrc'] += '_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s'
names['coherent_seqsrc'] += '_%(MOM)s_dt%(T_SEP)s_Nsnk%(N_SEQ)s_%(SS_PS)s'
names['seqprop']          = 'seqprop_%(ENS_S)s_%(CFG)s_%(PARTICLE)s_%(FLAV_SPIN)s'
names['seqprop']         += '_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s'
names['seqprop']         += '_%(MOM)s_dt%(T_SEP)s_Srcs%(SRC_LST)s_%(SS_PS)s'
names['formfac']          = 'formfac_%(ENS_S)s_%(CFG)s'
names['formfac']         += '_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s'
names['formfac']         += '_%(MOM)s_dt%(T_SEP)s_Nsnk%(N_SEQ)s_%(SRC)s_%(SS_PS)s'
names['formfac_4D']                = names['formfac'].replace('formfac','formfac_4D')
names['formfac_4D_tslice']         = names['formfac'].replace('formfac','formfac_4D_tslice')
names['formfac_4D_tslice_src_avg'] = names['formfac'].replace('formfac','formfac_4D_tslice_src_avg')

names['mixed_corr']       = 'dwf_hisq_spec_%(ENS_S)s_wflow%(FLOW_TIME)s_M5%(M5)s_L5%(L5)s'
names['mixed_corr']      += '_a%(alpha5)s_cfg_%(CFG)s_src%(SRC)s_%(SMR)s_ml%(MQ_L)s_ms%(MQ_S)s.corr'
names['hisq_corr']        = 'hisq_spec_%(ENS_S)s_ml%(MS_L)s_ms%(MS_S)s_%(CFG)s_%(SRC)s'

names['pipi']             = 'pipi_%(ENS_S)s_%(CFG)s_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s'
names['pipi']            += '_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(Q)s_%(SRC)s'
names['pik']              = 'pipi_%(ENS_S)s_%(CFG)s_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s'
names['pik']             += '_M5%(M5)s_L5%(L5)s_a%(alpha5)s_ml%(MV_L)s_ms%(MV_S)s_%(SRC)s'

names['fh_prop']          = 'fh_prop_%(ENS_S)s_%(CFG)s_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s'
names['fh_prop']         += '_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s_%(SRC)s_%(CURR)s'
names['fh_spec']          = 'fh_spec_%(ENS_S)s_%(CFG)s_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s'
names['fh_spec']         += '_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s_%(SRC)s'
names['fh_baryons']       = 'fh_baryons_%(ENS_S)s_%(CFG)s_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s'
names['fh_baryons']      += '_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s_%(SRC)s'
names['fh_mesons']       = 'fh_mesons_%(ENS_S)s_%(CFG)s_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s'
names['fh_mesons']      += '_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s_%(SRC)s'
