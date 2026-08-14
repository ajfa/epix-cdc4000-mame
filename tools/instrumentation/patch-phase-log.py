#!/usr/bin/env python3
"""Add the SCSI bus phase to the Auto PIO trace, plus one line per DMA transfer.

Auto PIO alone showed the kernel's commands reading zeros; to tell whether the
handshake is happening in the wrong phase we need the actual bus phase and the
phase the firmware said it expected (the SCSI signal register).  A line at the
start and end of each DMA transfer (not per byte) gives the same view of the
operations sash performs successfully, so the two can be compared.
"""
import os
import sys

MAME_SRC = os.environ.get("MAME_SRC", "mame")

SRC = os.path.join(MAME_SRC, "src/devices/machine/aic6250.cpp")

PH = ('nscsi_phase[m_scsi_bus->ctrl_r() & S_PHASE_MASK], '
      'aic6250_phase[m_scsi_signal_reg >> 5]')

EDITS = [
    ('logerror("AUTOPIO start (dma_cntrl 0x%02x)\\n", m_dma_cntrl);',
     'logerror("AUTOPIO start dma_cntrl 0x%02x bus %s expect %s\\n", m_dma_cntrl, ' + PH + ');'),

    ('''logerror("AUTOPIO req seen, %s\\n",
				(m_dma_cntrl & R05W_TRANSFER_DIR) ? "out" : "in");''',
     'logerror("AUTOPIO req %s bus %s expect %s\\n", (m_dma_cntrl & R05W_TRANSFER_DIR) ? "out" : "in", ' + PH + ');'),

    ('logerror("AUTOPIO in 0x%02x\\n", m_scsi_latch_data);',
     'logerror("AUTOPIO in 0x%02x bus %s expect %s\\n", m_scsi_latch_data, ' + PH + ');'),

    ('logerror("AUTOPIO out 0x%02x\\n", m_scsi_id_data);',
     'logerror("AUTOPIO out 0x%02x bus %s expect %s\\n", m_scsi_id_data, ' + PH + ');'),

    ('logerror("AUTOPIO done\\n");',
     'logerror("AUTOPIO done bus %s expect %s\\n", ' + PH + ');'),

    # one line per DMA transfer, not per byte
    ('''		LOGMASKED(LOG_DMA, "dma transfer %s memory, count %d\\n",
			data & R05W_TRANSFER_DIR ? "from" : "to", m_dma_count);''',
     '''		logerror("DMA start %s memory count %d bus %s expect %s\\n",
			data & R05W_TRANSFER_DIR ? "from" : "to", m_dma_count, ''' + PH + ');'),

    ('''	case DMA_IN_DONE:
		LOGMASKED(LOG_STATE, "dma in done\\n");''',
     '''	case DMA_IN_DONE:
		logerror("DMA in done bus %s expect %s\\n", ''' + PH + ');'),

    ('''	case DMA_OUT_DONE:
		LOGMASKED(LOG_STATE, "dma out done\\n");''',
     '''	case DMA_OUT_DONE:
		logerror("DMA out done bus %s expect %s\\n", ''' + PH + ');'),
]

text = open(SRC).read()
for old, new in EDITS:
    if old not in text:
        sys.exit(f"FAILED: not found:\n{old[:70]}")
    text = text.replace(old, new, 1)
open(SRC, "w").write(text)
print("patched", SRC)
