#!/usr/bin/env python2
from __future__ import print_function
import os, socket, sys#, utils
import argparse
import importlib
import numpy

os.environ["PYTHONHASHSEED"] = "0"
import random_patch as random

hn = socket.gethostname()
def src_start_stop(params,ens,stream):
    # default srcs
    params['si'] = 0
    params['sf'] = 7
    params['ds'] = 1
    #print('debug',ens,stream)
    # ensembles with modified src start/stop info
    if ens == 'a15m135XL':
        if any(host in hn for host in ['lassen']):
            if stream in ['b','c','d','e']:
                pass
            else:
                print('lassen is not running stream %s now with srcs 0-7 x 1' %stream)
                sys.exit()
        elif any(host in hn for host in ['login','batch']):
            if stream in ['b','c','d','e']:
                params['si'] = 8
                params['sf'] = 15
                params['ds'] = 1
            elif stream in ['s']:
                params['si'] = 24
                params['sf'] = 31
                params['ds'] = 1
            else:
                print('summit is not set to run stream %s yet with srcs 0-7 x 1' %stream)
                sys.exit()
    if ens == 'a12m130':
        if any(host in hn for host in ['lassen']):
            params['si'] = 16
            params['sf'] = 23
            params['ds'] = 1
        elif any(host in hn for host in ['login','batch']):
            params['si'] = 24
            params['sf'] = 31
            params['ds'] = 1
    return params

def xyzt(src):
    x = src.split('x')[1].split('y')[0]
    y = src.split('y')[1].split('z')[0]
    z = src.split('z')[1].split('t')[0]
    t = src.split('t')[1]
    return x,y,z,t
def src_split(src):
    x0 = src.split('x')[1].split('y')[0]
    y0 = src.split('y')[1].split('z')[0]
    z0 = src.split('z')[1].split('t')[0]
    t0 = src.split('t')[1]
    return 'x%s_y%s_z%s_t%s' %(x0,y0,z0,t0)

def xXyYzZtT(posn):
    if len(posn) is 4:
        return 'x%dy%dz%dt%d' %(int(posn[0]),int(posn[1]),int(posn[2]),int(posn[3]))
    else:
        print(sys.argv[0],": Position must be a four dimensional array to be stringified.")
        exit()

def modByLattice(nx, ny=None, nz=None):
    if ny is None and nz is None:
        def modder_iso(xyzt):
            # Doesn't mod out by time.
            return [xyzt[0] % int(nx), xyzt[1] % int(nx), xyzt[2] % int(nx), xyzt[3]]
        return modder_iso
    else:
        def modder(xyzt):
            # Doesn't mod out by time.
            return [xyzt[0] % int(nx), xyzt[1] % int(ny), xyzt[2] % int(nz), xyzt[3]]
        return modder

def origin(o):
    return {'O': o}

def antipode(nl):
    # nl: size of lattice
    def generator(o):
    # o[rigin]: a four-vector of integers:
        [x0, y0, z0, t0] = o
        dx = int(nl/2)
        a = {
            'A':    modByLattice(nl)([x0+dx, y0+dx, z0+dx, t0]),
        }
        return a
    return generator

def corners(nl, dx):
    # nl: spatial extent of lattice
    # dx: how far to put the corners around the origin.
    def generator(o):
        # o[rigin]: a four-vector of integers.
        [x0, y0, z0, t0] = o
        m = modByLattice(nl)
        c = {
            'C_1':  m([x0+dx, y0+dx, z0+dx, t0]),
            'C_2':  m([x0-dx, y0-dx, z0-dx, t0]),
            'C_3':  m([x0+dx, y0+dx, z0-dx, t0]),
            'C_4':  m([x0+dx, y0-dx, z0+dx, t0]),
            'C_5':  m([x0-dx, y0+dx, z0+dx, t0]),
            'C_6':  m([x0+dx, y0-dx, z0-dx, t0]),
            'C_7':  m([x0-dx, y0+dx, z0-dx, t0]),
            'C_8':  m([x0-dx, y0-dx, z0+dx, t0]),
        }
        return c
    return generator

