#!/usr/bin/env python3
"""Report free space of the FFS filesystems on the installed target disk."""
import struct

IMG = "/tmp/target.raw"
PARTS = {"/ (part0)": 2400, "/usr (part6)": 48000}

f = open(IMG, "rb")
for name, first in PARTS.items():
    base = first * 512
    f.seek(base + 8192)
    sb = f.read(2048)
    magic, = struct.unpack(">I", sb[1372:1376])
    if magic != 0x011954:
        print(f"{name}: sin superbloque FFS")
        continue
    u = lambda o: struct.unpack(">i", sb[o:o+4])[0]
    size, ncg, bsize, fsize, frag = u(36), u(44), u(48), u(52), u(56)
    # fs_cstotal at 192: ndir, nbfree, nifree, nffree
    ndir, nbfree, nifree, nffree = struct.unpack(">4i", sb[192:208])
    total_b = size * fsize
    free_b = nbfree * bsize + nffree * fsize
    print(f"{name}:")
    print(f"   tamano   {total_b/1048576:8.1f} MB")
    print(f"   libre    {free_b/1048576:8.1f} MB  ({100*free_b/total_b:.1f} %)")
    print(f"   inodos libres {nifree}, directorios {ndir}")
