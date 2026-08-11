# EP/IX 2.1.1 — analysis of the distribution media (2026-07-30)

Distribution contents:

| File | Size | What it is |
|---|---|---|
| `cdc_epix_2.1.1.iso` | 601,677,824 | **NOT an ISO9660** — a disk image with an SGI/MIPS volume header |
| `CDC EP _ IX (Enhanced Performance UNIX) - National Library. N.E.Bauman.pdf` | 359,330 | documentation |
| `Cray-Cyber - Control Data 4680 (majestix).pdf` | 121,716 | copy of the majestix page |

## 1. Image structure

SGI volume header (magic `0x0BE5A941`), `rootpt=0 swappt=1 bootfile='/unix'`.

Volume header directory (standalone programs, all **MIPSEB ECOFF**):

| Name | lbn | size | notes |
|---|---|---|---|
| sash | 960 | 189,680 | MIPS 5.05B, references to `r4030_asc_dma`, `R4000` |
| sash3 | 1331 | 271,776 | **`$Revision: EP/IX 1.4.3 $` + `CONTROL DATA PROPRIETARY PRODUCT`**, "Jaguar", Interphase 4210 |
| sash2 | 1862 | 132,896 | v4.32, **"V50 PROM version number"** → Rx2030 class |
| sash7 | 3406 | 284,592 | Jaguar / Interphase 4210 |
| format, format2/3/7, spanic3/7 | — | — | standalone utilities |

Partition table (16 entries, type 4 = bsd4.2):

- part0 blk 2880, 41.2 MB — root
- part1 blk 1095360, 38.4 MB — swap
- **part2 blk 9880, 568.5 MB — real big-endian FFS, `fs_fsmnt = /usr/netinstall`**
- part8 volhdr, part10 = the whole volume (573.3 MB)

## 2. Contents of `/usr/netinstall` (read with `ffs.py`, read-only)

```
epix2.1.1/       (1/, 2/, 3/, pkginfo, tape0..tape3)
utilities2.1.1/  (1/, pkginfo, tape0, tape1)
```

`epix2.1.1/1/` holds the **kernels for the whole CDC 4000 range**:

| File | Machine |
|---|---|
| **`unix.i2000_std`** | **RC2030 / RS2030** ← MAME emulates this one as WORKING |
| `unix.r3030_std` | CD4320 / CD4330 (= MIPS RC3230) |
| `unix.r2400_std` | CD4340 |
| `unix.r3200_std`, `unix.r3200_ijc` | CD4360 / CD4380 (M/2000) |
| `unix.r6000_std`, `unix.r6000_mp` | **CD4660 / CD4680 (R6000) = majestix** |
| `unix.rb3125_std` | CD4360-200/300, CD4350-300 |
| `unix.r4370_std`, `unix.r4370_mp` | CD4370 |
| `unix.r4030eb_std`, `unix.r4030vb_std` | CD44x0 (Magnum/Millenium, R4000) |

plus `sash.2030` (which says literally **"Rx2030 FLOPPY"**), `sash.std`, `sash.4370`,
`sash.r4000`, **`miniroot`** (19.9 MB, big-endian FFS v1, clean, 29 Mar 1993) and
`instd` (POSIX tar).

Target kernel stamp:

```
@(#)EP/IX 2.1.1 (i2000_std) -- Mon Mar 29 10:17:06 CST 1993 -- eduarte
@(#)Standard Release Kernel for EP/IX 2.1.1 b1r7
Control Data EP/IX Version %s
*        CONTROL DATA PROPRIETARY PRODUCT        *
*      Copyright Control Data Systems, Inc.      *
```

Its machine-name table includes: `rc2030`, RC3230, RS3230, RC3240, RC3330, RC4030,
RC6280, CD4370, CD4480.

## 3. The finding that changes everything

`epix2.1.1/epix2.1.1/pkginfo` declares as a first-class subpackage:

```
subpackage=rc2030
subpackage=RC2030
subpackage=rs2030
subpackage=RS2030
        id="RC2030/RS2030 Kernel and Devices"
        splitboms="root.i2000 rc2030_dev sppbin_2030 sppbin_bfs usr.mips1"
        bom=r2030
```

→ **EP/IX 2.1.1 officially supports the RC2030/RS2030, which is exactly the machine
MAME emulates without a `NOT_WORKING` flag** (`src/mame/mips/mips_i2000.cpp:714-715`,
flags 0).

The rest of the media: `bsd43` (4.3BSD utilities), `svr4`, `cmplrs` (C compiler 3.11)
plus bsd43/svr4 variants, `man`, `pTHREADS`, `uucp`, release notes. It is the complete
distribution, not a patch.

## 4. What is missing to boot it in MAME

Romset `rs2030` / `rc2030` (they share `rom_i2000`):

- `50-00121__005.u139`, `50-00120__005.u140`, `50-00119__005.u141`,
  `50-00118__005.u142` (v4.32, 64 KB each) — or the `__003` v4.30 variant
- `ds1287.bin` (64 bytes) — an NVRAM image handcrafted by MAME so the monitor can be
  reached, CRC32 `28369bf3`
- The U139-U142 dumps exist publicly:
  `bitsavers.org/bits/MIPS/RISCos/geekdot_com/Rx2030_firmwares.zip` and in the Wayback
  copy of `yahozna.dyndns.org/scratch/mips/U139.HEX`..`U142.HEX`

## 5. Proposed boot plan

1. Known-good baseline: boot RISC/os 4.52
   (`MIPS-rc2030-RISCos-4.52-hdimage.zip`) under `mame rs2030` → validates ROMs, driver
   and SCSI geometry.
