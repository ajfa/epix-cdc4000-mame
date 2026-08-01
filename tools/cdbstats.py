#!/usr/bin/env python3
"""Summarise the SCSI command opcodes seen in the MAME log."""
from collections import Counter

NAMES = {"00": "TEST UNIT READY", "03": "REQUEST SENSE", "04": "FORMAT UNIT",
         "08": "READ(6)", "0a": "WRITE(6)", "12": "INQUIRY", "15": "MODE SELECT(6)",
         "1a": "MODE SENSE(6)", "1b": "START/STOP UNIT", "25": "READ CAPACITY",
         "28": "READ(10)", "2a": "WRITE(10)", "37": "READ DEFECT DATA"}

lines = open("<path>/epix/rig/error.log", errors="replace").read().splitlines()
ops, cur = [], []
for l in lines:
    if "CDB " in l:
        cur.append(l.split("CDB ")[1].strip())
        if len(cur) == 6:
            ops.append(cur[0])
            cur = []
    else:
        cur = []

print(f"comandos completos: {len(ops)}")
for op, n in Counter(ops).most_common(12):
    print(f"  {op}  x{n:<6} {NAMES.get(op, '?')}")
