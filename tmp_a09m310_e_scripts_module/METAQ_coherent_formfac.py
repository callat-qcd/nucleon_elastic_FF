from __future__ import print_function
import os, sys, shutil, time
from glob import glob
import argparse
import xml_input
import metaq_input
import importlib
import management
import sources

try:
    ens_s = os.getcwd().split('/')[-3]
except:
    ens_s,junk = os.getcwd().split('/')[-3]
ens,stream = ens_s.split('_')

sys.path.append('area51_files')
area51 = importlib.import_module(ens)
params = area51.params
ens_long=params['ENS_LONG']
params['ENS_S'] = ens_s

parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('run',nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-s','--src',type=str)
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('-t','--t_sep',nargs='+',type=int,help='values of t_sep [default = all]')
parser.add_argument('-d','--debug',default=False,action='store_const',const=True,\
    help='run DEBUG? [%(default)s]')
parser.add_argument('-p','--priority',type=str,default='todo',help='put task in priority? [%(default)s]')
parser.add_argument('-v','--verbose',default=True,action='store_const',const=False,\
    help='run with verbose output? [%(default)s]')
args = parser.parse_args()
print('%s: Arguments passed' %sys.argv[0].split('/')[-1])
print(args)
print('')

''' time in minutes to define "old" file '''
time_delete = params['prop_time_delete']

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

''' BUILD SRC DICTIONARY '''
nt = int(params['NT'])
nl = int(params['NL'])
if args.src:
    if len(args.cfgs) > 1:
        print('if a src is passed, only 1 cfg can be specified which is presumably the right one')
        sys.exit(-1)
    else:
        cfgs = args.cfgs
        srcs = {int(args.cfgs[0]):[args.src]}
else:
    srcs = {}
    for c in cfgs_run:
        no = str(c)
        srcs_cfg = sources.make(no, nl=nl, nt=nt, t_shifts=params['t_shifts'],
            generator=params['generator'], seed=params['seed'][stream])
        srcs[c] = []
        for origin in srcs_cfg:
            try:
                src_gen = srcs_cfg[origin].iteritems()
            except AttributeError: # Python 3 automatically creates a generator
                src_gen = srcs_cfg[origin].items()
            for src_type, src in src_gen:
                srcs[c].append(sources.xXyYzZtT(src))
print('running ',cfgs_run[0],'-->',cfgs_run[-1])

if args.priority:
    priority = '-p'
    q = 'priority'
else:
    priority = ''
    q = 'todo'
params['PRIORITY'] = priority

smr = 'gf'+params['FLOW_TIME']+'_w'+params['WF_S']+'_n'+params['WF_N']
val = smr+'_M5'+params['M5']+'_L5'+params['L5']+'_a'+params['alpha5']
params['MQ'] = params['MV_L']

base_dir = management.base_dir % params
params['SCRIPT_DIR'] = management.script_dir % params
cfg_dir = base_dir+'/cfgs_flow'
metaq_dir  = management.metaq_dir

if args.t_sep == None:
    t_seps  = params['t_seps']
else:
    t_seps = args.t_sep
flavs = params['flavs']
spins = params['spins']
flav_spin = []
for f in flavs:
    for s in spins:
        flav_spin.append(f+'_'+s)
''' ONLY doing snk_mom 0 0 0 now '''
snk_mom = params['snk_mom'][0]
m0,m1,m2 = snk_mom.split()
params['M0']=m0
params['M1']=m1
params['M2']=m2
params['MOM'] = 'px%spy%spz%s' %(m0,m1,m2)

particles = params['particles']

coherent_ff_base = management.coherent_ff_base
seqprop_base     = management.seqprop_base
seqprop_size     = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
sp_ext           = params['SP_EXTENSION']
prop_base        = management.prop_base
n_curr = len(params['4d_curr'])
n_flav = len(params['flavs'])
n_spin = len(params['spins'])
n_par  = len(params['particles'])
coherent_ff_size_4d = n_curr * n_flav * n_spin * n_par *int(nt)*int(nx)**3 * 2*8

for c in cfgs_run:
    no = str(c)
    params['CFG'] = no
    if len(srcs[c]) == params['N_SEQ']:
        all_srcs = True
    else:
        all_srcs = False
    cfg_file = cfg_dir+'/'+ens_long+stream+'.'+no+'_wflow1.0.lime'
    if os.path.exists(cfg_file) and all_srcs:
        params.update({'CFG_FILE':cfg_file})
        print("Checking coherent formfactor for cfg: ",c)

        if not os.path.exists(base_dir+'/xml/'+no):
            os.makedirs(base_dir+'/xml/'+no)
        if not os.path.exists(base_dir+'/stdout/'+no):
            os.makedirs(base_dir+'/stdout/'+no)
        if not os.path.exists(base_dir+'/formfac/'+no):
            os.makedirs(base_dir+'/formfac/'+no)
        if not os.path.exists(base_dir+'/formfac_4D/'+no):
            os.makedirs(base_dir+'/formfac_4D/'+no)
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
        have_all_seqprops=True
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
                    seqprop_file  = base_dir+'/seqprop/'+no+'/'+seqprop_name+'.'+sp_ext
                    if os.path.exists(seqprop_file) and os.path.getsize(seqprop_file) < seqprop_size:
                        now = time.time()
                        file_time = os.stat(seqprop_file).st_mtime
                        if (now-file_time)/60 > time_delete:
                            print('DELETING BAD PROP',os.path.getsize(seqprop_file),seqprop_file.split('/')[-1])
                            shutil.move(seqprop_file,seqprop_file.replace('seqprop/'+no+'/','corrupt/'))
                    if not os.path.exists(seqprop_file):
                        print('    missing:',seqprop_file)
                        all_seqprops=False
                        have_all_seqprops=False
            if all_seqprops:
                ''' loop over srcs '''
                for s0 in srcs[c]:
                    params['SRC'] = s0
                    ''' Does the 3pt file exist? '''
                    coherent_formfac_name  = coherent_ff_base % params
                    coherent_formfac_file  = base_dir+'/formfac/'+no + '/'+coherent_formfac_name+'.h5'
                    coherent_formfac_file_4D = coherent_formfac_file.replace('formfac_','formfac_4D_').replace('/formfac/','/formfac_4D/')
                    params['THREE_PT_FILE'] = coherent_formfac_file
                    params['THREE_PT_FILE_4D'] = coherent_formfac_file_4D
                    if os.path.exists(coherent_formfac_file_4D) and os.path.getsize(coherent_formfac_file_4D) < coherent_ff_size_4d:
                        now = time.time()
                        file_time = os.stat(coherent_formfac_file_4D).st_mtime
                        if (now-file_time)/60 > time_delete:
                            print('DELETING BAD COHERENT_FF',os.path.getsize(coherent_formfac_file_4D),coherent_formfac_file_4D.split('/')[-1])
                            shutil.move(coherent_formfac_file_4D,coherent_formfac_file_4D.replace('formfac/'+no+'/','corrupt/'))
                            shutil.move(coherent_formfac_file,coherent_formfac_file.replace('formfac/'+no+'/','corrupt/'))
                            #sys.exit()
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
                            prop_name = prop_base % params
                            prop_file = base_dir+'/prop/'+no+'/'+prop_name+'.'+sp_ext
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
                                        seqprop_file  = base_dir+'/seqprop/'+no+'/'+seqprop_name+'.'+sp_ext
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
                                    ''' erase seqprops to reduce memory footprint '''
                                    fin.write(xml_input.qio_erase %{'OBJ_ID':f_dn_s_up_up_seqprop})
                                    fin.write(xml_input.qio_erase %{'OBJ_ID':f_dn_s_dn_dn_seqprop})
                                    fin.write(xml_input.qio_erase %{'OBJ_ID':f_up_s_dn_dn_seqprop})
                                    fin.write(xml_input.qio_erase %{'OBJ_ID':f_up_s_up_up_seqprop})

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
                            if not args.verbose:
                                print('  task exists:',metaq)
                    else:
                        if not args.verbose:
                            print('    exists:',coherent_formfac_file)
            else:
                print('    missing FLAV or SPIN seqprops, dt=',dt)
        if not have_all_seqprops:
            print('    missing FLAV or SPIN seqprops')
            os.system('python METAQ_coherent_seqprop.py %s -v' %(c))
        #else:
        #    print('    missing props')
    else:
        if not os.path.exists(cfg_file):
            print('  flowed cfg missing',cfg_file)
        elif not all_srcs:
            print('missing srcs [8]')
            print(c,srcs[c])
