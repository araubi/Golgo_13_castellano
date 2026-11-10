# Minimal Z80 interpreter (documented behaviour, enough for game logic)
SF,ZF,YF,HF,XF,PF,NF,CF=0x80,0x40,0x20,0x10,0x08,0x04,0x02,0x01
def parity(v):
    v^=v>>4; v^=v>>2; v^=v>>1; return 0 if v&1 else PF
SZP=[ (v&0xa8)|(ZF if v==0 else 0)|parity(v) for v in range(256)]
SZ=[ (v&0xa8)|(ZF if v==0 else 0) for v in range(256)]
class CPU:
    def __init__(s,mem,bus):
        s.m=mem; s.bus=bus
        s.a=s.f=s.b=s.c=s.d=s.e=s.h=s.l=0
        s.a_=s.f_=s.b_=s.c_=s.d_=s.e_=s.h_=s.l_=0
        s.ix=s.iy=0; s.sp=0xf380; s.pc=0; s.i=s.r=0; s.iff=0; s.halted=False
        s.cycles=0
    # memory
    def rb(s,a): return s.bus.rd(a&0xffff)
    def wb(s,a,v): s.bus.wr(a&0xffff,v&0xff)
    def rw(s,a): return s.rb(a)|(s.rb(a+1)<<8)
    def ww(s,a,v): s.wb(a,v); s.wb(a+1,v>>8)
    def fetch(s):
        v=s.rb(s.pc); s.pc=(s.pc+1)&0xffff; return v
    def fetchw(s):
        v=s.rw(s.pc); s.pc=(s.pc+2)&0xffff; return v
    def push(s,v): s.sp=(s.sp-2)&0xffff; s.ww(s.sp,v)
    def pop(s):
        v=s.rw(s.sp); s.sp=(s.sp+2)&0xffff; return v
    # pairs
    def gbc(s): return (s.b<<8)|s.c
    def gde(s): return (s.d<<8)|s.e
    def ghl(s): return (s.h<<8)|s.l
    def sbc_(s,v): s.b=(v>>8)&255; s.c=v&255
    def sde(s,v): s.d=(v>>8)&255; s.e=v&255
    def shl(s,v): s.h=(v>>8)&255; s.l=v&255
    # alu
    def add8(s,v,c=0):
        a=s.a; r=a+v+c
        s.f=SZ[r&255]|(CF if r>255 else 0)|((a^v^r)&HF)|(PF if ((a^~v)&(a^r)&0x80) else 0)
        s.a=r&255
    def sub8(s,v,c=0,store=True):
        a=s.a; r=a-v-c
        f=SZ[r&255]|NF|(CF if r<0 else 0)|((a^v^r)&HF)|(PF if ((a^v)&(a^r)&0x80) else 0)
        if store: s.a=r&255; s.f=f
        else: s.f=(f&~0x28)|(v&0x28)
    def and8(s,v): s.a&=v; s.f=SZP[s.a]|HF
    def xor8(s,v): s.a^=v; s.f=SZP[s.a]
    def or8(s,v): s.a|=v; s.f=SZP[s.a]
    def alu(s,op,v):
        if op==0: s.add8(v)
        elif op==1: s.add8(v,s.f&CF)
        elif op==2: s.sub8(v)
        elif op==3: s.sub8(v,s.f&CF)
        elif op==4: s.and8(v)
        elif op==5: s.xor8(v)
        elif op==6: s.or8(v)
        else: s.sub8(v,0,False)
    def inc8(s,v):
        r=(v+1)&255; s.f=(s.f&CF)|SZ[r]|(HF if (r&15)==0 else 0)|(PF if r==0x80 else 0); return r
    def dec8(s,v):
        r=(v-1)&255; s.f=(s.f&CF)|SZ[r]|NF|(HF if (r&15)==15 else 0)|(PF if r==0x7f else 0); return r
    def add16(s,a,b):
        r=a+b; s.f=(s.f&(SF|ZF|PF))|(CF if r>0xffff else 0)|(((a^b^r)>>8)&HF); return r&0xffff
    def adc16(s,a,b):
        c=s.f&CF; r=a+b+c
        s.f=(CF if r>0xffff else 0)|(((a^b^r)>>8)&HF)|(ZF if (r&0xffff)==0 else 0)|((r>>8)&SF)|(PF if ((a^~b)&(a^r)&0x8000) else 0)
        return r&0xffff
    def sbc16(s,a,b):
        c=s.f&CF; r=a-b-c
        s.f=NF|(CF if r<0 else 0)|(((a^b^r)>>8)&HF)|(ZF if (r&0xffff)==0 else 0)|((r>>8)&SF)|(PF if ((a^b)&(a^r)&0x8000) else 0)
        return r&0xffff
    def rot(s,op,v):
        c=s.f&CF
        if op==0: co=v>>7; v=((v<<1)|co)&255
        elif op==1: co=v&1; v=(v>>1)|(co<<7)
        elif op==2: co=v>>7; v=((v<<1)|c)&255
        elif op==3: co=v&1; v=(v>>1)|(c<<7)
        elif op==4: co=v>>7; v=(v<<1)&255
        elif op==5: co=v&1; v=(v>>1)|(v&0x80)
        elif op==6: co=v>>7; v=((v<<1)|1)&255
        else: co=v&1; v=v>>1
        s.f=SZP[v]|co; return v
    def cond(s,y):
        f=s.f
        return [not f&ZF, bool(f&ZF), not f&CF, bool(f&CF), not f&PF, bool(f&PF), not f&SF, bool(f&SF)][y]
    # register access by index
    def getr(s,k,idx=None,d=0):
        if k==0: return s.b
        if k==1: return s.c
        if k==2: return s.d
        if k==3: return s.e
        if k==4: return (s.ix>>8 if idx=='ix' else s.iy>>8) if idx else s.h
        if k==5: return (s.ix&255 if idx=='ix' else s.iy&255) if idx else s.l
        if k==6: return s.rb(s.addr(idx,d))
        return s.a
    def setr(s,k,v,idx=None,d=0):
        v&=255
        if k==0: s.b=v
        elif k==1: s.c=v
        elif k==2: s.d=v
        elif k==3: s.e=v
        elif k==4:
            if idx=='ix': s.ix=(s.ix&255)|(v<<8)
            elif idx=='iy': s.iy=(s.iy&255)|(v<<8)
            else: s.h=v
        elif k==5:
            if idx=='ix': s.ix=(s.ix&0xff00)|v
            elif idx=='iy': s.iy=(s.iy&0xff00)|v
            else: s.l=v
        elif k==6: s.wb(s.addr(idx,d),v)
        else: s.a=v
    def addr(s,idx,d):
        if idx=='ix': return (s.ix+d)&0xffff
        if idx=='iy': return (s.iy+d)&0xffff
        return s.ghl()
    def getrp(s,p,idx=None):
        if p==0: return s.gbc()
        if p==1: return s.gde()
        if p==2: return s.ix if idx=='ix' else (s.iy if idx=='iy' else s.ghl())
        return s.sp
    def setrp(s,p,v,idx=None):
        v&=0xffff
        if p==0: s.sbc_(v)
        elif p==1: s.sde(v)
        elif p==2:
            if idx=='ix': s.ix=v
            elif idx=='iy': s.iy=v
            else: s.shl(v)
        else: s.sp=v
    def getrp2(s,p,idx=None):
        if p==3: return (s.a<<8)|s.f
        return s.getrp(p,idx)
    def setrp2(s,p,v,idx=None):
        if p==3: s.a=(v>>8)&255; s.f=v&255
        else: s.setrp(p,v,idx)
    def step(s):
        s.cycles+=1
        o=s.fetch(); idx=None
        if o==0xdd or o==0xfd:
            idx='ix' if o==0xdd else 'iy'; o=s.fetch()
            if o==0xcb:
                d=s.fetch(); d=d-256 if d>127 else d; op=s.fetch()
                return s.cb(op,idx,d)
        if o==0xcb: return s.cb(s.fetch(),None,0)
        if o==0xed: return s.ed(s.fetch())
        x,y,z=o>>6,(o>>3)&7,o&7; p,q=y>>1,y&1
        def disp():
            d=s.fetch(); return d-256 if d>127 else d
        if x==1:
            if o==0x76: s.halted=True; return
            if idx and (y==6 or z==6):
                d=disp()
                if y==6: s.wb(s.addr(idx,d),s.getr(z))
                else: s.setr(y,s.rb(s.addr(idx,d)))
                return
            s.setr(y,s.getr(z,idx),idx); return
        if x==2:
            if z==6 and idx: d=disp(); v=s.rb(s.addr(idx,d))
            else: v=s.getr(z,idx)
            s.alu(y,v); return
        if x==0:
            if z==0:
                if y==0: return
                if y==1:
                    s.a,s.a_=s.a_,s.a; s.f,s.f_=s.f_,s.f; return
                e=disp()
                if y==2:
                    s.b=(s.b-1)&255
                    if s.b: s.pc=(s.pc+e)&0xffff
                    return
                if y==3 or s.cond(y-4): s.pc=(s.pc+e)&0xffff
                return
            if z==1:
                if q==0: s.setrp(p,s.fetchw(),idx)
                else: s.setrp(2,s.add16(s.getrp(2,idx),s.getrp(p,idx)),idx)
                return
            if z==2:
                if p==0:
                    if q==0: s.wb(s.gbc(),s.a)
                    else: s.a=s.rb(s.gbc())
                elif p==1:
                    if q==0: s.wb(s.gde(),s.a)
                    else: s.a=s.rb(s.gde())
                elif p==2:
                    a=s.fetchw()
                    if q==0: s.ww(a,s.getrp(2,idx))
                    else: s.setrp(2,s.rw(a),idx)
                else:
                    a=s.fetchw()
                    if q==0: s.wb(a,s.a)
                    else: s.a=s.rb(a)
                return
            if z==3:
                s.setrp(p,s.getrp(p,idx)+(1 if q==0 else -1),idx); return
            if z==4 or z==5:
                d=disp() if (idx and y==6) else 0
                v=s.getr(y,idx,d)
                s.setr(y,s.inc8(v) if z==4 else s.dec8(v),idx,d); return
            if z==6:
                d=disp() if (idx and y==6) else 0
                s.setr(y,s.fetch(),idx,d); return
            # z==7
            a=s.a
            if y==0: c=a>>7; s.a=((a<<1)|c)&255; s.f=(s.f&(SF|ZF|PF))|c
            elif y==1: c=a&1; s.a=(a>>1)|(c<<7); s.f=(s.f&(SF|ZF|PF))|c
            elif y==2: c=a>>7; s.a=((a<<1)|(s.f&CF))&255; s.f=(s.f&(SF|ZF|PF))|c
            elif y==3: c=a&1; s.a=(a>>1)|((s.f&CF)<<7); s.f=(s.f&(SF|ZF|PF))|c
            elif y==4:
                c=s.f&CF; h=s.f&HF; n=s.f&NF; corr=0; nc=0
                if h or (a&15)>9: corr|=6
                if c or a>0x99: corr|=0x60; nc=CF
                r=(a-corr if n else a+corr)&255
                s.f=SZP[r]|nc|n|((a^r)&HF); s.a=r
            elif y==5: s.a=a^255; s.f|=HF|NF
            elif y==6: s.f=(s.f&(SF|ZF|PF))|CF
            else: s.f=((s.f&(SF|ZF|PF))|(HF if s.f&CF else 0))|(0 if s.f&CF else CF)
            return
        # x==3
        if z==0:
            if s.cond(y): s.pc=s.pop()
            return
        if z==1:
            if q==0: s.setrp2(p,s.pop(),idx); return
            if p==0: s.pc=s.pop(); return
            if p==1:
                s.b,s.b_=s.b_,s.b; s.c,s.c_=s.c_,s.c; s.d,s.d_=s.d_,s.d; s.e,s.e_=s.e_,s.e; s.h,s.h_=s.h_,s.h; s.l,s.l_=s.l_,s.l; return
            if p==2: s.pc=s.getrp(2,idx); return
            s.sp=s.getrp(2,idx); return
        if z==2:
            a=s.fetchw()
            if s.cond(y): s.pc=a
            return
        if z==3:
            if y==0: s.pc=s.fetchw(); return
            if y==2: n=s.fetch(); s.bus.out(n,s.a); return
            if y==3: n=s.fetch(); s.a=s.bus.inp(n); return
            if y==4:
                v=s.rw(s.sp); s.ww(s.sp,s.getrp(2,idx)); s.setrp(2,v,idx); return
            if y==5: t=s.gde(); s.sde(s.ghl()); s.shl(t); return
            if y==6: s.iff=0; return
            s.iff=1; return
        if z==4:
            a=s.fetchw()
            if s.cond(y): s.push(s.pc); s.pc=a
            return
        if z==5:
            if q==0: s.push(s.getrp2(p,idx)); return
            a=s.fetchw(); s.push(s.pc); s.pc=a; return
        if z==6: s.alu(y,s.fetch()); return
        s.push(s.pc); s.pc=y*8
    def cb(s,op,idx,d):
        x,y,z=op>>6,(op>>3)&7,op&7
        if idx: v=s.rb(s.addr(idx,d))
        else: v=s.getr(z)
        if x==0:
            r=s.rot(y,v)
            if idx: s.wb(s.addr(idx,d),r)
            else: s.setr(z,r)
        elif x==1:
            s.f=(s.f&CF)|HF|(ZF|PF if not (v>>y)&1 else 0)|(SF if (y==7 and (v&0x80)) else 0)
        else:
            r=(v&~(1<<y)) if x==2 else (v|(1<<y))
            if idx: s.wb(s.addr(idx,d),r)
            else: s.setr(z,r)
    def ed(s,op):
        x,y,z=op>>6,(op>>3)&7,op&7; p,q=y>>1,y&1
        if x==1:
            if z==0:
                v=s.bus.inp(s.c)
                if y!=6: s.setr(y,v)
                s.f=(s.f&CF)|SZP[v]; return
            if z==1: s.bus.out(s.c,s.getr(y) if y!=6 else 0); return
            if z==2:
                if q==0: s.shl(s.sbc16(s.ghl(),s.getrp(p)))
                else: s.shl(s.adc16(s.ghl(),s.getrp(p)))
                return
            if z==3:
                a=s.fetchw()
                if q==0: s.ww(a,s.getrp(p))
                else: s.setrp(p,s.rw(a))
                return
            if z==4: v=s.a; s.a=0; s.sub8(v); return
            if z==5: s.pc=s.pop(); return
            if z==6: return
            if y==0: s.i=s.a
            elif y==1: s.r=s.a
            elif y==2: s.a=s.i; s.f=(s.f&CF)|SZ[s.a]|(PF if s.iff else 0)
            elif y==3: s.a=(s.cycles*7)&127; s.f=(s.f&CF)|SZ[s.a]|(PF if s.iff else 0)
            elif y==4:
                m=s.rb(s.ghl()); a=s.a
                s.wb(s.ghl(),((a&15)<<4)|(m>>4)); s.a=(a&0xf0)|(m&15); s.f=(s.f&CF)|SZP[s.a]
            elif y==5:
                m=s.rb(s.ghl()); a=s.a
                s.wb(s.ghl(),((m&15)<<4)|(a&15)); s.a=(a&0xf0)|(m>>4); s.f=(s.f&CF)|SZP[s.a]
            return
        if x==2 and y>=4 and z<=3:
            inc = 1 if (y&1)==0 else -1
            rep = y>=6
            while True:
                if z==0:
                    s.wb(s.gde(),s.rb(s.ghl())); s.shl(s.ghl()+inc); s.sde(s.gde()+inc)
                    bc=(s.gbc()-1)&0xffff; s.sbc_(bc)
                    s.f=(s.f&(SF|ZF|CF))|(PF if bc else 0)
                    if rep and bc: continue
                    return
                if z==1:
                    v=s.rb(s.ghl()); r=(s.a-v)&255; s.shl(s.ghl()+inc)
                    bc=(s.gbc()-1)&0xffff; s.sbc_(bc)
                    s.f=(s.f&CF)|NF|SZ[r]|((s.a^v^r)&HF)|(PF if bc else 0)
                    if rep and bc and r!=0: continue
                    return
                if z==2:
                    s.wb(s.ghl(),s.bus.inp(s.c)); s.shl(s.ghl()+inc); s.b=(s.b-1)&255
                    s.f=ZF|NF if s.b==0 else NF
                    if rep and s.b: continue
                    return
                if z==3:
                    s.bus.out(s.c,s.rb(s.ghl())); s.shl(s.ghl()+inc); s.b=(s.b-1)&255
                    s.f=ZF|NF if s.b==0 else NF
                    if rep and s.b: continue
                    return
        return
