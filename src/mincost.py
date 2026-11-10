import heapq
from mapper import M, TRAPS
STEP=[-16,1,16,-1]; ENTER=[0x02,0x04,0x08,0x01]
def dij(m,f,src,traps,lethal):
    dist={src:(0,0)}; h=[(0,0,src)]
    while h:
        hits,steps,x=heapq.heappop(h)
        if dist[x]<(hits,steps): continue
        for dd in range(4):
            y=(x+STEP[dd])&255
            if abs((x&15)-(y&15))>1: continue
            if m[y]&ENTER[dd]: continue
            t=traps.get((f,y))
            if t in lethal: continue
            nh=hits+(1 if t==1 else 0); ns=steps+1
            if y not in dist or (nh,ns)<dist[y]:
                dist[y]=(nh,ns); heapq.heappush(h,(nh,ns,y))
    return dist
if __name__=='__main__':
    pts={'start':0xd9,'r02':0x2c,'r03':0x4c,'r04':0xde,'r05':0xe6}
    m=M[0]
    for a,ca in pts.items():
        dd=dij(m,1,ca,TRAPS,{2,3,4,5,6,8})
        print(a,{b:dd.get(cb) for b,cb in pts.items()})
from msx import d,BASE
SH=[]
o=0x9607-BASE
while d[o]!=0xff: SH.append((d[o],d[o+1],d[o+2],d[o+3:o+12])); o+=12
def apply(m,f,ids):
    m=bytearray(m)
    for i,ff,c,patch in SH:
        if i in ids and ff==f:
            base=(c-0x11)&255
            for r in range(3):
                for k in range(3): m[(base+r*16+k)&255]=patch[r*3+k]
    return bytes(m)
