import tables as h5
import numpy as np
import matplotlib.pyplot as plt
np.set_printoptions(linewidth=180)

ga_nature  = 1.236
dga_nature = 0.011

dt_plot = [7,10,14]

def bs_corr(corr,Nbs,Mbs,seed=None,rescale=True,return_lst=False):
    corr_bs = np.zeros(tuple([Nbs]) + corr.shape[1:],dtype=corr.dtype)
    np.random.seed(seed) # if None - it does not seed - I checked 14 May 2013
    # make bs_lst of shape (Nbs,Mbs)
    bs_lst = np.random.randint(0,corr.shape[0],(Nbs,Mbs))
    # use bs_lst to make corr_bs entries
    for bs in range(Nbs):
        corr_bs[bs] = corr[bs_lst[bs]].mean(axis=0)
    if rescale:
        d_corr_bs = corr_bs - corr_bs.mean(axis=0)
        corr_bs = corr_bs.mean(axis=0) + d_corr_bs * np.sqrt(1. * Mbs / corr.shape[0])
    if return_lst:
        return corr_bs,bs_lst
    else:
        return corr_bs
def time_reverse(corr,phase=1,time_axis=1):
    ''' assumes time index is second of array '''
    ''' assumes phase = +- 1 '''
    if len(corr.shape) > 1:
        cr = phase * np.roll(corr[:,::-1],1,axis=time_axis)
        cr[:,0] = phase * cr[:,0]
    else:
        cr = phase * np.roll(corr[::-1],1)
        cr[0] = phase * cr[0]
    return cr
plt.ion()

fig1 = plt.figure(1,figsize=(12,4))
ax1  = plt.axes([.08, .13, .9, .85])

h5_file = h5.open_file('avg_a3_v4_spin.h5','r')
h5_spec = h5.open_file('../../../data/charges/a09m310_e_avg.h5','r')

proton_pp  = 0.5 * h5_spec.get_node('/gf1p0_w3p5_n45_M51p1_L56_a1p5/spec/ml0p00951/proton/px0_py0_pz0/spin_up').read()[:,:,0,0]
proton_pp += 0.5 * h5_spec.get_node('/gf1p0_w3p5_n45_M51p1_L56_a1p5/spec/ml0p00951/proton/px0_py0_pz0/spin_dn').read()[:,:,0,0]
proton_np  = 0.5 * h5_spec.get_node('/gf1p0_w3p5_n45_M51p1_L56_a1p5/spec/ml0p00951/proton_np/px0_py0_pz0/spin_up').read()[:,:,0,0]
proton_np += 0.5 * h5_spec.get_node('/gf1p0_w3p5_n45_M51p1_L56_a1p5/spec/ml0p00951/proton_np/px0_py0_pz0/spin_dn').read()[:,:,0,0]
proton = 0.5 * (proton_pp + time_reverse(proton_np,phase=-1,time_axis=1))
proton_bs = bs_corr(proton,784,784,seed=10)
h5_spec.close()

a3_sum = np.zeros_like(proton)
v4_sum = np.zeros_like(proton)

