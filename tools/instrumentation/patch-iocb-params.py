#!/usr/bin/env python3
"""Dump the parameter block of every SCSI IOCB in MAME's Rx2030 driver.

The command code alone (0x0200 for both RISC/os and EP/IX) says nothing about
which disk block, buffer address or transfer length was requested, and that is
where the two systems must differ -- EP/IX's SCSI operations time out where
RISC/os' identical command codes succeed.  IOCBs live at RAM 0x1000, 24 entries
of 16 bytes; bytes 0-3 of an entry point at the parameter block (also relative
to 0x1000), whose bytes 2-3 hold the command.  SCSI units are IOCBs 7..14.
"""
import sys

SRC = "<home>/ews4800/mame/src/mame/mips/mips_i2000.cpp"

OLD = """							default:
								LOGMASKED(LOG_IOCB, "iocb %s command 0x%04x (%s)\\n",
									iop_commands[iocb], iop_cmd,
									machine().describe_context());
								break;"""

NEW = """							case 7:  case 8:  case 9:  case 10:
							case 11: case 12: case 13: case 14: // scsi
								{
									// the command code is the same for every
									// transfer, so dump the parameter block too
									char params[3 * 32 + 1];
									for (unsigned i = 0; i < 32; i++)
										snprintf(params + i * 3, 4, " %02x", m_ram->read(0x1000 + iocb_cmdparam + i));

									LOGMASKED(LOG_IOCB, "iocb %s command 0x%04x param 0x%x:%s (%s)\\n",
										iop_commands[iocb], iop_cmd, iocb_cmdparam, params,
										machine().describe_context());
								}
								break;

							default:
								LOGMASKED(LOG_IOCB, "iocb %s command 0x%04x (%s)\\n",
									iop_commands[iocb], iop_cmd,
									machine().describe_context());
								break;"""

text = open(SRC).read()
if OLD not in text:
    sys.exit("FAILED: default case not found (already patched?)")
if text.count(OLD) != 1:
    sys.exit(f"FAILED: default case matches {text.count(OLD)} times")
open(SRC, "w").write(text.replace(OLD, NEW))
print("patched", SRC)
