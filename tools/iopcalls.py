#!/usr/bin/env python3
"""Find near-calls to a physical address in the IOP ROM.

A near call (0xe8 rel16) stays inside its segment, so the target's physical
address is caller_phys + 3 + rel16 as long as both live in the same segment --
good enough to map out who drives the AIC-6250 register helpers.
"""
import os
import struct
import sys

ROM = os.environ.get("EPIX_IOP", "boot/iop.bin")
BASE = 0xc0000

d = open(ROM, "rb").read()
targets = [int(a, 16) for a in sys.argv[1:]] or [0xf7623, 0xf7637]

for t in targets:
    hits = []
    for i in range(len(d) - 3):
        if d[i] != 0xE8:
            continue
        rel, = struct.unpack("<h", d[i+1:i+3])
        if BASE + i + 3 + rel == t:
            hits.append(BASE + i)
    print(f"# llamadas a 0x{t:05x}: {len(hits)}")
    print("   " + " ".join(f"0x{h:05x}" for h in hits))
