from __future__ import print_function
import os, sys
from glob import glob
import argparse
import xml_input
import metaq_input

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

ens = 'a12m310_a'
stream = ens.split('_')[-1]
base_dir = '/p/gpfs1/walkloud/c51/x_files/project_2/production/a12m310_a/coherent_test'
cfg_dir = '/p/gpfs1/walkloud/c51/x_files/project_2/production/a12m310_a/cfgs_flow'
metaq_test_dir = '/p/gpfs1/walkloud/c51/x_files/project_2/production/a12m310_a/runs'
metaq_run_dir = '/p/gpfs1/walkloud/c51/x_files/project_2/metaq/priority/gpu'

metaq_dir = metaq_run_dir

smr = 'gf1.0_w3.0_n30'
val = smr+'_M51.2_L58_a1.5'
mq = '0.0126'
params = {'RES':1e-8}

cfg_srcs = open(args.f).readlines()
cfgs = []
for c in cfg_srcs:
    cfgs.append(c.split()[0])
cfgs = list(set(cfgs))

srcs = {}
for c in cfgs:
    srcs[c] = []


for c in cfgs:
    for cs in cfg_srcs:
        no,x0,y0,z0,t0,snk_spin,src_spin,m0,m1,m2,sinkt,flavor = cs.split()
        if no == c:
            srcs[c].append(cs)

prop_srcs = {}
for c in cfgs:
    prop_srcs[c] = []


for c in cfgs:
    for cs in cfg_srcs:
        no,x0,y0,z0,t0,snk_spin,src_spin,m0,m1,m2,sinkt,flavor = cs.split()
        if no == c:
            src = '{} {} {} {} {}'.format(no,x0,y0,z0,t0)
            if src not in prop_srcs[c]:
                prop_srcs[c].append(src)


