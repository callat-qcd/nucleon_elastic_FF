gflow='''#!/bin/bash
#METAQ NODES %(NODES)s
#METAQ GPUS %(GPUS)s
#METAQ MIN_WC_TIME %(WALL_TIME)s
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT seqsource_%(ENS_S)s

#BSUB -nnodes %(NODES)s
#BSUB -cn_cu 'maxcus=1'
#BSUB -P LGT100
#BSUB -W %(WALL_TIME)s
#BSUB -alloc_flags smt4

source /ccs/proj/lgt100/c51/software/summit_smpi/install/env.sh
cd /gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/a09m310_e

ini=%(XML_IN)s
out=%(XML_OUT)s
stdout=%(STDOUT)s

export OMP_NUM_THREADS=4
PROG=$LALIBE_CPU
APP=/ccs/proj/lgt100/c51/software/callat_build_scripts/binding_scripts/summit_bind_cpu.N32.sh
#jsrun -n1 -r1 -a32 -c32 -b none -d packed $APP $PROG -i $ini -o $out > $stdout 2>&1
jsrun --nrs 2 -r2 -a16 -c16 -l cpu-cpu -b packed:smt:4 $PROG -i $ini -o $out > $stdout 2>&1

cd %(SCRIPT_DIR)s
python METAQ_src.py %(CR)s

sleep 5

'''

prop = '''#!/bin/bash
#METAQ NODES 0
#METAQ GPUS 6
#METAQ MIN_WC_TIME 15:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT prop_%(ENS_S)s

#BSUB -nnodes 1
#BSUB -cn_cu 'maxcus=1'
#BSUB -P LGT100
#BSUB -W 15
#BSUB -alloc_flags smt4

source /ccs/proj/lgt100/c51/software/summit_smpi/install/env.sh
cd /gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/a09m310_e

export QUDA_RESOURCE_PATH=`pwd`/quda_no_gdr
if [[ ! -d $QUDA_RESOURCE_PATH ]]; then
    mkdir $QUDA_RESOURCE_PATH
fi

ini=%(XML_IN)s
out=%(XML_OUT)s
stdout=%(STDOUT)s

export OMP_NUM_THREADS=4
PROG="$LALIBE_GPU -geom 1 1 1 6"
APP=/ccs/proj/lgt100/c51/software/callat_build_scripts/binding_scripts/summit_gpu_bind.sh
#jsrun -n1 -r1 -a6 -g6 -c6 -b none -d packed $APP $PROG -i $ini -o $out > $stdout 2>&1
jsrun -n1 -r1 -a6 -g6 -c6 -l gpu-cpu -b packed:smt:4 $APP $PROG -i $ini -o $out > $stdout 2>&1

%(CLEANUP)s

'''


seqsource='''#!/bin/bash
#METAQ NODES 1
#METAQ GPUS 0
#METAQ MIN_WC_TIME 15:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT seqsource_%(ENS_S)s

#BSUB -nnodes 1
#BSUB -cn_cu 'maxcus=1'
#BSUB -P LGT100
#BSUB -W 20
#BSUB -alloc_flags smt4

source /ccs/proj/lgt100/c51/software/summit_smpi/install/env.sh
cd /gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/a09m310_e

ini=%(XML_IN)s
out=%(XML_OUT)s
stdout=%(STDOUT)s

export OMP_NUM_THREADS=4
PROG=$LALIBE_CPU
APP=/ccs/proj/lgt100/c51/software/callat_build_scripts/binding_scripts/summit_bind_cpu.N32.sh
#jsrun -n1 -r1 -a32 -c32 -b none -d packed $APP $PROG -i $ini -o $out > $stdout 2>&1
jsrun --nrs 2 -r2 -a16 -c16 -l cpu-cpu -b packed:smt:4 $PROG -i $ini -o $out > $stdout 2>&1

cd %(SCRIPT_DIR)s
python METAQ_coherent_seqprop.py %(CR)s %(T_SEP)s

'''

