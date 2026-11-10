from msx import d,BASE
M=[d[0x9200-BASE+f*256:0x9200-BASE+f*256+256] for f in range(3)]
def parse(label_addr,n,end=0xff):
    pass
TRAPS={}
o=0x9562-BASE
while d[o]!=0xff: TRAPS[(d[o],d[o+1])]=d[o+2]; o+=3
ROOMS={}
o=0x9678-BASE
while d[o]!=0xff: ROOMS[(d[o],d[o+1])]=d[o+2]; o+=3
def draw(f,marks={}):
    m=M[f-1]
    out=[]
    out.append('    '+''.join('%x   '%c for c in range(16)))
    for r in range(16):
        top='   +'; mid='%x  '%r
        for c in range(16):
            v=m[r*16+c]
            top+=('---' if v&8 else ('DDD' if v&0x80 else '   '))+'+'
        out.append(top)
        line='%x  '%r
        for c in range(16):
            v=m[r*16+c]; cell=r*16+c
            w='|' if v&4 else ('D' if v&0x40 else ' ')
            if c==0: line+=w
            t=marks.get((f,cell))
            if t is None:
                if (v&0x0f)==0x0f and not v&0xf0: t='###'
                elif (f,cell) in ROOMS: t='R%02x'%ROOMS[(f,cell)]
                elif (f,cell) in TRAPS: t='T%d '%TRAPS[(f,cell)]
                else: t='   '
            line+=t
            line+=('|' if v&1 else ('D' if v&0x10 else ' '))
        out.append(line)
    bot='   +'
    for c in range(16):
        v=m[15*16+c]; bot+=('---' if v&2 else ('DDD' if v&0x20 else '   '))+'+'
    out.append(bot)
    return '\n'.join(out)
if __name__=='__main__':
    for f in (1,2,3):
        print('FLOOR',f); print(draw(f,{(1,0xd9):'@@@'}))
