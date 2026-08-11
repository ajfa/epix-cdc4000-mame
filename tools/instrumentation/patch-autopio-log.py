#!/usr/bin/env python3
"""Log only the AIC-6250 Auto PIO path, unconditionally.

The IOP firmware's polled SCSI routine drives the chip in Auto PIO mode
(control register 1 bit 7 = R08W_AUTO_SCSI_PIO_REQ, data read a byte at a time
import os
from register 0x0f) and polls status register 1 bit 3 (Command Done).  Tracing
just those states costs a handful of lines per command, unlike LOG_STATE which
prints a line per byte of every DMA transfer and produces hundreds of MB.
"""
import sys

MAME_SRC = os.environ.get("MAME_SRC", "mame")

SRC = os.path.join(MAME_SRC, "src/devices/machine/aic6250.cpp")

EDITS = [
    ("""			m_state = AUTO_PIO;
			m_state_timer->adjust(attotime::zero);""",
     """			logerror("AUTOPIO start (dma_cntrl 0x%02x)\\n", m_dma_cntrl);
			m_state = AUTO_PIO;
			m_state_timer->adjust(attotime::zero);"""),

    ("""			LOGMASKED(LOG_STATE, "auto pio\\n");

			m_state = (m_dma_cntrl & R05W_TRANSFER_DIR) ? AUTO_PIO_OUT : AUTO_PIO_IN;""",
     """			logerror("AUTOPIO req seen, %s\\n",
				(m_dma_cntrl & R05W_TRANSFER_DIR) ? "out" : "in");

			m_state = (m_dma_cntrl & R05W_TRANSFER_DIR) ? AUTO_PIO_OUT : AUTO_PIO_IN;"""),

    ("""		LOGMASKED(LOG_STATE, "auto pio in 0x%02x\\n", m_scsi_latch_data);""",
     """		logerror("AUTOPIO in 0x%02x\\n", m_scsi_latch_data);"""),

    ("""		LOGMASKED(LOG_STATE, "auto pio out 0x%02x\\n", m_scsi_id_data);""",
     """		logerror("AUTOPIO out 0x%02x\\n", m_scsi_id_data);"""),

    ("""			LOGMASKED(LOG_STATE, "auto pio done\\n");""",
     """			logerror("AUTOPIO done\\n");"""),
]

text = open(SRC).read()
for old, new in EDITS:
    if old not in text:
        sys.exit(f"FAILED: block not found:\n{old[:60]}")
    text = text.replace(old, new, 1)
open(SRC, "w").write(text)
print("patched", SRC)