for c in cfgs:
    cfg_file = cfg_dir+'/l2464f211b600m0102m0509m635'+stream+'.'+c+'_wflow1.0.lime'
    params.update({'CFG_FILE':cfg_file})
    print("Making coherent sources for cfg: ",c)
    if not os.path.exists(base_dir+'/props/'+no):
        os.makedirs(base_dir+'/props/'+no)

    run_props = False
    all_props = True

    # Check if all props there.
    for ci,cs in enumerate(prop_srcs[c]):
        cr = ri+ci
        no,x0,y0,z0,t0 = cs.split()
        s0 = 'x%sy%sz%st%s' %(x0,y0,z0,t0)

        src_name  = 'src_'+ens+'_'+smr+'_'+no+'_'+s0
        prop_name = 'prop_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0
        prop_file = base_dir+'/props/'+no + '/' + prop_name+'.h5'
        prop_xml  = prop_file.replace('/props/','/xml/').replace('.h5','.out.xml')

        if not os.path.exists(prop_file):
            all_props = False

    if all_props:
        props_to_run = []
    # Check if all seqprops there.
        for ci,cs in enumerate(srcs[c]):
            cr = ri+ci
            no,x0,y0,z0,t0,snk_spin,src_spin,m0,m1,m2,sinkt,flavor = cs.split()
            s0 = 'x%sy%sz%st%s' %(x0,y0,z0,t0)

            mom = 'px%spy%spz%s' %(m0,m1,m2)

            src_name  = 'src_'+ens+'_'+smr+'_'+no+'_'+s0
            seqsrc_name = 'prot_'+ flavor+'_'+snk_spin+'_'+src_spin+'_'+src_name + '_'+mom

            seqprop_name = 'prop_prot_' + flavor + '_' + snk_spin+'_'+src_spin+'_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0 + '_'+mom
            seqprop_file = base_dir+'/props/'+no+'/'+seqprop_name+'.h5'
            seqprop_xml_file = seqprop_file.replace('/props/','/xml/').replace('.h5','.out.xml')

            if not os.path.exists(seqprop_file):
                run_props = True
                props_to_run.append(cs)
    else:
        print("Missing propagators. Run METAQ_make_props.py")
        continue


    if run_props:
        xmlini = base_dir+'/xml/'+c+'/seqprops_'+ens+'_'+val+'_'+c+'.ini.xml'
        fin = open(xmlini,'w')
        fin.write(xml_input.head)

    # Check if all props there.
        for ci,cs in enumerate(prop_srcs[c]):
            cr = ri+ci
            no,x0,y0,z0,t0 = cs.split()
            s0 = 'x%sy%sz%st%s' %(x0,y0,z0,t0)

            src_name  = 'src_'+ens+'_'+smr+'_'+no+'_'+s0
            prop_name = 'prop_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0
            prop_file = base_dir+'/props/'+no + '/' + prop_name+'.h5'
            prop_xml  = prop_file.replace('/props/','/xml/').replace('.h5','.out.xml')

            params.update({'PROP_NAME':prop_name,'PROP_FILE':prop_file})
            fin.write(xml_input.hdf5_read % params)


        for ci,cs in enumerate(props_to_run):
            cr = ri+ci
            no,x0,y0,z0,t0,snk_spin,src_spin,m0,m1,m2,sinkt,flavor = cs.split()
            s0 = 'x%sy%sz%st%s' %(x0,y0,z0,t0)
       	    mom	= 'px%spy%spz%s' %(m0,m1,m2)

            prop_name = 'prop_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0

            src_name  = 'src_'+ens+'_'+smr+'_'+no+'_'+s0
            seqsrc_name = 'prot_'+ flavor+'_'+snk_spin+'_'+src_spin+'_'+src_name + '_' + mom

            params.update({
                    'UP_QUARK':prop_name,'DOWN_QUARK':prop_name,
                    'M0':m0,'M1':m1,'M2':m2,'TSINK':sinkt,'FLAVOR':flavor,'SINK_SPIN':snk_spin,
                    'SOURCE_SPIN':src_spin,'SEQSOURCE':seqsrc_name})

            seqprop_name = 'prop_prot_' + flavor + '_' + snk_spin+'_'+src_spin+'_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0+'_'+mom
            seqprop_file = base_dir+'/props/'+no+'/'+seqprop_name+'.h5'
            if not os.path.exists(seqprop_file):
                fin.write(xml_input.lalibe_proton_seqsource % params)
        for ci,cs in enumerate(props_to_run):
            cr = ri+ci
            no,x0,y0,z0,t0,snk_spin,src_spin,m0,m1,m2,sinkt,flavor = cs.split()
            s0 = 'x%sy%sz%st%s' %(x0,y0,z0,t0)

            mom = 'px%spy%spz%s' %(m0,m1,m2)

            src_name  = 'src_'+ens+'_'+smr+'_'+no+'_'+s0
            seqsrc_name = 'prot_'+ flavor+'_'+snk_spin+'_'+src_spin+'_'+src_name + '_'+mom

            seqprop_name = 'prop_prot_' + flavor + '_' + snk_spin+'_'+src_spin+'_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0+'_'+mom
            seqprop_file = base_dir+'/props/'+no+'/'+seqprop_name+'.h5'
            seqprop_xml_file = seqprop_file.replace('/props/','/xml/').replace('.h5','.out.xml')

            params.update({'SRC_NAME':seqsrc_name,'PROP_NAME':seqprop_name,'PROP_XML':seqprop_xml_file})
            if not os.path.exists(seqprop_file):
                fin.write(xml_input.quda_nef % params)

        for ci,cs in enumerate(props_to_run):
            cr = ri+ci
            no,x0,y0,z0,t0,snk_spin,src_spin,m0,m1,m2,sinkt,flavor = cs.split()
            s0 = 'x%sy%sz%st%s' %(x0,y0,z0,t0)
            mom = 'px%spy%spz%s' %(m0,m1,m2)

            src_name  = 'src_'+ens+'_'+smr+'_'+no+'_'+s0
            seqsrc_name = 'prot_'+ flavor+'_'+snk_spin+'_'+src_spin+'_'+src_name + '_'+mom

            seqprop_name = 'prop_prot_' + flavor + '_' + snk_spin+'_'+src_spin+'_'+ens+'_'+val+'_mq'+mq+'_'+no+'_'+s0 + '_'+mom
            seqprop_file = base_dir+'/props/'+no+'/'+seqprop_name+'.h5'
            seqprop_xml_file = seqprop_file.replace('/props/','/xml/').replace('.h5','.out.xml')

            params.update({'SRC_NAME':seqsrc_name,'PROP_NAME':seqprop_name,'PROP_FILE':seqprop_file,'PROP_XML':seqprop_xml_file})
            if not os.path.exists(seqprop_file):
                fin.write(xml_input.hdf5_write % params)

        fin.write(xml_input.tail % params)


    if run_props:
        if os.path.exists(cfg_file):
            metaq  = 'seqprops_'+ens+'_'+val+'_'+no+'.sh'
            metaq_file = metaq_dir +'/'+metaq
            print('  making propagators')

            task_exist = False
            task_working = False
            if os.path.exists(metaq_dir+'/'+metaq):
                task_exist = True
            if not task_exist:
                params.update({'XML_IN':xmlini,'XML_OUT':xmlini.replace('.ini.xml','.out.xml'),
                              'STDOUT':xmlini.replace('.ini.xml','.stdout').replace('/xml/','/stdout/'),
                              'METAQ_LOG':base_dir+'/metaq/log/'+metaq.replace('.sh','.log'),
                              'BASE_DIR':base_dir,'METAQ_RUN':metaq_file,'METAQ_FINISHED':metaq_file.replace('runs','finished')})
                m_in = open(metaq_file,'w')
                m_in.write(metaq_input.coherent_src_formfac % params)
                m_in.close()
                os.chmod(metaq_file,0770)
            else:
                print('  task exists:',metaq)
        else:
            print('  flowed cfg missing',cfg_file)
    else:
	print('  all props made.')
