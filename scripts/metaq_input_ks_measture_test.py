strange_charm_loops='''#!/usr/bin/env bash
#METAQ NODES %(NODES)s
#METAQ GPUS %(GPUS)s
#METAQ MIN_WC_TIME %(WTIME)s
#METAQ LOG %(LOG)s
#METAQ PROJECT %(PROJECT)s

#BSUB -nnodes 1
#BSUB -cn_cu 'maxcus=1'
#BSUB -q pbatch
#BSUB -G latticgc
#BSUB -W %(BWTIME)s
#BSUB -J c51
#BSUB -core_isolation 2
#BSUB -alloc_flags smt4

echo "HOSTS"
tail -n +2 ~/.lsbatch/*.${LSB_JOBID}.hostfile | sort -u
echo ""

cd /usr/workspace/coldqcd/software/callat_build_scripts/from_arjun
source /usr/workspace/coldqcd/software/lassen_smpi_RR/install/env.sh

export OMP_NUM_THREADS=4
EXEC=/usr/workspace/coldqcd/software/lassen_smpi_RR/install/lattice_milc_qcd/ks_measure_hisq
APP=/usr/workspace/coldqcd/software/callat_build_scripts/binding_scripts/lassen_bind_gpu.omp4.sh

ini=%(INI)s
out=%(OUT)s

echo "TIME STAMP: START `date`" > $out
jsrun --nrs 1 -r1 -a4 -g4 -c4 -b none -d packed $APP $EXEC -qmp-geom 1 1 1 4 -qmp-logic-map 3 2 1 0 -qmp-alloc-map 3 2 1 0 $ini >> $out 2>&1
echo "TIME STAMP: END `date`" >> $out
'''
