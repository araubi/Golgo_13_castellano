import sys, collections
import os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv)<3: sys.exit('Uso: python3 build.py golgo13_jp.rom golgo13_es.rom')
from asm import assemble
from es_text import MSG, INLINE, STATUS, SHORT, VOCAB, EXTRA_SENT
ORIG=open(sys.argv[1],'rb').read()
import hashlib
if hashlib.sha1(ORIG).hexdigest()!='031a611ba1f75b7d5fe3ed088a61c24598b4b314': sys.exit('ROM original desconocida (se espera SHA-1 031a611b...)')
rom=bytearray(ORIG)
B=0x4000
def W(addr,data): rom[addr-B:addr-B+len(data)]=data
def R(addr,n): return bytes(rom[addr-B:addr-B+n])

CMAP={'á':0xA0,'é':0x82,'í':0xA1,'ó':0xA2,'ú':0xA3,'ñ':0xA4,'Ñ':0xA5,'¿':0xA8,'¡':0xAD,'«':0xAE,'»':0xAF,
      'ü':0x81,'É':0x90,'Á':0x83,'Í':0x84,'Ó':0x85,'Ú':0x86,'\r':0x0D,'\b':0x08,'\f':0x0C}
def raw(s):
    out=bytearray()
    for c in s:
        if c in CMAP: out.append(CMAP[c])
        elif 0x20<=ord(c)<0x7f: out.append(ord(c))
        else: raise ValueError('char %r in %r'%(c,s))
    return bytes(out)
# ---------- DTE ----------
DTE_BASE=0xB0; DTE_N=0xFF-DTE_BASE   # codes B0..FE
texts=[raw(t) for t in MSG.values()]+[raw(t) for t in INLINE.values()]
def best_pairs(texts,n):
    pairs=[]
    cur=[bytearray(t) for t in texts]
    for k in range(n):
        cnt=collections.Counter()
        for t in cur:
            i=0
            while i<len(t)-1:
                a,b=t[i],t[i+1]
                if a<DTE_BASE and b<DTE_BASE and a>=0x20 and b>=0x20:
                    cnt[(a,b)]+=1
                i+=1
        if not cnt: break
        (a,b),c=cnt.most_common(1)[0]
        if c<3: break
        code=DTE_BASE+k; pairs.append((a,b))
        for t in cur:
            i=0
            while i<len(t)-1:
                if t[i]==a and t[i+1]==b: t[i:i+2]=bytes([code])
                i+=1
    return pairs
PAIRS=best_pairs(texts,DTE_N)
def comp(bs):
    t=bytearray(bs)
    for k,(a,b) in enumerate(PAIRS):
        i=0
        while i<len(t)-1:
            if t[i]==a and t[i+1]==b: t[i:i+2]=bytes([DTE_BASE+k])
            i+=1
    return bytes(t)
DTE_TABLE=b''.join(bytes(p) for p in PAIRS)
# ---------- data blobs ----------
msgs=bytearray()
for k in sorted(MSG): msgs+=bytes([k])+comp(raw(MSG[k]))+b'\x00'
msgs+=b'\xff'
dic=bytearray()
for k,ws in VOCAB.items():
    for w in ws.split(): dic+=bytes([k])+w.encode()+b'\x00'
dic+=b'\xff'
# sentences: original table + extras
o=0x9c29-B; sent=bytearray()
while ORIG[o]!=0xff: sent+=ORIG[o:o+3]; o+=3
for r,a,b in EXTRA_SENT: sent+=bytes([r,a,b])
sent+=b'\xff'
CUSTOM_FONT=bytes([
 0x10,0x20,0x70,0x88,0xF8,0x88,0x88,0x00,  # 83 Á
 0x10,0x20,0x70,0x20,0x20,0x20,0x70,0x00,  # 84 Í
 0x10,0x20,0x70,0x88,0x88,0x88,0x70,0x00,  # 85 Ó
 0x10,0x20,0x88,0x88,0x88,0x88,0x70,0x00]) # 86 Ú
