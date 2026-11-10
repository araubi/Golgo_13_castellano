from PIL import Image,ImageDraw,ImageFont
# MSX international charset 0x80-0xFF approx (CP437-like)
hi=('ÇüéâäàåçêëèïîìÄÅ'
    'ÉæÆôöòûùÿÖÜ¢£¥₧ƒ'
    'áíóúñÑªº¿⌐¬½¼¡«»'
    'ÃãĨĩÕõŨũĲĳ¾∽◊‰¶§'
    '▂▚▆▔◾▇▎▞▊▕▉▨▧▼▲▶'
    '◀⧗⧓▘▗▝▖▒Δǂω█▄▌▐▀'
    'αβΓπΣσμτΦΘΩδ∞φ∈∩'
    '≡±≥≤⌠⌡÷≈°∙·√ⁿ²■ ')
def make():
    f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',8)
    out=bytearray(2048)
    for c in range(32,256):
        ch=chr(c) if c<128 else hi[c-128]
        if c==127: continue
        im=Image.new('1',(8,8),0); dr=ImageDraw.Draw(im)
        dr.text((1,-1),ch,font=f,fill=1)
        for y in range(8):
            v=0
            for x in range(8):
                if im.getpixel((x,y)): v|=0x80>>x
            out[c*8+y]=v
    return bytes(out)
PAL=[(0,0,0),(0,0,0),(33,200,66),(94,220,120),(84,85,237),(125,118,252),(212,82,77),(66,235,245),(252,85,84),(255,121,120),(212,193,84),(230,206,128),(33,176,59),(201,91,186),(204,204,204),(255,255,255)]
def render(vram,path,scale=3):
    im=Image.new('RGB',(256,192))
    px=im.load()
    for row in range(24):
        for col in range(32):
            n=vram[0x1800+row*32+col]; bank=row//8
            for y in range(8):
                p=vram[bank*0x800+n*8+y]; cl=vram[0x2000+bank*0x800+n*8+y]
                fg,bg=PAL[cl>>4],PAL[cl&15]
                for x in range(8):
                    px[col*8+x,row*8+y]=fg if p&(0x80>>x) else bg
    im.resize((256*scale,192*scale),Image.NEAREST).save(path)
