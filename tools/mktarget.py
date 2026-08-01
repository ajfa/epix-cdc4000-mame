#!/usr/bin/env python3
"""Prepare the EP/IX target disk.

The release notes' procedure is:
    >> boot -f dksd(,2,8)sash
    sash: cp -b 16k dksd(,2,2)epix2.1.1/1/miniroot dksd(,,1)
    sash: boot -f dksd(,2,2)epix2.1.1/1/unix.<mach> root=sdc0d0s1

which needs the target disk to already carry an SGI volume header (so that
partition 1 = swap exists).  A blank disk has none, so we write one here,
copied from the known-good RISC/os disk (identical geometry: 1731/15/80), with
the volume directory cleared -- inst will populate it with sash.2030 later.

We also drop the miniroot straight into the swap partition, which is exactly
what the sash 'cp' step above would do.
"""
import struct, sys

RISCOS = "/tmp/riscos.raw"
MINIROOT = "<path>/epix/boot/miniroot"
OUT = "/tmp/epix-target.raw"
SIZE = 1731 * 15 * 80 * 512          # 1,063,526,400 -- matches the blank CHD


def csum(block):
    """SGI volume header checksum: the 128 big-endian words must sum to 0."""
    total = 0
    for i in range(0, 512, 4):
        total = (total + struct.unpack(">i", block[i:i+4])[0]) & 0xFFFFFFFF
    return total


vh = bytearray(open(RISCOS, "rb").read(512))
assert struct.unpack(">I", vh[0:4])[0] == 0x0BE5A941, "source is not a volume header"
before = csum(vh)
print(f"checksum of the RISC/os volume header: 0x{before:08x} "
      f"({'ok' if before == 0 else 'UNEXPECTED'})")

# partition table stays; wipe the volume directory (points at RISC/os' sash)
vh[0x48:0x138] = bytes(0xF0)

# recompute vh_csum at 0x1f8 so the total is zero again
vh[0x1F8:0x1FC] = b"\0\0\0\0"
fix = (-csum(vh)) & 0xFFFFFFFF
vh[0x1F8:0x1FC] = struct.pack(">I", fix)
assert csum(vh) == 0, "checksum fixup failed"
print(f"new vh_csum = 0x{fix:08x}, verified")

parts = {}
for i in range(16):
    nblks, first, ptype = struct.unpack(">iii", vh[0x138+i*12:0x138+i*12+12])
    if nblks:
        parts[i] = (first, nblks, ptype)
        print(f"  part{i:<2} first={first:<9} nblks={nblks:<9} type={ptype}")

swap_first, swap_blks, _ = parts[1]
mini = open(MINIROOT, "rb").read()
print(f"\nminiroot: {len(mini)} bytes ({len(mini)//512} blocks) -> "
      f"swap partition 1 at block {swap_first} ({swap_blks} blocks)")
assert len(mini) <= swap_blks * 512, "miniroot does not fit in swap"

with open(OUT, "wb") as f:
    f.truncate(SIZE)
    f.seek(0)
    f.write(vh)
    f.seek(swap_first * 512)
    f.write(mini)
print(f"wrote {OUT}")
