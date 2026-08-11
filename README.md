# epix-cdc4000-mame

Three fixes to [MAME](https://github.com/mamedev/mame) that make **EP/IX 2.1.1** —
Control Data's UNIX for the CDC 4000 series — install and boot on the emulated
MIPS RS2030, plus the reverse-engineering tools used to find them.

EP/IX is an extension of MIPS RISC/os. Its `pkginfo` lists `rc2030`/`rs2030` as a
first-class target, which is exactly the machine MAME emulates in
`src/mame/mips/mips_i2000.cpp` with no `MACHINE_NOT_WORKING` flag. It still would
not boot: the install media's device probe hit three separate emulation bugs.

```
epix Console login: root

****************************************************
*        CONTROL DATA PROPRIETARY PRODUCT          *
*     Copyright Control Data Systems, Inc.         *
*            1990, 1991, 1992, 1993                *
****************************************************
(C) Copyright 1986-1992, MIPS Computer Systems

epix, EP/IX Version 2.1.1

epix # uname -a
epix epix 2.1.1 RISCos mips
epix # df
Filesystem        Type   kbytes     use    avail %use  Mounted on
/dev/root          ffs    19770   10270     9500  52%  /
/dev/usr           ffs   850894  365655   485239  43%  /usr
```

## Applying

The patches are against **MAME 0.288** and apply from the source root:

```bash
git clone --depth 1 --branch mame0288 https://github.com/mamedev/mame.git
cd mame
for p in ../epix-cdc4000-mame/patches/*.diff; do patch -p1 < "$p"; done
make SOURCES=src/mame/mips/mips_i2000.cpp SUBTARGET=mips2030 TOOLS=1 NOWERROR=1 -j"$(nproc)"
```

`patches/` are the fixes; `patched/` has the complete resulting files if you
prefer to drop them in.

## The bugs

### 1. The AIC-6250 DMA byte counter is 24 bits, MAME treats it as 32

`patches/01-aic6250-24bit-dma-count.diff`

The datasheet is explicit — *"24-Bit DMA Byte Counter"*, *"The 24-bit counter
allows data transfers up to 16 Mbytes without a DMA wrap"* (registers 00-02).
MAME keeps it in a `u32 m_dma_count` that

* is never initialised (it only ever appears in a `save_item`), and
* is loaded a byte at a time with masks that clear only their own byte:
  `m_dma_count &= ~0x0000ff`, so **bits 24-31 are never touched**.

The top byte therefore keeps whatever was in the freshly allocated device
object. On the Rx2030 this made the IOP's power-up diagnostic fail about half
the time — the intermittency is the giveaway, since it tracks heap contents:

```
SCSI Test...: SCSI Power Up Failure: dma count 0 bit invalid
```

with a trace showing a 6-byte SCSI command loaded as

```
[:aic6250] dma_cntrl_w 0x03
[:aic6250] dma transfer from memory, count 1392508934      <- 0x53000006
```

The low 24 bits are the correct 6. Because the count never reaches zero,
*DMA BYTE COUNT ZERO* (status register 0, bit 0) never comes on and the transfer
never completes.

**This one is not EP/IX-specific**: it affects every machine driving an
AIC-6250 — MIPS Rx2030, Data General AViiON, Microbotics HardFrame, pc532.

*Verification*: 8 consecutive `rc2030` boots produced byte-identical console
snapshots, all with `SCSI Test...Passed`; before the fix roughly half failed.
RISC/os 4.52 still boots to its login prompt, so no regression.

### 2. Datasheet transfer conditions for DMA in/out

`patches/02-aic6250-init-and-transfer-conditions.diff`

Initialises the counter, and implements what the datasheet requires before the
chip moves a byte as initiator: *the SCSI phase matches the expected phase, REQ
is asserted, the transfer byte count is not zero, and the FIFO is not full (in)
/ not empty (out)*. It also stops the memory prefetch once the FIFO holds the
rest of the transfer, per *"the AIC-6250 will stop the memory prefetch when the
number of bytes in the FIFO, plus the number of bytes already transferred on the
SCSI bus, sums to the total transfer length"*.

MAME checked only the FIFO condition; its own source said so:

```c
// FIXME: assert ack when: req asserted && phase match && count not zero && fifo not empty
```

This closes that FIXME. On its own it changes no observed behaviour, but it
removes latent protocol violations (ACK before REQ, leftover prefetched bytes
from a previous transfer).

### 3. `nscsi_hd` does not implement MODE SENSE page 0x38

`patches/03-nscsi-hd-mode-sense-page-38.diff`

**This is the one that actually blocked the boot.** EP/IX's device probe issues

```
CDB 1a 00 38 00 1c 00     MODE SENSE(6), page 0x38, allocation length 28
```

Page 0x38 is the cache control page of the Common Command Set, which drives of
the era implemented. `src/devices/bus/nscsi/hd.cpp` knows pages 00, 01, 02, 03,
04, 08 and 30, so 0x38 falls through to `default: fail = true` and the disk
answers CHECK CONDITION. The Rx2030 IOP firmware then stops servicing that
unit's IOCBs altogether and EP/IX retries the request forever:

```
iocb SCSI0 command 0x0200      <- the request
iocb UART0 command 0x0003      <- "SCSI 0L0: POLLED timeout" printed
...repeat...
```

The 28-byte allocation length says exactly what the driver expects back: 4 bytes
of header + 8 of block descriptor + 16 of page, i.e. a page 0x38 whose
page-length byte is 14. Seven lines, and EP/IX boots.

## How the bugs were found

Both sides were disassembled, because the failure sits between them.

**The kernel.** `unix.i2000_std` is MIPSEB ECOFF and *not stripped* — 5296
external symbols. `tools/ecoff.py` parses the symbolic header (HDRR, magic
0x7009) and disassembles with capstone. That located the IOP ABI from the
kernel's own code: `iopb` is a table of 24 sixteen-byte entries with the command
parameter at +0, the result at +4, the command semaphore at +8, the **response
semaphore at +0xa** (what `iop_wait` polls) and the buffer pointer at +0xc. The
address that showed up in every stuck log, `0x8017070c`, turned out to be
`iop_poke+0x180` — the `sb $t7, 3($t9)` that rings the IOP doorbell, proving the
kernel's side was fine.

**The IOP.** `tools/mkiop.py` rebuilds the 256 KB NEC V50 firmware from the four
PROMs with the interleave `ROM_START(i2000)` uses; `tools/iopdis.py` disassembles
it as 16-bit x86. Searching for the AIC-6250 port addresses found the register
primitives (`aic_read` at 0xf7623, `aic_write` at 0xf7637) and, from there, the
polled transfer loop that waits on status register 1 bit 3 (Command Done). It
also settled who was complaining: the kernel's string is `POLLED time out`, the
firmware's is `POLLED timeout` — the one on screen was the firmware's.

**The instrumentation.** Tracing the AIC-6250 at register level produces
hundreds of MB (a line per byte and per REQ/ACK transition) and slows the machine
so much it never reaches the failure. What worked was logging the IOCB parameter
blocks in the driver, then only the SCSI bus phase, and finally only the bytes
sent in COMMAND phase — a handful of lines per command, which is how the
offending CDB surfaced. Those instrumentation patches are in
`tools/instrumentation/` (they contain absolute paths; treat them as a record of
method rather than something to run as-is).

## Tools

| file | what it does |
|---|---|
| `ecoff.py` | MIPS ECOFF symbol table + disassembler (`syms`, `which`, `xrefs`, `dis`) |
| `mkiop.py`, `iopdis.py`, `iopcalls.py`, `iopref.py` | rebuild and disassemble the NEC V50 IOP firmware |
| `ffs.py` | read-only reader for big-endian 4.2BSD FFS (`ls`, `tree`, `cat`, `get`, `extract`) |
| `vh.py`, `chdinfo.py`, `fsfree.py` | SGI volume header, CHD header, FFS free space |
| `mktarget.py` | write a volume header and drop a miniroot into the swap partition |
| `cdbstats.py` | summarise SCSI opcodes from a MAME log |

`ecoff.py` and `iopdis.py` need `pip install capstone`.

## What is not here

No ROMs, no disk images and no EP/IX media. EP/IX is proprietary software of
Control Data Systems; this repository contains only emulator fixes and analysis
tools.

`docs/FINDINGS.md` is the full working diary, including the install procedure and
the dead ends. `docs/NOTES.md` has the exact installer answers.

## License

The tooling and documentation in this repository are under the **GNU General
Public License v3.0**, see [LICENSE](LICENSE).

**`patches/` and `patched/` are different**: they are modifications to MAME and
remain under MAME's own license, **BSD-3-Clause**, because that is what MAME
requires of contributions. See [NOTICE.md](NOTICE.md).

Contributions require the agreement in [CLA.md](CLA.md); see
[CONTRIBUTING.md](CONTRIBUTING.md).
