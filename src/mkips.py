def ips(orig,new):
    out=bytearray(b'PATCH'); i=0; n=len(new)
    while i<n:
        if i<len(orig) and orig[i]==new[i]: i+=1; continue
        j=i
        while j<n and (j>=len(orig) or orig[j]!=new[j] or (j+1<n and j+1<len(orig) and orig[j+1]!=new[j+1])) and j-i<0xffff: j+=1
        out+=i.to_bytes(3,'big')+(j-i).to_bytes(2,'big')+new[i:j]; i=j
    out+=b'EOF'; return bytes(out)
def apply(orig,p):
    r=bytearray(orig); k=5
    while p[k:k+3]!=b'EOF':
        o=int.from_bytes(p[k:k+3],'big'); l=int.from_bytes(p[k+3:k+5],'big'); k+=5
        r[o:o+l]=p[k:k+l]; k+=l
    return bytes(r)
if __name__=='__main__':
    import sys
    a=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read()
    p=ips(a,b); open(sys.argv[3],'wb').write(p)
    assert apply(a,p)==b; print('ips',len(p))