def faces(nl, dx):
    # nl: spatial extent of lattice
    # dx: how far to put the corners around the origin.
    def generator(o):
        # o[rigin]: a four-vector of integers.
        [x0, y0, z0, t0] = o
        m = modByLattice(nl)
        f = {
            'F_1':  m([x0+dx, y0,       z0,     t0]),
            'F_2':  m([x0-dx, y0,       z0,     t0]),
            'F_3':  m([x0,    y0+dx,    z0,     t0]),
            'F_4':  m([x0,    y0-dx,    z0,     t0]),
            'F_5':  m([x0,    y0,       z0+dx,  t0]),
            'F_6':  m([x0,    y0,       z0-dx,  t0]),
        }
        return f
    return generator

def edges(nl, dx):
    def generator(o):
        [x0, y0, z0, t0] = o
        m = modByLattice(nl)
        e = {
            'E_1':  m([x0+dx, y0+dx, z0,    t0]),
            'E_2':  m([x0+dx, y0-dx, z0,    t0]),
            'E_3':  m([x0-dx, y0+dx, z0,    t0]),
            'E_4':  m([x0-dx, y0-dx, z0,    t0]),
            'E_5':  m([x0+dx, y0,    z0+dx, t0]),
            'E_6':  m([x0+dx, y0,    z0-dx, t0]),
            'E_7':  m([x0-dx, y0,    z0+dx, t0]),
            'E_8':  m([x0-dx, y0,    z0-dx, t0]),
            'E_9':  m([x0,    y0+dx, z0+dx, t0]),
            'E_10': m([x0,    y0+dx, z0-dx, t0]),
            'E_11': m([x0,    y0-dx, z0+dx, t0]),
            'E_12': m([x0,    y0-dx, z0-dx, t0]),
        }
        return e
    return generator

def displaced(nl, dxyz):
    def generator(o):
        [x0, y0, z0, t0] = o
        [dx, dy, dz] = dxyz
        m = modByLattice(nl)
        disp = m([x0+dx, y0+dy, z0+dz, t0])
        return { xXyYzZtT(disp): disp }
    return generator

def n_squared(nl, nsq):
    def generator(o):
        [x0, y0, z0, t0] = o
        n = int(numpy.ceil(numpy.sqrt(nsq)))+1
        n2_vecs = []
        for x in range(n):
            for y in range(n):
                for z in range(n):
                    if x**2 + y**2 + z**2 == nsq:
                        n2_vecs.append( ( (x0+x) % int(nl), (y0+y) % int(nl), (z0+z) % int(nl), t0 ) )
                        n2_vecs.append( ( (x0+x) % int(nl), (y0+y) % int(nl), (z0-z) % int(nl), t0 ) )
                        n2_vecs.append( ( (x0+x) % int(nl), (y0-y) % int(nl), (z0+z) % int(nl), t0 ) )
                        n2_vecs.append( ( (x0+x) % int(nl), (y0-y) % int(nl), (z0-z) % int(nl), t0 ) )
                        n2_vecs.append( ( (x0-x) % int(nl), (y0+y) % int(nl), (z0+z) % int(nl), t0 ) )
                        n2_vecs.append( ( (x0-x) % int(nl), (y0+y) % int(nl), (z0-z) % int(nl), t0 ) )
                        n2_vecs.append( ( (x0-x) % int(nl), (y0-y) % int(nl), (z0+z) % int(nl), t0 ) )
                        n2_vecs.append( ( (x0-x) % int(nl), (y0-y) % int(nl), (z0-z) % int(nl), t0 ) )
        # The above loop can produce duplicates.  For example, if there's a solution where z == 0.
        # Then ( x0+x, y0+y, z0 + and - z ) are the same source.  Use python's set data structure to take the union and remove duplicates.
        # set needs hashable ingredients, which is why the ingredients are (tuples), rather than [lists], and why I don't use modByLattice.
        n2_vecs = list(set(n2_vecs))
        n2=dict()
        for i in range(len(n2_vecs)):
            n2[i] = n2_vecs[i]
        return n2
    return generator

def nn(nl, dx=None):
    def generator(o):
        if dx is None:
            d = int((3*nl)/8)
        else:
            d = int(dx)
        nn = dict()
        nn.update(origin(o))
        nn.update(antipode(nl)(o))
        nn.update(corners(nl, d)(o))
        return nn
    return generator