ACC=bytes([0xA0,ord('A'),0x82,ord('E'),0xA1,ord('I'),0xA2,ord('O'),0xA3,ord('U'),0x81,ord('U'),0xA4,0xA5,0x90,ord('E'),0])
shortblob=bytearray(); SHORTADR={}
# ---------- regions ----------
REGIONS=[[0x6550,0x6A00],[0x990B,0xA7FD],[0x4117,0x4300],[0x6C00,0x6C80],[0x9880,0x9900],[0xBF77,0xC000]]
for a,b in REGIONS: W(a,b'\xff'*(b-a))
def alloc(size,name):
    best=None
    for r in REGIONS:
        if r[1]-r[0]>=size:
            if best is None or (r[1]-r[0])<(best[1]-best[0]): best=r
    if best is None: raise MemoryError('no room for %s (%d)'%(name,size))
    a=best[0]; best[0]+=size; return a
CODE_ADDR=0x6550; CODE_MAX=0x300
REGIONS[0][0]+=CODE_MAX  # reserve code space
LAB={}
LAB['MSGS']=alloc(len(msgs),'msgs'); W(LAB['MSGS'],msgs)
LAB['DICT']=alloc(len(dic),'dict'); W(LAB['DICT'],dic)
LAB['SENT']=alloc(len(sent),'sent'); W(LAB['SENT'],sent)
LAB['DTE']=alloc(len(DTE_TABLE),'dte'); W(LAB['DTE'],DTE_TABLE)
LAB['CFONT']=alloc(len(CUSTOM_FONT),'font'); W(LAB['CFONT'],CUSTOM_FONT)
LAB['ACCT']=alloc(len(ACC),'acc'); W(LAB['ACCT'],ACC)
for k,v in SHORT.items():
    b=raw(v)+b'\x00'; a=alloc(len(b),'short'); W(a,b); SHORTADR[k]=a
