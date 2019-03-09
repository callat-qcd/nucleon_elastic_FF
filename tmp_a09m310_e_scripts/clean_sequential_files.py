from __future__ import print_function
import os, sys, shutil, time
from glob import glob
import argparse

try:
    ens = os.getcwd().split('/')[-3]
except:
    ens,junk = os.getcwd().split('/')[-3]
stream = ens.split('_')[-1]
ens_long='l3296f211b630m0074m037m440'

parser = argparse.ArgumentParser(description='delete seqsrcs and seqprops when formfac finished')# %sys.argv[0].split('/')[-1])
parser.add_argument('run',nargs='+',type=int,help='start [stop] run number')
parser.add_argument('-f',type=str,default=ens+'_src.lst',help='cfg/src file')
parser.add_argument('--seqsrc',default=False,action='store_const',const=True,\
    help='delete seqsrc files? [%(default)s]')
parser.add_argument('--seqprop',default=False,action='store_const',const=True,\
    help='delete seqprop files? [%(default)s]')
parser.add_argument('-v','--verbose',default=False,action='store_const',const=True,\
    help='verbose? [%(default)s]')
parser.add_argument('--debug',default=True,action='store_const',const=False,\
    help='debug mode? [%(default)s]')
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
    }

base_dir = '/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/'+ens

t_seps  = [3,4,5,6,7,8,9,10,11,12]
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

seqsrc_base       = 'seqsrc_%(PARTICLE)s_%(FLAV_SPIN)s_'+ens+'_'+val+'_mq'+mq+'_%(CFG)s_'
seqsrc_base      += '%(SRC)s_'+mom+'_'+SS_PS

sp_ext = 'lime'
coherent_ff_size_4d = 8*10 *int(nt)*int(nx)**3 * 2*8

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

for c in cfgs:
    no = str(c)
    if args.verbose:
        print(no)
    params['CFG'] = no
    del_sequential = True
    for dt_int in t_seps:
        dt = str(dt_int)
        for s0 in srcs[c]:
            params['SRC'] = s0
            coherent_formfac_name  = coherent_ff_base %{'CFG':c,'T_SEP':dt,'SRC':s0}
            coherent_formfac_file  = base_dir+'/formfac/'+c + '/'+coherent_formfac_name+'.h5'
            coherent_formfac_file_4D = coherent_formfac_file.replace('.h5','_4D.h5').replace('/formfac/','/formfac_4D/')
            if os.path.exists(coherent_formfac_file_4D) and os.path.getsize(coherent_formfac_file_4D) < coherent_ff_size_4d:
                now = time.time()
                file_time = os.stat(coherent_formfac_file_4D).st_mtime
                if (now-file_time)/60 > time_delete:
                    print('DELETING BAD COHERENT_FF',os.path.getsize(coherent_formfac_file_4D),coherent_formfac_file_4D.split('/')[-1])
                    shutil.move(coherent_formfac_file_4D,coherent_formfac_file_4D.replace('formfac/'+c+'/','corrupt/'))
                    shutil.move(coherent_formfac_file,coherent_formfac_file.replace('formfac/'+c+'/','corrupt/'))
            if not os.path.exists(coherent_formfac_file_4D):
                del_sequential = False
    if del_sequential:
        for fs in flav_spin:
            flav,snk_spin,src_spin=fs.split('_')
            params['FLAV']=flav
            params['SOURCE_SPIN']=snk_spin
            params['SINK_SPIN']=src_spin
            spin = snk_spin+'_'+src_spin
            params['FLAV_SPIN']=fs
            for particle in particles:
                params['PARTICLE'] = particle
                ''' SEQSRC '''
                for s0 in srcs[c]:
                    params['SRC'] = s0
                    seqsrc_name = seqsrc_base % params
                    seqsrc_file = base_dir+'/seqsrc/'+c+'/'+seqsrc_name+'.'+sp_ext
                    if args.seqsrc:
                        if args.debug:
                            print('DEBUG: DELETING',seqsrc_name)
                        else:
                            if os.path.exists(seqsrc_file):
                                print('DELETING',seqsrc_name)
                                os.remove(seqsrc_file)
                            else:
                                print('ALREADY DELETED',seqsrc_name)
                    else:
                        if args.verbose:
                            print('ready for deleting',seqsrc_name)
                ''' SEQPROP '''
                for dt_int in t_seps:
                    dt = str(dt_int)
                    if '_np' in particle:
                        params['T_SEP'] = '-'+dt
                    else:
                        params['T_SEP'] = dt
                    seqprop_name  = seqprop_base % params
                    seqprop_file  = base_dir+'/seqprop/'+c+'/'+seqprop_name+'.'+sp_ext
                    if args.seqprop:
                        if args.debug:
                            print('DEBUG: DELETING',seqprop_name)
                        else:
                            if os.path.exists(seqprop_file):
                                print('DELETING',seqprop_name)
                                os.remove(seqprop_file)
                            else:
                                print('ALREADY DELETED',seqprop_name)
                    else:
                        if args.verbose:
                            print('ready for deleting',seqprop_name)