def oa(nl):
    def generator(o):
        oa_ = dict()
        oa_.update({"O": o})
        oa_.update(antipode(nl)(o))
        return oa_

    return generator

def o_hack():
    def generator(o):
        o_ = dict()
        o_.update({"O": o})
        return o_
    return generator

def union(gens):
    # Takes a list of generators that only need an origin passed to them.
    # For example,
    # sources.union([ sources.edges(24,2), sources.faces(24,2), sources.corners(24,2), sources.oa(24) ])
    def generator(o):
        result = dict()
        for g in gens:
            result.update(g(o))
        return result
    return generator

# Default to O only.
def make(no, nl, nt, t_shifts=None, generator=None, seed="seed"):
    """
    no = str(cfg)
    nl = str(L)
    nt = str(T)
    t_shifts = [0,T/2,...] list of time srcs to use
    generator = a function like any of the above functions
        (origin, antipode, corners, nn, oa, etc.)
        NOTE: only be passed the origin four-tuple.
        All the other arguments need to have been partially evaluated arleady
    seed = seed to use for random number generator
        - typically this is "1a" to denote 1=first run, a = stream a
    """
    generator = generator or (lambda o: {"O": o})
    t_shifts = t_shifts or [0]

    random.seed(seed + "." + no)

    srcs = dict()
    for ti, t in enumerate(t_shifts):
        # set up origin for each t0
        x0_0 = random.randint(0, int(nl) - 1)
        y0_0 = random.randint(0, int(nl) - 1)
        z0_0 = random.randint(0, int(nl) - 1)
        if ti == 0:
            t0_0 = random.randint(0, int(nt) - 1)
            t0 = (t0_0 + t) % int(nt)
        else:
            t0 = (t0_0 + t) % int(nt)

        o = [x0_0, y0_0, z0_0, t0]

        srcs[xXyYzZtT(o)] = generator(o)

    return srcs

if __name__ == '__main__':
    '''
    ensemble = c51.ensemble()
    ep = importlib.import_module(ensemble["area51"])

    print('ens:',ensemble["ens"],'-->',ensemble["long"])
    '''
    parser = argparse.ArgumentParser(description='manage source production')
    parser.add_argument('--cfg',type=int,default=300,help='cfg: n')
    parser.add_argument('--src',type=str,help='pass a specific src if desired, xXyYzZtT')
    parser.add_argument('--smr',type=str,help='pass a specific smearing if desired, wW_nN')
    parser.add_argument('--status',type=str,help='A new status for this source.  Status can be "None", ""')
    parser.add_argument('-p','--print',default=False,action='store_const',const=True,\
        help='print list of srcs for testing? [%(default)s]')
    parser.add_argument('--seed',type=str,default='1a',help='seed used in src generation [%(default)s]')
    parser.add_argument('--nl',type=int,default=32,help='spatial volume [%(default)s]')
    parser.add_argument('--nt',type=int,default=96,help='spatial time extent [%(default)s]')
    parser.add_argument('--t_shifts',nargs='+',type=int,default=[0,48,24,72],\
        help='list of t_shifts to use in random src generation [%(default)s]')
    parser.add_argument('--generator',default='oa',\
        help='generator to use in random src generation [%(default)s]')
    args = parser.parse_args()
    print('Arguments passed')
    print(args)
    print('')

    if args.generator == 'oa':
        generator = oa(args.nl)
    elif args.generator == 'o':
        generator = o_hack()
    elif args.generator == 'a':
        generator = antipode(args.nl)
    else:
        print('we only support print testing of o, a, oa at the moment - add more if you like')
        sys.exit()

    cfg = args.cfg
    no=str(cfg)

    if args.print:
        print('printing list of srcs')
        srcs = make(no, nl=args.nl, nt=args.nt, t_shifts=args.t_shifts,
            generator=generator, seed=args.seed)
        '''
        for origin in srcs:
            try:
                src_gen = srcs[origin].iteritems()
            except AttributeError: # Python 3 automatically creates a generator
                src_gen = srcs[origin].items()
            for src_type, src in src_gen:
                print(no,src_type,xXyYzZtT(src))
        '''
        for s_key, s_val in srcs.items():
            for src, val in s_val.items():
                print(no, src, val)