# ---------- new code ----------
LAB.update(dict(PEND=0xF2F0,LSEP=0xF2F1,LADF=0xF2F2,DRWF=0xF2F3,COL=0xC729,ROW=0xC72A,PUTC=0x55CD,GETK=0x55D9,DTEB=DTE_BASE))
CODE=r'''
; ---- GETC: next char from (DE) with DTE expansion. Z set at end (A=0)
GETC:   ld a,(PEND)
        or a
        jr z,gc_mem
        push af
        xor a
        ld (PEND),a
        pop af
        ret                 ; NZ (a!=0)
gc_mem: ld a,(de)
        inc de
        cp DTEB
        jr c,gc_lit
        cp $ff
        jr z,gc_lit
        push hl
        push bc
        sub DTEB
        ld l,a
        ld h,0
        add hl,hl
        ld bc,DTE
        add hl,bc
        ld a,(hl)
        inc hl
        ld c,a
        ld a,(hl)
        ld (PEND),a
        ld a,c
        pop bc
        pop hl
gc_lit: or a
        ret
; ---- PRINTS: print string at DE (DTE + word wrap); DE -> after terminator
PRINTS: push bc
        push hl
        xor a
        ld (PEND),a
        inc a
        ld (LSEP),a
ps_l:   call GETC
        jr z,ps_e
        call PUTW
        jr ps_l
ps_e:   pop hl
        pop bc
        ret
PUTW:   cp $20
        jr z,pw_sp
        jr c,pw_ct
        ld c,a
        ld a,(LSEP)
        or a
        jr z,pw_o
        xor a
        ld (LSEP),a
        push de
        ld a,(PEND)
        push af
        ld b,1
pw_m:   call GETC
        jr z,pw_me
        cp $21
        jr c,pw_me
        inc b
        jr pw_m
pw_me:  pop af
        ld (PEND),a
        pop de
        ld a,(ROW)
        cp 4
        jr c,pw_o
        ld a,(COL)
        or a
        jr z,pw_o
        add a,b
        cp 13
        jr c,pw_o
        ld a,13
        call PUTC
pw_o:   ld a,c
        jp PUTC
pw_sp:  ld a,1
        ld (LSEP),a
        ld a,(ROW)
        cp 4
        jr c,pw_s2
        ld a,(COL)
        or a
        ret z
pw_s2:  ld a,$20
        jp PUTC
pw_ct:  ld c,a
        ld a,1
        ld (LSEP),a
        ld a,c
        jp PUTC
; ---- INLINE: replacement for 4c86 (string follows call)
INLINE: ex (sp),hl
        push de
        ex de,hl
        call PRINTS
        ex de,hl
        pop de
        ex (sp),hl
        ret
; ---- SENT: sentence lookup with swapped-order retry. E=w1 D=w2 -> A
SENTF:  push hl
        push de
        call SFIND
        jr nz,sn_ok
        ld a,d
        ld d,e
        ld e,a
        call SFIND
sn_ok:  pop de
        pop hl
        ret
SFIND:  push bc
        ld hl,SENT
sf_l:   ld a,(hl)
        inc hl
        cp $ff
        jr z,sf_no
        ld b,a
        ld a,(hl)
        inc hl
        cp e
        jr nz,sf_n
        ld a,(hl)
        cp d
        jr nz,sf_n
        ld a,b
        or a
        pop bc
        ret
sf_n:   inc hl
        jr sf_l
sf_no:  xor a
        pop bc
        ret
; ---- SPLIT: first word -> (HL), last word -> (BC); input at DE
SPLIT:  push hl
        push de
        push bc
        push af
        ld ($c70e),hl
        ld (hl),0
        ld ($c710),bc
        xor a
        ld (bc),a
sp_s:   ld a,(de)
        inc de
        cp $20
        jr z,sp_s
        dec de
sp_w1:  ld a,(de)
        inc de
        or a
        jr z,sp_d
        cp $20
        jr z,sp_w2
        ld (hl),a
        inc hl
        ld (hl),0
        jr sp_w1
sp_w2:  ld a,(de)
        inc de
        or a
        jr z,sp_d
        cp $20
        jr z,sp_w2
        ld hl,($c710)
sp_c:   ld (hl),a
        inc hl
        ld (hl),0
        ld a,(de)
        inc de
        or a
        jr z,sp_d
        cp $20
        jr z,sp_w2
        jr sp_c
sp_d:   pop af
        pop bc
        pop de
        pop hl
        ret
; ---- UPC: input filter. A=char; C<-converted, carry set if control (<$20)
UPC:    cp $20
        ret c
        call UPA
        ld c,a
        or a
        ret
UPA:    cp $61
        jr c,ua_h
        cp $7b
        jr nc,ua_h
        sub $20
        ret
ua_h:   push hl
        push bc
        ld hl,ACCT
        ld b,a
ua_l:   ld a,(hl)
        inc hl
        or a
        jr z,ua_e
        cp b
        ld a,(hl)
        inc hl
        jr nz,ua_l
        ld b,a
ua_e:   ld a,b
        pop bc
        pop hl
        ret
GETUP:  call GETK
        jp UPA
; ---- ladder fix (original self-modified ROM at 4e61)
LADCHK: ld a,(hl)
        push hl
        ld hl,LADF
        add a,(hl)
        pop hl
        cp b
        ret
LADUP:  ld a,$ff
        ld (LADF),a
        jp $4e51
; ---- drawer-unlock fix (original self-modified ROM at 505b)
DRWX:   call $506d
        or a
        ret z
        ld a,(DRWF)
        or a
        jr z,dx1
        ld c,e
dx1:    ld a,1
        or a
        ret
; ---- FONTA: A=char -> HL=glyph address (custom glyphs 83..86)
FONTA:  cp $83
        jr c,fa_n
        cp $87
        jr nc,fa_n
        sub $83
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,CFONT
        add hl,de
        ret
fa_n:   ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,($f920)
        add hl,de
        ret
'''
code,LAB=assemble(CODE,CODE_ADDR,LAB)
assert len(code)<=CODE_MAX, len(code)
W(CODE_ADDR,code)
def A(src,org): return assemble(src,org,LAB)[0]
# ---------- hooks ----------
W(0x4c07,bytes([LAB['DICT']&255,LAB['DICT']>>8]))          # ld hl,DICT
W(0x4c41,A('jp SENTF',0x4c41))
W(0x4cf6,bytes([LAB['MSGS']&255,LAB['MSGS']>>8]))          # ld hl,MSGS
W(0x4c6a,A('''push af
 push de
 call PRINTS
 ld h,d
 ld l,e
 pop de
 pop af
 ret''',0x4c6a))
