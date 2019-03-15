import shutil
import time


base_dir   = '/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/%(ENS_S)s'
script_dir = '/ccs/proj/lgt100/c51/x_files/project_2/production/%(ENS_S)s/scripts'
metaq_dir  = '/ccs/proj/lgt100/c51/x_files/project_2/metaq'

src_base       = 'src_%(ENS_S)s_%(CFG)s_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s_%(SRC)s'
prop_base      = 'prop_%(ENS_S)s_%(CFG)s_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s'
prop_base     += '_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s_%(SRC)s'
''' the xml generation may incluce multiple quark masses, so no mq info '''
prop_xml_base  = 'prop_%(ENS_S)s_%(CFG)s_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s'
prop_xml_base += '_M5%(M5)s_L5%(L5)s_a%(alpha5)s_%(SRC)s'
spec_base      = 'spec_%(ENS_S)s_%(CFG)s_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s'
spec_base     += '_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s_%(SRC)s'
sp_ext = 'lime'

seqsrc_base       = 'seqsrc_%(ENS_S)s_%(CFG)s_%(PARTICLE)s_%(FLAV_SPIN)s'
seqsrc_base      += '_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s'
seqsrc_base      += '_%(MOM)s_%(SRC)s_%(SS_PS)s'

coherent_seqsrc   = 'seqsrc_%(ENS_S)s_%(CFG)s_%(PARTICLE)s_%(FLAV_SPIN)s'
coherent_seqsrc  += '_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s'
coherent_seqsrc  += '_%(MOM)s_dt%(T_SEP)s_Nsnk%(N_SEQ)s_%(SS_PS)s'

seqprop_base      = 'seqprop_%(ENS_S)s_%(CFG)s_%(PARTICLE)s_%(FLAV_SPIN)s'
seqprop_base     += '_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s'
seqprop_base     += '_%(MOM)s_dt%(T_SEP)s_Nsnk%(N_SEQ)s_%(SS_PS)s'

coherent_ff_base  = 'formfac_%(ENS_S)s_%(CFG)s'
coherent_ff_base += '_gf%(FLOW_TIME)s_w%(WF_S)s_n%(WF_N)s_M5%(M5)s_L5%(L5)s_a%(alpha5)s_mq%(MQ)s'
coherent_ff_base += '_%(MOM)s_dt%(T_SEP)s_Nsnk%(N_SEQ)s_%(SRC)s_%(SS_PS)s'

def check_file(f_name,f_size,time_delete,bad_file_dir):
    if os.path.exists(f_name) and os.path.getsize(f_name) < f_size:
        now = time.time()
        file_time = os.stat(f_name).st_mtime
        ''' check last update of file in minutes '''
        if (now-file_time)/60 > time_delete:
            print('DELETING BAD FILE',os.path.getsize(f_name),f_name.split('/')[-1])
            shutil.move(f_name,bad_file_dir+'/'+f_name.split('/')[-1])
    return os.path.exists(f_name)
