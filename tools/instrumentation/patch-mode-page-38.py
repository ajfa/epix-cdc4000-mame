#!/usr/bin/env python3
"""Add MODE SENSE page 0x38 to MAME's SCSI hard disk.

EP/IX's device probe issues

    CDB 1a 00 38 00 1c 00     MODE SENSE(6), page 0x38, allocation length 28

which is the cache control page of the Common Command Set that drives of the
era implemented.  src/devices/bus/nscsi/hd.cpp knows pages 00, 01, 02, 03, 04,
08 and 30, so 0x38 falls through to `default: fail = true` and the disk answers
CHECK CONDITION.  The Rx2030 IOP firmware then stops servicing that unit's
IOCBs altogether, and EP/IX retries the request forever.

The 28-byte allocation length says exactly what the driver expects back:
4 bytes of header + 8 of block descriptor + 16 of page, i.e. a page 0x38 whose
page-length byte is 14.
"""
import sys

SRC = "<home>/ews4800/mame/src/devices/bus/nscsi/hd.cpp"

OLD = """			case 0x30: { // Apple firmware ID page"""

NEW = """			case 0x38: // CCS cache control page
				m_scsi_cmdbuf[pos++] = 0x38; // !PS, page id
				m_scsi_cmdbuf[pos++] = 0x0e; // page length
				std::fill_n(&m_scsi_cmdbuf[pos], 14, 0x00);
				pos += 14;
				break;

			case 0x30: { // Apple firmware ID page"""

text = open(SRC).read()
if OLD not in text:
    sys.exit("FAILED: no encontrado el case 0x30")
if text.count(OLD) != 1:
    sys.exit(f"FAILED: {text.count(OLD)} coincidencias")
open(SRC, "w").write(text.replace(OLD, NEW, 1))
print("patched", SRC)
