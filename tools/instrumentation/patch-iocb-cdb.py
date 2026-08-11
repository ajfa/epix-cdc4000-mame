#!/usr/bin/env python3
"""Also dump the block the SCSI IOCB's pointer field points at.

The 32-byte parameter block looks like:
    [0-1] flags/unit   [2-3] command   [4-7] pointer   [8-11] length
    [12..] list of page numbers
so the actual SCSI command descriptor block must live at the pointer.  Dump it
both as an absolute RAM offset and relative to the IOCB area at 0x1000, since
it is not yet clear which the field is.
"""
import os
import sys

MAME_SRC = os.environ.get("MAME_SRC", "mame")

SRC = os.path.join(MAME_SRC, "src/mame/mips/mips_i2000.cpp")

OLD = """									LOGMASKED(LOG_IOCB, "iocb %s command 0x%04x param 0x%x:%s (%s)\\n",
										iop_commands[iocb], iop_cmd, iocb_cmdparam, params,
										machine().describe_context());"""

NEW = """									u32 const ptr = m_ram->read(0x1000 + iocb_cmdparam + 4)
										| (m_ram->read(0x1000 + iocb_cmdparam + 5) << 8)
										| (m_ram->read(0x1000 + iocb_cmdparam + 6) << 16)
										| (m_ram->read(0x1000 + iocb_cmdparam + 7) << 24);

									char abs_buf[3 * 16 + 1], rel_buf[3 * 16 + 1];
									for (unsigned i = 0; i < 16; i++)
									{
										snprintf(abs_buf + i * 3, 4, " %02x", m_ram->read((ptr + i) & 0xffffff));
										snprintf(rel_buf + i * 3, 4, " %02x", m_ram->read((0x1000 + ptr + i) & 0xffffff));
									}

									LOGMASKED(LOG_IOCB, "iocb %s command 0x%04x param 0x%x:%s | abs%s | rel%s (%s)\\n",
										iop_commands[iocb], iop_cmd, iocb_cmdparam, params, abs_buf, rel_buf,
										machine().describe_context());"""

text = open(SRC).read()
if OLD not in text:
    sys.exit("FAILED: log line not found (apply patch-iocb-params.py first?)")
open(SRC, "w").write(text.replace(OLD, NEW))
print("patched", SRC)
