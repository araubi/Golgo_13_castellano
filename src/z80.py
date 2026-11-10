r=['b','c','d','e','h','l','(hl)','a']
rp=['bc','de','hl','sp']; rp2=['bc','de','hl','af']
cc=['nz','z','nc','c','po','pe','p','m']
alu=['add a,','adc a,','sub ','sbc a,','and ','xor ','or ','cp ']
rot=['rlc','rrc','rl','rr','sla','sra','sll','srl']
def dis(m,pc,base):
    """m: bytes; pc: address; returns (text,len)"""
    def b(i): return m[pc-base+i]
    def w(i): return b(i)|(b(i+1)<<8)
    o=b(0); ix=None; n=0
    if o in (0xdd,0xfd):
        ix='ix' if o==0xdd else 'iy'; n=1; o=b(1)
        if o in (0xdd,0xfd,0xed): return ('db %02x'%b(0),1)
    def R(k,d=None):
        if ix is None: return r[k]
        if k==6: return '(%s%+d)'%(ix,d)
        return {4:ix+'h',5:ix+'l'}.get(k,r[k])
    def RP(k): return ix if (ix and k==2) else rp[k]
    def RP2(k): return ix if (ix and k==2) else rp2[k]
    def sd(x): return x-256 if x>127 else x
    x,y,z=o>>6,(o>>3)&7,o&7; p,q=y>>1,y&1
    L=1+n
    if o==0xcb:
        if ix:
            dd=sd(b(n+1)); op=b(n+2); L=4
            xx,yy,zz=op>>6,(op>>3)&7,op&7; t='(%s%+d)'%(ix,dd)
        else:
            op=b(1); L=2; xx,yy,zz=op>>6,(op>>3)&7,op&7; t=r[zz]
        if xx==0: return ('%s %s'%(rot[yy],t),L)
        return ('%s %d,%s'%(['','bit','res','set'][xx],yy,t),L)
    if o==0xed:
        op=b(1); xx,yy,zz=op>>6,(op>>3)&7,op&7; pp,qq=yy>>1,yy&1
        if xx==1:
            if zz==0: return ('in %s,(c)'%(r[yy] if yy!=6 else 'f'),2)
            if zz==1: return ('out (c),%s'%(r[yy] if yy!=6 else '0'),2)
            if zz==2: return ('%s hl,%s'%('sbc' if qq==0 else 'adc',rp[pp]),2)
            if zz==3:
                a=b(2)|(b(3)<<8)
                return (('ld (%04x),%s'%(a,rp[pp])) if qq==0 else ('ld %s,(%04x)'%(rp[pp],a)),4)
            if zz==4: return ('neg',2)
            if zz==5: return ('retn' if yy!=1 else 'reti',2)
            if zz==6: return ('im %s'%['0','0/1','1','2'][yy&3],2)
            return (['ld i,a','ld r,a','ld a,i','ld a,r','rrd','rld','nop','nop'][yy],2)
        if xx==2 and zz<=3 and yy>=4:
            return ([['ldi','cpi','ini','outi'],['ldd','cpd','ind','outd'],['ldir','cpir','inir','otir'],['lddr','cpdr','indr','otdr']][yy-4][zz],2)
        return ('db ed,%02x'%op,2)
    # displacement for (ix+d)
    usesd = ix and ((x==1 and (y==6 or z==6) and not(y==6 and z==6)) or (x==2 and z==6) or (x==0 and z in(4,5,6) and y==6))
    dd=sd(b(n+1)) if usesd else 0
    if usesd: L+=1
    a0=n+1+(1 if usesd else 0)
    if x==0:
        if z==0:
            if y==0: return ('nop',L)
            if y==1: return ("ex af,af'",L)
            e=sd(b(a0)); t=(pc+2+e)&0xffff
            if y==2: return ('djnz %04x'%t,L+1)
            if y==3: return ('jr %04x'%t,L+1)
            return ('jr %s,%04x'%(cc[y-4],t),L+1)
        if z==1:
            if q==0: return ('ld %s,%04x'%(RP(p),w(a0)),L+2)
            return ('add %s,%s'%(RP(2),RP(p)),L)
        if z==2:
            if p==0: return (['ld (bc),a','ld a,(bc)'][q],L)
            if p==1: return (['ld (de),a','ld a,(de)'][q],L)
            if p==2: return ((('ld (%04x),%s'%(w(a0),RP(2))) if q==0 else ('ld %s,(%04x)'%(RP(2),w(a0)))),L+2)
            return ((('ld (%04x),a'%w(a0)) if q==0 else ('ld a,(%04x)'%w(a0))),L+2)
        if z==3: return ('%s %s'%(['inc','dec'][q],RP(p)),L)
        if z==4: return ('inc %s'%R(y,dd),L)
        if z==5: return ('dec %s'%R(y,dd),L)
        if z==6: return ('ld %s,%02x'%(R(y,dd),b(a0)),L+1)
        return (['rlca','rrca','rla','rra','daa','cpl','scf','ccf'][y],L)
    if x==1:
        if o==0x76: return ('halt',L)
        if y==6 or z==6:
            return ('ld %s,%s'%(R(y,dd) if y!=6 else R(6,dd), (r[z] if (ix and y==6) else R(z,dd)) if z!=6 else R(6,dd)) if not(ix and z==6) else 'ld %s,%s'%(r[y],R(6,dd)),L)
        return ('ld %s,%s'%(R(y),R(z)),L)
    if x==2: return (alu[y]+R(z,dd),L)
    if z==0: return ('ret %s'%cc[y],L)
    if z==1:
        if q==0: return ('pop %s'%RP2(p),L)
        return (['ret','exx','jp (%s)'%RP(2),'ld sp,%s'%RP(2)][p],L)
    if z==2: return ('jp %s,%04x'%(cc[y],w(a0)),L+2)
    if z==3:
        if y==0: return ('jp %04x'%w(a0),L+2)
        if y==2: return ('out (%02x),a'%b(a0),L+1)
        if y==3: return ('in a,(%02x)'%b(a0),L+1)
        return (['','','','','ex (sp),%s'%RP(2),'ex de,hl','di','ei'][y],L)
    if z==4: return ('call %s,%04x'%(cc[y],w(a0)),L+2)
    if z==5:
        if q==0: return ('push %s'%RP2(p),L)
        return ('call %04x'%w(a0),L+2)
    if z==6: return (alu[y]+'%02x'%b(a0),L+1)
    return ('rst %02x'%(y*8),L)
