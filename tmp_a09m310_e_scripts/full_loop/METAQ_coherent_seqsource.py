from __future__ import print_function
import os, sys, time
from glob import glob
import argparse
import xml_input
import metaq_input

parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('run',nargs='+',type=int,help='start [stop] run cfg number')
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

''' time in minutes to define "old" file '''
time_delete = 10

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
wf_s='3.0'
wf_n='30'
smr = 'gf1.0_w'+wf_s+'_n'+wf_n
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
    'WF_S':wf_s,'WF_N':wf_n}

base_dir = '/p/gpfs1/walkloud/c51/x_files/project_2/production/a12m310_a'
params['BASE_DIR'] = base_dir
cfg_dir = '/p/gpfs1/walkloud/c51/x_files/project_2/production/a12m310_a/cfgs_flow'
metaq_test_dir = '/p/gpfs1/walkloud/c51/x_files/project_2/production/a12m310_a/runs'
metaq_run_dir  = '/p/gpfs1/walkloud/c51/x_files/project_2/metaq'

metaq_dir = metaq_run_dir

SS_PS = 'SS'

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
#print('total cfgs = ',len(cfgs))
#cfgs = cfgs[ri:rf:dr]
print('running ',cfgs[0],'-->',cfgs[-1])

if args.t_sep == None:
    t_seps  = [3,4,5,6,7,8,9,10,11,12]
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
        print("Making coherent sources for cfg: ",c)

        if not os.path.exists(base_dir+'/props/'+c):
            os.makedirs(base_dir+'/props/'+c)
        if not os.path.exists(base_dir+'/xml/'+c):
            os.makedirs(base_dir+'/xml/'+c)
        if not os.path.exists(base_dir+'/stdout/'+c):
            os.makedirs(base_dir+'/stdout/'+c)
        if not os.path.exists(base_dir+'/spectrum/'+c):
            os.makedirs(base_dir+'/spectrum/'+c)
        if not os.path.exists(base_dir+'/snks/'+c):
            os.makedirs(base_dir+'/snks/'+c)

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
                        params['M0']=m0
                        params['M1']=m1
                        params['M2']=m2
                        mom = 'px%spy%spz%s' %(m0,m1,m2)
                        ''' Does the 3pt file exist? '''
                        coherent_formfac_name  = 'formfac_prot_'+ens+'_'+val+'_mq'+mq
                        coherent_formfac_name += '_'+c+'_'+mom+'_dt_'+dt+'_'
                        coherent_formfac_name += 'srcs_'+str(lim)+'_'+SS_PS
                        coherent_formfac_file  = base_dir+'/corrs_3pt/'+c + '/'
                        coherent_formfac_file += coherent_formfac_name + '.h5'
                        coherent_formfac_file_4D = coherent_formfac_file.replace('.h5','_4D.h5')
                        if not os.path.exists(coherent_formfac_file) and not os.path.exists(coherent_formfac_file_4D):
                            for flav in flavs:
                                params['FLAV']=flav
                                for spin in spins:
                                    snk_spin,src_spin=spin.split('_')
                                    params['SOURCE_SPIN']=snk_spin
                                    params['SINK_SPIN']=src_spin
                                    seqprop_name  = 'prop_prot_'+flav+'_'+spin
                                    seqprop_name += '_'+ens+'_'+val+'_mq'+mq+'_'+c+'_'+mom
                                    seqprop_name += '_dt_'+dt+'_srcs_'+str(lim)+'_'+SS_PS
                                    seqprop_file  = base_dir+'/props/'+c+'/'+seqprop_name+'.h5'
                                    ''' check SEQPROP file size
                                        delete if small and older than time_delete
                                    '''
                                    seqprop_size = int(nt)* int(nx)**3 * 3**2 * 4**2 * 2 * 4
                                    if os.path.exists(seqprop_file) and os.path.getsize(seqprop_file) < seqprop_size:
                                        now = time.time()
                                        file_time = os.stat(seqprop_file).st_mtime
                                        if (now-prop_time)/60 > time_delete:
                                            print('DELETING BAD PROP',os.path.getsize(seqprop_file),seqprop_file.split('/')[-1])
                                            os.remove(seqprop_file)
                                    seqsrc_name  = seqprop_name.replace('prop_prot','snk_prot')
                                    seqsrc_file  = base_dir+'/snks/'+c+'/'
                                    seqsrc_file += seqsrc_name+'.lime'
                                    if not os.path.exists(seqprop_file):
                                        ''' check if coherent sink exists and size is good '''
                                        if os.path.exists(seqsrc_file) and os.path.getsize(seqsrc_file) < seqprop_size:
                                            now = time.time()
                                            file_time = os.stat(seqsrc_file).st_mtime
                                            if (now-prop_time)/60 > time_delete:
                                                print('DELETING BAD COHERENT SINK',os.path.getsize(seqsrc_file),seqsrc_file.split('/')[-1])
                                                os.remove(seqsrc_file)
                                        if not os.path.exists(seqsrc_file):
                                            metaq  = seqsrc_name+'.sh'
                                            metaq_file = metaq_dir +'/priority/cpu/'+'/'+metaq
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
                                                xmlini = seqsrc_file.replace('snks/','xml/').replace('.lime','.ini.xml')
                                                fin = open(xmlini,'w')
                                                fin.write(xml_input.head)
                                                ''' read all props '''
                                                params['OBJ_TYPE']    = 'LatticePropagatorF'
                                                params['H5_PATH']     = ''
                                                params['H5_OBJ_NAME'] = 'propagator'
                                                for si,s0 in enumerate(srcs[c]):
                                                    t0=int(s0.split('t')[1])
                                                    params['TSINK']=str( (t0 + dt_int) % int(nt))
                                                    prop_name = 'prop_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0
                                                    prop_file = base_dir+'/props/'+no + '/' + prop_name+'.h5'
                                                    params['OBJ_ID']      = prop_name
                                                    params['H5_FILE']     = prop_file
                                                    fin.write(xml_input.hdf5_read % params)
                                                    ''' do smearing if need be '''
                                                    if SS_PS == 'SS':
                                                        params['SMEARED_PROP'] = prop_name+'_SS'
                                                        fin.write(xml_input.shell_smearing % params)
                                                        params['UP_QUARK']=prop_name+'_SS'
                                                        params['DOWN_QUARK']=prop_name+'_SS'
                                                    else:
                                                        params['UP_QUARK']=prop_name
                                                        params['DOWN_QUARK']=prop_name
                                                    params['SEQSOURCE']='prot_'+flav+'_'+spin+'_'+s0+'_'
                                                    params['SEQSOURCE']+=snk_mom+'_dt_'+dt+'_'+SS_PS
                                                    params['SEQSOURCE_'+str(si)]=params['SEQSOURCE']
                                                    ''' make seqsource '''
                                                    fin.write(xml_input.lalibe_seqsource % params)
                                                params['COHERENT_SEQSOURCE']=seqsrc_name
                                                ''' make coherent seqsource and write to disk '''
                                                fin.write(xml_input.add_8_coherent_sinks % params)
                                                params['OBJ_ID']=seqsrc_name
                                                params['OBJ_TYPE']='LatticePropagatorF'
                                                params['LIME_FILE'] = seqsrc_file
                                                fin.write(xml_input.qio_write % params)

                                                fin.write(xml_input.tail % params)
                                                fin.close()

                                                ''' Make METAQ task '''
                                                params['METAQ_LOG'] = base_dir+'/metaq/log/'+metaq.replace('.sh','.log')
                                                params['XML_IN'] = xmlini
                                                params['XML_OUT'] = xmlini.replace('.ini.xml','.out.xml')
                                                params['STDOUT'] = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                                                params['CR'] = c
                                                params['T_SEP'] = dt

                                                m_in = open(metaq_file,'w')
                                                m_in.write(metaq_input.seqsource % params)
                                                m_in.close()
                                                os.chmod(metaq_file,0o770)

                                            else:
                                                print('    task exists:',metaq)
                                        else:
                                            print('    seqsrc exists:',seqsrc_file)
                                    else:
                                        print('    already exists: removing coherent sink')
                                        ''' check SEQPROP file size and remove src '''
                                        if os.path.exists(seqprop_file) and os.path.getsize(seqprop_file) >= seqprop_size:
                                            os.remove(seqsrc_file)
                                            for xml_r in ['_propagator_file.xml','_propagator_record.xml']:
                                                if os.path.exists(seqsrc_file.replace('.h5',xml_r)):
                                                    os.remove(seqsrc_file.replace('.h5',xml_r))
                        else:
                            print('    3pt corr exists:',coherent_formfac_file)
        else:
            print('    missing some props')
    else:
        if not os.path.exists(cfg_file):
            print('  flowed cfg missing',cfg_file)
        elif not all_srcs:
            print('missing srcs [8]')
            print(c,srcs[c])
