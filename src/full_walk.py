import sys, json
import os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from walk2 import *
REC=[]
def D(g,c):
    o=do(g,c,quiet=True); REC.append(('t',c,clean(o)))
    if 'Arma=' in o: REC.append(('k','3',''))
def G(g,cell,label,face=None):
    f=pos(g)[0]
    if face is None: face=doordir(bytes(g.m.ram[(f-1)*256:f*256]),cell)
    seq=go(g,cell,face); REC.append(('m',''.join(seq),label))
def T(g,label,cmds):
    REC.append(('h',label,''))
    for c in cmds: D(g,c)
g=Game(sys.argv[1] if len(sys.argv)>1 else 'golgo13_es.rom')
REC.append(('h','P.B',''))
G(g,0x2c,'Sala 2'); T(g,'Sala 2: llave 1',['abrir puerta','registrar estanteria','coger llave','salir'])
G(g,0x4c,'Sala 3'); T(g,'Sala 3: interruptor de la escalera',['usar llave','abrir puerta','mirar mesa','abrir cajon','apagar interruptor','salir'])
G(g,0xde,'Sala 4'); T(g,'Sala 4: llave 2',['abrir puerta','mirar mesa','abrir cajon','coger llave','salir'])
G(g,0xe6,'Sala 5'); T(g,'Sala 5: escalera',['abrir puerta','bajar','salir'])
G(g,0x10,'Sala 7'); T(g,'Sala 7: llave 3',['abrir puerta','registrar estanteria','coger llave','salir'])
G(g,0xef,'Sala 8'); T(g,'Sala 8: Último Batallón',['abrir puerta','salir'])
G(g,0x0e,'Sala 9'); T(g,'Sala 9: escalera',['usar llave','abrir puerta','bajar','salir'])
G(g,0x3a,'Erik'); T(g,'Erik',['usar llave','abrir puerta','disparar','preguntar','mirar mesa','abrir cajon','apagar interruptor','salir'])
G(g,0xb1,'Kestner'); T(g,'Kestner',['abrir puerta','disparar','preguntar','registrar cadaver','coger llave','mirar mesa','usar llave','abrir cajon','apagar interruptor','salir'])
G(g,0xe4,'Documentos'); T(g,'Documentos',['abrir puerta','mirar estanteria','leer documentos','mirar mesa','abrir cajon','apagar interruptor','salir'])
G(g,0xea,'Wessel'); T(g,'Wessel',['abrir puerta','disparar','preguntar','registrar cadaver','coger llave','mirar mesa','usar llave','abrir cajon','apagar interruptor','salir'])
G(g,0x3e,'Bormann'); T(g,'Bormann',['abrir puerta','disparar','preguntar','salir'])
G(g,0x3a,'Erik (huida)'); T(g,'Erik huida',['usar llave','abrir puerta','mirar mesa','abrir cajon','apagar interruptor','salir'])
G(g,0xe4,'Documentos (huida)'); T(g,'Doc huida',['abrir puerta','mirar mesa','abrir cajon','apagar interruptor','salir'])
G(g,0xea,'Wessel (huida)'); T(g,'Wessel huida',['abrir puerta','mirar mesa','usar llave','abrir cajon','apagar interruptor','salir'])
G(g,0x1b,'Sala 10'); T(g,'Sala 10: subir',['usar llave','abrir puerta','subir','salir'])
G(g,0xf1,'Sala 6'); T(g,'Sala 6: subir',['abrir puerta','subir','salir'])
G(g,0xd9,'Salida',face=2); T(g,'Salida',['abrir puerta'])
print('FINAL dmg %04x turn %d'%(dmg(g),tm(g,1)))
json.dump(REC,open('walk_rec.json','w'),ensure_ascii=False,indent=0)
shot(g,'final.png')
