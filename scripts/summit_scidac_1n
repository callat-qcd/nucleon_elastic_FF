#!/bin/bash
#BSUB -nnodes 1
#BSUB -cn_cu 'maxcus=1'
#BSUB -P LGT100
#BSUB -W 120
#BSUB -J milc_scidac
#BSUB -o /gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/a09m260_a/jlog/%J.log
#BSUB -alloc_flags smt4

### These should then go into a python dictionary, built from the area51 file
email='rinaldi2@llnl.gov'
ens_long='l4896f211b630m0052m0363m430'
ens_abbr='a09m260'
stream='a'
nl=48
nt=96
u0=0.874164

cd /gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/${ens_abbr}_${stream}
source /ccs/proj/lgt100/c51/software/summit_smpi/install/env.sh
module load python/3.7.0-anaconda3-5.3.0

export OMP_NUM_THREADS=4
PROG="$KS_HISQ_SPEC  -qmp-geom 1 1 3 2"
export QUDA_RESOURCE_PATH=/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/${ens_abbr}_${stream}/quda_resource_hisq
[[ -d $QUDA_RESOURCE_PATH ]] || mkdir $QUDA_RESOURCE_PATH

milc_in=/ccs/proj/lgt100/c51/x_files/project_2/production/${ens_abbr}_${stream}/scripts/milc_to_scidac.in
ini=/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/${ens_abbr}_${stream}/milc_to_scidac.input

if [[ ! -d cfgs_scidac ]]; then
  mkdir cfgs_scidac
fi

echo "START  "$(date "+%Y-%m-%dT%H:%M")

for no in $(seq 1904 2 3904); do
  echo "cfgs_scidac/${ens_long}${stream}.$no.scidac"
  out=/gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/${ens_abbr}_${stream}/log/${ens_long}${stream}.${no}.log
  if [[ ! -e cfgs_scidac/${ens_long}${stream}.$no.scidac && -e cfgs/${ens_long}${stream}.$no ]]; then
      sed 's/NL/'"$nl"'/g; s/NT/'"$nt"'/g; s/CFG/'"$no"'/g; s/ENS/'"$ens_long"'/g; s/STREAM/'"$stream"'/g; s/TADPOLE/'"$u0"'/g' $milc_in > $ini
      jsrun --nrs 1 -r1 -a6 -g6 -c6 -l gpu-cpu -b packed:smt:4 $PROG $ini >> $out
  fi
done

echo "FINISH WORK "$(date "+%Y-%m-%dT%H:%M")
