#!/usr/bin/env python3
"""Patch MAME's AIC-6250 model to follow the datasheet's DMA transfer rules.

AIC-6250_1988.pdf, "DMA TRANSFER - ASYNCHRONOUS SCSI", initiator:

  Read from SCSI:  the chip asserts ACK when the SCSI phase matches the
                   expected phase, REQ is asserted, the transfer byte count is
                   not zero, and the FIFO is not full.
  Write to SCSI:   same conditions, with "FIFO is not empty".

  "Through special logic, the AIC-6250 will stop the memory prefetch when the
   number of bytes in the FIFO, plus the number of bytes already transferred
   on the SCSI bus, sums to the total transfer length."

MAME checked only the FIFO condition (its own FIXME says so) and prefetched
until the FIFO was full or fewer than 8 bytes were left, so:

  * ACK could be asserted before the target asserted REQ, and in a phase the
    firmware was not expecting;
  * with the count already at zero, leftover prefetched bytes were still
    pushed onto the bus and `m_dma_count--` wrapped the 24-bit counter to
    0xffffffff, so DMA BYTE COUNT ZERO (status register 0, bit 0) never came
    back on -- which is exactly the "dma count 0 bit invalid" failure the
    Rx2030 IOP firmware reports at power-up.
"""
import sys

SRC = "<home>/ews4800/mame/src/devices/machine/aic6250.cpp"

DMA_IN_OLD = """	case DMA_IN:
		// FIXME: assert ack when: req asserted && phase match && count not zero && fifo not full
		if (!m_fifo.full())
		{
			u8 const data = m_scsi_bus->data_r();
			LOGMASKED(LOG_STATE, "dma in 0x%02x\\n", data);

			m_status_reg_0 &= ~R07R_SCSI_REQ_ON;
			m_dma_count--;
			m_fifo.enqueue(data);

			m_state = DMA_IN_NEXT;

			m_scsi_bus->ctrl_w(m_scsi_refid, S_ACK, S_ACK);
		}
		else
		{
			delay = -1;
			m_breq_cb(1);
		}
		break;
"""

DMA_IN_NEW = """	case DMA_IN:
		// assert ack when: req asserted && phase match && count not zero && fifo not full
		if (!m_dma_count)
			// transfer count exhausted: don't consume more than was asked for
			m_state = DMA_IN_DRAIN;
		else if (m_fifo.full())
		{
			delay = -1;
			m_breq_cb(1);
		}
		else if ((m_scsi_bus->ctrl_r() & S_REQ) && phase_match(m_scsi_signal_reg, m_scsi_bus->ctrl_r()))
		{
			u8 const data = m_scsi_bus->data_r();
			LOGMASKED(LOG_STATE, "dma in 0x%02x\\n", data);

			m_status_reg_0 &= ~R07R_SCSI_REQ_ON;
			m_dma_count--;
			m_fifo.enqueue(data);

			m_state = DMA_IN_NEXT;

			m_scsi_bus->ctrl_w(m_scsi_refid, S_ACK, S_ACK);
		}
		// otherwise wait here for req/phase
		break;
"""

DMA_OUT_OLD = """	case DMA_OUT:
		// FIXME: assert ack when: req asserted && phase match && count not zero && fifo not empty
		if (!m_fifo.empty())
		{
			u8 const data = m_fifo.dequeue();
			LOGMASKED(LOG_STATE, "dma out 0x%02x\\n", data);

			m_status_reg_0 &= ~R07R_SCSI_REQ_ON;
			m_dma_count--;

			m_state = DMA_OUT_NEXT;

			// drive data, assert ACK
			m_scsi_bus->data_w(m_scsi_refid, data);
			m_scsi_bus->ctrl_w(m_scsi_refid, S_ACK, S_ACK);
		}
		else
		{
			delay = -1;
			m_breq_cb(1);
		}
		break;
"""

DMA_OUT_NEW = """	case DMA_OUT:
		// assert ack when: req asserted && phase match && count not zero && fifo not empty
		if (!m_dma_count)
			// transfer count exhausted: don't push prefetched bytes onto the
			// bus, and above all don't wrap the byte counter doing it
			m_state = DMA_OUT_DONE;
		else if (m_fifo.empty())
		{
			delay = -1;
			m_breq_cb(1);
		}
		else if ((m_scsi_bus->ctrl_r() & S_REQ) && phase_match(m_scsi_signal_reg, m_scsi_bus->ctrl_r()))
		{
			u8 const data = m_fifo.dequeue();
			LOGMASKED(LOG_STATE, "dma out 0x%02x\\n", data);

			m_status_reg_0 &= ~R07R_SCSI_REQ_ON;
			m_dma_count--;

			m_state = DMA_OUT_NEXT;

			// drive data, assert ACK
			m_scsi_bus->data_w(m_scsi_refid, data);
			m_scsi_bus->ctrl_w(m_scsi_refid, S_ACK, S_ACK);
		}
		// otherwise wait here for req/phase
		break;
"""

PREFETCH_OLD = """		if (m_dma_cntrl & R05W_TRANSFER_DIR)
			if (m_fifo.full() || m_dma_count < 8)"""

PREFETCH_NEW = """		if (m_dma_cntrl & R05W_TRANSFER_DIR)
			// stop prefetching once the FIFO holds the rest of the transfer
			// (m_dma_count is what is left to put on the SCSI bus)
			if (m_fifo.full() || m_fifo.queue_length() >= m_dma_count)"""

text = open(SRC).read()
for name, old, new in (("DMA_IN", DMA_IN_OLD, DMA_IN_NEW),
                       ("DMA_OUT", DMA_OUT_OLD, DMA_OUT_NEW),
                       ("prefetch", PREFETCH_OLD, PREFETCH_NEW)):
    if old not in text:
        sys.exit(f"FAILED: {name} block not found (already patched?)")
    if text.count(old) != 1:
        sys.exit(f"FAILED: {name} block matches {text.count(old)} times")
    text = text.replace(old, new)
    print(f"  patched {name}")

open(SRC, "w").write(text)
print("wrote", SRC)
