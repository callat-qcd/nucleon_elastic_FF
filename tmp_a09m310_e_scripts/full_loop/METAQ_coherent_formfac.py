from __future__ import print_function
import os, sys
from glob import glob
import argparse
import xml_input
import metaq_input

parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('run',nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-f',type=str,default='a12m310_a_src.lst',help='cfg/src file')
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('-t','--t_sep',nargs='+',type=int,help='values of t_sep [default = all]')
parser.add_argument('-d','--debug',default=False,action='store_const',const=True,\
    help='run DEBUG? [%(default)s]')
args = parser.parse_args()
print('%s: Arguments passed' %sys.argv[0].split('/')[-1])
print(args)
print('')

ri = args.run[0]
if len(args.run) == 1:
    rf = ri+1
    dr = 1
elif len(args.run) == 2:
    rf = args.run[1]+1
    dr = 1
else:
    rf = args.run[1]+1
    dr = args.run[2]
cfgs_run = range(ri,rf,dr)

print(args.run)
nt = '64'
nx = '24'
M5 = '1.2'
L5 = '8'
b5 = '1.25'
c5 = '0.25'
alpha5 = '1.5'
smr = 'gf1.0_w3.0_n30'
val = smr+'_M5'+M5+'_L5'+L5+'_a'+alpha5
mq = '0.0126'
max_iter = '12000'
rsd_target = '5.e-7'
delta = '0.1'
rsd_tol = '100'

ens = 'a12m310_a'
stream = ens.split('_')[-1]

params = {
    'ENS':ens,
    'NL':nx,'NT':nt,
    'M5':M5,'L5':L5,'B5':b5,'C5':c5,'MQ':mq,
    'MAX_ITER':max_iter,'RSD_TARGET':rsd_target,'Q_DELTA':delta,'RSD_TOL':rsd_tol,
    }

base_dir       = '/p/gpfs1/walkloud/c51/x_files/project_2/production/a12m310_a'
cfg_dir        = '/p/gpfs1/walkloud/c51/x_files/project_2/production/a12m310_a/cfgs_flow'
metaq_test_dir = '/p/gpfs1/walkloud/c51/x_files/project_2/production/a12m310_a/runs'
metaq_run_dir  = '/p/gpfs1/walkloud/c51/x_files/project_2/metaq'

metaq_dir = metaq_run_dir

smr = 'gf1.0_w3.0_n30'
val = smr+'_M51.2_L58_a1.5'
mq  = '0.0126'

SS_PS = 'PS'

cfg_srcs = open(args.f).readlines()
cfgs = []
srcs = {}
for c in cfg_srcs:
    no = c.split()[0]
    cfg = int(no)
    if no not in cfgs and cfg in cfgs_run:
        cfgs.append(no)
    if no not in srcs:
        srcs[no] = []
print('running ',cfgs[0],'-->',cfgs[-1])

if args.t_sep == None:
    t_seps  = [1,2,3,4,5,6,7,8,9,10,11,12]
else:
    t_seps = args.t_sep
flavs    = ['UU','DD']
spins    = ['up_up','dn_dn']
''' ONLY doing snk_mom 0 0 0 now '''
snk_moms = ['0 0 0']

print(t_seps)
seqsource_lims = [8]

for cs in cfg_srcs:
    no,x0,y0,z0,t0 = cs.split()
    src = 'x'+x0+'y'+y0+'z'+z0+'t'+t0
    if src not in srcs[no]:
        srcs[no].append(src)
if args.debug:
    for c in cfgs:
        print(c,srcs[c])

for c in cfgs:
    no = c
    if len(srcs[c]) == 8:#hard wired to 8 coherent sinks
        all_srcs = True
    else:
        all_srcs = False
    cfg_file = cfg_dir+'/l2464f211b600m0102m0509m635'+stream+'.'+c+'_wflow1.0.lime'
    if os.path.exists(cfg_file) and all_srcs:
        params.update({'CFG_FILE':cfg_file})
        print("Checking coherent formfactor for cfg: ",c)

        if not os.path.exists(base_dir+'/props/'+c):
            os.makedirs(base_dir+'/props/'+c)
        if not os.path.exists(base_dir+'/xml/'+c):
            os.makedirs(base_dir+'/xml/'+c)
        if not os.path.exists(base_dir+'/stdout/'+c):
            os.makedirs(base_dir+'/stdout/'+c)
        if not os.path.exists(base_dir+'/corrs_3pt/'+c):
            os.makedirs(base_dir+'/corrs_3pt/'+c)

        # make sure all props are ready
        all_props=True
        for s0 in srcs[c]:
            prop_name = 'prop_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0
            prop_file = base_dir+'/props/'+no + '/' + prop_name+'.h5'
            if not os.path.exists(prop_file):
                print('    missing',prop_file)
                all_props=False

        if all_props:
            for lim in seqsource_lims:
                for dt_int in t_seps:
                    dt = str(dt_int)
                    for snk_mom in snk_moms:
                        m0,m1,m2 = snk_mom.split()
                        mom = 'px%spy%spz%s' %(m0,m1,m2)
                        ''' Does the 3pt file exist? '''
                        coherent_formfac_name  = 'formfac_prot_'+ens+'_'+val+'_mq'+mq
                        coherent_formfac_name += '_'+c+'_'+mom+'_dt_'+dt+'_'
                        coherent_formfac_name += 'srcs_'+str(lim)+'_'+SS_PS
                        coherent_formfac_file  = base_dir+'/corrs_3pt/'+c + '/'
                        coherent_formfac_file += coherent_formfac_name + '.h5'
                        coherent_formfac_file_4D = coherent_formfac_file.replace('.h5','_4D.h5')
                        params['THREE_PT_FILE'] = coherent_formfac_file
                        params['THREE_PT_FILE_4D'] = coherent_formfac_file_4D
                        if not os.path.exists(coherent_formfac_file) and not os.path.exists(coherent_formfac_file_4D):
                            # loop over FLAV and SPIN as all in 1 file
                            all_seqprops=True
                            for flav in flavs:
                                for spin in spins:
                                    seqprop_name  = 'prop_prot_'+flav+'_'+spin
                                    seqprop_name += '_'+ens+'_'+val+'_mq'+mq+'_'+c+'_'+mom
                                    seqprop_name += '_dt_'+dt+'_srcs_'+str(lim)+'_'+SS_PS
                                    seqprop_file = base_dir+'/props/'+c+'/'+seqprop_name+'.h5'
                                    if not os.path.exists(seqprop_file):
                                        print('    missing:',seqprop_file)
                                        all_seqprops=False
                            if all_seqprops:
                                metaq  = coherent_formfac_name+'.sh'
                                metaq_file = metaq_dir +'/priority/cpu/'+metaq
                                task_exist = False
                                task_working = False
                                if os.path.exists(metaq_file):
                                    task_exist = True
                                for m_dir in ['todo/cpu','priority/cpu','hold']:
                                    if os.path.exists(metaq_dir+'/'+m_dir+'/'+metaq):
                                        task_exist = True
                                task_lst = glob(metaq_dir+'/working/*/*.sh')
                                task_lst += glob(metaq_dir+'/working/*/*/*.sh')
                                for task in task_lst:
                                    if metaq == task.split('/')[-1]:
                                        task_exist = True
                                        task_working = True
                                if not task_exist or (args.o and task_exist and not task_working):
                                    xmlini = coherent_formfac_file.replace('/corrs_3pt/','/xml/').replace('.h5','.ini.xml')
                                    fin = open(xmlini,'w')
                                    fin.write(xml_input.head)
                                    ''' read all props '''
                                    for s0 in srcs[c]:
                                        prop_name = 'prop_'+ens+'_'+val+'_mq'+mq+'_'+c+'_'+s0
                                        prop_file = base_dir+'/props/'+c+'/'+prop_name+'.h5'
                                        params['H5_FILE']=prop_file
                                        params['OBJ_ID']=prop_name
                                        params['H5_PATH']=''
                                        params['H5_OBJ_NAME']='propagator'
                                        params['OBJ_TYPE']='LatticePropagatorF'
                                        fin.write(xml_input.hdf5_read % params)
                                    ''' read all seq props '''
                                    for flav in flavs:
                                        for spin in spins:
                                            seqprop_name  = 'prop_prot_'+flav+'_'+spin+'_'+ens+'_'
                                            seqprop_name += val+'_mq'+mq+'_'+c+'_'+mom+'_dt_'+dt+'_'+'srcs_'+str(lim)+'_'+SS_PS
                                            seqprop_file = base_dir+'/props/'+c+'/'+seqprop_name+'.h5'
                                            params['H5_FILE']=seqprop_file
                                            params['OBJ_ID']=seqprop_name
                                            fin.write(xml_input.hdf5_read % params)
                                    f_seqprop_base  = 'prop_prot_%s_'+ens+'_'+val+'_mq'+mq+'_'+c+ '_'+mom+'_dt_'+dt+'_'
                                    f_seqprop_base += 'srcs_'+str(lim) + '_'+SS_PS
                                    f_dn_s_up_up_seqprop = f_seqprop_base %('DD_up_up')
                                    f_dn_s_dn_dn_seqprop = f_seqprop_base %('DD_dn_dn')
                                    f_up_s_dn_dn_seqprop = f_seqprop_base %('UU_dn_dn')
                                    f_up_s_up_up_seqprop = f_seqprop_base %('UU_up_up')
                                    params.update({
                                        'UU_FLAVOR_UU_SPIN_SEQPROP_NAME':f_up_s_up_up_seqprop,
                                        'DD_FLAVOR_UU_SPIN_SEQPROP_NAME':f_dn_s_up_up_seqprop,
                                        'UU_FLAVOR_DD_SPIN_SEQPROP_NAME':f_up_s_dn_dn_seqprop,
                                        'DD_FLAVOR_DD_SPIN_SEQPROP_NAME':f_dn_s_dn_dn_seqprop
                                        })
                                    ''' make 3pt contractions '''
                                    for s0 in srcs[c]:
                                        prop_name = 'prop_'+ens+'_'+val+'_mq'+mq+'_'+c+'_'+s0
                                        params['PROP_NAME'] = prop_name
                                        fin.write(xml_input.lalibe_formfac % params)
                                    fin.write(xml_input.tail % params)
                                    fin.close()

                                    # Make METAQ task
                                    params.update({
                                        'XML_IN':xmlini,'XML_OUT':xmlini.replace('.ini.xml','.out.xml'),
                                        'STDOUT':xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/'),
                                        'METAQ_LOG':base_dir+'/metaq/log/'+metaq.replace('.sh','.log'),
                                        'BASE_DIR':base_dir,'METAQ_RUN':metaq_file,'METAQ_FINISHED':metaq_file.replace('runs','finished')
                                        })
                                    m_in = open(metaq_file,'w')
                                    m_in.write(metaq_input.formfac_contractions % params)
                                    m_in.close()
                                    os.chmod(metaq_file,0o770)
                                else:
                                    print('  task exists:',metaq)
                            else:
                                print('    missing FLAV or SPIN seqprops')
                                os.system('python METAQ_coherent_seqprop.py %s -t %d' %(c,dt_int))
                        else:
                            print('    exists:',coherent_formfac_file)
        else:
            print('    missing props')
    else:
        if not os.path.exists(cfg_file):
            print('  flowed cfg missing',cfg_file)
        elif not all_srcs:
            print('missing srcs [8]')
            print(c,srcs[c])
