import os, sys
from glob import glob

def check_task(task,mtype,params,folder='todo',overwrite=False,task_type='metaq'):
    if task_type == 'metaq':
        ''' METAQ TASKS '''
        task_exist = False
        for tdir in ['todo','priority','hold']:
            if os.path.exists(params['METAQ_DIR']+'/'+tdir+'/'+mtype+'/'+task):
                task_exist = True
        task_lst  = glob(params['METAQ_DIR']+'/working/*/*.sh')
        task_lst += glob(params['METAQ_DIR']+'/working/*/*/*.sh')
        task_working = False
        for t in task_lst:
            if task == t.split('/')[-1]:
                task_exist = True
                task_working = True
    elif task_type == 'mpi_jm':
        ''' MPI_JM TASKS '''
        print('mpi_jm task generation not supported yet')
        task_exist = True
        task_working = True
        sys.exit()

    return task_exist,task_working

def make_task(task,mtype,params,folder='todo',task_type='metaq'):
    ''' METAQ TASKS '''
    if task_type == 'metaq':
        shebang = """#!/usr/bin/env bash\n\n"""
        print(params['METAQ_DIR']+'/'+folder+'/'+mtype+'/'+task)
        if not os.path.exists(params['METAQ_DIR']+'/'+folder+'/'+mtype):
            os.makedirs(params['METAQ_DIR']+'/'+folder+'/'+mtype)
        metaQ = open(params['METAQ_DIR']+'/'+folder+'/'+mtype+'/'+task,'w')
        metaQ.write(shebang)
        metaQ.write(metaq_tags % params)
        metaQ.write(qsub[params['machine']] % params)
        metaQ.write(args % params)
        metaQ.write(mpirun[params['machine']] % params)
        metaQ.write(cleanup % params)
        metaQ.close()
        os.chmod(params['METAQ_DIR']+'/'+folder+'/'+mtype+'/'+task, 0o770)

    elif task_type == 'mpi_jm':
        print('mpi_jm task generation not supported yet')
        sys.exit()

''' DEFINE A BUNCH OF METAQ TASK INFO '''

metaq_tags = """
#METAQ NODES %(METAQ_NODES)s
#METAQ GPUS %(METAQ_GPUS)s
#METAQ MIN_WC_TIME %(WALL_TIME)s:00
#METAQ LOG %(METAQ_LOG)s
#METAQ PROJECT %(METAQ_PROJECT)s

"""

qsub = dict()
qsub['summit'] = '''
#BSUB -nnodes %(NODES)s
#BSUB -cn_cu 'maxcus=%(MAXCUS)s'
#BSUB -q batch
#BSUB -P LGT100
#BSUB -W %(WALL_TIME)s
#BSUB -alloc_flags smt4

'''

qsub['lassen'] = '''
#BSUB -nnodes %(NODES)s
#BSUB -cn_cu 'maxcus=%(MAXCUS)s'
#BSUB -q pbatch
#BSUB -G latticgc
#BSUB -W %(WALL_TIME)s
#BSUB -core_isolation 2
#BSUB -alloc_flags smt4

'''

qsub['pascal'] = '''
### ADD PASCAL MSUB STUFF

'''

qsub['default'] = '''
### MY_LOCAL_MACHINE

'''

args = '''
cd %(RUN_DIR)s
%(SOURCE_ENV)s

export OMP_NUM_THREADS=%(OMP_NUM_THREADS)s
PROG=%(PROG)s
ini=%(INI)s
out=%(OUT)s
stdout=%(STDOUT)s

echo "START  "$(date "+%%Y-%%m-%%dT%%H:%%M")

'''

mpirun = dict()
mpirun['lassen'] = '''
%(APP)s
jsrun %(NRS)s %(RS_NODE)s %(A_RS)s %(G_RS)s %(C_RS)s -b none -d packed $APP $PROG %(IO_OUT)s
if [ $? -eq 0 ]; then
    echo "successful jsrun"
    cleanup=0
else
    echo "failed jsrun"
    cleanup=1
fi
'''

mpirun['summit'] = '''
%(APP)s
jsrun %(NRS)s %(RS_NODE)s %(A_RS)s %(G_RS)s %(C_RS)s %(L_GPU_CPU)s -b packed:smt:%(OMP_NUM_THREADS)s $PROG %(IO_OUT)s
if [ $? -eq 0 ]; then
    echo "successful jsrun"
    cleanup=0
else
    echo "failed jsrun"
    cleanup=1
fi

'''

mpirun['pascal'] = '''
%(APP)s
#srun -NN -nn %(PROG)s %(IO_OUT)s

'''

mpirun['default'] = '''
#my_mpi_run
'''



cleanup = """
echo "FINISH WORK "$(date "+%%Y-%%m-%%dT%%H:%%M")

# look for failing jsrun connection
if [[ `grep "JSM server is not responding" $stdout | wc -l` > 0 ]]; then
    echo "`date`    ${LSB_JOBID}    $LLNL_COMPUTE_NODES" >> %(JSRUN_FAIL)s
    bkill ${LSB_JOBID}
fi

echo "CLEANING UP"

%(CLEANUP)s

echo "CLEANED UP"

echo "FINISH JOB "$(date "+%%Y-%%m-%%dT%%H:%%M")
"""
