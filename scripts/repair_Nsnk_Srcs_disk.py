import os, sys, shutil
from glob import glob

test=False

try:
    srcs = sys.argv[1].split('Srcs')[1].split('_')[0].split('.')[0]
except:
    sys.exit('file name does not inform what src_set it is from - should have name like prop_lst_a09m135_a_Srcs0-7.lst')

ens,s = sys.argv[1].split('_')[2], sys.argv[1].split('_')[3]

ff_val = {
    'a09m135':  'gf1.0_w3.5_n45_M51.1_L512_a2.0_mq0.00152',
    'a15m135XL':'gf1.0_w3.0_n30_M51.3_L524_a3.5_mq0.00237',
}
t_seps = {
    'a09m135':  range(3,13),
    'a15m135XL':range(3,10),
}

repair_lst = open(sys.argv[1]).readlines()
for p in repair_lst:
    no = p.split('/')[0]
    src = p.split('_')[-1].split('.')[0]
    ff_base = ens+'_'+s+'/formfac/'+no+'/formfac_'+ens+'_'+s+'_'+no+'_'+ff_val[ens]+'_px0py0pz0_dt*_Nsnk8_'+src+'_SS.h5'
    ff_4D_base = ff_base.replace('formfac','formfac_4D')
    ff_4D_tslice_base = ff_base.replace('formfac','formfac_4D_tslice')
    ff_4D_tslice_src_avg_base = ens+'_'+s+'/formfac_4D_tslice_src_avg/'+no+'/formfac_4D_tslice_src_avg_'+ens+'_'+s+'_'+no+'_'+ff_val[ens]+'_px0py0pz0_dt*_Nsnk8_src_avg'+srcs+'_SS.h5'
    for base in [ff_base, ff_4D_base, ff_4D_tslice_base, ff_4D_tslice_src_avg_base]:
        ffs = glob(base)
        for f in ffs:
            if os.path.exists(f):
                print(f)
                print('    -->',f.replace('Nsnk8','Srcs'+srcs).replace('src_avg'+srcs+'_SS','src_avg_SS'))
                if not test:
                    shutil.move(f,f.replace('Nsnk8','Srcs'+srcs).replace('src_avg'+srcs+'_SS','src_avg_SS'))
    '''
    ffs = glob(ens+'_'+s+'/formfac/'+no+'/formfac_'+ens+'_'+s+'_'+no+'_'+ff_val[ens]+'_px0py0pz0_dt*_Nsnk8_'+src+'_SS.h5')

    for ff in ffs:
        ff_4D = ff.replace('formfac','formfac_4D')
        ff_4D_tslice = ff.replace('formfac','formfac_4D_tslice')
        ff_4D_tslice_src_avg = ff.replace('formfac','formfac_4D_tslice_src_avg').replace(src,'src_avg'+srcs)
        for f in [ff, ff_4D, ff_4D_tslice]:
            print(f)
            if os.path.exists(f):
                print(f)
                print('    -->',f.replace('Nsnk8','Srcs'+srcs))
                if not test:
                    shutil.move(f,f.replace('Nsnk8','Srcs'+srcs))
        if os.path.exists(ff_4D_tslice_src_avg):
            print(ff_4D_tslice_src_avg)
            print('    -->',ff_4D_tslice_src_avg.replace('Nsnk8','Srcs'+srcs).replace('src_avg'+srcs,'src_avg'))
            if not test:
                shutil.move(ff_4D_tslice_src_avg,ff_4D_tslice_src_avg.replace('Nsnk8','Srcs'+srcs).replace('src_avg'+srcs,'src_avg'))
    '''