2. `chdman createhd` over `cdc_epix_2.1.1.iso` (512-byte sectors, no header) → attach as
   a second SCSI disk.
3. From the PROM monitor, boot the volume header standalone (`sash2`, the V50 one) or
   `sash.2030` from the netinstall tree.
4. Boot the `miniroot` and run the installer against `/usr/netinstall/epix2.1.1`,
   selecting the `rs2030` + `usr` + `bsd43` + `cmplrs` subpackages.
5. Install onto a blank CHD → a bootable EP/IX 2.1.1 system.

## 6. EXECUTION — results (2026-07-30, same session)

### Rig

- A slim MAME 0.288 binary with only the i2000 driver
  (`make SOURCES=src/mame/mips/mips_i2000.cpp SUBTARGET=mips2030 TOOLS=1 REGENIE=1
  NOWERROR=1 -j6`), plus `chdman`.
- ROMs: a complete `rs2030.zip` (including the 64-byte `ds1287.bin` that is not on
  bitsavers) plus `at_keybc.zip` and `kb_ms_natural.zip`. The eight PROM dumps
  downloaded from bitsavers (S-record, not Intel HEX) **match MAME's eight by CRC32**.
- Disks: `epix-dist.chd` (the EP/IX image, 1223/15/64), `epix-target.chd`
  (1731/15/80), `riscos-work.chd` (a copy — the original is never touched).

### Verified milestones

1. **The PROM boots**: `MIPS Monitor Version 4.32 ... 1990`, 16 MB, `>>` prompt.
   `printenv` → `bootfile=dksd(0,0,8)sash`, `bootmode=e`, `console=a`.
2. **RISC/os 4.52 boots to login** (`The system is ready.` / `exedra Console login:`)
   → the rig is validated end to end.
3. **EP/IX's `sash2` boots from the distribution's volume header**
   (`boot -f dksd(,1,8)sash2` → *Standalone Shell 4.32 ... Sat Feb 29 1992 marker*).
4. **★ THE EP/IX 2.1.1 KERNEL BOOTS**:

   ```
   CPU0: MIPS R2000A Processor Chip Revision: 1.0
   FPU0: MIPS R2010A VLSI Floating Point Chip Revision: 1.0
   Control Data EP/IX Version 2.1.1
   *  CONTROL DATA PROPRIETARY PRODUCT  *
   *  Copyright Control Data Systems, Inc. 1990, 1991, 1992, 1993
   Total real memory = 16777216
   start I/O probe
   ```

### The recipe (from EP/IX's own release notes, §4.4.6, adapted to the rs2030)

Original, for a 44x0 from a local CD-ROM:

```
>> boot -f dksd(,2,8)sash
sash: cp -b 16k dksd(,2,2)epix2.1.1/1/miniroot dksd(,,1)
sash: boot -f dksd(,2,2)epix2.1.1/1/unix.r4030eb_std root=sdc0d0s1
```

This version (distribution on SCSI 1, target on SCSI 0):

```
>> boot -f dksd(,1,8)sash2
sash: boot -f dksd(,1,2)epix2.1.1/1/unix.i2000_std root=sdc0d0s1
```

The `cp` of the miniroot into swap is done from outside with `mktarget.py`, which also
writes a valid volume header onto the target disk (copied from the RISC/os disk — same
geometry — with the volume directory cleared and the checksum recomputed; the algorithm
is "the sum of the 128 big-endian words of block 0 must be zero", verified against the
real disk).

### Diagnosing the hang (with `#define VERBOSE (LOG_IOCB)` in mips_i2000.cpp:127)

On the Rx2030 the kernel does not talk to SCSI directly: it leaves **IOCBs** (I/O
control blocks) in shared RAM and rings a doorbell at `0x02000000`; the V50 IOP — which
runs real PROM firmware — processes them. Counting IOCBs over a full boot:

| System | Total IOCBs | of which SCSI |
|---|---|---|
| RISC/os 4.52 (boots to login) | **21,725** | 20,726 |
| EP/IX 2.1.1 (hangs) | **28** | 4 |

And EP/IX's 28 are **all from the PROM/sash** (loading sash2 and the kernel): **the
EP/IX kernel emits not a single IOCB**. It hangs waiting (`SCSI 0L0: POLLED timeout`)
without ever having asked the IOP for anything.

The kernel's only anomalous access is a write to `0x01FF1000`, which MAME reports as
unmapped… and which is **commented out in the driver itself**:

```cpp
void mips_i2000_state::rs2030_map(address_map &map)
{
    map(0x01000000, 0x011fffff).ram().share("vram");
    map(0x01ffff00, 0x01ffffff).m(m_ramdac, FUNC(bt458_device::map)).umask32(0xff);

    //map(0x01ff1000, 0x01ff1001).w() // graphics register?
    //map(0x01ff0080, 0x01ff0081).w() // graphics register?
}
```

In other words: MAME's author saw those writes, could not identify the register and
left it unimplemented. EP/IX 2.1.1 (1993) uses it; RISC/os 4.52 (1991) does not.

### ★ rc2030 gets MUCH further

With the serial console and the kernel loaded from the distribution:

```
>> boot -f dksd(,1,8)sash2
108464+26084+257920 entry: 0xa0300000
MIPS Standalone Shell Version 4.32 MIPS OPT Sat Feb 29 16:58:16 PST 1992 marker
sash: boot -f dksd(,1,2)epix2.1.1/1/unix.i2000_std root=sdc0d0s1
1804464+222688+642304 entry: 0x80050010
```

