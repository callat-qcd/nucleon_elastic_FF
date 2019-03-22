from __future__ import print_function
import os, sys, time, shutil
from glob import glob
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__),'area51_files'))
import xml_input
import metaq_input
import importlib
import management
import sources

try:
    ens_s = os.getcwd().split('/')[-2]
except:
    ens_s,junk = os.getcwd().split('/')[-2]
ens,stream = ens_s.split('_')

sys.path.append('area51_files')
area51 = importlib.import_module(ens)
params = area51.params
ens_long=params['ENS_LONG']
params['ENS_S'] = ens_s

parser = argparse.ArgumentParser(description='make xml input for %s that need running' %sys.argv[0].split('/')[-1])
parser.add_argument('cfgs',nargs='+',type=int,help='start [stop] run cfg number')
parser.add_argument('-s','--src',type=str)
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

ri = args.cfgs[0]
if len(args.cfgs) == 1:
    rf = ri+1
    dr = 1
elif len(args.cfgs) == 2:
    rf = args.cfgs[1]+1
    dr = 1
else:
    rf = args.cfgs[1]+1
    dr = args.cfgs[2]
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
params['ENS_DIR']    = management.ens_dir % params
params['SCRIPT_DIR'] = management.script_dir
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
seqsrc_base      = management.seqsrc_base
seqsrc_size      = int(nt)* int(nl)**3 * 3**2 * 4**2 * 2 * 4
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
        print("Making coherent sources for cfg: ",no)

        if not os.path.exists(base_dir+'/xml/'+no):
            os.makedirs(base_dir+'/xml/'+no)
        if not os.path.exists(base_dir+'/stdout/'+no):
            os.makedirs(base_dir+'/stdout/'++no)
        if not os.path.exists(base_dir+'/seqsrc/'+no):
            os.makedirs(base_dir+'/seqsrc/'+no)
        if not os.path.exists(base_dir+'/corrupt'):
            os.makedirs(base_dir+'/corrupt')

        ''' Do the 3pt files exist? '''
        have_3pts = True
        for dt_int in t_seps:
            dt = str(dt_int)
            params['T_SEP'] = dt
            for s0 in srcs[c]:
                params['SRC'] = s0
                coherent_formfac_name  = coherent_ff_base % params
                coherent_formfac_file  = base_dir+'/formfac/' +no+ '/'+coherent_formfac_name + '.h5'
                coherent_formfac_file_4D = coherent_formfac_file.replace('formfac_','formfac_4D_')
                if not os.path.exists(coherent_formfac_file) and not os.path.exists(coherent_formfac_file_4D):
                    have_3pts = False

        if not have_3pts:
            # loop over props to make a time-dense seqsource for each prop
            for s0 in srcs[c]:
                params['SRC'] = s0
                prop_name = prop_base % params
                prop_file = base_dir+'/prop/'+no + '/' + prop_name+'.'+sp_ext
                if os.path.exists(prop_file):
                    for fs in flav_spin:
                        flav,snk_spin,src_spin=fs.split('_')
                        params['FLAV']=flav
                        params['SOURCE_SPIN']=snk_spin
                        params['SINK_SPIN']=src_spin
                        params['FLAV_SPIN']=fs
                        spin = snk_spin+'_'+src_spin
                        have_seqsrc = True
                        for particle in particles:
                            params['PARTICLE']=particle
                            seqsrc_name = seqsrc_base %params
                            seqsrc_file  = base_dir+'/seqsrc/'+no+'/'+seqsrc_name+'.'+sp_ext
                            if os.path.exists(seqsrc_file) and os.path.getsize(seqsrc_file) < seqsrc_size:
                                now = time.time()
                                file_time = os.stat(seqsrc_file).st_mtime
                                if (now-file_time)/60 > time_delete:
                                    print('DELETING BAD SINK',os.path.getsize(seqsrc_file),seqsrc_file.split('/')[-1])
                                    shutil.move(seqsrc_file,seqsrc_file.replace('seqsrc/'+no,'corrupt'))
                            if not os.path.exists(seqsrc_file):
                                have_seqsrc = False
                        if not have_seqsrc:
                            params['PARTICLE'] = particles[0]
                            seqsrc_name = seqsrc_base %params
                            metaq  = seqsrc_name+'.sh'
                            metaq_file = metaq_dir +'/'+q+'/cpu/'+'/'+metaq
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
                            if not task_exist or (args.o and not task_working):
                                xmlini = base_dir+'/xml/'+no+'/'+seqsrc_name+'.'+'ini.xml'
                                fin = open(xmlini,'w')
                                fin.write(xml_input.head)
                                ''' read prop '''
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
                                if params['SS_PS'] == 'SS':
                                    params['SMEARED_PROP'] = prop_name+'_SS'
                                    fin.write(xml_input.shell_smearing % params)
                                    params['UP_QUARK']=prop_name+'_SS'
                                    params['DOWN_QUARK']=prop_name+'_SS'
                                else:
                                    params['UP_QUARK']=prop_name
                                    params['DOWN_QUARK']=prop_name

                                for particle in particles:
                                    params['PARTICLE'] = particle
                                    params['SEQSOURCE'] = seqsrc_base %params
                                    seqsrc_file  = base_dir+'/seqsrc/'+no+'/'+params['SEQSOURCE']+'.'+sp_ext
                                    if not os.path.exists(seqsrc_file):
                                        ''' make seqsource '''
                                        fin.write(xml_input.lalibe_seqsource % params)
                                        params['OBJ_ID']    = params['SEQSOURCE']
                                        params['OBJ_TYPE']  = 'LatticePropagatorF'
                                        params['LIME_FILE'] = seqsrc_file
                                        fin.write(xml_input.qio_write % params)
                                ''' END '''
                                fin.write(xml_input.tail % params)
                                fin.close()

                                ''' Make METAQ task '''
                                params['METAQ_LOG'] = metaq_dir+'/log/'+metaq.replace('.sh','.log')
                                params['XML_IN'] = xmlini
                                params['XML_OUT'] = xmlini.replace('.ini.xml','.out.xml')
                                params['STDOUT'] = xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/')
                                params['CR'] = c
                                params['T_SEP'] = ''

                                m_in = open(metaq_file,'w')
                                m_in.write(metaq_input.seqsource % params)
                                m_in.close()
                                os.chmod(metaq_file,0o770)
                                print('    making task:',metaq)
                            else:
                                if not args.verbose:
                                    print('    task exists:',metaq)
                else:
                    print('    missing',prop_file)
                    print('python METAQ_prop.py %s -s %s --force' %(c,s0))
                    os.system('python %s/METAQ_prop.py %s -s %s --force' %(params['SCRIPT_DIR'],c,s0))
                    #sys.exit()
        else:
            print('    coherent_formfacs exist')
    else:
        if not os.path.exists(cfg_file):
            print('  flowed cfg missing',cfg_file)
        elif not all_srcs:
            print('missing srcs [8]')
            print(c,srcs[c])
