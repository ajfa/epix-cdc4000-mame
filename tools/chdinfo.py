#!/usr/bin/env python3
"""Minimal CHD v5 header/metadata dumper (no chdman needed)."""
import struct, sys

for path in sys.argv[1:]:
    f = open(path, "rb")
    hdr = f.read(124)
    if hdr[:8] != b"MComprHD":
        print(f"{path}: not a CHD"); continue
    hlen, ver = struct.unpack(">II", hdr[8:16])
    print(f"=== {path}\n  version={ver} headerlen={hlen}")
    if ver != 5:
        print("  (only v5 parsed here)"); continue
    comp = struct.unpack(">4I", hdr[16:32])
    logical, mapoff, metaoff = struct.unpack(">QQQ", hdr[32:56])
    hunkbytes, unitbytes = struct.unpack(">II", hdr[56:64])
    tag = lambda c: "".join(chr((c >> s) & 0xFF) for s in (24, 16, 8, 0)) if c else "none"
    print(f"  logical={logical} ({logical/1048576:.1f} MB) hunkbytes={hunkbytes} "
          f"unitbytes={unitbytes}")
    print(f"  compressors={[tag(c) for c in comp]}")
    off = metaoff
    while off:
        f.seek(off)
        m = f.read(16)
        if len(m) < 16:
            break
        mtag = m[0:4].decode("latin1")
        flags = m[4]
        length = int.from_bytes(m[5:8], "big")
        nxt = struct.unpack(">Q", m[8:16])[0]
        data = f.read(length)
        txt = data.split(b"\0")[0].decode("latin1", "replace")
        print(f"  meta {mtag} len={length}: {txt}")
        off = nxt
