import heapq
from mapper import M, TRAPS, ROOMS
from mincost import apply, SH
STEP=[-16,1,16,-1]; ENTER=[0x02,0x04,0x08,0x01]; DOOR=[0x80,0x10,0x20,0x40]
def moves(m,c,d):
    # forward
    for name,dd,nd in (('8',d,d),('2',(d+2)&3,d)):
        y=(c+STEP[dd])&255
        if abs((c&15)-(y&15))>1: continue
        # back move checks c722 = ENTER of opposite? use same rule: dest cell entering side
        if m[y]&ENTER[dd]: continue
        yield name,y,nd
    # run: forward until blocked
    x=c; n=0
    while True:
        y=(x+STEP[d])&255
        if abs((x&15)-(y&15))>1 or m[y]&ENTER[d]: break
        x=y; n+=1
        if n>16: break
    if n>=2: yield 'C',x,d
    yield '6',c,(d+1)&3
    yield '4',c,(d+3)&3
def solve(m,f,src,sdir,dst,ddir,traps,lethal,allow_back=True):
    start=(src,sdir); dist={start:(0,0)}; prev={start:None}
    h=[(0,0,src,sdir)]
    while h:
        hits,n,c,d=heapq.heappop(h)
        if (c,d)==(dst,ddir) or (ddir is None and c==dst): 
            seq=[]; s=(c,d)
            while prev[s]: s,a=prev[s]; seq.append(a)
            return hits,seq[::-1]
        if dist[(c,d)]<(hits,n): continue
        for a,y,nd in moves(m,c,d):
            if a=='2' and not allow_back: continue
            t=traps.get((f,y))
            if t in lethal: continue
            nh=hits+(1 if t==1 else 0)
            s=(y,nd)
            if s not in dist or (nh,n+1)<dist[s]:
                dist[s]=(nh,n+1); prev[s]=((c,d),a); heapq.heappush(h,(nh,n+1,y,nd))
    return None
def doordir(m,c):
    return [k for k in range(4) if m[c]&DOOR[k]][0]
def solve_once(m,f,src,sdir,dst,ddir,traps,lethal,once=8):
    start=(src,sdir,0); dist={start:(0,0)}; prev={start:None}
    h=[(0,0,src,sdir,0)]
    while h:
        hits,n,c,d,u=heapq.heappop(h)
        if c==dst and (ddir is None or d==ddir):
            seq=[]; s=(c,d,u)
            while prev[s]: s,a=prev[s]; seq.append(a)
            return hits,seq[::-1]
        if dist[(c,d,u)]<(hits,n): continue
        for a,y,nd in moves(m,c,d):
            t=traps.get((f,y)); nu=u
            if t==once:
                if u: continue
                nu=1
            elif t in lethal: continue
            nh=hits+(1 if t==1 else 0)
            s=(y,nd,nu)
            if s not in dist or (nh,n+1)<dist[s]:
                dist[s]=(nh,n+1); prev[s]=((c,d,u),a); heapq.heappush(h,(nh,n+1,y,nd,nu))
    return None