and the kernel **does talk to the IOP: 2,432 IOCBs and climbing** (on the rs2030 it was
**0**). That is the proof that the rs2030's graphics path was what blocked the kernel.
It still crawls afterwards, so at least one more problem lies ahead.

Two rig details for rc2030: it needs its own `rc2030.zip` (a copy of `rs2030.zip`), and
input goes through the **serial terminal**, not the AT keyboard → `natkeyboard:post()`
works as is and **loses neither capitals nor parentheses** (`KBD=nat` in `type2.lua`). A
cold boot takes about 250 emulated seconds to reach `>>`.

### Earlier rc2030 test (server, no graphics)

`rc2030` needs its own `rc2030.zip` (a copy of `rs2030.zip`). It gives a serial console
with the IOP self-test (`SCSI Test...Passed`, `Kick Start the R2000`) and reaches **452
IOCBs** with a SCSI0..SCSI6 probe, but the R2000 monitor's output goes to **tty1**
(`m_tty[1]` → "terminal" in `rc2030()`), a second screen that the capture script does
not yet photograph. Outstanding: capture both screens so the R2000 monitor can be typed
at.

## 7. rc2030 session — exactly where it dies

With per-machine warm NVRAM (`rig/nvram-good-rc2030`, restored by `run.sh`) and the
two-step sequence, a good boot gets this far:

```
SCSI Test...Passed
Kick Start the R2000
MIPS Monitor Version 4.32 MIPS OPT Tue Nov 27 19:36:21 PST 1990 root
>> boot -f dksd(,1,8)sash2
108464+26084+257920 entry: 0xa0300000
MIPS Standalone Shell Version 4.32 MIPS OPT Sat Feb 29 16:58:16 PST 1992 marker
sash: boot -f dksd(,1,2)epix2.1.1/1/unix.i2000_std root=sdc0d0s1
1804464+222688+642304 entry: 0x80050010
```

and from there the kernel enters an **infinite retry loop**, visible in the IOCB log
(kernel PC `8017070C`):

```
iocb SCSI0 command 0x0200   ← SCSI operation on unit 0
iocb UART0 command 0x0003   ← prints the error on the console
...  (1215 UART0, 523 UART1, 499 SCSI1, 51 SCSI0)  ...
```

So: **it is not hung, it is failing**. Every SCSI operation the kernel issues fails,
prints `SCSI 0L0: POLLED timeout` and retries; the emulation's "crawl" is that torrent
of text.

### Why the kernel fails and the PROM does not

The PROM and `sash` **do** read from SCSI (they load a 1.8 MB kernel from unit 1 without
trouble): they do simple, polled I/O with no disconnection. The EP/IX kernel driver
(1993) uses the chip's full path. And `src/devices/machine/aic6250.cpp` says of itself:

```
 * Status: very WIP, enough to load RISC/os on MIPS Rx2030 driver, but many
 * unimplemented and incorrect behaviours.
 * TODO
 *   - fix problems with ATN
 *   - 16 bit DMA odd address start and HBV/LBV selection
 *   - disconnect/reselect          ← not implemented
 *   - phase checks
```

### Second symptom, same origin: the IOP self-test fails ~50 % of the time

```
SCSI Test...: SCSI Power Up Failure: dma count 0 bit invalid
...Failed, error= ffff
```

Register trace (with `#define VERBOSE (LOG_GENERAL|LOG_REG|LOG_STATE|LOG_SCSI)` in
aic6250.cpp): arbitration won → `selection: complete` → `phase COMMAND REQ` →
`scsi_signal_reg_w 0x80` (waits for the COMMAND phase) → **`dma_cntrl_w 0x03`** (starts
the DMA of the command bytes) → and the `R07R_DMA_BYTE_CNT_ZERO` bit (status_reg_0
bit 0, derived from `!m_dma_count`) does not settle the way the firmware expects → it
aborts and resets the chip. That it is **intermittent** points at a race in the DMA
state machine rather than fixed logic. Note: `m_offset_count_zero` (bit 0x20 of
fifo_status) is assigned `true` in two places and **never updated** — a stub, and a
possible further clue.

### Conclusion

The media and the operating system are fine; what is missing is **emulation**. The
blocker is MAME's AIC-6250 model, which is just enough for what RISC/os does and falls
short for EP/IX. Fixing it is MAME device work, using the datasheet
`bitsavers.org/pdf/adaptec/asic/AIC-6250_1988.pdf` (the one the file itself cites).

### Current blocker

After the banner, the I/O probe gives `SCSI 0L0: POLLED timeout` and the emulation
crawls (9:45 of real CPU for ~240 emulated seconds). Prime suspect: MAME's AIC6250 is
declared in its own header as *"very WIP, enough to load RISC/os on MIPS Rx2030 driver,
but many unimplemented and incorrect behaviours"*, with **disconnect/reselect
unimplemented** (`src/devices/machine/aic6250.cpp`). RISC/os 4.52 (a 1991 driver) does
not use it; EP/IX 2.1.1 (1993) probably does. To be confirmed with an instrumented run.

## 8. Datasheet session — A MAME BUG FOUND AND FIXED

Datasheet: `bitsavers.org/pdf/adaptec/asic/AIC-6250_1988.pdf` → `doc/aic6250.txt`
(extracted with `pdftotext -layout`).

### 8.1 The bug: the DMA byte counter is 24-bit, MAME treats it as 32

The datasheet is explicit: *"24-Bit DMA Byte Counter"*, *"The 24-bit counter allows data
transfers up to 16 Mbytes without a DMA wrap"* (registers 00-02). And about the status
bit: *"DMA BYTE COUNT ZERO: When this bit is found to be 1, the DMA Byte Count Registers
(Registers 00-02) are all zero"* (status register 0, bit 0).

