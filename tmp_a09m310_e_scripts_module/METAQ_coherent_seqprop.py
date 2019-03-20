from __future__ import print_function
import os, sys, time, shutil
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
parser.add_argument('run',nargs='+',type=int,help='start [stop] run cfg number')
parser.add_argument('-o',default=False,action='store_const',const=True,\
    help='overwrite xml and metaq files? [%(default)s]')
parser.add_argument('-t','--t_sep',nargs='+',type=int,help='values of t_sep [default = all]')
parser.add_argument('-d','--debug',default=False,action='store_const',const=True,\
    help='run DEBUG? [%(default)s]')
parser.add_argument('-p','--priority',default=False,action='store_const',const=True,help='put task in priority? [%(default)s]')
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
''' the COHERENT SEQPROP needs all srcs, so the option of passing a src does not make sense '''
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
coherent_seqsrc  = management.coherent_seqsrc
seqsrc_base      = management.seqsrc_base
seqprop_size     = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
sp_ext           = params['SP_EXTENSION']

prop_base        = management.prop_base

for c in cfgs_run:
    no = str(c)
    params['CFG'] = c
    if len(srcs[c]) == params['N_SEQ']:
        all_srcs = True
    else:
        all_srcs = False
    cfg_file = cfg_dir+'/'+ens_long+stream+'.'+no+'_wflow1.0.lime'
    if os.path.exists(cfg_file) and all_srcs:
        params.update({'CFG_FILE':cfg_file})
        print("Making coherent sources and seqprops for cfg: ",c)

        if not os.path.exists(base_dir+'/seqprop/'+no):
            os.makedirs(base_dir+'/seqprop/'+no)
        if not os.path.exists(base_dir+'/xml/'+no):
            os.makedirs(base_dir+'/xml/'+no)
        if not os.path.exists(base_dir+'/stdout/'+no):
            os.makedirs(base_dir+'/stdout/'+no)
        if not os.path.exists(base_dir+'/corrupt'):
            os.makedirs(base_dir+'/corrupt')
        if not os.path.exists(base_dir+'/formfac/'+no):
            os.makedirs(base_dir+'/formfac/'+no)

        have_seqsrc = True
        have_all_3pts = True
        for dt_int in t_seps:
            dt = str(dt_int)
            params['T_SEP'] = dt
            ''' Do the 3pt files exist? '''
            have_3pts = True
            for s0 in srcs[c]:
                params['SRC'] = s0
                coherent_formfac_name  = coherent_ff_base % params
                coherent_formfac_file  = base_dir+'/formfac/'+no + '/'+coherent_formfac_name + '.h5'
                coherent_formfac_file_4D = coherent_formfac_file.replace('formfac_','formfac_4D_')
                if not os.path.exists(coherent_formfac_file) and not os.path.exists(coherent_formfac_file_4D):
                    have_3pts = False
                    have_all_3pts = False
            if not have_3pts:
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
                            params['QUARK_SPIN'] = 'LOWER'
                            params['T_SEP'] = '-'+dt
                        else:
                            params['QUARK_SPIN'] = 'UPPER'
                            params['T_SEP'] = dt
                        seqprop_name  = seqprop_base % params
                        seqprop_file  = base_dir+'/seqprop/'+no+'/'+seqprop_name+'.'+sp_ext
                        ''' check SEQPROP file size
                            delete if small and older than time_delete
                        '''
                        if os.path.exists(seqprop_file) and os.path.getsize(seqprop_file) < seqprop_size:
                            now = time.time()
                            file_time = os.stat(seqprop_file).st_mtime
                            if (now-file_time)/60 > time_delete:
                                print('DELETING BAD PROP',os.path.getsize(seqprop_file),seqprop_file.split('/')[-1])
                                shutil.move(seqprop_file,seqprop_file.replace('seqprop/'+no+'/','corrupt/'))
                        if not os.path.exists(seqprop_file):
                            ''' make sure all seqsource files exists '''
                            have_seqsrc_t = True
                            for s0 in srcs[c]:
                                params['SRC'] = s0
                                seqsrc_name = seqsrc_base % params
                                seqsrc_file = base_dir+'/seqsrc/'+no+'/'+seqsrc_name+'.'+sp_ext
                                if not os.path.exists(seqsrc_file):
                                    if args.verbose:
                                        print('    missing sink',seqsrc_file)
                                    have_seqsrc_t = False
                                    have_seqsrc   = False
                            if have_seqsrc_t:
                                metaq  = seqprop_name+'.sh'
                                metaq_file = metaq_dir +'/'+q+'/gpu/'+'/'+metaq
                                task_exist = False
                                task_working = False
                                if os.path.exists(metaq_file):
                                    task_exist = True
                                for m_dir in ['todo/gpu','priority/gpu','hold']:
                                    if os.path.exists(metaq_dir+'/'+m_dir+'/'+metaq):
                                        task_exist = True
                                task_lst = glob(metaq_dir+'/working/*/*.sh')
                                task_lst += glob(metaq_dir+'/working/*/*/*.sh')
                                for task in task_lst:
                                    if metaq == task.split('/')[-1]:
                                        task_exist = True
                                        task_working = True
                                if not task_exist or (args.o and task_exist and not task_working):
                                    xmlini = seqprop_file.replace('seqprop/','xml/').replace('.'+sp_ext,'.ini.xml')
                                    fin = open(xmlini,'w')
                                    fin.write(xml_input.head)

                                    ''' read all seqsources '''
                                    for si,s0 in enumerate(srcs[c]):
                                        params['SRC'] = s0
                                        seqsrc_name = seqsrc_base % params
                                        seqsrc_file = base_dir+'/seqsrc/'+no+'/'+seqsrc_name+'.'+sp_ext
                                        params['OBJ_ID']    = seqsrc_name
                                        params['OBJ_TYPE']  = 'LatticePropagator'
                                        params['LIME_FILE'] = seqsrc_file
                                        fin.write(xml_input.qio_read % params)
                                        params['SEQSOURCE_'+str(si)] = seqsrc_name
                                    ''' make coherent_seqsource '''
                                    coherent_seqsrc_name = coherent_seqsrc % params
                                    params['COHERENT_SEQSOURCE'] = coherent_seqsrc_name
                                    fin.write(xml_input.coherent_seqsrc % params)

                                    ''' solve seqprop '''
                                    params['SRC_NAME']  = coherent_seqsrc_name
                                    params['PROP_NAME'] = seqprop_name
                                    params['PROP_XML']  = ''
                                    fin.write(xml_input.quda_nef % params)

                                    ''' save seqprop '''
                                    params['OBJ_ID']      = seqprop_name
                                    params['OBJ_TYPE']    = 'LatticePropagatorF'
                                    params['LIME_FILE']   = seqprop_file
                                    '''
                                    params['H5_FILE']     = seqprop_file
                                    params['H5_PATH']     = ''
                                    params['H5_OBJ_NAME'] = 'propagator'
                                    '''
                                    fin.write(xml_input.qio_write % params)

                                    fin.write(xml_input.tail % params)
                                    fin.close()

                                    ''' Make METAQ task '''
                                    params['METAQ_LOG'] = base_dir+'/metaq/log/'+metaq.replace('.sh','.log')
                                    params['XML_IN'] = xmlini
                                    params['XML_OUT'] = xmlini.replace('.ini.xml','.out.xml')
                                    params['STDOUT'] = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                                    params['CR'] = c
                                    params['T_SEP'] = dt_int

                                    m_in = open(metaq_file,'w')
                                    m_in.write(metaq_input.seqprop % params)
                                    m_in.close()
                                    os.chmod(metaq_file,0o770)
                                    print('    making task:',metaq)
                                else:
                                    if not args.verbose:
                                        print('    task is in use or overwrite is false')
                        else:
                            print('seqprop exists',seqprop_file)
            else:
                if args.verbose:
                    print('    3pt corr exists:',coherent_formfac_file)
        if not have_seqsrc and not have_all_3pts:
            print('python METAQ_seqsource.py %s -v' %(c))
            os.system('python METAQ_seqsource.py %s %s -v' %(c,priority))

    else:
        if not os.path.exists(cfg_file):
            print('  flowed cfg missing',cfg_file)
        elif not all_srcs:
            print('missing srcs [8]')
            print(c,srcs[c])
