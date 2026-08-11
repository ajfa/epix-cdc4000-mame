# Project notes: EP/IX 2.1.1 on MAME

A summary of what it took to get here, in case any of it has to be redone or
debugged.

## The media

The distribution image `cdc_epix_2.1.1.iso` is **not an ISO9660**: it is a disk
image with an SGI/MIPS volume header (magic `0x0BE5A941`). Partition 2 (block
9880, 568 MB) is a big-endian FFS mounted as `/usr/netinstall`, holding the
complete distribution: kernels for the whole CDC 4000 range (`unix.i2000_std`
for the RC2030/RS2030, `unix.r3030_std`, `unix.r6000_std`…), `sash.2030`, a
19.9 MB `miniroot`, a C compiler, and BSD 4.3 and SVR4 utilities.

Its `pkginfo` declares `subpackage=rc2030/rs2030` as a first-class target,
which is exactly the machine MAME emulates without "not working" flags.

## Booting and installing

The recipe from EP/IX's own release notes, adapted to this unit:

```
>> boot -f dksd(,1,8)sash2
sash: cp -b 16k dksd(,1,2)epix2.1.1/1/miniroot dksd(,,1)
sash: boot -f dksd(,1,2)epix2.1.1/1/unix.i2000_std root=sdc0d0s1
# From=cd
# CDpath=sdc0d1s2
# Product=epix2.1.1
# inst
```

Installer answers, in order: `<CR>` (package root), `y` (information correct),
`y` (install all subpackages), `y` (time zone), `y` (clock), `y` (sash into the
volume header), `6` (`/usr` partition), **`y` (initialize filesystems)**, and
`<CR>` for the rest.

⚠ After choosing the `/usr` partition the question is **not** the swap one that
the release-notes transcript shows — that transcript is from an *update*
install — but `Initialize filesystems (y n) [y]?`. Answering `n` there makes
the mount fail and `inst` aborts.

Extracting the ~30 subpackages takes about five hours of wall clock: it runs at
roughly 0.78x real time, far below the ~250% of the lighter phases.

## After installing

`comply` warns that `/unix` is missing: the kernel does not copy itself. It can
be fixed from inside the running system, without repeating the install:

```
epix # mount -r /dev/dsk/sdc0d1s2 /mnt
epix # cp /mnt/epix2.1.1/1/unix.i2000_std /unix.i2000_std
epix # ln /unix.i2000_std /unix
epix # umount /mnt ; sync
```

And for a boot without the NFS noise (`mountd: couldn't register MOUNTPROG`):

```
epix # cp /etc/inittab /etc/inittab.orig
epix # sed s\|respawn:/usr/etc/rpc.mountd\|off:/usr/etc/rpc.mountd\| /etc/inittab.orig > /etc/inittab
epix # init q
```

(the `sed` uses a backslash-escaped `|` as its delimiter so that no quotes are
needed — quotes are awkward to type through the emulated keyboard).

## rc2030 versus rs2030

Both boot. `rs2030` is the comfortable one: the kernel console comes out on the
graphics screen and the AT keyboard works. On `rc2030` the kernel console and
the keyboard end up on different serial ports (MAME binds the natural keyboard
to `:tty0:terminal:keyboard` while the kernel prints on the other), so you
cannot type at the shell without fighting it.

## Tools included (`tools/`)

- `mkdisks.sh`, `mktarget.py` — create the CHDs and prepare the target disk
  (volume header + miniroot in the swap partition).
- `ffs.py` — read-only reader for big-endian 4.2BSD FFS: `ls`, `tree`, `cat`,
  `get`, `extract`. Useful for looking inside the images without mounting them.
- `vh.py`, `chdinfo.py`, `fsfree.py` — SGI volume header, CHD header and
  filesystem free space.
- `ecoff.py` — MIPS ECOFF symbol table parser plus disassembler (needs
  `pip3 install capstone`). This is what located `iop_poke` and the kernel's
  IOCB ABI.
- `mkiop.py`, `iopdis.py`, `iopcalls.py` — rebuild the IOP (NEC V50) ROM from
  the four PROMs and disassemble it; this is how it was found that the firmware
  services requests using the AIC-6250's Auto PIO mode.
- `patch-*.py` — the MAME patches, including the instrumentation ones used for
  debugging (IOCB dumps, SCSI bus phase traces, CDBs).

## Paths

The tools take their inputs from environment variables with relative defaults,
so nothing is tied to one machine:

| Variable | Default | What it points at |
|---|---|---|
| `EPIX_IMG` | `cdc_epix_2.1.1.iso` | the distribution image |
| `EPIX_KERNEL` | `boot/unix.i2000_std` | the extracted kernel |
| `EPIX_IOP` | `boot/iop.bin` | the rebuilt IOP ROM |
| `EPIX_ROMS` | `roms/rs2030` | the PROM dumps |
| `EPIX_MINIROOT` | `boot/miniroot` | the extracted miniroot |
| `EPIX_LOG` | `rig/error.log` | the MAME log to analyse |
| `MAME_SRC` | `mame` | a MAME source tree, for the patch scripts |
