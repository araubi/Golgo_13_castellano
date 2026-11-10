import sys
import os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from cpu import CPU,CF,ZF
class NeedInput(Exception): pass
class Reset(Exception): pass
class MSX:
    def __init__(s,rom,font=None):
        s.low=bytearray(0x4000); s.low[6]=0x98; s.low[7]=0x98
        if font is None:
            from font import make; font=make()
        if font: s.low[0x1bbf:0x1bbf+2048]=font
        s.rom=bytearray(rom)+bytearray(0x8000-len(rom)) if len(rom)<0x8000 else bytearray(rom[:0x8000])
        s.ram=bytearray(0x4000)
        s.vram=bytearray(0x4000); s.vaddr=0; s.vlatch=None; s.vregs=[0]*8
        s.keys=[]; s.log=[]
        s.cpu=CPU(None,s)
        s.ram[0xf920-0xc000]=0xbf; s.ram[0xf921-0xc000]=0x1b
        s.cpu.sp=0xf380; s.cpu.pc=0x4010
        s.beeps=0
        s.tout=[]; s.pages=0; s.pagewait=0x57d4; s.charout=0x57a3
        s.skips={0x56d1:'ret',0x5b55:0x5b5e}
    def rd(s,a):
        if a<0x4000: return s.low[a]
        if a<0xc000: return s.rom[a-0x4000]
        return s.ram[a-0xc000]
    def wr(s,a,v):
        if a>=0xc000: s.ram[a-0xc000]=v
        else: s.log.append(('romwrite',hex(a),v,hex(s.cpu.pc)))
    def out(s,p,v):
        if p==0x98: s.vram[s.vaddr]=v; s.vaddr=(s.vaddr+1)&0x3fff
        elif p==0x99:
            if s.vlatch is None: s.vlatch=v
            else:
                if v&0x80: s.vregs[v&7]=s.vlatch
                else: s.vaddr=((v&0x3f)<<8)|s.vlatch
                s.vlatch=None
    def inp(s,p): return 0xff
    def bios(s,a):
        c=s.cpu
        if a==0x9f:
            if c.rw(c.sp+8)==s.pagewait:
                s.pages+=1; c.a=32; c.pc=c.pop(); s.tout.append(0x7c); return
            if not s.keys: raise NeedInput()
            c.a=s.keys.pop(0)
        elif a==0x9c:
            c.f = (c.f&~ZF) if s.keys else (c.f|ZF)
        elif a==0x53: s.vaddr=c.ghl()&0x3fff
        elif a==0x56:
            for i in range(c.gbc()): s.vram[(c.ghl()+i)&0x3fff]=c.a
        elif a==0x5c:
            for i in range(c.gbc()): s.vram[(c.gde()+i)&0x3fff]=s.rd((c.ghl()+i)&0xffff)
        elif a==0x47: s.vregs[c.c&7]=c.b
        elif a==0x4a: c.a=s.vram[c.ghl()&0x3fff]
        elif a==0x4d: s.vram[c.ghl()&0x3fff]=c.a
        elif a==0x138: c.a=0x50
        elif a==0x72:
            for i in range(768): s.vram[0x1800+i]=i&255
            for i in range(0x1800): s.vram[i]=0
            col=(s.ram[0xf3e9-0xc000]<<4)|s.ram[0xf3ea-0xc000]
            for i in range(0x1800): s.vram[0x2000+i]=col
        elif a==0xc0: s.beeps+=1
        elif a in (0xe1,0xe4,0xea,0xed): c.f|=CF
        elif a==0x0000: raise Reset()
        # others: no-op
        c.pc=c.pop()
    def run(s,maxsteps=50_000_000):
        c=s.cpu; n=0
        while n<maxsteps:
            if c.pc<0x4000:
                try: s.bios(c.pc)
                except NeedInput:
                    return 'input'
                except Reset:
                    return 'reset'
                continue
            if c.pc==s.charout: s.tout.append(c.a)
            sk=s.skips.get(c.pc)
            if sk is not None:
                if sk=='ret': c.pc=c.pop(); c.a=0
                else: c.pc=sk
                continue
            c.step(); n+=1
        return 'timeout'
    def text(s):
        b=s.ram[0xed00-0xc000:0xed00-0xc000+25*11]
        rows=[]
        for r in range(11):
            w=25 if r<4 else 12
            rows.append(bytes(b[r*25:r*25+w]))
        return rows
    def type(s,txt,cr=True):
        from msx import enc
        s.keys+=list(enc(txt))+([13] if cr else [])