In MAME, `m_dma_count` is a `u32` that:

- is **never initialised** (it only appears in `save_item`), and
- is loaded byte by byte with masks that clear only their own byte:
  `m_dma_count &= ~0x0000ff;` → **bits 24-31 are never touched**.

The result: the top 8 bits keep whatever was in the object's freshly allocated memory.
Trace of the failure (`log-cf1.log`), with a 6-byte SCSI command:

```
[:aic6250] dma_cntrl_w 0x03
[:aic6250] dma transfer from memory, count 1392508934      ← 0x53000006
```

`0x53000006`: the low 24 bits are 6 (correct), the `0x53` on top is garbage. Since the
counter never reaches zero, the DMA BYTE COUNT ZERO bit never comes on and the transfer
never completes → the Rx2030 IOP's power-on diagnostic aborts with
`SCSI Test...: SCSI Power Up Failure: dma count 0 bit invalid`. That the garbage varies
between runs is exactly what produced the **~50 % intermittency**.

**Fix** (`aic6250.h.diff` plus part of `aic6250.cpp.diff`): 24-bit masks in the three
setters, and `m_dma_count = 0` in `device_start()`.

**Verification**: eight consecutive `rc2030` boots, screenshots **byte-for-byte
identical** (md5 `71fad366835c463435e892eee633c4b9`), every one with `SCSI Test...Passed`
and a monitor prompt. Before: ~50 % failures. No regression: RISC/os 4.52 still boots to
`exedra Console login:`.

### 8.2 Second patch: the datasheet's transfer conditions

`DMA TRANSFER - ASYNCHRONOUS SCSI`, initiator: the chip asserts ACK when **the phase
matches the expected one, REQ is asserted, the counter is non-zero and the FIFO is not
full/empty**; further, *"the AIC-6250 will stop the memory prefetch when the number of
bytes in the FIFO, plus the number of bytes already transferred on the SCSI bus, sums to
the total transfer length"*.

MAME only checked the FIFO (its own `FIXME` said so) and prefetched until the FIFO was
full or fell below 8 bytes. Patched in `DMA_IN`/`DMA_OUT` and in `back_w`. It does not
change observed behaviour, but it removes latent protocol violations (ACK before REQ,
leftover bytes from an earlier prefetch) and it is what the datasheet says.

### 8.3 What still fails

