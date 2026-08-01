#!/usr/bin/env python3
"""Read-only reader for the big-endian 4.2BSD FFS in the EP/IX image.

Usage:  ffs.py ls <path>
        ffs.py tree <path> [depth]
        ffs.py cat <path> [maxbytes]
        ffs.py extract <path> <destdir>
"""
import os, struct, sys, stat

IMG = os.environ.get("EPIX_IMG", "<path>/epix/cdc_epix_2.1.1.iso")
PART_OFF = int(os.environ.get("EPIX_OFF", 9880 * 512))   # default: part2 = /usr/netinstall
SB_OFF = 8192


class FFS:
    def __init__(self, path, base):
        self.f = open(path, "rb")
        self.base = base
        sb = self._raw(base + SB_OFF, 2048)
        u = lambda o: struct.unpack(">i", sb[o:o+4])[0]
        assert struct.unpack(">I", sb[1372:1376])[0] == 0x011954, "bad FFS magic"
        self.iblkno, self.cgoffset, self.cgmask = u(16), u(24), u(28)
        self.ncg, self.bsize, self.fsize, self.frag = u(44), u(48), u(52), u(56)
        self.inopb, self.ipg, self.fpg = u(120), u(184), u(188)
        self.fsmnt = sb[212:212+512].split(b"\0")[0].decode("latin1")
        self.nindir = u(116)

    def _raw(self, off, n):
        self.f.seek(off)
        return self.f.read(n)

    def frag_read(self, fragno, n):
        return self._raw(self.base + fragno * self.fsize, n)

    def cgstart(self, c):
        return self.fpg * c + self.cgoffset * (c & ~self.cgmask)

    def inode(self, ino):
        cg, off = divmod(ino, self.ipg)
        imin = self.cgstart(cg) + self.iblkno
        frag = imin + (off // self.inopb) * self.frag
        d = self.frag_read(frag, self.bsize)
        i = (off % self.inopb) * 128
        raw = d[i:i+128]
        mode, nlink = struct.unpack(">Hh", raw[0:4])
        size = struct.unpack(">Q", raw[8:16])[0]
        mtime = struct.unpack(">i", raw[24:28])[0]
        db = struct.unpack(">12i", raw[40:88])
        ib = struct.unpack(">3i", raw[88:100])
        uid, gid = struct.unpack(">HH", raw[4:8])
        return dict(mode=mode, nlink=nlink, size=size, mtime=mtime,
                    db=db, ib=ib, uid=uid, gid=gid)

    def _indirect(self, frag, level, want, out):
        if frag == 0 or len(out) >= want:
            return
        blk = self.frag_read(frag, self.bsize)
        ptrs = struct.unpack(">%di" % (self.bsize // 4), blk)
        for p in ptrs:
            if len(out) >= want:
                return
            if level == 1:
                out.append(p)
            else:
                self._indirect(p, level - 1, want, out)

    def blocks(self, ino):
        nblk = (ino["size"] + self.bsize - 1) // self.bsize
        out = [b for b in ino["db"][:min(12, nblk)]]
        if nblk > 12:
            for lvl, frag in enumerate(ino["ib"], start=1):
                self._indirect(frag, lvl, nblk, out)
                if len(out) >= nblk:
                    break
        return out[:nblk]

    def read(self, ino, limit=None):
        size = ino["size"] if limit is None else min(ino["size"], limit)
        data = bytearray()
        for b in self.blocks(ino):
            if len(data) >= size:
                break
            data += self.frag_read(b, self.bsize) if b else bytes(self.bsize)
        return bytes(data[:size])

    def readdir(self, ino):
        data = self.read(ino)
        ents, off = [], 0
        while off + 8 <= len(data):
            eino, reclen, namlen = struct.unpack(">IHH", data[off:off+8])
            if reclen < 8 or off + reclen > len(data):
                break
            if eino:
                name = data[off+8:off+8+namlen].split(b"\0")[0].decode("latin1")
                ents.append((name, eino))
            off += reclen
        return ents

    def lookup(self, path):
        ino_n, ino = 2, self.inode(2)
        for part in [p for p in path.strip("/").split("/") if p]:
            if not stat.S_ISDIR(ino["mode"]):
                raise SystemExit(f"not a directory: {part}")
            hit = dict(self.readdir(ino)).get(part)
            if hit is None:
                raise SystemExit(f"not found: {path} (at {part!r})")
            ino_n, ino = hit, self.inode(hit)
        return ino_n, ino


def fmt(name, ino, fs):
    m = ino["mode"]
    kind = ("d" if stat.S_ISDIR(m) else "l" if stat.S_ISLNK(m) else
            "b" if stat.S_ISBLK(m) else "c" if stat.S_ISCHR(m) else "-")
    perm = "".join(("r" if m & (0o400 >> i*3) else "-") +
                   ("w" if m & (0o200 >> i*3) else "-") +
                   ("x" if m & (0o100 >> i*3) else "-") for i in range(3))
    extra = ""
    if stat.S_ISLNK(m):
        extra = " -> " + fs.read(ino).decode("latin1", "replace")
    return f"{kind}{perm} {ino['uid']:>4}/{ino['gid']:<4} {ino['size']:>10}  {name}{extra}"


def main():
    fs = FFS(IMG, PART_OFF)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ls"
    path = sys.argv[2] if len(sys.argv) > 2 else "/"

    if cmd == "ls":
        n, ino = fs.lookup(path)
        print(f"# {fs.fsmnt}{path}  (inode {n})")
        if stat.S_ISDIR(ino["mode"]):
            for name, en in sorted(fs.readdir(ino)):
                if name in (".", ".."):
                    continue
                print(fmt(name, fs.inode(en), fs))
        else:
            print(fmt(path, ino, fs))

    elif cmd == "tree":
        depth = int(sys.argv[3]) if len(sys.argv) > 3 else 2
        def walk(p, ino, d, pre=""):
            if d < 0:
                return
            for name, en in sorted(fs.readdir(ino)):
                if name in (".", ".."):
                    continue
                e = fs.inode(en)
                isdir = stat.S_ISDIR(e["mode"])
                print(f"{pre}{name}{'/' if isdir else ''}"
                      + ("" if isdir else f"  ({e['size']})"))
                if isdir and d > 0:
                    walk(p + "/" + name, e, d - 1, pre + "  ")
        n, ino = fs.lookup(path)
        walk(path, ino, depth)

    elif cmd == "cat":
        lim = int(sys.argv[3]) if len(sys.argv) > 3 else 8192
        n, ino = fs.lookup(path)
        sys.stdout.write(fs.read(ino, lim).decode("latin1", "replace"))

    elif cmd == "get":
        n, ino = fs.lookup(path)
        out = sys.argv[3]
        with open(out, "wb") as fh:
            fh.write(fs.read(ino))
        print(f"wrote {ino['size']} bytes to {out}")

    elif cmd == "extract":
        dest = sys.argv[3]
        def rec(p, ino, out):
            os.makedirs(out, exist_ok=True)
            for name, en in fs.readdir(ino):
                if name in (".", ".."):
                    continue
                e = fs.inode(en)
                if stat.S_ISDIR(e["mode"]):
                    rec(p + "/" + name, e, os.path.join(out, name))
                elif stat.S_ISREG(e["mode"]):
                    with open(os.path.join(out, name), "wb") as fh:
                        fh.write(fs.read(e))
        n, ino = fs.lookup(path)
        rec(path, ino, dest)
        print("extracted to", dest)


main()
