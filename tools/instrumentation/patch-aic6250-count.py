#!/usr/bin/env python3
"""Keep MAME's AIC-6250 DMA byte counter to the 24 bits the chip actually has.

The AIC-6250 has a 24-bit DMA Byte Counter, held in registers 00-02
(AIC-6250_1988.pdf: "24-Bit DMA Byte Counter", "The 24-bit counter allows data
transfers up to 16 Mbytes without a DMA wrap").

MAME keeps it in a u32 `m_dma_count` that

  * is never initialised, and
  * is loaded a byte at a time with masks that only clear their own byte
    (`m_dma_count &= ~0x0000ff`), so bits 24-31 are never touched.

So the top 8 bits keep whatever was in the freshly allocated device object.
On the MIPS Rx2030 this showed up as the IOP power-up diagnostic failing about
half the time with

    SCSI Test...: SCSI Power Up Failure: dma count 0 bit invalid

with the trace showing a 6-byte SCSI command loaded as

    dma transfer from memory, count 1392508934      (0x53000006)

Because the count is never zero, DMA BYTE COUNT ZERO (status register 0,
bit 0) never comes on and the transfer never ends.  Masking the loads to 24
bits and clearing the counter at start fixes both.
"""
import sys

HDR = "<home>/ews4800/mame/src/devices/machine/aic6250.h"
SRC = "<home>/ews4800/mame/src/devices/machine/aic6250.cpp"

HDR_OLD = """	void dma_count_l_w(u8 data) { m_dma_count &= ~0x0000ff; m_dma_count |= (data << 0); }
	void dma_count_m_w(u8 data) { m_dma_count &= ~0x00ff00; m_dma_count |= (data << 8); }
	void dma_count_h_w(u8 data) { m_dma_count &= ~0xff0000; m_dma_count |= (data << 16); }"""

HDR_NEW = """	// the DMA byte counter is 24 bits wide; masking with 24-bit constants
	// keeps bits 24-31 clear instead of leaving stale data above the counter
	void dma_count_l_w(u8 data) { m_dma_count = (m_dma_count & 0xffff00U) | (u32(data) << 0); }
	void dma_count_m_w(u8 data) { m_dma_count = (m_dma_count & 0xff00ffU) | (u32(data) << 8); }
	void dma_count_h_w(u8 data) { m_dma_count = (m_dma_count & 0x00ffffU) | (u32(data) << 16); }"""

SRC_OLD = """	m_rev_cntrl = 0x02;

	m_state_timer = timer_alloc(FUNC(aic6250_device::state_loop), this);"""

SRC_NEW = """	m_rev_cntrl = 0x02;
	m_dma_count = 0;

	m_state_timer = timer_alloc(FUNC(aic6250_device::state_loop), this);"""

for path, old, new, what in ((HDR, HDR_OLD, HDR_NEW, "24-bit count loads"),
                             (SRC, SRC_OLD, SRC_NEW, "count initialisation")):
    text = open(path).read()
    if old not in text:
        sys.exit(f"FAILED: {what} not found in {path}")
    if text.count(old) != 1:
        sys.exit(f"FAILED: {what} matches {text.count(old)} times")
    open(path, "w").write(text.replace(old, new))
    print(f"  patched {what} in {path.split('/')[-1]}")
