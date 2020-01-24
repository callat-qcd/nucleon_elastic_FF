import os
import sys

ens_s = sys.argv[1]

cfgs = {
    'a15m135XL':range(500,2996,5),
    'a09m135'  :range(78,3103,6),
    'a12m130'  :'300-5295',
    'a12m180L' :'800-1795',
    'a09m220'  :'300-6300',
}

cfg_set = cfgs[ens_s.split('_')[0]]

for cfg in cfg_set:
    no = str(cfg)
    tape_file_querry = os.popen('hsi -P ls /proj/lgt100/c51/x_files/project_2/production/'+ens_s+'/formfac_4D_tslice_src_avg/'+no+' | grep formfac_4D | grep h5').read().split('\n')
    tape_file = []
    for t in tape_file_querry:
        tape_file.append(t.strip())

    for ff in tape_file:
        if 'Nsnk8' in ff:
            src_set = ff.split('Nsnk8_src_avg')[1].split('_')[0]
            print(ff)
            print('    -->  ',ff.replace('Nsnk8_src_avg'+src_set,'Srcs'+src_set+'_src_avg'))
            os.system('hsi -P "cd /proj/lgt100/c51/x_files/project_2/production/'+ens_s+'/formfac_4D_tslice_src_avg/'+no+'; mv '+ff+' '+ff.replace('Nsnk8_src_avg'+src_set,'Srcs'+src_set+'_src_avg')+'"')