for dt in [3,4,5,6,7,8,9,10,11,12,13,14]:
    '''
    a3 = h5_file.get_node('/tsep_'+str(dt)+'/a3').read()
    v4 = h5_file.get_node('/tsep_'+str(dt)+'/v4').read()
    '''
    a3_u_pp = h5_file.get_node('/tsep_'+str(dt)+'/a3_u_pp').read()
    v4_u_pp = h5_file.get_node('/tsep_'+str(dt)+'/v4_u_pp').read()
    a3_u_np = h5_file.get_node('/tsep_'+str(dt)+'/a3_u_np').read()
    v4_u_np = h5_file.get_node('/tsep_'+str(dt)+'/v4_u_np').read()
    a3_d_pp = h5_file.get_node('/tsep_'+str(dt)+'/a3_d_pp').read()
    v4_d_pp = h5_file.get_node('/tsep_'+str(dt)+'/v4_d_pp').read()
    a3_d_np = h5_file.get_node('/tsep_'+str(dt)+'/a3_d_np').read()
    v4_d_np = h5_file.get_node('/tsep_'+str(dt)+'/v4_d_np').read()
    a3_u = 0.5*(a3_u_pp + a3_u_np)
    v4_u = 0.5*(v4_u_pp + v4_u_np)
    a3_d = 0.5*(a3_d_pp + a3_d_np)
    v4_d = 0.5*(v4_d_pp + v4_d_np)

    #a3_sum[:,dt] = np.sum(a3[:,1:dt],axis=1)
    #v4_sum[:,dt] = np.sum(v4[:,1:dt],axis=1)
    a3_u_bs = bs_corr(a3_u,784,784,seed=10)
    v4_u_bs = bs_corr(v4_u,784,784,seed=10)
    a3_d_bs = bs_corr(a3_d,784,784,seed=10)
    v4_d_bs = bs_corr(v4_d,784,784,seed=10)

    x  = np.arange(96)[1:dt]-float(dt)/2
    y  = ((a3_u-a3_d).mean(axis=0)/(v4_u+v4_d).mean(axis=0))[1:dt]
    dy = (((a3_u_bs-a3_d_bs)/(v4_u_bs+v4_d_bs)).std(axis=0))[1:dt]
    if dt in dt_plot:
        ax1.errorbar(x,y,yerr=dy,linestyle='None',marker='s',mfc='None',label=r'$t_{sep}=%d$'%(dt))

    x   = np.arange(96)[1:dt]-float(dt)/2-0.05
    y   = ((a3_u).mean(axis=0)/(v4_u).mean(axis=0))[1:dt]
    dyu = (((a3_u_bs)/(v4_u_bs)).std(axis=0))[1:dt]
    if dt in dt_plot:
        ax1.errorbar(x,y,yerr=dy,color='k',linestyle='None',marker='o',mfc='None',alpha=.3)

    var_ratio = dy * np.sqrt(2) / dyu
    string = str(dt)
    for i in var_ratio:
        string += ' &%.2f' %i
    string = string + '\\\\'
    print(string)
    #print(dt,dyu/dy/np.sqrt(2))

    x  = np.arange(96)[1:dt]-float(dt)/2+0.05
    y  = ((-a3_d).mean(axis=0)/(v4_d).mean(axis=0))[1:dt]
    dy = (((a3_d_bs)/(v4_d_bs)).std(axis=0))[1:dt]
    if dt in dt_plot:
        ax1.errorbar(x,y,yerr=dy,color='k',linestyle='None',marker='o',mfc='None',alpha=.3)


#ax1.fill_between(np.arange(-11,11.1,.1),ga_nature-dga_nature,ga_nature+dga_nature,color='k',alpha=.2)
ax1.axis([-6.5,6.5,0.95,1.3])
ax1.legend(loc=2,ncol=4,fontsize=16)
ax1.set_xlabel(r'$\tau-t_{sep}/2$',fontsize=16)
ax1.set_ylabel(r'$g_A/g_V$',fontsize=20)
plt.savefig('../fh_vs_seq/figures/gA_gV_spin_a09m310_e.pdf',transparent=True)

a3_sum_bs = bs_corr(a3_sum,784,784,seed=10)
v4_sum_bs = bs_corr(v4_sum,784,784,seed=10)

''' collector script already takes IMAG part of a3 '''
a3_r = np.real(a3_sum.mean(axis=0)) / np.real(proton.mean(axis=0))
v4_r = np.real(v4_sum.mean(axis=0)) / np.real(proton.mean(axis=0))

a3_r_bs = np.real(a3_sum_bs) / np.real(proton_bs)
v4_r_bs = np.real(v4_sum_bs) / np.real(proton_bs)


