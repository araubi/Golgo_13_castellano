import os
# ROM original japonesa: variable de entorno G13_ORIG
d=open(os.environ.get('G13_ORIG','golgo13_jp.rom'),'rb').read()
BASE=0x4000
kata='。「」、・ヲァィゥェォャュョッーアイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン゛゜'
def ch(b):
    if 0x20<=b<0x7f: return chr(b)
    if 0xa1<=b<=0xdf: return kata[b-0xa1]
    return '{%02X}'%b
def dec(bs): 
    s=''.join(ch(b) for b in bs)
    # merge dakuten
    out=''
    import unicodedata
    for c in s:
        if c=='゛' and out: 
            n=unicodedata.normalize('NFC',out[-1]+'゙'); out=out[:-1]+n if len(n)==1 else out+c
        elif c=='゜' and out:
            n=unicodedata.normalize('NFC',out[-1]+'゚'); out=out[:-1]+n if len(n)==1 else out+c
        else: out+=c
    return out
def hx(a,n=256):
    o=a-BASE
    for i in range(o,o+n,16):
        print('%04x '%(i+BASE)+d[i:i+16].hex(' ')+'  '+''.join(chr(b) if 32<=b<127 else '.' for b in d[i:i+16]))
import unicodedata
def enc(s):
    out=bytearray()
    for c in s:
        if c in kata: out.append(0xa1+kata.index(c)); continue
        dcmp=unicodedata.normalize('NFD',c)
        if len(dcmp)==2 and dcmp[0] in kata:
            out.append(0xa1+kata.index(dcmp[0])); out.append(0xde if dcmp[1]=='゙' else 0xdf); continue
        out+=c.encode('latin1')
    return bytes(out)
