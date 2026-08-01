#!/usr/bin/env python3
import struct, sys

F = "<path>/epix/cdc_epix_2.1.1.iso"
d = open(F, "rb").read(4096)

magic, rootpt, swappt = struct.unpack(">Ihh", d[0:8])
bootfile = d[8:24].split(b"\0")[0].decode("latin1")
print(f"magic=0x{magic:08x} rootpt={rootpt} swappt={swappt} bootfile={bootfile!r}")

print("\n=== volume directory (offset 0x48) ===")
off = 0x48
for i in range(15):
    name = d[off:off+8].split(b"\0")[0].decode("latin1").strip()
    lbn, nbytes = struct.unpack(">ii", d[off+8:off+16])
    if name:
        print(f"  {name:<10} lbn={lbn:<10} ({lbn*512:>12} bytes off)  size={nbytes:>10}")
    off += 16

print("\n=== partition table (offset 0x138) ===")
PT = {0:"volhdr",1:"trkrepl",2:"secrepl",3:"raw/swap",4:"bsd4.2",5:"sysv",
      6:"volume(entire)",7:"efs",8:"lvol",9:"rlvol",10:"xfs",11:"xfslog",12:"xlv"}
off = 0x138
for i in range(16):
    nblks, first, ptype = struct.unpack(">iii", d[off:off+12])
    if nblks:
        print(f"  part{i:<2} first={first:<10} nblks={nblks:<10} "
              f"({nblks*512/1048576:8.1f} MB)  type={ptype} ({PT.get(ptype,'?')})")
    off += 12