"""
fig2 = plt.figure(2)
ax2  = plt.axes([.12, .12, .85, .85])
for t in range(3,14):
    if t == 3:
        label=r'$g_A$'
    else:
        label=''
    ax2.errorbar(t,a3_r[t+1]-a3_r[t],yerr=(a3_r_bs[:,t+1]-a3_r_bs[:,t]).std(),
        marker='s',color='b',mfc='None',linestyle='None',label=label)
    if t == 3:
        label=r'$g_V$'
    else:
        label=''
    ax2.errorbar(t,v4_r[t+1]-v4_r[t],yerr=(v4_r_bs[:,t+1]-v4_r_bs[:,t]).std(),
        marker='*',color='b',mfc='None',linestyle='None',label=label)
ax2.legend(loc=7,fontsize=16)
ga_raw  = 1.266
dga_raw = 0.011
gv_raw  = 1.024
dgv_raw = 0.001
ax2.fill_between(np.arange(-11,14.1,.1),ga_raw-dga_raw,ga_raw+dga_raw,color='k',alpha=.2)
ax2.fill_between(np.arange(-11,14.1,.1),gv_raw-dgv_raw,gv_raw+dgv_raw,color='k',alpha=.2)
ax2.axis([0,14,0.9,1.35])
ax2.set_xlabel(r'$t_{sep}$',fontsize=16)
ax2.set_ylabel(r'$\sum_{\tau} g_A(\tau,t_{sep})$',fontsize=16)
plt.savefig('../fh_vs_seq/figures/gA_summed_a09m310_e.pdf',transparent=True)

fig3 = plt.figure(3)
ax3  = plt.axes([.12, .12, .85, .85])
for t in range(3,14):
    if t == 3:
        label=r'$g_A/g_V$'
    else:
        label=''
    ax3.errorbar(t,(a3_r[t+1]-a3_r[t])/(v4_r[t+1]-v4_r[t]),
        yerr=((a3_r_bs[:,t+1]-a3_r_bs[:,t])/(v4_r_bs[:,t+1]-v4_r_bs[:,t])).std(),
        marker='s',color='b',mfc='None',linestyle='None',label=label)
ax3.legend(loc=2,fontsize=16)
gagv  = 1.236
dgagv = 0.011
ax3.fill_between(np.arange(-11,14.1,.1),gagv-dgagv,gagv+dgagv,color='k',alpha=.2)
ax3.fill_between(np.arange(-11,14.1,.1),gagv-dgagv,gagv+dgagv,color='k',alpha=.2)
ax3.axis([0,14,0.9,1.35])
ax3.set_xlabel(r'$t_{sep}$',fontsize=16)
ax3.set_ylabel(r'$\sum_{\tau} g_A(\tau,t_{sep}) / \sum_\tau g_V(\tau,t_{sep})$',fontsize=16)
plt.savefig('../fh_vs_seq/figures/gAgV_summed_a09m310_e.pdf',transparent=True)


'''
a3_np = h5_file.get_node('/a3_np').read()
v4_np = h5_file.get_node('/v4_np').read()

a3_np_bs = bs_corr(a3_np,800,800,seed=10)
v4_np_bs = bs_corr(v4_np,800,800,seed=10)

fig2 = plt.figure(2)
ax2  = plt.axes([.1, .1, .8, .8])
ax2.axis([0,11,1.,1.4])
ax2.set_title(r'$g_A/g_V$ neg parity')

ax2.errorbar(np.arange(96),a3_np.mean(axis=0)/v4_np.mean(axis=0),
    yerr=(a3_np_bs/v4_np_bs).std(axis=0))
ax2.fill_between(np.arange(0,11.1,.1),ga_nature-dga_nature,ga_nature+dga_nature,color='k',alpha=.2)
plt.savefig('../fh_vs_seq/figures/gA_gV_np_tsep10_a09m310_e.pdf',transparent=True)

fig3 = plt.figure(3)
ax3  = plt.axes([.1, .1, .8, .8])
ax3.errorbar(np.arange(96),(a3-a3_np).mean(axis=0)/(v4-v4_np).mean(axis=0),
    yerr=((a3_bs-a3_np_bs)/(v4_bs-v4_np_bs)).std(axis=0))
ax3.fill_between(np.arange(0,11.1,.1),ga_nature-dga_nature,ga_nature+dga_nature,color='k',alpha=.2)
ax3.axis([0,11,1.,1.4])
ax3.set_title(r'$g_A/g_V$')
plt.savefig('../fh_vs_seq/figures/gA_gV_tsep10_a09m310_e.pdf',transparent=True)
'''

'''
fig4 = plt.figure(4)
ax4  = plt.axes([.1, .1, .8, .8])
ax4.errorbar(np.arange(96),(a3).mean(axis=0),
    yerr=(v4_bs).std(axis=0))
ax4.errorbar(np.arange(96)+.2,(a3_np).mean(axis=0),
    yerr=(v4_np_bs).std(axis=0))
'''

"""

h5_file.close()

plt.ioff()
plt.show()
