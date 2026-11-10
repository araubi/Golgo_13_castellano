import re
from z80 import dis
# Build template table by enumerating opcodes
T={}
def add(prefix,extra_len_guess):
    pass
def build():
    seqs=[]
    for a in range(256):
        if a in (0xcb,0xed,0xdd,0xfd): continue
        seqs.append(bytes([a]))
    for a in range(256): seqs.append(bytes([0xcb,a])); seqs.append(bytes([0xed,a]))
    for p in (0xdd,0xfd):
        for a in range(256):
            if a in (0xcb,0xed,0xdd,0xfd): continue
            seqs.append(bytes([p,a]))
        for a in range(256): seqs.append(bytes([p,0xcb,0x05,a]))
    for s in seqs:
        m=bytearray(s)+bytes([0x34,0x12,0x00,0x00])
        if s[0] in (0xdd,0xfd) and len(s)==2:
            # might have displacement: try with d=0x05 then n
            m=bytearray(s)+bytes([0x05,0x34,0x12,0])
        t,l=dis(bytes(m),0x8000,0x8000)
        if t.startswith('db'): continue
        # template
        if t.split()[0] in('jr','djnz'):
            t2=re.sub(r'[0-9a-f]{4}$','REL',t)
            T.setdefault(t2,(bytes(m[:l-1]),'rel'))
            continue
        kind=None; t2=t
        if '1234' in t: t2=t.replace('1234','NN'); kind='nn'
        elif re.search(r'\b34\b',t): t2=re.sub(r'\b34\b','N',t); kind='n'
        if '+5)' in t2: t2=t2.replace('+5)','+D)'); kind=(kind or '')+'d'
        if l==len(s) and kind is None: T.setdefault(t2,(bytes(m[:l]),None))
        else: T.setdefault(t2,(bytes(m[:l]),kind,len(s)))
build()
def assemble(src,org,labels=None):
    labels=dict(labels or {})
    lines=[]
    for raw in src.split('\n'):
        ln=raw.split(';')[0].strip()
        if not ln: continue
        lines.append(ln)
    for pas in (0,1):
        pc=org; out=bytearray()
        for ln in lines:
            m=re.match(r'^(\w+):\s*(.*)$',ln)
            if m:
                labels[m.group(1)]=pc; labels[m.group(1).lower()]=pc; ln=m.group(2).strip()
                if not ln: continue
            if ln.startswith('db '):
                for it in split_args(ln[3:]):
                    if it.startswith('"'):
                        b=it[1:-1].encode('latin1'); out+=b; pc+=len(b)
                    else: out.append(ev(it,labels,pas)&255); pc+=1
                continue
            if ln.startswith('dw '):
                for it in split_args(ln[3:]):
                    v=ev(it,labels,pas); out+=bytes([v&255,(v>>8)&255]); pc+=2
                continue
            b=enc(ln,pc,labels,pas); out+=b; pc+=len(b)
    return bytes(out),labels
def split_args(s):
    res=[];cur='';q=False
    for c in s:
        if c=='"': q=not q
        if c==',' and not q: res.append(cur.strip()); cur=''
        else: cur+=c
    if cur.strip(): res.append(cur.strip())
    return res
def ev(x,labels,pas):
    x=x.strip()
    L={k.lower():v for k,v in labels.items()}
    try: return int(eval(re.sub(r'\$([0-9a-fA-F]+)',r'0x\1',x.lower()),{},L))
    except Exception:
        if pas==0: return 0
        raise ValueError('bad expr '+x)
def enc(ln,pc,labels,pas):
    ln=re.sub(r'\s+',' ',ln.lower()).replace(', ',',')
    op=ln.split(' ',1); mn=op[0]; args=op[1] if len(op)>1 else ''
    # relative
    if mn in('jr','djnz'):
        parts=args.split(',')
        tgt=parts[-1]; pre=','.join(parts[:-1])
        key=mn+' '+(pre+',' if pre else '')+'REL'
        b,_=T[key]; v=ev(tgt,labels,pas); e=v-(pc+len(b)+1)
        if pas and not -128<=e<=127: raise ValueError('jr range '+ln)
        return b+bytes([e&255])
    # try exact
    key=(mn+' '+args).strip()
    if key in T and T[key][1] is None: return T[key][0]
    # try with operand forms: find (expr) or expr in args
    cands=[]
    m=re.match(r'^(.*?)\((ix|iy)([+-][^)]*)\)(.*)$',args)
    if m:
        d=ev(m.group(3),labels,pas)
        rest=m.group(4)
        for k2,kind in ((rest,'d'),):
            pass
        a2=m.group(1)+'('+m.group(2)+'+D)'+m.group(4)
        # with possible immediate
        for form,needn in ((a2,False),):
            k=(mn+' '+form)
            if k in T: 
                b=T[k][0]; bb=bytearray(b)
                if bb[1]==0xcb: bb[2]=d&255
                else: bb[2]=d&255
                return bytes(bb)
        # ld (ix+d),n
        mm=re.match(r'^\((ix|iy)\+D\),(.+)$',a2)
        if mm:
            k=mn+' ('+mm.group(1)+'+D),N'
            b=bytearray(T[k][0]); b[2]=d&255; b[3]=ev(mm.group(2),labels,pas)&255; return bytes(b)
        raise ValueError('cant '+ln)
    # replace one numeric/label operand
    toks=re.split(r'([,()])',args)
    regs={'a','b','c','d','e','h','l','af','bc','de','hl','sp','ix','iy','i','r','nz','z','nc','po','pe','p','m',"af'",'ixh','ixl','iyh','iyl','(c)'}
    for i,t in enumerate(toks):
        if t in ('',',','(',')') or t in regs: continue
        if mn in ('bit','res','set','im','rst') and i==0: continue
        v=ev(t,labels,pas)
        for form,size in (('NN',2),('N',1)):
            k=mn+' '+''.join(toks[:i]+[form]+toks[i+1:])
            if k in T:
                b=bytearray(T[k][0])
                if size==2: b[-2]=v&255; b[-1]=(v>>8)&255
                else: b[-1]=v&255
                return bytes(b)
    if mn=='rst':
        return bytes([0xc7+int(args,16)])
    raise ValueError('cant assemble: '+ln)
