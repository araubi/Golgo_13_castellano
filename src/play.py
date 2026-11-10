import sys, os
_H=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,os.path.join(_H,'emu')); sys.path.insert(0,_H)
from msxemu import MSX
from msx import dec
ES=True
ESMAP={0xA0:'á',0x82:'é',0xA1:'í',0xA2:'ó',0xA3:'ú',0xA4:'ñ',0xA5:'Ñ',0xA8:'¿',0xAD:'¡',0xAE:'«',0xAF:'»',0x81:'ü',0x90:'É',0x83:'Á',0x84:'Í',0x85:'Ó',0x86:'Ú'}
def tr(bs):
    o=''
    for b in bs:
        if b==13: o+='\n'
        elif b==0x7c: o+=' ⏎PAGE⏎ '
        elif b==12: o+='\n[CLS]\n'
        elif b==8: o=o[:-1]
        elif b<32: o+='{%02X}'%b
        elif ES and b>=0x80: o+=ESMAP.get(b,'{%02X}'%b)
        else: o+=dec(bytes([b]))
    return o
class Game:
    def __init__(s,rom,fast=True):
        s.m=MSX(open(rom,'rb').read()); s.m.keys=[32]; s.r=s.m.run(); s.m.tout=[]
    def cmd(s,c,raw=False):
        if raw: s.m.keys+=list(c)
        else: s.m.keys+=list(c.encode('latin1'))+[13]
        s.r=s.m.run(); o=tr(s.m.tout); s.m.tout=[]; return o
if __name__=='__main__':
    g=Game(sys.argv[1])
    for c in sys.argv[2:]:
        print(g.cmd(c).strip('\n')); 
    print('['+g.r+']')
def screen(g):
    rows=[]
    for r in g.m.text(): rows.append('|'+''.join(ESMAP.get(b,chr(b) if 32<=b<127 else '·') for b in r)+'|')
    return '\n'.join(rows)
def shot(g,path):
    from font import render
    render(g.m.vram,path)
