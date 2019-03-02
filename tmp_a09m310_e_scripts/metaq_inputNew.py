gflow = '''#!/bin/bash

#METAQ NODES 4
#METAQ MIN_WC_TIME 25:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT src_a06m310_a

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
APRUNVAR="lrun -p192 $PROG"
$APRUNVAR -i $ini -o $out > $stdout 2>&1
'''

src = '''#!/bin/bash

#METAQ NODES 4
#METAQ MIN_WC_TIME 5:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT src_a06m310_a

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
APRUNVAR="lrun -p144 -M \\"-mca io romio314\\" $PROG"
$APRUNVAR -i $ini -o $out > $stdout 2>&1
'''

prop = '''#!/bin/bash

#METAQ NODES 4
#METAQ GPUS 16
#METAQ MIN_WC_TIME 100:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT prop_a06m310_a

#BSUB -nnodes 4
#BSUB -q pbatch
#BSUB -G guests
#BSUB -W 135

source /nfs/tmp2/lattice_qcd/software/sierra_smpi/install/env.sh

#export QUDA_RESOURCE_PATH=/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/a06m310_a/quda_resource
export QUDA_RESOURCE_PATH=%(BASE_DIR)s/quda_smpi_no_gdr
if [[ ! -d $QUDA_RESOURCE_PATH ]]; then
    mkdir $QUDA_RESOURCE_PATH
fi

#export QUDA_ENABLE_GDR=1
export OMP_NUM_THREADS=8
#export QUDA_ENABLE_DSLASH_POLICY="2,3"

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
#METAQ PROJECT prop_a06m310_a

#BSUB -nnodes 4
#BSUB -q pbatch
#BSUB -G guests
#BSUB -W 160

source /nfs/tmp2/lattice_qcd/software/sierra_smpi/install/env.sh

#export QUDA_RESOURCE_PATH=%(BASE_DIR)s/quda_smpi
#export QUDA_RESOURCE_PATH=%(BASE_DIR)s/quda_smpi_gdr_qmp
export QUDA_RESOURCE_PATH=%(BASE_DIR)s/quda_smpi_no_gdr

#export QUDA_ENABLE_GDR=1
export OMP_NUM_THREADS=8
#export QUDA_ENABLE_DSLASH_POLICY="2,3"

APP=%(BASE_DIR)s/binding_scripts/sierra_bind_gpu.sh

ini=%(XML_IN)s
out=%(XML_OUT)s
stdout=%(STDOUT)s

PROG="$LALIBE_GPU -geom 1 1 2 8 -qmp-geom 1 1 2 8 -qmp-alloc-map 3 2 1 0 -qmp-logic-map  3 2 1 0"

APRUNVAR="jsrun -p16 -g1 -M \"-gpu\" --bind=none $APP $PROG"



$APRUNVAR -i $ini -o $out > $stdout 2>&1
'''
