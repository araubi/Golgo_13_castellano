import sys, pickle, copy
import os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from nav import *
import solver
from solver import doordir
LOG=[]
def dmg(g): return R(g,0xc5c0)|(R(g,0xc5c1)<<8)
def clean(o): return o.replace('\n',' ').replace(' ⏎PAGE⏎ ','')
def do(g,c,quiet=False):
    o=g.cmd(c); LOG.append(('cmd',c,o))
    if not quiet: print('>',c,'|',clean(o)[:230])
    if 'Arma=' in o:
        o2=g.cmd(b'3',raw=True); LOG.append(('key','3',o2)); print('   [FIGHT] -> 3 |',clean(o2)[:200])
    return o
def go(g,cell,face,lethal_extra=(),allow8=False):
    f,c,d=pos(g)
    m=bytes(g.m.ram[(f-1)*256:(f-1)*256+256])
    act=traps_active(g)
    allow8 = allow8 or R(g,0xc5e1)!=0
    lethal={2,3,4,5,6,7,9} | (set() if allow8 else {8})
    tr={k:(t if t in (1,) or t in lethal else 0) for k,t in act.items()}
    tr={k:t for k,t in tr.items() if t}
    r=solver.solve(m,f,c,d,cell,face,tr,lethal)
    if r is None: raise Exception('no route to %x'%cell)
    seq=r[1]; outs=''
    for a in seq:
        o=do(g,'CORRER' if a=='C' else a,quiet=True); outs+=o
        if g.r!='input': break
    LOG.append(('go',seq))
    print('GO f%d %02x->%02x: %s  hits=%d cmds=%d dmg=%04x pos=%s'%(f,c,cell,''.join(seq),r[0],len(seq),dmg(g),pos(g)))
    for kw in ('¡','Golgo','Arma'):
        if kw in outs: print('   !!',clean(outs)[-300:]); break
    return seq
def save(g,name): pickle.dump((g,LOG),open('snap_%s.pkl'%name,'wb'))
def load(name):
    global LOG
    g,l=pickle.load(open('snap_%s.pkl'%name,'rb')); LOG[:]=l; return g
def tm(g,i): return R(g,0xc58b+4*(i-1))|(R(g,0xc58c+4*(i-1))<<8)
