from __future__ import print_function
import os, sys, shutil
from glob import glob
import argparse
import xml_input_ff as xml_input
import metaq_input_ff as metaq_input

try:
    ens = os.getcwd().split('/')[-3]
except:
    ens,junk = os.getcwd().split('/')[-3]
stream = ens.split('_')[-1]
ens_long='l3296f211b630m0074m037m440'

parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('run',nargs='+',type=int,help='start [stop] run number')
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
    }

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
coherent_ff_base  = 'formfac_'+ens+'_'+val+'_mq'+mq+'_%(CFG)s_'
coherent_ff_base += mom+'_dt%(T_SEP)s_Nsnk'+str(n_seq)+'_%(SRC)s_'+SS_PS
seqprop_base      = 'seqprop_%(PARTICLE)s_%(FLAV_SPIN)s_'+ens+'_'+val+'_mq'+mq+'_%(CFG)s_'
seqprop_base     += mom+'_dt%(T_SEP)s_Nsnk'+str(n_seq)+'_'+SS_PS
seqprop_size = int(nt)* int(nx)**3 * 3**2 * 4**2 * 2 * 4
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
    params['CFG'] = no
    if len(srcs[c]) == n_seq:
        all_srcs = True
    else:
        all_srcs = False
    cfg_file = cfg_dir+'/'+ens_long+stream+'.'+c+'_wflow1.0.lime'
    if os.path.exists(cfg_file) and all_srcs:
        params.update({'CFG_FILE':cfg_file})
        print("Checking coherent formfactor for cfg: ",c)

        if not os.path.exists(base_dir+'/xml/'+c):
            os.makedirs(base_dir+'/xml/'+c)
        if not os.path.exists(base_dir+'/stdout/'+c):
            os.makedirs(base_dir+'/stdout/'+c)
        if not os.path.exists(base_dir+'/formfac/'+c):
            os.makedirs(base_dir+'/formfac/'+c)
        if not os.path.exists(base_dir+'/corrupt'):
            os.makedirs(base_dir+'/corrupt')

        # make sure all props are ready
        '''
        all_props=True
        for s0 in srcs[c]:
            prop_name = prop_base %{'CFG':no,'SRC':s0}
            prop_file = base_dir+'/props/'+no + '/' + prop_name+'.'+sp_ext
            if not os.path.exists(prop_file):
                print('    missing',prop_file)
                all_props=False
        To improve load balancing of work, we are splitting each src to a different task
        '''
        #if all_props:
        for dt_int in t_seps:
            dt = str(dt_int)
            ''' Do all seqprops exist? '''
            all_seqprops=True
            for fs in flav_spin:
                flav,snk_spin,src_spin=fs.split('_')
                params['FLAV']=flav
                params['SOURCE_SPIN']=snk_spin
                params['SINK_SPIN']=src_spin
                spin = snk_spin+'_'+src_spin
                params['FLAV_SPIN']=fs
                for particle in particles:
                    params['PARTICLE'] = particle
                    if '_np' in particle:
                        params['T_SEP'] = '-'+dt
                    else:
                        params['T_SEP'] = dt
                    seqprop_name  = seqprop_base % params
                    seqprop_file  = base_dir+'/seqprops/'+c+'/'+seqprop_name+'.'+sp_ext
                    if os.path.exists(seqprop_file) and os.path.getsize(seqprop_file) < seqprop_size:
                        now = time.time()
                        file_time = os.stat(seqprop_file).st_mtime
                        if (now-prop_time)/60 > time_delete:
                            print('DELETING BAD PROP',os.path.getsize(seqprop_file),seqprop_file.split('/')[-1])
                            shutil.move(seqprop_file,seqprop_file.replace('seqprops/'+c+'/','corrupt/'))
                    if not os.path.exists(seqprop_file):
                        print('    missing:',seqprop_file)
                        all_seqprops=False
            if all_seqprops:
                ''' loop over srcs '''
                for s0 in srccs[c]:
                    params['SRC'] = s0
                    ''' Does the 3pt file exist? '''
                    coherent_formfac_name  = coherent_ff_base %{'CFG':c,'T_SEP':dt,'SRC':s0}
                    coherent_formfac_file  = base_dir+'/formfac/'+c + '/'+coherent_formfac_name+'.h5'
                    coherent_formfac_file_4D = coherent_formfac_file.replace('.h5','_4D.h5')
                    params['THREE_PT_FILE'] = coherent_formfac_file
                    params['THREE_PT_FILE_4D'] = coherent_formfac_file_4D
                    if not os.path.exists(coherent_formfac_file) and not os.path.exists(coherent_formfac_file_4D):
                        # loop over FLAV and SPIN as all in 1 file
                        metaq  = coherent_formfac_name+'.sh'
                        metaq_file = metaq_dir +'/'+args.priority+'/cpu/'+metaq
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
                            prop_name = prop_base %{'CFG':no,'SRC':s0}
                            prop_file = base_dir+'/props/'+c+'/'+prop_name+'.'+sp_ext
                            if os.path.exists(prop_file):
                                xmlini = coherent_formfac_file.replace('/formfac/','/xml/').replace('.h5','.ini.xml')
                                fin = open(xmlini,'w')
                                fin.write(xml_input.head)
                                ''' read all props '''
                                #for s0 in srcs[c]:
                                params['H5_FILE']=prop_file
                                params['H5_PATH']=''
                                params['H5_OBJ_NAME']='propagator'
                                params['LIME_FILE'] = prop_file
                                params['OBJ_ID']    = prop_name
                                params['OBJ_TYPE']  = 'LatticePropagator'
                                fin.write(xml_input.qio_read % params)

                                ''' read all seq props and do contractions '''
                                for particle in particles:
                                    params['PARTICLE'] = particle
                                    if '_np' in particle:
                                        t_sep = '-'+dt
                                    else:
                                        t_sep = dt
                                    params['T_SEP'] = t_sep
                                    for fs in flav_spin:
                                        flav,snk_spin,src_spin=fs.split('_')
                                        params['FLAV']=flav
                                        params['SOURCE_SPIN']=snk_spin
                                        params['SINK_SPIN']=src_spin
                                        spin = snk_spin+'_'+src_spin
                                        params['FLAV_SPIN']=fs
                                        seqprop_name  = seqprop_base % params
                                        seqprop_file  = base_dir+'/seqprops/'+c+'/'+seqprop_name+'.'+sp_ext
                                        params['LIME_FILE'] = seqprop_file
                                        params['OBJ_ID']    = seqprop_name
                                        fin.write(xml_input.qio_read % params)
                                    f_dn_s_up_up_seqprop = seqprop_base %{'PARTICLE':particle,'FLAV_SPIN':'DD_up_up','CFG':c,'T_SEP':t_sep}
                                    f_dn_s_dn_dn_seqprop = seqprop_base %{'PARTICLE':particle,'FLAV_SPIN':'DD_dn_dn','CFG':c,'T_SEP':t_sep}
                                    f_up_s_dn_dn_seqprop = seqprop_base %{'PARTICLE':particle,'FLAV_SPIN':'UU_dn_dn','CFG':c,'T_SEP':t_sep}
                                    f_up_s_up_up_seqprop = seqprop_base %{'PARTICLE':particle,'FLAV_SPIN':'UU_up_up','CFG':c,'T_SEP':t_sep}
                                    params.update({
                                        'UU_FLAVOR_UU_SPIN_SEQPROP_NAME':f_up_s_up_up_seqprop,
                                        'DD_FLAVOR_UU_SPIN_SEQPROP_NAME':f_dn_s_up_up_seqprop,
                                        'UU_FLAVOR_DD_SPIN_SEQPROP_NAME':f_up_s_dn_dn_seqprop,
                                        'DD_FLAVOR_DD_SPIN_SEQPROP_NAME':f_dn_s_dn_dn_seqprop
                                        })
                                    #for s0 in srcs[c]:
                                    prop_name = prop_base %{'CFG':no,'SRC':s0}
                                    params['PROP_NAME'] = prop_name

                                    ''' make 3pt contractions '''
                                    fin.write(xml_input.lalibe_formfac % params)
                                    #''' erase seqprops '''
                                    #fin.write(xml_input.qio_erase %{'OBJ_ID':f_dn_s_up_up_seqprop})
                                    #fin.write(xml_input.qio_erase %{'OBJ_ID':f_dn_s_dn_dn_seqprop})
                                    #fin.write(xml_input.qio_erase %{'OBJ_ID':f_up_s_dn_dn_seqprop})
                                    #fin.write(xml_input.qio_erase %{'OBJ_ID':f_up_s_up_up_seqprop})

                                fin.write(xml_input.tail % params)
                                fin.close()

                                # Make METAQ task
                                params.update({
                                    'XML_IN':xmlini,'XML_OUT':xmlini.replace('.ini.xml','.out.xml'),
                                    'STDOUT':xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/'),
                                    'METAQ_LOG':metaq_run_dir+'/log/'+metaq.replace('.sh','.log'),
                                    'BASE_DIR':base_dir,'METAQ_RUN':metaq_file,'METAQ_FINISHED':metaq_file.replace('runs','finished')
                                    })
                                m_in = open(metaq_file,'w')
                                m_in.write(metaq_input.formfac_contractions % params)
                                m_in.close()
                                os.chmod(metaq_file,0o770)
                                print('    making task:',metaq)
                            else:
                                print('MISSING prop',prop_file)
                        else:
                            print('  task exists:',metaq)
                    else:
                        print('    exists:',coherent_formfac_file)
            else:
                print('    missing FLAV or SPIN seqprops')
                os.system('python METAQ_coherent_seqprop.py %s -t %d' %(c,abs(dt_int)))
        #else:
        #    print('    missing props')
    else:
        if not os.path.exists(cfg_file):
            print('  flowed cfg missing',cfg_file)
        elif not all_srcs:
            print('missing srcs [8]')
            print(c,srcs[c])
