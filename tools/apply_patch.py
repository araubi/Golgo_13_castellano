#!/usr/bin/env python3
"""Aplica golgo13_es.ips a tu propia ROM japonesa de Golgo 13 - Okami no Su,
comprobando las sumas antes y despues.

Uso:  python3 apply_patch.py golgo13_jp.rom golgo13_es.ips golgo13_es.rom
"""
import hashlib
import sys

SHA1_JP = "031a611ba1f75b7d5fe3ed088a61c24598b4b314"
SHA1_ES = "71bf403b9d2afeb303281da045ec375d0791b3f2"


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    rom = bytearray(open(sys.argv[1], "rb").read())
    h = hashlib.sha1(rom).hexdigest()
    if h != SHA1_JP:
        sys.exit("ROM desconocida (SHA-1 " + h + "). Se necesita la ROM japonesa de 32 KB con SHA-1 " + SHA1_JP + ".")
    ips = open(sys.argv[2], "rb").read()
    if ips[:5] != b"PATCH":
        sys.exit("El fichero de parche no es un IPS valido.")
    i = 5
    while ips[i:i + 3] != b"EOF":
        a = int.from_bytes(ips[i:i + 3], "big")
        n = int.from_bytes(ips[i + 3:i + 5], "big")
        rom[a:a + n] = ips[i + 5:i + 5 + n]
        i += 5 + n
    if hashlib.sha1(rom).hexdigest() != SHA1_ES:
        sys.exit("El resultado no coincide con la traduccion esperada.")
    open(sys.argv[3], "wb").write(rom)
    print("OK: " + sys.argv[3] + " (Golgo 13 en castellano v1.0)")


if __name__ == "__main__":
    main()
