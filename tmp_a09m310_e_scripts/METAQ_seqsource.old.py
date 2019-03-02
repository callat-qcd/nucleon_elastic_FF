from __future__ import print_function
import os, sys, time
from glob import glob
import argparse
import xml_input_ff as xml_input
import metaq_input_ff as metaq_input

#ens = 'a09m310_e'
try:
    ens = os.getcwd().split('/')[-2]
except:
    ens,junk = os.getcwd().split('/')[-2]
stream = ens.split('_')[-1]
ens_long='l3296f211b630m0074m037m440'

parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('run',nargs='+',type=int,help='start [stop] run cfg number')
parser.add_argument('-f',type=str,default=ens+'_src.lst',help='cfg/src file')
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('-t','--t_sep',nargs='+',type=int,help='values of t_sep [default = all]')
parser.add_argument('-d','--debug',default=False,action='store_const',const=True,\
    help='run DEBUG? [%(default)s]')
parser.add_argument('-p','--priority',type=str,default='todo',help='put task in priority? [%(default)s]')
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
nt = '96'
nx = '32'
M5 = '1.1'
L5 = '6'
b5 = '1.25'
c5 = '0.25'
alpha5 = '1.5'
wf_s='3.5'
wf_n='45'
smr = 'gf1.0_w'+wf_s+'_n'+wf_n
val = smr+'_M5'+M5+'_L5'+L5+'_a'+alpha5
mq = '0.00951'
max_iter = '12000'
rsd_target = '1.e-7'
delta = '0.1'
rsd_tol = '80'

params = {
    'ENS':ens,
    'NL':nx,'NT':nt,
    'M5':M5,'L5':L5,'B5':b5,'C5':c5,'MQ':mq,
    'MAX_ITER':max_iter,'RSD_TARGET':rsd_target,'Q_DELTA':delta,'RSD_TOL':rsd_tol,
    'WF_S':wf_s,'WF_N':wf_n}

base_dir = '/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/'+ens
params['SCRIPT_DIR'] = '/ccs/proj/lgt100/c51/x_files/project_2/production/'+ens+'/scripts'
cfg_dir = '/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/'+ens+'/cfgs_flow'
metaq_run_dir  = '/ccs/proj/lgt100/c51/x_files/project_2/metaq'
metaq_dir = metaq_run_dir

if args.t_sep == None:
    t_seps  = [3,4,5,6,7,8,9,10,11,12]
else:
    t_seps = args.t_sep
flavs = ['UU','DD']
spins = ['up_up','dn_dn']
flav_spin = []
for f in flavs:
    for s in spins:
        flav_spin.append(f+'_'+s)
''' ONLY doing snk_mom 0 0 0 now '''
snk_mom = '0 0 0'
m0,m1,m2 = snk_mom.split()
params['M0']=m0
params['M1']=m1
params['M2']=m2
mom = 'px%spy%spz%s' %(m0,m1,m2)

SS_PS = 'SS'
n_seq=8
particles = ['proton','proton_np']
seqsrc_base       = 'seqsrc_%(PARTICLE)s_%(FLAV_SPIN)s_'+ens+'_'+val+'_mq'+mq+'_%(CFG)s_'
seqsrc_base      += '_%(SRC)s_'+mom+'_'+SS_PS
seqsrc_size       = int(nt)* int(nx)**3 * 3**2 * 4**2 * 2 * 4
sp_ext = 'lime'