seqprop = '''#!/bin/bash
#METAQ NODES 0
#METAQ GPUS 6
#METAQ MIN_WC_TIME 15:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT seqprop_%(ENS_S)s

#BSUB -nnodes 1
#BSUB -cn_cu 'maxcus=1'
#BSUB -P LGT100
#BSUB -W 20
#BSUB -alloc_flags smt4

source /ccs/proj/lgt100/c51/software/summit_smpi/install/env.sh
cd /gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/a09m310_e

export QUDA_RESOURCE_PATH=`pwd`/quda_no_gdr
if [[ ! -d $QUDA_RESOURCE_PATH ]]; then
    mkdir $QUDA_RESOURCE_PATH
fi

ini=%(XML_IN)s
out=%(XML_OUT)s
stdout=%(STDOUT)s

export OMP_NUM_THREADS=4
PROG="$LALIBE_GPU -geom 1 1 1 6"
APP=/ccs/proj/lgt100/c51/software/callat_build_scripts/binding_scripts/summit_gpu_bind.sh
#jsrun -n1 -r1 -a6 -g6 -c6 -b none -d packed $APP $PROG -i $ini -o $out > $stdout 2>&1
jsrun -n1 -r1 -a6 -g6 -c6 -l gpu-cpu -b packed:smt:4 $APP $PROG -i $ini -o $out > $stdout 2>&1

cd %(SCRIPT_DIR)s
python METAQ_coherent_formfac.py %(CR)s -t %(T_SEP)s

'''

formfac_contractions='''#!/bin/bash
#METAQ NODES 1
#METAQ GPUS 0
#METAQ MIN_WC_TIME 15:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT formfac_%(ENS_S)s

#BSUB -nnodes 1
#BSUB -cn_cu 'maxcus=1'
#BSUB -P LGT100
#BSUB -W 20
#BSUB -alloc_flags smt4

source /ccs/proj/lgt100/c51/software/summit_smpi/install/env.sh
cd /gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/a09m310_e

ini=%(XML_IN)s
out=%(XML_OUT)s
stdout=%(STDOUT)s

export OMP_NUM_THREADS=4
PROG=$LALIBE_CPU
APP=/ccs/proj/lgt100/c51/software/callat_build_scripts/binding_scripts/summit_bind_cpu.N32.sh
#jsrun -n1 -r1 -a32 -c32 -b none -d packed $APP $PROG -i $ini -o $out > $stdout 2>&1
jsrun --nrs 2 -r2 -a16 -c16 -l cpu-cpu -b packed:smt:4 $PROG -i $ini -o $out > $stdout 2>&1

'''