W(0x4c86,A('jp INLINE',0x4c86))
W(0x4bc8,A('jp SPLIT',0x4bc8))
W(0x4b97,A('call UPC\n jr c,$4b70',0x4b97))
W(0x5c4d,A('call GETUP\n nop\n cp $53',0x5c4d))
W(0x5843,A('call FONTA\n'+'nop\n'*8,0x5843))
# --- bug fixes for ROM-conversion self-modifying code
assert R(0x4e60,3)==bytes([0x7e,0x3d,0xb8])
W(0x4e60,A('call LADCHK',0x4e60))
sys1c=A('''ld a,1
 ld (LADF),a
 call $4e51
 push af
 ld a,$ff
 ld (LADF),a
 pop af
 ret''',0x4e6d); assert len(sys1c)<=19; W(0x4e6d,sys1c+b'\x00'*(19-len(sys1c)))
W(0x54f5+2*0x1b,bytes([LAB['LADUP']&255,LAB['LADUP']>>8]))
assert R(0x5053,9)==bytes([0x32,0x5b,0x50,0xcd,0x6d,0x50,0xb7,0xc8,0x49])
W(0x5053,A('ld (DRWF),a\n call DRWX\n ret z\n nop\n nop',0x5053))
# status template (100 chars, in place)
st=raw(STATUS); assert len(st)==100; W(0x5d06,st); assert R(0x5d6a,1)==b'\x00'
# short string pointers
def setde(ins,key):
    assert rom[ins-B]==0x11; a=SHORTADR[key]; W(ins+1,bytes([a&255,a>>8]))
setde(0x5933,'RED'); setde(0x5938,'GREEN'); setde(0x593d,'YELLOW')
setde(0x5966,'B2'); setde(0x596b,'F1'); setde(0x5970,'B1')
setde(0x598a,'O'); setde(0x5996,'N'); setde(0x599b,'E'); setde(0x59a0,'S')
# inline stubs
for adr,txt in INLINE.items():
    o=adr-B
    if ORIG[o:o+4]==b'\xcd\x00\x43\x13': s=o+4
    elif ORIG[o:o+3]==b'\xcd\x86\x4c': s=o+3
    else: raise ValueError(hex(adr))
    e=ORIG.index(b'\x00',s); after=e+1+B
    L=after-adr; assert L>=5,(hex(adr),L)
    stub=None
    body=comp(raw(txt))
    size=3+len(body)+1+1
    sa=alloc(size,'stub %x'%adr)
    W(sa,A('call $4c86',sa)+body+b'\x00\xc9')
    patch=A('call %d\n jr %d'%(sa,after),adr)
    W(adr,patch+b'\x00'*(L-len(patch)))
open(sys.argv[2],'wb').write(rom)
if True:
    print('pairs',len(PAIRS),'msgs',len(msgs),'dict',len(dic),'sent',len(sent),'code',len(code))
    for r in REGIONS: print('free %04x-%04x %d'%(r[0],r[1],r[1]-r[0]))
