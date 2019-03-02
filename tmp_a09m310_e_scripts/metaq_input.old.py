gflow = '''#!/bin/bash

#METAQ NODES 4
#METAQ MIN_WC_TIME 25:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT src_a15m135_a

#BSUB -nnodes 4
#BSUB -q pbatch
#BSUB -G guests
#BSUB -W 10

source /nfs/tmp2/lattice_qcd/software/sierra_smpi/install/env.sh

ini=%(XML_IN)s
out=%(XML_OUT)s
stdout=%(STDOUT)s

export OMP_NUM_THREADS=8
PROG=$LALIBE_CPU
#We don't need a geom for cpu tasks.
APRUNVAR="lrun -p144 $PROG"
$APRUNVAR -i $ini -o $out > $stdout 2>&1
'''

src = '''#!/bin/bash

#METAQ NODES 4
#METAQ MIN_WC_TIME 5:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT src_a12m130_a

#BSUB -nnodes 4
#BSUB -q pbatch
#BSUB -G guests
#BSUB -W 10

source /nfs/tmp2/lattice_qcd/software/sierra_smpi/install/env.sh

ini=%(XML_IN)s
out=%(XML_OUT)s
stdout=%(STDOUT)s

export OMP_NUM_THREADS=8
PROG=$LALIBE_CPU
#We don't need a geom for cpu tasks.
APRUNVAR="lrun -p144 $PROG"
$APRUNVAR -i $ini -o $out > $stdout 2>&1
'''

prop = '''#!/bin/bash

#METAQ NODES 4
#METAQ GPUS 16
#METAQ MIN_WC_TIME 100:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT prop_a12m130_a

#BSUB -nnodes 4
#BSUB -q pbatch
#BSUB -G guests
#BSUB -W 135

source /nfs/tmp2/lattice_qcd/software/sierra_smpi/install/env.sh

#export QUDA_RESOURCE_PATH=%(BASE_DIR)s/quda_smpi
export QUDA_RESOURCE_PATH=%(BASE_DIR)s/quda_smpi_gdr_qmp

export QUDA_ENABLE_GDR=1
export OMP_NUM_THREADS=8
export QUDA_ENABLE_DSLASH_POLICY="2,3"

APP=%(BASE_DIR)s/binding_scripts/sierra_bind_gpu.sh

ini=%(XML_IN)s
out=%(XML_OUT)s
stdout=%(STDOUT)s

PROG="$LALIBE_GPU -geom 1 1 2 8 -qmp-geom 1 1 2 8 -qmp-alloc-map 3 2 1 0 -qmp-logic-map  3 2 1 0"

APRUNVAR="jsrun -p16 -g1 -M \"-gpu\" --bind=none $APP $PROG"


$APRUNVAR -i $ini -o $out > $stdout 2>&1
'''

fhprop = '''#!/bin/bash

#METAQ NODES 4
#METAQ GPUS 16
#METAQ MIN_WC_TIME 100:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT prop_a12m130_a

#BSUB -nnodes 4
#BSUB -q pbatch
#BSUB -G guests
#BSUB -W 160

source /nfs/tmp2/lattice_qcd/software/sierra_smpi/install/env.sh

#export QUDA_RESOURCE_PATH=%(BASE_DIR)s/quda_smpi
export QUDA_RESOURCE_PATH=%(BASE_DIR)s/quda_smpi_gdr_qmp

export QUDA_ENABLE_GDR=1
export OMP_NUM_THREADS=8
export QUDA_ENABLE_DSLASH_POLICY="2,3"

APP=%(BASE_DIR)s/binding_scripts/sierra_bind_gpu.sh

ini=%(XML_IN)s
out=%(XML_OUT)s
stdout=%(STDOUT)s

PROG="$LALIBE_GPU -geom 1 1 2 8 -qmp-geom 1 1 2 8 -qmp-alloc-map 3 2 1 0 -qmp-logic-map  3 2 1 0"

APRUNVAR="jsrun -p16 -g1 -M \"-gpu\" --bind=none $APP $PROG"



$APRUNVAR -i $ini -o $out > $stdout 2>&1
'''

hisq_spec = '''#!/bin/bash

#METAQ NODES 4
#METAQ GPUS 16
#METAQ MIN_WC_TIME 20:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT hisq_spec_%(ENS_S)s

#BSUB -nnodes 4
#BSUB -q pbatch
#BSUB -G guests
#BSUB -W 20

source /nfs/tmp2/lattice_qcd/software/sierra_smpi/install/env.sh
export QUDA_RESOURCE_PATH=%(BASE_DIR)s/quda_hisq
if [[ ! -d $QUDA_RESOURCE_PATH ]]; then
    mkdir $QUDA_RESOURCE_PATH
fi
export QUDA_ENABLE_GDR=1
export OMP_NUM_THREADS=4
APP=/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/binding_scripts/sierra_bind_gpu.sh
EXE=/nfs/tmp2/lattice_qcd/software/sierra_smpi/install_hisq/build/milc_qcd_devel/ks_spectrum/ks_spectrum_hisq_mx2

ini=%(HISQ_IN)s
out=%(HISQ_OUT)s
PROG="$EXE -qmp-geom 1 1 2 8 -qmp-logic-map 3 2 1 0 -qmp-alloc-map 3 2 1 0"
APRUNVAR="jsrun -p16 -g1 -M \"-gpu\" --bind=none $APP $PROG"
echo "TIME STAMP: START `date`" > $out
$APRUNVAR $ini >> $out 2>&1
echo "TIME STAMP: END `date`" >> $out

'''