prop_base = 'prop_'+ens+'_'+val+'_mq'+mq+'_%(CFG)s_%(SRC)s'

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
    if len(srcs[c]) == n_seq:
        all_srcs = True
    else:
        all_srcs = False
    cfg_file = cfg_dir+'/'+ens_long+stream+'.'+c+'_wflow1.0.lime'
    if os.path.exists(cfg_file) and all_srcs:
        params.update({'CFG_FILE':cfg_file})
        print("Making coherent sources for cfg: ",c)

        if not os.path.exists(base_dir+'/xml/'+c):
            os.makedirs(base_dir+'/xml/'+c)
        if not os.path.exists(base_dir+'/stdout/'+c):
            os.makedirs(base_dir+'/stdout/'+c)
        if not os.path.exists(base_dir+'/snks/'+c):
            os.makedirs(base_dir+'/snks/'+c)
        if not os.path.exists(base_dir+'/corrupt'):
            os.makedirs(base_dir+'/corrupt')

        # loop over props to make a time-dense seqsource for each prop
        for s0 in srcs[c]:
            prop_name = prop_base %{'CFG':no,'SRC':s0}
            prop_file = base_dir+'/props/'+no + '/' + prop_name+'.'+sp_ext
            if os.path.exists(prop_file):
                for particle in particles:
                    params['PARTICLE'] = particle
                    for fs in flav_spin:
                        flav,snk_spin,src_spin=fs.split('_')
                        params['FLAV']=flav
                        params['SOURCE_SPIN']=snk_spin
                        params['SINK_SPIN']=src_spin
                        spin = snk_spin+'_'+src_spin
                        seqsrc_name = seqsrc_base %{'PARTICLE':particle,'FLAV_SPIN':fs,'CFG':c,'SRC':s0}
                        seqsrc_file  = base_dir+'/snks/'+c+'/'+seqsrc_name+'.'+sp_ext
                        if os.path.exists(seqsrc_file) and os.path.getsize(seqsrc_file) < seqsrc_size:
                            now = time.time()
                            file_time = os.stat(seqsrc_file).st_mtime
                            if (now-file_time)/60 > time_delete:
                                print('DELETING BAD SINK',os.path.getsize(seqsrc_file),seqsrc_file.split('/')[-1])
                                shutil.move(seqsrc_file,seqsrc_file.replace('snks/'+c,'corrupt'))
                        if not os.path.exists(seqsrc_file):
                            metaq  = seqsrc_name+'.sh'
                            metaq_file = metaq_dir +'/'+args.priority+'/cpu/'+'/'+metaq
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
                                params['OBJ_TYPE']    = 'LatticePropagator'
                                params['H5_PATH']     = ''
                                params['H5_OBJ_NAME'] = 'propagator'
                                t0=int(s0.split('t')[1])
                                params['OBJ_ID']      = prop_name
                                ''' ADD SWITCH BASED ON PROP EXTENSION, H5 vs LIME '''
                                params['H5_FILE']     = prop_file
                                params['LIME_FILE']   = prop_file
                                params['PROP_NAME']   = prop_name
                                fin.write(xml_input.qio_read % params)
                                ''' do smearing if need be '''
                                if SS_PS == 'SS':
                                    params['SMEARED_PROP'] = prop_name+'_SS'
                                    fin.write(xml_input.shell_smearing % params)
                                    params['UP_QUARK']=prop_name+'_SS'
                                    params['DOWN_QUARK']=prop_name+'_SS'
                                else:
                                    params['UP_QUARK']=prop_name
                                    params['DOWN_QUARK']=prop_name
                                params['SEQSOURCE']=snk_base %{'FLAV_SPIN':fs,'CFG':c,'SRC':s0,'DT':dt}
                                params['SEQSOURCE_'+str(si)]=params['SEQSOURCE']
                                ''' make seqsource '''
                                fin.write(xml_input.lalibe_seqsource % params)
                                fin.write(xml_input.qio_erase % {'OBJ_ID':prop_name})
                                if SS_PS == 'SS':
                                    fin.write(xml_input.qio_erase % {'OBJ_ID':prop_name+'_SS'})

            else:
                print('    missing',prop_file)


                            if not os.path.exists(seqsrc_file):
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
                                    params['METAQ_LOG'] = metaq_run_dir+'/log/'+metaq.replace('.sh','.log')
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
                                if os.path.exists(seqsrc_file):
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
