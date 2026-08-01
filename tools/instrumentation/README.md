# Instrumentation

These are the scripts that applied the fixes and, more interestingly, the
debug instrumentation used to find them:

| script | what it added |
|---|---|
| `patch-aic6250.py`, `patch-aic6250-count.py`, `patch-mode-page-38.py` | the three fixes (the diffs in `patches/` are generated from these) |
| `patch-iocb-params.py`, `patch-iocb-cdb.py` | dump the parameter block of every SCSI IOCB in the Rx2030 driver |
| `patch-phase-log.py` | add the SCSI bus phase (and the phase the firmware said it expected) to the trace |
| `patch-autopio-log.py` | log only the AIC-6250 Auto PIO states |

They contain absolute paths from the machine they were written on. They are
kept as a record of method — read them, don't run them blind.

The lesson worth carrying: tracing the AIC-6250 with MAME's own `LOG_REG` /
`LOG_STATE` masks produces hundreds of MB (a line per byte and per REQ/ACK
transition) and slows the machine so much it never reaches the failure.
Instrumenting the *driver* at IOCB level, and then narrowing to one line per
SCSI command, is what made the bug visible.