With both patches the EP/IX kernel stays in its loop: `SCSI0 0x0200` → `UART0 0x0003`
(error message) → retry → and eventually `SCSI0 0x0205` (bus reset, which is the
console's `scsi: attention: bus reset for operation timeout`).

A new and useful data point: **RISC/os uses exactly the same IOCB codes** (0x0200 11,899
times, plus 0x0100 and 0x0500) and works. So the difference is not in the command code
but in **the IOCB parameters** (CDB, buffer address, length).

Concrete next step: extend the IOCB log in `mips_i2000.cpp` to dump the parameter block
of every SCSI IOCB (CDB + address + length) and compare RISC/os against EP/IX. That is
low-volume instrumentation — a full AIC-6250 trace is useless: it produces hundreds of
MB because it logs every byte and every REQ/ACK transition on the bus.

## 9. Dumping and comparing the IOCBs

Patch `patch-iocb-params.py` over `mips_i2000.cpp`: for SCSI IOCBs (indices 7..14) it
dumps the 32 bytes of the parameter block alongside the command code. Low volume, unlike
tracing the AIC-6250.

Deduced structure (little-endian, the V50's):

| offset | contents |
|---|---|
| 0-1 | request type/flags |
| 2-3 | command (0x0200 in every case) |
| 4-7 | pointer (not a readable RAM address: dumping it gives zeros) |
| 8-11 | transfer length |
| 12.. | list of page numbers (for the IOP's MMU) |

Comparison **within the same boot**:

```
sash → SCSI1 (WORKS, loads the 1.8 MB kernel)
  04 00 | 00 02 | a4 07 3c 00 | 00 20 00 00 | 20 03 00 00 | 21 03 00 00 | 22 03 00 00 | 00...
  type=4  cmd=0x0200  ptr=0x3c07a4  len=0x2000 (8192)  pages: 0x320 0x321 0x322

EP/IX kernel → SCSI0 (FAILS, retry loop)
  00 00 | 00 02 | 80 05 3c 00 | 18 00 00 00 | 9c 09 00 00 | 00 00 00 00 | ...
  type=0  cmd=0x0200  ptr=0x3c0580  len=0x18 (24)  pages: 0x99c
```

Kernel lengths in successive requests: 0x14, 0x18, 0x1c, 0x20, 0x24 (20, 24, 28, 32, 36
bytes) — small, varying transfers, not disk block reads.

**The difference is in the type field (bytes 0-1): 4 in the ones that work, 0 in the
ones that fail.** The command code is identical in both.

## 10. The SCSI transport is fine — conclusive proof

Ran, in sash, the literal step from the release notes, which **reads from unit 1 and
writes to unit 0**:

```
sash: cp -b 16k dksd(,1,2)epix2.1.1/1/miniroot dksd(,,1)
..........................................................
19922944 (0x1300000) bytes copied
sash:
```

**19.9 MB copied without a single error**, across both units, through the IOP and the
patched AIC-6250. And afterwards the full manual sequence (sash → cp → `boot -f
dksd(,1,2)epix2.1.1/1/unix.i2000_std root=sdc0d0s1`) again ends in the same kernel retry
loop.

Conclusion: **it is not the disk, nor the synthesised volume header, nor the miniroot,
nor the SCSI transport**. It is how the EP/IX kernel formulates the request (type 0)
versus how the PROM firmware formulates it (type 4).

The natural next step: disassemble the SCSI IOCB handler in the IOP firmware (the V50
ROM from `rs2030.zip`, mapped at 0x80000-0xbffff of the IOP's space) to see what it does
with the type field. Alternative: look at EP/IX's SCSI driver in the media itself
(`unix.i2000_std` is not stripped) and see which structure it fills in.

## 11. Disassembling the kernel (`unix.i2000_std`)

`unix.i2000_std` is MIPSEB ECOFF and **not stripped**: 5,296 external symbols.
`ecoff.py` parses the symbolic header (HDRR, magic 0x7009) and disassembles with
capstone (MIPS32 big-endian). Sections: `.text` 0x80050000 (1,604,464 B), `.rdata`
0x801d7b70, `.data` 0x801db550, `.sdata` 0x8020b080, `.bss` 0x8020ec90. `$gp =
0x80213070`.

Commands: `ecoff.py sections | syms <regex> | which <hex> | xrefs <sym> | dis <sym> [n]
| disat <hex> [n]`.

### 11.1 The IOP ABI, from the kernel itself

`iopb` (0x8020ead8) is a table of 24 entries of 16 bytes. From disassembling `iop_poke`,
`iop_wait` and `iop_setbuf`:

| offset | field | who touches it |
|---|---|---|
| +0x0 | command parameter | `iop_poke`: `sw $a2, ($s0)` |
| +0x4 | result | `iop_wait`: `lw $t7, 4($s0)` → returned to the caller |
| +0x8 | command semaphore (halfword) | `iop_poke`: `sh 0xff, 8($s0)` |
| +0xa | **response semaphore** (halfword) | `iop_wait`: polls it |
| +0xc | buffer pointer | `iop_setbuf`: `sw $a1, 0xc($t9)` |

`iop_poke(idx, mode, cmdparam, chan)`: validates idx<24, waits for the command semaphore
to clear (mode 1 = non-blocking, 3 = spin, otherwise = `sleep`), writes the cmdparam,
sets the semaphore to 0xff, **waits for bit 0x40 of `0xa2000003`** and writes a 4 there
(the doorbell). `cmdparam = (physical address of the block) − 0x1000`, which is exactly
how MAME decodes it.

### 11.2 What `0x8017070C` is

`ecoff.py which 8017070C` → **`iop_poke+0x180`**, and the instruction is literally:

```
80170708  jal   0x8016fe38   <ssplx>
8017070c  sb    $t7, 3($t9)        ; $t7 = 4, $t9 = 0xa2000000  → rings the doorbell
```

That is, **the kernel rings the IOP's doorbell correctly**. What never happens is the
IOP setting the response semaphore at +0xa.

### 11.3 Who fails

`ecoff.py xrefs iop_poke` → the only SCSI caller is **`isdedtinit`** (0x80178204), the
device probe of the `isd` driver (the i2000's low-level one:
`isdopen/isdstrategy/isdintr/isd_low_scsi/isd_syncmode/isd_newproms/isd_un/isd_tab`).
The probe does:

```
addiu $a0, 7            ; IOCB 7 = SCSI0
jal   iop_alloc         ; reserves 0x60 bytes of shared area
sb    $t1, ($v0)        ; byte 0 = command code
sw    $t2, 8($v0)       ; length/flags
and   $s0, $s7, 0x1fffffff ; KSEG0 → physical
addiu $s0, $s0, -0x1000    ; → cmdparam
jal   iop_poke
```

and **immediately afterwards it arms a watchdog**:

```
801787fc  lw   $t5, -0x5778($gp)   ; isd_newproms
8017883c  jal  0x8007a070 <timeout>
80178848  sw   $v0, 0x28($s0)      ; stores the timeout id
```

That `timeout()` is what produces `SCSI 0L0: POLLED timeout` and triggers the retry. The
observed loop is exactly: poke → nobody answers → watchdog → message → retry.

### 11.4 The shape of the request

Byte 3 of the command block is a **bitfield of flags**, set conditionally:

```
80178790  andi $v0, $v0, 0x20      ; device capability bit
80178794  beqz $v0, 0x801787c0
8017879c  lw   $t8, ($s1)
801787a4  ori  $t9, $t8, 4         ; bit 2 in a status word
801787ac  lbu  $t0, 3($s2)
801787b4  ori  $t1, $t0, 1         ; bit 0 in the command flags byte
801787bc  sb   $t1, 3($s2)
```

Ruled out that it comes from the emulated disk's INQUIRY: in
`src/devices/bus/nscsi/hd.cpp` byte 7 of the response (sync/wide/linked/cmdque) is
**never filled in** and stays 0.

The lengths of the failing requests (20, 24, 28, 32, **36**) are probe response sizes —
36 is the standard INQUIRY length. So: **the kernel is stuck probing devices**, before
reading a single block of data.

### 11.5 What remains

The next link is the **IOP firmware** (V50, the `rs2030.zip` ROM mapped at
0x80000-0xbffff of the IOP's space): find out why its SCSI IOCB handler services the
PROM's commands (codes 1 and 2 with flags 4) and does not complete the kernel's (code 2
with flags 0). It is now well bounded: it is known which fields to look at (+0/+4/+8/
+0xa/+0xc of the IOCB entry, and the block at `0x1000 + cmdparam`) and which commands to
compare.

## 12. Disassembling the IOP firmware (NEC V50)

`mkiop.py` rebuilds the 256 KB image from the four PROMs with the interleave from
`ROM_START(i2000)`: u139/u140 = even/odd bytes of the low half, u142/u141 = even/odd of
the high half. It maps at 0x80000-0xbffff with a mirror at 0xc0000-0xfffff. Reset vector
at rom 0x3fff0 = `jmp far 0xec00:0x0010`; start-up sets **DS = ES = SS = 0** (the IOP's
RAM) and copies its data to RAM. Disassembler: `iopdis.py` (capstone, 16-bit x86).

### 12.1 ★ Who prints the error

The EP/IX kernel contains `POLLED time out` (two words) and the IOP firmware
`SCSI %dL%d: POLLED timeout` (one word, rom 0x26371). **What appears on screen is the
one-word form** ⇒ the failure is reported by **the IOP firmware**, not by EP/IX. That
is: the IOP receives the command, attempts the operation and gives up itself.

### 12.2 The chip access routines

Searching for `mov dx,0x80` / `mov dx,0x82` (the AIC-6250 ports in `iop_io_map`) turns
up the two primitives:

```
f7623  aic_read(reg):   mov ax,[bp+4]; mov dx,0x80; out dx,al; mov dx,0x82; in al,dx; ret
f7637  aic_write(reg,v): mov ax,[bp+4]; mov dx,0x80; out dx,al; mov ax,[bp+6]; ...
```

`iopcalls.py` finds 34 calls to the first and 95 to the second, all between 0xf4100 and
0xf6c90: that is the firmware's SCSI driver.

### 12.3 ★★ The loop that gives up — and why sash works

```
f69e3  mov ax,9  ; call aic_read     ; register 9 = SCSI signal
f69ed  test al,2                     ; bit 1 = REQ
f69f1  mov ax,0xf; call aic_read     ; register 0x0f = SCSI LATCH DATA  ← byte at a time
f6a12  or  byte [0x4441],0x80        ; bit 7 of control register 1 ...
f6a1d  mov ax,8  ; call aic_write    ; ... = R08W_AUTO_SCSI_PIO_REQ    ← AUTO PIO!
...
f6aac  mov ax,8  ; call aic_read     ; register 8 = STATUS REGISTER 1
f6ab6  test al,8                     ; bit 3 = COMMAND DONE
f6aa1  cmp word [bp-6],0x32          ; retry counters 0x32 / 0x3e8
```

**The firmware services these requests with the chip's Auto PIO mode** (byte by byte
through register 0x0f, polling Command Done), not with DMA. And there is the asymmetry
that had been elusive all session: **sash's bulk reads use the DMA path (which works)
and the kernel's requests use the Auto PIO path**, which in MAME's model is the least
developed one (its only comment is `// TODO: test expected phase`).

### 12.4 Confirmed in execution

Instrumenting **only** the Auto PIO states (`patch-autopio-log.py`, minimal volume
compared with LOG_STATE, which prints a line per byte of every DMA and generates
hundreds of MB), the trace confirms the correspondence one to one:

```
[:] iocb SCSI0 command 0x0200 param 0x234: ... (':cpu' (8017070C))
[:aic6250] AUTOPIO start (dma_cntrl 0x00)
[:aic6250] AUTOPIO req seen, in
[:aic6250] AUTOPIO in 0x02
[:aic6250] AUTOPIO done
```

4,120 Auto PIO transfers in the run. The path **does complete** every byte (start → req
→ in → done), but **what it reads is zeros** (`AUTOPIO in 0x00`, occasionally `0x02`)
and only a couple of bytes come out per command, all in the *in* direction — never
*out*, meaning the CDB never gets sent this way.

### 12.5 Next step

Add the **SCSI bus phase** to those trace lines (one more line in `AUTO_PIO_IN/OUT`) and
compare against a good sash operation: it has to be seen in which phase those zeros are
being read and why the sequence does not advance to sending the CDB. The
`// TODO: test expected phase` in `case AUTO_PIO:` is the natural suspect — MAME does
not check that the phase matches the expected one before handshaking.

## 13. ★★★ THE EP/IX MINIROOT BOOTS

### 13.1 The trace with phase: the kernel's commands **do work**

Adding the bus phase to the trace (`patch-phase-log.py`), a good sash command looks like
this:

```
DMA start from memory count 6 bus COMMAND expect COMMAND    ← CDB
DMA out done bus DATA IN expect COMMAND
DMA start to memory count 36 bus DATA IN expect DATA IN     ← data
DMA in done bus STATUS expect DATA IN
AUTOPIO ... bus STATUS expect STATUS      in 0x00           ← GOOD status
AUTOPIO ... bus MESSAGE IN expect MESSAGE IN  in 0x00       ← command complete
```

and **the kernel's are identical**: same phases, `bus == expect` throughout, status
0x00. So the broken-Auto-PIO hypothesis was false: the path works.

### 13.2 Where it really breaks

Counting requests: **16 serviced by the chip, 28 with no chip activity at all**. The
transition is exact:

```
8576: DMA start from memory count 6 bus COMMAND expect COMMAND
8577: DMA out done bus STATUS expect COMMAND       ← jumps to STATUS with no data phase
8580: AUTOPIO in 0x02 bus STATUS expect STATUS     ← ★ status 0x02 = CHECK CONDITION
...from here on the IOP never touches the chip again for that unit
```

And what kept repeating in the log were not new requests: it was **the same stuck IOCB**
with its semaphore uncleared, re-registered every time the kernel rang the doorbell for
something else (printing on UART0).

### 13.3 The guilty command

Logging the bytes that go out in the COMMAND phase (`patch-cdb-log.py`):

```
x5  status=0x00  CDB 00 00 00 00 00 00   TEST UNIT READY
x1  status=0x00  CDB 12 01 80 00 10 00   INQUIRY EVPD page 0x80
x1  status=0x02  CDB 1a 00 38 00 1c 00   MODE SENSE(6) page 0x38  ← REJECTED
```

`0x1a` = MODE SENSE(6), **page 0x38** (the Common Command Set cache page), length 28.
`src/devices/bus/nscsi/hd.cpp` implements pages 00, 01, 02, 03, 04, 08 and 30; 0x38
falls into `default: fail = true` → `scsi_status_complete(SS_CHECK_CONDITION)`. The
arithmetic matches exactly: 4-byte header + 8-byte block descriptor + 16-byte page =
**28**, so the driver expects a page 0x38 of length 14.

### 13.4 The fix and the result

`hd.cpp.diff`: add `case 0x38` with page length 0x0e. With that:

```
Total real memory  = 16777216
start I/O probe
I/O probe complete                        ← the probe COMPLETES
Root on dev 0x840001, Dump on dev 0x840001
Root fstype ffs                           ← root mounted (the miniroot in swap)
New swplo: 38912  swap size: 344K bytes
Miniroot run level 1                      ← ★★ THE MINIROOT BOOTS
erase=^W, kill=^U, interrupt=^C           ← ★★★ its .profile, shell ready
```

9,215 complete SCSI commands in the run: **8,185 WRITE(6) and 1,000 READ(6)** on top of
the probe. EP/IX 2.1.1 is doing real disk I/O.

Rig detail: on `rc2030` MAME only attaches a terminal to `tty1`; the kernel console
comes out of the other port, so it has to be started with **`-tty0 terminal`** and both
screens captured (`type2.lua` already iterates `manager.machine.screens`).

### 13.5 Next step

Type `inst` at the miniroot shell: that is the installer, with `Pkg=/epix2.1.1` mounted
from the distribution and `Pkgroot=/mnt` on the target disk, selecting subpackages
`rs2030` + `usr` + `bsd43` + `cmplrs`.

## 14. ★★★ THE `inst` INSTALLER RUNS

### 14.1 rs2030 boots too

With the page 0x38 fix, **`rs2030` boots just as well as `rc2030`**: that machine's
blocker was the same SCSI problem, not the unimplemented `0x01ff1000` graphics register
(that write is benign). And it is the machine to work on, because the kernel console
comes out on the graphics screen and the keyboard already works:

```
Miniroot run level 1
erase=^H, kill=^U, interrupt=^C
#
```

On `rc2030` the kernel console and the keyboard end up on different serial ports
(`natkeyboard` binds to `:tty0:terminal:keyboard` while the kernel prints on the other),
so typing never reaches the shell — which is why `rs2030` is preferable.

### 14.2 The installation recipe

From the release notes (the CD-ROM section), adapting the device to unit 1:

```
# From=cd
# CDpath=sdc0d1s2          (the default would be sdc0d2s2)
# Product=epix2.1.1
# inst
```

`inst` mounts the distribution on `/relroot` by itself; no manual `mount` is needed. The
`/dev/dsk/sdc0d1s2` node already exists in the miniroot.

### 14.3 The dialogue, as far as it goes

```
Software package installation
cd installation selected.
Local package root [/relroot]?            → <CR>
...
Is the information above correct? (y n)?  → y
...
========== selecting subpackages ==========
   uucp, sccs, games, hwmaint, EZview, EasyBench, mhs, sat, ccm, man_ccm,
   EPIX1.4.3-compat, reconfig_i/ii/i_mp/ii_mp/iii ...
Install ALL subpackages (y n) [n]?        → y
...
========== setting system clock/calendar ==========
The timezone is currently set to: CST6CDT
Is this correct (y n) [y]?                ← this is where it is now
```

The typing sequence that reproduces the above (emulated times, `rs2030`):

```
45:boot -f dksd(,1,8)sash2
110:boot -f dksd(,1,2)epix2.1.1/1/unix.i2000_std root=sdc0d0s1
420:From=cd   430:CDpath=sdc0d1s2   440:Product=epix2.1.1   455:inst
600:<CR>      660:y                 1040:y
```

### 14.4 Cost of iteration

Every new answer means repeating the whole boot (~10 minutes of wall clock: PROM, sash,
kernel, miniroot, and walking the dialogue again). To make progress it is better either
to batch answers in `CMDS`, or to try a MAME savestate right after the miniroot prompt.

## 15. ★★★ THE INSTALL RUNS: mkfs, fsck and package extraction

Full dialogue walked through (all times are emulated seconds on `rs2030`):

| t | answer | question |
|---|---|---|
| 600 | `<CR>` | Local package root [/relroot]? |
| 660 | `y` | Is the information above correct? |
| 1040 | `y` | Install ALL subpackages (y n) [n]? |
| 1120 | `y` | timezone CST6CDT correct? |
| 1145 | `y` | clock correct? |
| 1170 | `y` | install sash in the volume header? |
| 1750 | `6` | which partition for /usr? (951 MB) |
| 1830 | `y` | **Initialize filesystems (y n) [y]?** |
| 1900+ | `<CR>`×6 | accept the remaining defaults |

**Important warning**: after choosing the `/usr` partition the question is NOT the swap
one shown in the release-notes transcript (that one is an *update*), but
**`Initialize filesystems (y n) [y]?`**. Answering `n` there (the first attempt here)
makes the mount fail with `Couldn't mount /dev/root: Invalid argument` and `inst` aborts
tidily to the shell — nothing is damaged, but it has to be repeated.

With `y`, the installation does the real work:

```
Initializing the filesystem on /dev/root...
/dev/root:  45600 sectors in 38 cylinders of 15 tracks, 80 sectors
            23.3Mb in 3 cyl groups (16 c/g, 9.83Mb/g, 2048 i/g, 1 cg/inc)
mkfs.ffs: installed random inode generation numbers
Checking the filesystem on /dev/root...
** Phase 1 - Check Blocks and Sizes ... ** Phase 5 - Check Cyl groups
2 files, 9 used, 21958 free (14 frags, 2743 blocks, 0.1% fragmentation)
Initializing the filesystem on /dev/usr...
...
========== verifying disk space ==========
There is enough space.
========== extracting files from subpackage archives ==========
Subpackages were compressed.
Loading subpackage: rn... root... rc2030... bsd43... svr4... usr...
                    cmplrs... cmplrs-bsd43... cmplrs-svr4... man...
```

`mkfs.ffs` plus `fsck` on the target disk and extraction of the subpackages,
**including `rc2030`** (this machine's kernel and devices) and `cmplrs` (the C
compiler).

Extracting the ~30 subpackages does not fit in a short run: it has to be launched with a
large `SNAP_UNTIL` (≥14000 emulated seconds, ~1 hour of wall clock) so it finishes in
one go, because cutting it short leaves the disk half-written and forces `inst` to be
repeated from the beginning.

## 16. ★★★ PROJECT COMPLETE — EP/IX 2.1.1 installed, self-hosting, clean prompt

```
epix Console login: root
Welcome to the EP/IX Software System.
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

### 16.1 Making it self-hosting

The install left everything except the kernel (`comply: missing file: unix.i2000_std`).
It can be fixed from inside the system itself, without repeating the five-hour `inst`:

```
epix # mount -r /dev/dsk/sdc0d1s2 /mnt
epix # cp /mnt/epix2.1.1/1/unix.i2000_std /unix.i2000_std
epix # ln /unix.i2000_std /unix
epix # ls -l /unix /unix.i2000_std
-rw-r--r--   2 root  other  4550656 Aug 23 04:10 /unix
-rw-r--r--   2 root  other  4550656 Aug 23 04:10 /unix.i2000_std
epix # umount /mnt ; sync
```

And from then on it boots **from its own disk alone**, without the distribution:

```
>> boot                          (loads the sash that inst put in the volume header)
sash: boot -f dksd(,0,0)unix     (the installed kernel, partition 0)
```

### 16.2 A clean prompt (disabling rpc.mountd)

The flood of `mountd: couldn't register MOUNTPROG` at boot is NFS with no network; init
retries it, gives up with *"Command is respawning too rapidly"* and leaves the noise on
screen. It goes away by setting the inittab action to `off`:

```
epix # cp /etc/inittab /etc/inittab.orig
epix # sed s\|respawn:/usr/etc/rpc.mountd\|off:/usr/etc/rpc.mountd\| /etc/inittab.orig > /etc/inittab
epix # grep mountd /etc/inittab
m2:234:off:/usr/etc/rpc.mountd -f `sed -n 1p /etc/rpc.mountd.conf`
epix # init q
```

Result: `OSI daemons:.` → `The system is ready.` → login, without a single MOUNTPROG
line.

**Typing gotcha**: getting quotes through the emulated keyboard is awkward; using `sed`
with a **backslash-escaped** `|` delimiter (`s\|a\|b\|`) avoids quotes entirely. Ready
script: `rig/clean.sh`.

### Files

- `hd.cpp.diff` — MODE SENSE page 0x38 (plus `hd.cpp.pristine`)
- `patch-phase-log.py`, `patch-cdb-log.py`, `cdbstats.py` — this phase's instrumentation
- `mkiop.py` — rebuilds the IOP ROM; `iopdis.py` — 16-bit x86 disassembler;
  `iopcalls.py` — finds nearby calls; `iopref.py` — finds string references
- `patch-autopio-log.py` — instruments only the Auto PIO path
- `ecoff.py` — ECOFF parser + MIPS disassembler (needs `pip3 install capstone`)
- `aic6250.h.diff`, `aic6250.cpp.diff` — the patches against MAME 0.288
- `aic6250.h.pristine`, `aic6250.cpp.pristine` — originals, to revert
- `patch-aic6250.py`, `patch-aic6250-count.py` — apply the patches (idempotent, they
  fail if the block does not match)
- `doc/aic6250.txt` — the datasheet as text
- `rig/selftest.sh` — measures the SCSI self-test success rate (N short boots + md5)
- `rig/catchfail.sh` — repeats boots until it captures a trace of the failure

## Tools written for this work (`tools/`)

- `vh.py` — parses the SGI volume header and the partition table
- `ffs.py` — read-only reader for big-endian 4.2BSD FFS: `ls`, `tree`, `cat`, `get`,
  `extract`
- `fs.py` — locates FFS superblocks in the partitions
- `extract_vh.sh`, `getkernels.sh` — extract standalone programs and kernels

All of them take their inputs from environment variables with relative defaults
(`EPIX_IMG`, `EPIX_KERNEL`, `EPIX_IOP`, `EPIX_ROMS`, `EPIX_MINIROOT`, `EPIX_LOG`,
`MAME_SRC`), so nothing is tied to one machine. See `NOTES.md`.

WSL gotcha: calling `wsl -d Ubuntu-22.04 -- bash -lc '...'` from Git Bash mangles
`/mnt/...` paths; use **script files** and prefix with `MSYS_NO_PATHCONV=1`.
