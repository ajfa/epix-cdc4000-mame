#!/usr/bin/env python3
"""Rebuild the Rx2030 IOP (NEC V50) firmware image from the four PROMs.

MAME's ROM_START(i2000) loads them into a 0x40000 little-endian region:
    u139 -> 0x00000 skip 1   (even bytes of the low half)
    u140 -> 0x00001 skip 1   (odd  bytes of the low half)
    u141 -> 0x20001 skip 1   (odd  bytes of the high half)
    u142 -> 0x20000 skip 1   (even bytes of the high half)

iop_program_map puts that region at 0x80000-0xbffff with a 0x40000 mirror, so
the V50 reset vector at physical 0xffff0 is ROM offset 0x3fff0.
"""
import os

R = "<path>/epix/roms/rs2030"
OUT = "<path>/epix/boot/iop.bin"

def rd(name):
    return open(os.path.join(R, name), "rb").read()

lo_e, lo_o = rd("50-00121__005.u139"), rd("50-00120__005.u140")
hi_o, hi_e = rd("50-00119__005.u141"), rd("50-00118__005.u142")

rom = bytearray(0x40000)
for i in range(0x10000):
    rom[0x00000 + i * 2] = lo_e[i]
    rom[0x00001 + i * 2] = lo_o[i]
    rom[0x20000 + i * 2] = hi_e[i]
    rom[0x20001 + i * 2] = hi_o[i]

open(OUT, "wb").write(rom)
print(f"wrote {OUT} ({len(rom)} bytes)")
print("reset vector area (rom 0x3fff0):", rom[0x3fff0:0x3fff0+8].hex(" "))
