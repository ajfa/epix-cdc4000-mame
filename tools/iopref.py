#!/usr/bin/env python3
"""Find code in the IOP ROM that references a given string.

Real-mode x86 loads a string by its offset within some data segment, so try
every plausible segment base: for each, compute what the 16-bit offset of the
string would be and search the ROM for that little-endian immediate.
"""
import os
import struct
import sys

ROM = os.environ.get("EPIX_IOP", "boot/iop.bin")
# the ROM answers at 0x80000-0xbffff and again at 0xc0000-0xfffff
BASES = (0x80000, 0xc0000)

d = open(ROM, "rb").read()
needle = sys.argv[1].encode() if len(sys.argv) > 1 else b"POLLED timeout"
str_off = d.find(needle)
if str_off < 0:
    sys.exit(f"string not found: {needle!r}")
print(f"string {needle!r} at rom 0x{str_off:05x}")

for base in BASES:
    phys = base + str_off
    print(f"\n# with the rom at 0x{base:05x}, the string is at physical 0x{phys:05x}")
    for seg in range(0, 0x10000, 0x10):
        off = phys - (seg << 4)
        if not (0 <= off <= 0xffff):
            continue
        imm = struct.pack("<H", off)
        hits = []
        start = 0
        while True:
            i = d.find(imm, start)
            if i < 0:
                break
            hits.append(i)
            start = i + 1
            if len(hits) > 4:
                break
        if hits and len(hits) <= 4:
            print(f"  seg 0x{seg:04x} off 0x{off:04x}: rom " +
                  " ".join(f"0x{h:05x}" for h in hits))
