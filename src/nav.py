import sys, copy, collections
import os
_H=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,_H); sys.path.insert(0,os.path.join(_H,'emu'))
from play import *
STEP=[-16,1,16,-1]; ENTER=[0x02,0x04,0x08,0x01]; DOOR=[0x80,0x10,0x20,0x40]
def R(g,a): return g.m.ram[a-0xc000]
def pos(g): return (R(g,0xc702)-0xbf, R(g,0xc701), R(g,0xc717))
def traps_active(g):
    # trap table c362: floor,cell,type ; trap switch c4f8: type,sw ; switch status c51a: sw,room,state
    tsw={}; a=0xc4f8
    while R(g,a)!=0xff: tsw[R(g,a)]=R(g,a+1); a+=2
    sst={}; a=0xc51a
    while R(g,a)!=0xff: sst[R(g,a)]=R(g,a+2); a+=3
    act={}; a=0xc362
    while R(g,a)!=0xff:
        f,c,t=R(g,a),R(g,a+1),R(g,a+2); a+=3
        sw=tsw.get(t,0)
        on = True if sw==0 else (sst.get(sw,0)!=0)
        if on: act[(f,c)]=t
    return act
def cellv(g,f,c): return R(g,0xc000+(f-1)*256+c)
COST={1:60,8:5000}
def path(g,target,allow=()):
    import heapq
    f,c,d=pos(g); act=traps_active(g)
    prev={c:None}; dist={c:0}; h=[(0,c)]
    while h:
        dx,x=heapq.heappop(h)
        if x==target: break
        if dx>dist[x]: continue
        for dd in range(4):
            y=(x+STEP[dd])&255
            if abs((x&15)-(y&15))>1: continue
            if cellv(g,f,y)&ENTER[dd]: continue
            t=act.get((f,y))
            w=1
            if t and y not in allow:
                if t in COST: w+=COST[t]
                else: continue
            nd=dx+w
            if y not in dist or nd<dist[y]:
                dist[y]=nd; prev[y]=(x,dd); heapq.heappush(h,(nd,y))
    if target not in prev: return None
    moves=[]; x=target
    while prev[x]: px,dd=prev[x]; moves.append(dd); x=px
    return moves[::-1]
def turn_cmds(cur,want):
    k=(want-cur)&3
    return {0:[],1:['6'],2:['6','6'],3:['4']}[k]
def goto(g,target,face=None,log=None,**kw):
    mv=path(g,target,**kw)
    if mv is None: raise Exception('no path to %x from %s'%(target,pos(g)))
    cmds=[]
    d=pos(g)[2]
    for dd in mv:
        cmds+=turn_cmds(d,dd)+['8']; d=dd
    if face is not None: cmds+=turn_cmds(d,face)
    out=''
    for c in cmds:
        o=g.cmd(c); out+=o
        if g.r!='input' or 'FIN' in o: break
    if log is not None: log.append((cmds,out))
    return cmds,out
