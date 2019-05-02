from __future__ import print_function
import os, sys
from glob import glob
import c51_mdwf_hisq as c51
import argparse
import xml_input
import metaq_input

sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
sys.path.append(os.path.join(os.path.dirname(__file__),'scripts'))
import importlib

ens,stream = c51.ens_base()
ens_s = ens+'_'+stream

area51 = importlib.import_module(ens)
params = area51.params
params['machine'] = c51.machine
params['ENS_LONG'] = c51.ens_long[ens]
params['ENS_S']    = ens_s
params['STREAM']   = stream
params['METAQ_PROJECT'] = 'spec_'+ens_s

save_prop=True

parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs',nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-f',type=str,default='a12m180L_a_src.lst',help='cfg/src file')
parser.add_argument('-p',default=False,action='store_const',const=True,\
    help='put task.sh in priority queue? [%(default)s]')
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
args = parser.parse_args()
print('%s: Arguments passed' %sys.argv[0].split('/')[-1])
print(args)
print('')

ci = args.cfgs[0]
if len(args.cfgs) == 1:
    cf = ci+1
    dc = 1
else:
    cf = args.cfgs[1]+1
    dc = args.cfgs[2]

if args.p:
    q = 'priority'
else:
    q = 'todo'

base_dir = c51.base_dir%{'ENS_S':ens_s}#'/p/gpfs1/walkloud/c51/x_files/project_2/'

nl = params['NL']
nt = params['NT']
beta = '600'
u0 = params['U0'] 
ml = params['MS_L']
ms = params['MS_S']  
mc = params['MS_C']

metaq_dir=c51.metaq_dir
params.update(area51.mpirun_params(c51.machine))
params['APP']         = c51.bind_dir+params['gpu_bind']
params['GEOM']=params['gpu_geom_milc'][1::]
params['GPU_P']=params['gpu_p_milc']
params['ENV']=c51.env

ens_long = 'l'+nl+nt+'f211b'+beta+'m'+ml.split('.')[1]+'m'+ms.split('.')[1]+'m'+mc.split('.')[1]+stream

#t_srcs = [0,8,16,24,32,40,48,56]
t_srcs = params['t_shifts']
cfgs = range(ci,cf,dc)

for idir in ['xml','props','stdout','cfgs_coul']:
   if not os.path.exists(base_dir+'/'+idir):
      os.makedirs(base_dir+'/'+idir)