one_by_one_src_formfac = '''#!/bin/bash

#METAQ NODES 4
#METAQ GPUS 16
#METAQ MIN_WC_TIME 140:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT formfac_a15m310_a

#BSUB -csm y
#BSUB -jsm y
#BSUB -R "1*{select[LN]}+1*{select[CN]span[ptile=1]cu[maxcus=1]}"
#####    this selects 1 launch node (LN) and 6 nodes cause ptile=1, and max racks=1 (maxcus=1)
#BSUB -q pbatch
#BSUB -G latticgc
#BSUB -W 6
#BSUB -J c51
#BSUB -core_isolation 2
#BSUB -sp 1

source /nfs/tmp2/lattice_qcd/software/sierra_smpi/install/env.sh

export QUDA_RESOURCE_PATH=/p/gpfs1/walkloud/c51/x_files/project_2/quda_siera_no_gdr

#export QUDA_ENABLE_GDR=1
export OMP_NUM_THREADS=8
#export QUDA_ENABLE_DSLASH_POLICY="2,3"

APP=/p/gpfs1/walkloud/c51/x_files/project_2/binding_scripts/sierra_bind_gpu.sh

ini=%(XML_IN)s
out=%(XML_OUT)s
stdout=%(STDOUT)s

PROG="$LALIBE_GPU -geom 1 1 1 4 -qmp-geom 1 1 1 4 -qmp-alloc-map 3 2 1 0 -qmp-logic-map  3 2 1 0"

APRUNVAR="jsrun -p4 -g1 --bind=none $APP $PROG"

$APRUNVAR -i $ini -o $out > $stdout 2>&1

'''
OLDone_by_one_src_formfac = '''#!/bin/bash


#METAQ NODES 4
#METAQ GPUS 16
#METAQ MIN_WC_TIME 140:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT formfac_a15m310_a

#BSUB -csm y
#BSUB -jsm y
#BSUB -R "1*{select[LN]}+4*{select[CN]span[ptile=1]cu[maxcus=1]}"
#####    this selects 1 launch node (LN) and 6 nodes cause ptile=1, and max racks=1 (maxcus=1)
#BSUB -q pbatch
#BSUB -G latticgc
#BSUB -W 100
#BSUB -J c51
#BSUB -core_isolation 2
#BSUB -sp 1


#source /usr/workspace/wsb/brantley/code/devel/scripts/sierra/test_env_sierra.sh
source /nfs/tmp2/lattice_qcd/software/sierra_smpi/install/env.sh

#export QUDA_RESOURCE_PATH=/usr/workspace/wsb/brantley/code/devel/tests/three_pt_test/quda_resource
export QUDA_RESOURCE_PATH=/p/gpfs1/walkloud/c51/x_files/project_2/quda_smpi_gdr_qmp

export QUDA_ENABLE_GDR=1
export OMP_NUM_THREADS=8
export QUDA_ENABLE_DSLASH_POLICY="2,3"

APP=/p/gpfs1/walkloud/c51/x_files/project_2/binding_scripts/sierra_bind_gpu.sh

ini=%(XML_IN)s
out=%(XML_OUT)s
stdout=%(STDOUT)s

PROG="$LALIBE_GPU -geom 1 1 1 16 -qmp-geom 1 1 1 16 -qmp-alloc-map 3 2 1 0 -qmp-logic-map  3 2 1 0"

APRUNVAR="jsrun -p16 -g1 -M \"-gpu\" --bind=none $APP $PROG"

$APRUNVAR -i $ini -o $out > $stdout 2>&1

%(CLEANUP)s
'''


contractions='''#!/bin/bash

#METAQ NODES 4
#METAQ MIN_WC_TIME 100:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT src_a09m130_a

#BSUB -nnodes 4
#BSUB -q pbatch
#BSUB -G latticgc
#BSUB -W 100

#source /nfs/tmp2/lattice_qcd/software/sierra_smpi/install/lalibe_gpu_devel/env.sh
source /nfs/tmp2/lattice_qcd/software/sierra_smpi/install/env.sh


ini=%(XML_IN)s
out=%(XML_OUT)s
stdout=%(STDOUT)s

export OMP_NUM_THREADS=8
PROG=$LALIBE_CPU
#We don't need a geom for cpu tasks.
APRUNVAR="lrun -p128 $PROG"
$APRUNVAR -i $ini -o $out > $stdout 2>&1

'''


'''
#BSUB -csm y
#BSUB -jsm y
#BSUB -R "1*{select[LN]}+6*{select[CN]span[ptile=1]cu[maxcus=1]}"
#####    this selects 1 launch node (LN) and 6 nodes cause ptile=1, and max racks=1 (maxcus=1)
#BSUB -q pbatch
#BSUB -G latticgc
#BSUB -W 240
#BSUB -J c51
#BSUB -o /p/gpfs1/walkloud/c51/x_files/project_2/metaq/jobs/%J.log
#BSUB -core_isolation 2


#METAQ NODES 4
#METAQ GPUS 16
#METAQ MIN_WC_TIME 140:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT formfac_a15m310_a

#BSUB -nnodes 4
#BSUB -q pbatch
#BSUB -G callat
#BSUB -W 140

'''
