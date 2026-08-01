#!/usr/bin/env python3
"""Read the MIPS ECOFF symbol table of EP/IX's kernel and disassemble it.

  ecoff.py syms [regex]        list external symbols matching regex
  ecoff.py dis <symbol> [n]    disassemble n instructions from a symbol
  ecoff.py disat <hex> [n]     disassemble from a virtual address

The kernel (unix.i2000_std) is not stripped, so the external symbol table gives
us names and addresses for every driver entry point.
"""
import re
import struct
import sys

FILE = "<path>/epix/boot/unix.i2000_std"


class Ecoff:
    def __init__(self, path):
        self.d = open(path, "rb").read()
        magic, nscns, timdat, symptr, nsyms, opthdr, flags = struct.unpack(
            ">HHIIIHH", self.d[0:20])
        assert magic == 0x0160, f"not MIPSEB ECOFF (magic 0x{magic:04x})"
        self.sections = []
        off = 20 + opthdr
        for i in range(nscns):
            s = self.d[off:off+40]
            name = s[0:8].split(b"\0")[0].decode("latin1")
            paddr, vaddr, size, scnptr = struct.unpack(">IIII", s[8:24])
            self.sections.append(dict(name=name, vaddr=vaddr, size=size, scnptr=scnptr))
            off += 40

        # symbolic header
        h = self.d[symptr:symptr+96]
        hmagic, = struct.unpack(">H", h[0:2])
        assert hmagic == 0x7009, f"bad symbolic header magic 0x{hmagic:04x}"
        (self.issExtMax, self.cbSsExtOffset) = struct.unpack(">iI", h[64:72])
        (self.iextMax, self.cbExtOffset) = struct.unpack(">iI", h[88:96])

    def externals(self):
        """Yield (name, value, storage_class) for each external symbol."""
        out = []
        for i in range(self.iextMax):
            e = self.cbExtOffset + i * 16
            ifd, = struct.unpack(">h", self.d[e+2:e+4])
            iss, value, bits = struct.unpack(">iII", self.d[e+4:e+16])
            st = (bits >> 26) & 0x3f
            sc = (bits >> 21) & 0x1f
            if 0 <= iss < self.issExtMax:
                s = self.cbSsExtOffset + iss
                end = self.d.index(b"\0", s)
                name = self.d[s:end].decode("latin1")
            else:
                name = f"<iss {iss}>"
            out.append((name, value, st, sc))
        return out

    def read_at(self, vaddr, n):
        for s in self.sections:
            if s["vaddr"] <= vaddr < s["vaddr"] + s["size"] and s["scnptr"]:
                o = s["scnptr"] + (vaddr - s["vaddr"])
                return self.d[o:o+n]
        return b""


def disasm(e, vaddr, count, symmap=None):
    from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_BIG_ENDIAN
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_BIG_ENDIAN)
    code = e.read_at(vaddr, count * 4)
    if not code:
        print(f"(no section covers 0x{vaddr:08x})")
        return
    for ins in md.disasm(code, vaddr):
        tag = ""
        if symmap:
            m = re.search(r"0x([0-9a-f]+)", ins.op_str)
            if m:
                tag = symmap.get(int(m.group(1), 16), "")
                tag = f"   <{tag}>" if tag else ""
        print(f"  {ins.address:08x}  {ins.mnemonic:<9} {ins.op_str}{tag}")


def main():
    e = Ecoff(FILE)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "syms"
    ext = e.externals()
    byname = {n: v for n, v, st, sc in ext}
    byaddr = {v: n for n, v, st, sc in ext}

    if cmd == "sections":
        for s in e.sections:
            print(f"  {s['name']:<10} vaddr=0x{s['vaddr']:08x} size={s['size']:<9} "
                  f"fileoff={s['scnptr']}")

    elif cmd == "syms":
        pat = re.compile(sys.argv[2] if len(sys.argv) > 2 else ".", re.I)
        hits = [(n, v) for n, v, st, sc in ext if pat.search(n)]
        print(f"# {len(hits)} de {len(ext)} simbolos externos")
        for n, v in sorted(hits, key=lambda x: x[1]):
            print(f"  0x{v:08x}  {n}")

    elif cmd == "xrefs":
        # find every "jal <target>" in .text
        target = byname.get(sys.argv[2]) if sys.argv[2] in byname else int(sys.argv[2], 16)
        text = next(s for s in e.sections if s["name"] == ".text")
        want = 0x0C000000 | ((target >> 2) & 0x03FFFFFF)
        code = e.d[text["scnptr"]:text["scnptr"] + text["size"]]
        code_syms = sorted((v, n) for n, v, st, sc in ext
                           if text["vaddr"] <= v < text["vaddr"] + text["size"])
        print(f"# llamadas a 0x{target:08x}")
        for i in range(0, len(code) - 3, 4):
            word, = struct.unpack(">I", code[i:i+4])
            if word == want:
                a = text["vaddr"] + i
                fn = ""
                for v, n in code_syms:
                    if v <= a:
                        fn = f"{n}+0x{a - v:x}"
                    else:
                        break
                print(f"  0x{a:08x}  {fn}")

    elif cmd == "which":
        # which function contains this address?
        a = int(sys.argv[2], 16)
        code = sorted((v, n) for n, v, st, sc in ext if 0x80050000 <= v < 0x801d7b70)
        prev = None
        for v, n in code:
            if v > a:
                break
            prev = (v, n)
        nxt = next(((v, n) for v, n in code if v > a), None)
        if prev:
            print(f"  0x{a:08x} esta en {prev[1]} (+0x{a - prev[0]:x}, empieza en 0x{prev[0]:08x})")
        if nxt:
            print(f"  siguiente simbolo: 0x{nxt[0]:08x} {nxt[1]}")

    elif cmd == "dis":
        name = sys.argv[2]
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 40
        if name not in byname:
            sys.exit(f"no such symbol: {name}")
        print(f"=== {name} @ 0x{byname[name]:08x}")
        disasm(e, byname[name], n, byaddr)

    elif cmd == "disat":
        a = int(sys.argv[2], 16)
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 40
        print(f"=== 0x{a:08x}")
        disasm(e, a, n, byaddr)


main()