for cfg in cfgs:
    no = str(cfg)
    for idir in ['xml','props','stdout']:
       if not os.path.exists(base_dir+'/'+idir+'/'+no):
          os.makedirs(base_dir+'/'+idir+'/'+no)

    cfg_file = base_dir+'/cfgs/'+ens_long+'.'+no
    cfg_coul = base_dir+'/cfgs_coul/'+ens_long+'.'+no+'.coulomb'
    have_coul = os.path.exists(cfg_coul)
    t0 = str(t_srcs[0])  #CHECK THIS
    hisq_spec = base_dir+'/spectrum/'+no+'/hisq_spec_ml'+ml+'_ms'+ms+'_x0y0z0t'+t0
    V3 = int(nl)**3
    params.update({'HISQ_CORR_FILE':hisq_spec,'V_INV':1./V3,
            'NL':nl,'NT':nt,'JOB_ID':ens+'_'+no+'_hisq',
            'T0':t0,'MAX_CG_ITER':7000,'MAX_CG_RESTART':5,
            'M_L':ml,'M_S':ms,'M_C':mc,'NAIK_c':-0.358919895,
            'ERR_L':1.e-7,'REL_ERR_L':0,
            })
    if save_prop:
        params.update({
            'PROP_L':'save_parallel_scidac_ksprop '+base_dir+'/props/'+no+'/hisq_prop_mq'+ml+'_t'+t0,
            'PROP_S':'save_parallel_scidac_ksprop '+base_dir+'/props/'+no+'/hisq_prop_mq'+ms+'_t'+t0,
            'PROP_C':'save_parallel_scidac_ksprop '+base_dir+'/props/'+no+'/hisq_prop_mq'+mc+'_t'+t0
            })
    else:
        params.update({'PROP_L':'forget_ksprop','PROP_S':'forget_ksprop','PROP_C':'forget_ksprop'})
    if not have_coul:
        cfg_in = '''
reload_parallel %s
u0 %s
coulomb_gauge_fix
save_parallel %s
        ''' %(cfg_file,u0,cfg_coul)
    else:
        cfg_in = '''
reload_parallel %s
u0 %s
no_gauge_fix
forget
        ''' %(cfg_coul,u0)
    params.update({'CFG_INPUT':cfg_in})
    if not os.path.exists(hisq_spec) and os.path.exists(cfg_file):
        spec_name = 'hisq_spec_ml'+ml+'_ms'+ms+'_'+no+'_x0y0z0t'+t0
        metaq  = spec_name+'.sh'

        metaq_file = metaq_dir+'/'+q+'/gpu/'+metaq
        task_exist = False
        task_working = False
        for m_dir in ['todo/gpu','priority/gpu','hold']:
            if os.path.exists(metaq_dir+'/'+m_dir+'/'+metaq):
                task_exist = True
        task_lst = glob(base_dir+'/metaq/working/*/*.sh')
        task_lst += glob(base_dir+'/metaq/working/*/*/*.sh')
        for task in task_lst:
            if metaq == task.split('/')[-1]:
                task_exist = True
                task_working = True
        if not task_exist or (args.o and task_exist and not task_working):
            in_file = base_dir+'/xml/'+no+'/'+spec_name+'.in'
            out_file = in_file.replace('.in','.out').replace('/xml/','/stdout/')
            fin = open(in_file,'w')
            in_tmp = open('hisq_spec.in').read()
            fin.write(in_tmp % params)
            fin.close()        
            print('making ',in_file.split('/')[-1])
            params.update({
                'METAQ_LOG':metaq_dir+'/log/'+metaq.replace('.sh','.log'),
                'BASE_DIR':base_dir,
                'HISQ_IN':in_file,'HISQ_OUT':out_file,
                })
            m_in = open(metaq_file,'w')
            m_in.write(metaq_input.hisq_spec % params)
            m_in.close()
            os.chmod(metaq_file,0770)
        else:
            print('  task exists:',metaq)
    elif os.path.exists(hisq_spec):
        print('spec exists',hisq_spec.split('/')[-1])

    if have_coul:
        for t in t_srcs[1:]:
            t0 = str(t)
            hisq_spec = base_dir+'/spectrum/'+no+'/hisq_spec_ml'+ml+'_ms'+ms+'_x0y0z0t'+t0
            if not os.path.exists(hisq_spec):
                params.update({'T0':t0,'HISQ_CORR_FILE':hisq_spec})
                if save_prop:
                    params.update({
                        'PROP_L':'save_parallel_scidac_ksprop '+base_dir+'/props/'+no+'/hisq_prop_mq'+ml+'_t'+t0,
                        'PROP_S':'save_parallel_scidac_ksprop '+base_dir+'/props/'+no+'/hisq_prop_mq'+ms+'_t'+t0,
                        'PROP_C':'save_parallel_scidac_ksprop '+base_dir+'/props/'+no+'/hisq_prop_mq'+mc+'_t'+t0
                        })
                else:
                    params.update({'PROP_L':'forget_ksprop','PROP_S':'forget_ksprop','PROP_C':'forget_ksprop'})

                spec_name = 'hisq_spec_ml'+ml+'_ms'+ms+'_'+no+'_x0y0z0t'+t0
                metaq  = spec_name+'.sh'
                metaq_file = metaq_dir+'/'+q+'/gpu/'+metaq
                task_exist = False
                task_working = False
                for m_dir in ['todo/gpu','priority/gpu','hold']:
                    if os.path.exists(metaq_dir+'/'+m_dir+'/'+metaq):
                        task_exist = True
                task_lst = glob(base_dir+'/metaq/working/*/*.sh')
                task_lst += glob(base_dir+'/metaq/working/*/*/*.sh')
                for task in task_lst:
                    if metaq == task.split('/')[-1]:
                        task_exist = True
                        task_working = True
                if not task_exist or (args.o and task_exist and not task_working):
                    in_file = base_dir+'/xml/'+no+'/'+spec_name+'.in'
                    out_file = in_file.replace('.in','.out').replace('/xml/','/stdout/')
                    fin = open(in_file,'w')
                    in_tmp = open('hisq_spec.in').read()
                    fin.write(in_tmp % params)
                    fin.close()        
                    print('making ',in_file.split('/')[-1])
                    params.update({
                        'METAQ_LOG':metaq_dir+'/log/'+metaq.replace('.sh','.log'),
                        'BASE_DIR':base_dir,
                        'HISQ_IN':in_file,'HISQ_OUT':out_file,
                        })
                    m_in = open(metaq_file,'w')
                    m_in.write(metaq_input.hisq_spec % params)
                    m_in.close()
                    os.chmod(metaq_file,0770)
                else:
                    print('  task exists:',metaq)

