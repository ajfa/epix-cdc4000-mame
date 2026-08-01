#!/usr/bin/env python3
"""Disassemble the Rx2030 IOP (NEC V50 = 8086/V30) firmware.

  iopdis.py <rom_offset_hex> [count] [phys_base_hex]

The ROM image answers at physical 0x80000 and again at 0xc0000; addresses are
printed as physical so they can be matched against segment:offset pairs.
"""
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

ROM = "<path>/epix/boot/iop.bin"

d = open(ROM, "rb").read()
off = int(sys.argv[1], 16)
count = int(sys.argv[2]) if len(sys.argv) > 2 else 40
base = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0xc0000

md = Cs(CS_ARCH_X86, CS_MODE_16)
n = 0
for ins in md.disasm(d[off:off + count * 8], base + off):
    print(f"  {ins.address:05x}  {ins.bytes.hex():<14} {ins.mnemonic:<7} {ins.op_str}")
    n += 1
    if n >= count:
        break
