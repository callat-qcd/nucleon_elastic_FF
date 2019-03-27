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
    manage    = '/p/lustre1/walkloud/c51/x_files/project_2'
    scratch   = '/p/lustre1/walkloud/c51/x_files/project_2'
    machine   = 'pascal'
    env       = ''
    bind_dir  = ''
elif any(host in hn for host in ['lassen']):
    manage    = '/p/gpfs1/walkloud/c51/x_files/project_2'
    scratch   = '/p/gpfs1/walkloud/c51/x_files/project_2'
    machine   = 'lassen'
    env       = 'source /usr/workspace/coldqcd/software/lassen_smpi_RR/install/env.sh'
    bind_dir  = '/usr/workspace/coldqcd/software/callat_build_scripts/binding_scripts/'
    bind_c_36 = 'lassen_bind_cpu.N36.sh'
    bind_g_4  = 'lassen_bind_gpu.omp4.sh'
elif any(host in hn for host in ['login']):
    ''' TERRIBLE LOGIN NAME FOR SUMMIT '''
    manage   = '/ccs/proj/lgt100/c51/x_files/project_2'
    scratch  = '/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2'
    machine  = 'summit'
    env      = ''
    bind_dir = ''
else:
    print("Host "+hn+" unknown, using default.")
    manage   = os.path.dirname(os.path.abspath(__file__))
    root     = os.path.dirname(os.path.abspath(__file__))+'/c51/x_files/project_2'
    machine  = 'default'
    env      = ''
    bind_dir = ''
print("c51 manage dir is",manage)
print("c51 scratch dir is",scratch)

ens_long = {
    'a15m400'  :'l1648f211b580m0217m065m838',
    'a15m350'  :'l1648f211b580m0166m065m838',
    'a15m310'  :'l1648f211b580m013m065m838',
    'a15m310L' :'l2448f211b580m013m065m838',
    'a15m310XL':'l4864f211b580m013m065m838',
    'a15m260XL':'',
    'a15m220'  :'l2448f211b580m0064m0640m828',
    'a15m220XL':'l4864f211b580m0064m0640m828',
    'a15m130'  :'l3248f211b580m00235m0647m831',
    'a15m135XL':'',
    'a12m400'  :'l2464f211b600m0170m0509m635',
    'a12m350'  :'l2464f211b600m0130m0509m635',
    'a12m310'  :'l2464f211b600m0102m0509m635',
    'a12m310L' :'',
    'a12m310XL':'',
    'a12m260'  :'',
    'a12m220'  :'l3264f211b600m00507m0507m628',
    'a12m220S' :'l2464f211b600m00507m0507m628',
    'a12m220L' :'l4064f211b600m00507m0507m628',
    'a12m180L' :'',
    'a12m130'  :'l4864f211b600m00184m0507m628',
    'a12m135XL':'',
    'a09m400'  :'l3264f211b630m0124m037m440',
    'a09m350'  :'l3264f211b630m00945m037m440',
    'a09m310'  :'l3296f211b630m0074m037m440',
    'a09m260'  :'',
    'a09m220'  :'l4896f211b630m00363m0363m430',
    'a09m130'  :'l6496f211b630m0012m0363m432',
    }

base_dir   = scratch+'/production/%(ENS_S)s'
ens_dir    = manage +'/production/%(ENS_S)s/scripts'
script_dir = manage +'/production/nucleon_elastic_FF/scripts'
metaq_dir  = manage +'/metaq'

def ensemble(params):
    milc_cfg              = params['ENS_LONG']+params['STREAM']+'.'+params['CFG']
    params['prod']        = scratch + "/production/" + params['ENS_S']
    params['milc_cfg']    = params['prod']+'/cfgs/'+milc_cfg
    params['scidac_cfg']  = params['prod']+'/cfgs_scidac/'+milc_cfg+'.scidac'
    params['flowed_cfg']  = params['prod']+'/cfgs_flow/'+milc_cfg+'_wflow'+params['FLOW_TIME']+'.lime'

    ''' DIRECTORIES '''
    params['METAQ_DIR']   = metaq_dir
    dirs    = ['flowed','corrupt','src','quda_resource']
    dirs_no = ['xml','stdout','prop','spec','spec_4D','seqsrc','seqprop','formfac','formfac_4D',]
    for d in dirs:
        params[d] = params['prod']+'/'+d
    for d in dirs_no:
        params[d] = params['prod']+'/'+d+'/'+params['CFG']
    for d in dirs+dirs_no:
        utils.ensure_dirExists(params[d])

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
names['seqsrc']           = 'seqsrc_%(ENS_S)s_%(CFG)s_%(PARTICLE)s_%(FLAV_SPIN)s'
names['seqsrc']          += '_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s'
names['seqsrc']          += '_%(MOM)s_%(SRC)s_%(SS_PS)s'
names['coherent_seqsrc']  = 'seqsrc_%(ENS_S)s_%(CFG)s_%(PARTICLE)s_%(FLAV_SPIN)s'
names['coherent_seqsrc'] += '_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s'
names['coherent_seqsrc'] += '_%(MOM)s_dt%(T_SEP)s_Nsnk%(N_SEQ)s_%(SS_PS)s'
names['seqprop']          = 'seqprop_%(ENS_S)s_%(CFG)s_%(PARTICLE)s_%(FLAV_SPIN)s'
names['seqprop']         += '_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s'
names['seqprop']         += '_%(MOM)s_dt%(T_SEP)s_Nsnk%(N_SEQ)s_%(SS_PS)s'
names['coherent_ff']      = 'formfac_%(ENS_S)s_%(CFG)s'
names['coherent_ff']     += '_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s'
names['coherent_ff']     += '_%(MOM)s_dt%(T_SEP)s_Nsnk%(N_SEQ)s_%(SRC)s_%(SS_PS)s'

def check_file(f_name,f_size,time_delete,bad_file_dir):
    if os.path.exists(f_name) and os.path.getsize(f_name) < f_size:
        now = time.time()
        file_time = os.stat(f_name).st_mtime
        ''' check last update of file in minutes '''
        if (now-file_time)/60 > time_delete:
            print('DELETING BAD FILE',os.path.getsize(f_name),f_name.split('/')[-1])
            shutil.move(f_name,bad_file_dir+'/'+f_name.split('/')[-1])
    return os.path.exists(f_name)