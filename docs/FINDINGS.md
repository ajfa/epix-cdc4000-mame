# EP/IX 2.1.1 — análisis del medio aportado por el usuario (2026-07-30)

Fichero origen: `<path>\CDC EP-IX 2.11.7z` (334 MiB, 7z sólido LZMA2)

Contenido:
| Fichero | Tamaño | Qué es |
|---|---|---|
| `cdc_epix_2.1.1.iso` | 601 677 824 | **NO es ISO9660** — imagen de disco con volume header SGI/MIPS |
| `CDC EP _ IX (Enhanced Performance UNIX) - National Library. N.E.Bauman.pdf` | 359 330 | doc |
| `Cray-Cyber - Control Data 4680 (majestix).pdf` | 121 716 | copia de la página de majestix |

## 1. Estructura de la imagen

Volume header SGI (magic `0x0BE5A941`), `rootpt=0 swappt=1 bootfile='/unix'`.

Directorio del volume header (programas standalone, todos **MIPSEB ECOFF**):

| Nombre | lbn | tamaño | notas |
|---|---|---|---|
| sash | 960 | 189 680 | MIPS 5.05B, referencias a `r4030_asc_dma`, `R4000` |
| sash3 | 1331 | 271 776 | **`$Revision: EP/IX 1.4.3 $` + `CONTROL DATA PROPRIETARY PRODUCT`**, "Jaguar", Interphase 4210 |
| sash2 | 1862 | 132 896 | v4.32, **"V50 PROM version number"** → clase Rx2030 |
| sash7 | 3406 | 284 592 | Jaguar / Interphase 4210 |
| format, format2/3/7, spanic3/7 | — | — | utilidades standalone |

Tabla de particiones (16 entradas, tipo 4 = bsd4.2):
- part0 blk 2880, 41.2 MB — raíz
- part1 blk 1095360, 38.4 MB — swap
- **part2 blk 9880, 568.5 MB — FFS big-endian real, `fs_fsmnt = /usr/netinstall`**
- part8 volhdr, part10 = volumen entero (573.3 MB)

## 2. Contenido de `/usr/netinstall` (leído con `ffs.py`, solo lectura)

```
epix2.1.1/       (1/, 2/, 3/, pkginfo, tape0..tape3)
utilities2.1.1/  (1/, pkginfo, tape0, tape1)
```

`epix2.1.1/1/` contiene los **kernels de toda la gama CDC 4000**:

| Fichero | Máquina |
|---|---|
| **`unix.i2000_std`** | **RC2030 / RS2030** ← MAME lo emula FUNCIONANDO |
| `unix.r3030_std` | CD4320 / CD4330 (= MIPS RC3230) |
| `unix.r2400_std` | CD4340 |
| `unix.r3200_std`, `unix.r3200_ijc` | CD4360 / CD4380 (M/2000) |
| `unix.r6000_std`, `unix.r6000_mp` | **CD4660 / CD4680 (R6000) = majestix** |
| `unix.rb3125_std` | CD4360-200/300, CD4350-300 |
| `unix.r4370_std`, `unix.r4370_mp` | CD4370 |
| `unix.r4030eb_std`, `unix.r4030vb_std` | CD44x0 (Magnum/Millenium, R4000) |

más `sash.2030` (dice literalmente **"Rx2030 FLOPPY"**), `sash.std`, `sash.4370`,
`sash.r4000`, **`miniroot`** (19.9 MB, FFS v1 big-endian, limpio, 29-mar-1993) e `instd`
(tar POSIX).

Sello del kernel objetivo:
```
@(#)EP/IX 2.1.1 (i2000_std) -- Mon Mar 29 10:17:06 CST 1993 -- eduarte
@(#)Standard Release Kernel for EP/IX 2.1.1 b1r7
Control Data EP/IX Version %s
*        CONTROL DATA PROPRIETARY PRODUCT        *
*      Copyright Control Data Systems, Inc.      *
```
Su tabla de nombres de máquina incluye: `rc2030`, RC3230, RS3230, RC3240, RC3330, RC4030,
RC6280, CD4370, CD4480.

## 3. El hallazgo que lo cambia todo

`epix2.1.1/epix2.1.1/pkginfo` declara como subpaquete de primera clase:

```
subpackage=rc2030
subpackage=RC2030
subpackage=rs2030
subpackage=RS2030
        id="RC2030/RS2030 Kernel and Devices"
        splitboms="root.i2000 rc2030_dev sppbin_2030 sppbin_bfs usr.mips1"
        bom=r2030
```

→ **EP/IX 2.1.1 soporta oficialmente la RC2030/RS2030, que es justo la máquina que MAME
emula sin flag `NOT_WORKING`** (`src/mame/mips/mips_i2000.cpp:714-715`, flags 0).

El resto del medio: `bsd43` (utilidades 4.3BSD), `svr4`, `cmplrs` (compilador C 3.11) +
variantes bsd43/svr4, `man`, `pTHREADS`, `uucp`, release notes. Es la distribución completa,
no un parche.

## 4. Requisitos que faltan para arrancar en MAME

Romset `rs2030` / `rc2030` (comparten `rom_i2000`):
- `50-00121__005.u139`, `50-00120__005.u140`, `50-00119__005.u141`, `50-00118__005.u142`
  (v4.32, 64 KB cada una) — o la variante `__003` v4.30
- `ds1287.bin` (64 bytes) — imagen NVRAM hecha a mano por MAME para entrar al monitor,
  CRC32 `28369bf3`
- Los volcados U139-U142 existen públicamente: `bitsavers.org/bits/MIPS/RISCos/geekdot_com/Rx2030_firmwares.zip`
  y en el Wayback de `yahozna.dyndns.org/scratch/mips/U139.HEX`..`U142.HEX`

## 5. Plan de arranque propuesto

1. Baseline conocido-bueno: arrancar RISC/os 4.52 (`MIPS-rc2030-RISCos-4.52-hdimage.zip`) en
   `mame rs2030` → valida ROMs + driver + geometría SCSI.
2. `chdman createhd` sobre `cdc_epix_2.1.1.iso` (sectores de 512 B, sin cabecera) → adjuntar
   como segundo disco SCSI.
3. Desde el monitor PROM arrancar el standalone del volume header (`sash2`, el de V50) o
   `sash.2030` del árbol netinstall.
4. Arrancar el `miniroot` y lanzar el instalador contra `/usr/netinstall/epix2.1.1`
   seleccionando el subpaquete `rs2030` + `usr` + `bsd43` + `cmplrs`.
5. Instalar sobre un CHD en blanco → sistema EP/IX 2.1.1 arrancable.

## 6. EJECUCIÓN — resultados (2026-07-30, misma sesión)

### Rig
- Binario slim MAME 0.288 con solo el driver i2000: `~/ews4800/mame/mips2030`
  (`make SOURCES=src/mame/mips/mips_i2000.cpp SUBTARGET=mips2030 TOOLS=1 REGENIE=1 NOWERROR=1 -j6`),
  más `chdman`.
- ROMs: el `roms.zip` del usuario trae `rs2030.zip` completo (incluye el `ds1287.bin` de 64 B
  que no está en bitsavers) + `at_keybc.zip` + `kb_ms_natural.zip`. Los 8 volcados de PROM
  bajados de bitsavers (S-record, no Intel HEX) **coinciden en CRC32 con los 8 de MAME**.
- Discos: `epix-dist.chd` (imagen EP/IX, 1223/15/64), `epix-target.chd` (1731/15/80),
  `riscos-work.chd` (copia del disco del usuario — el original no se toca).

### Hitos verificados
1. **PROM arranca**: `MIPS Monitor Version 4.32 ... 1990`, 16 MB, prompt `>>`.
   `printenv` → `bootfile=dksd(0,0,8)sash`, `bootmode=e`, `console=a`.
2. **RISC/os 4.52 arranca a login** (`The system is ready.` / `exedra Console login:`)
   → rig validado de extremo a extremo.
3. **`sash2` de EP/IX arranca desde el volume header de la distribución**
   (`boot -f dksd(,1,8)sash2` → *Standalone Shell 4.32 ... Sat Feb 29 1992 marker*).
4. **★ EL KERNEL DE EP/IX 2.1.1 ARRANCA**:
   ```
   CPU0: MIPS R2000A Processor Chip Revision: 1.0
   FPU0: MIPS R2010A VLSI Floating Point Chip Revision: 1.0
   Control Data EP/IX Version 2.1.1
   *  CONTROL DATA PROPRIETARY PRODUCT  *
   *  Copyright Control Data Systems, Inc. 1990, 1991, 1992, 1993
   Total real memory = 16777216
   start I/O probe
   ```

### Receta (de las propias release notes, §4.4.6, adaptada al rs2030)
Original para 44x0 desde CD-ROM local:
```
>> boot -f dksd(,2,8)sash
sash: cp -b 16k dksd(,2,2)epix2.1.1/1/miniroot dksd(,,1)
sash: boot -f dksd(,2,2)epix2.1.1/1/unix.r4030eb_std root=sdc0d0s1
```
Nuestra versión (distribución en SCSI 1, destino en SCSI 0):
```
>> boot -f dksd(,1,8)sash2
sash: boot -f dksd(,1,2)epix2.1.1/1/unix.i2000_std root=sdc0d0s1
```
El paso `cp` del miniroot a swap se hace desde fuera con `mktarget.py`, que además escribe
en el disco destino un volume header válido (copiado del disco RISC/os — misma geometría —
con el directorio de volumen borrado y el checksum recalculado; el algoritmo es "la suma de
las 128 palabras big-endian del bloque 0 debe dar 0", verificado contra el disco real).

### Diagnóstico del bloqueo (con `#define VERBOSE (LOG_IOCB)` en mips_i2000.cpp:127)

En el Rx2030 el kernel no habla con el SCSI directamente: deja **IOCBs** (bloques de control
de E/S) en RAM compartida y toca un timbre en `0x02000000`; el IOP V50 —que ejecuta firmware
real del PROM— los procesa. Contando IOCBs en un arranque completo:

| Sistema | IOCBs totales | de ellos SCSI |
|---|---|---|
| RISC/os 4.52 (arranca a login) | **21 725** | 20 726 |
| EP/IX 2.1.1 (se cuelga) | **28** | 4 |

Y los 28 de EP/IX son **todos del PROM/sash** (cargar sash2 y el kernel): **el kernel de EP/IX
no emite ni un solo IOCB**. Se cuelga esperando (`SCSI 0L0: POLLED timeout`) sin haber llegado
a pedir nada al IOP.

El único acceso anómalo del kernel es una escritura a `0x01FF1000`, que MAME reporta como no
mapeada... y que está **comentada en el propio driver**:

```cpp
void mips_i2000_state::rs2030_map(address_map &map)
{
    map(0x01000000, 0x011fffff).ram().share("vram");
    map(0x01ffff00, 0x01ffffff).m(m_ramdac, FUNC(bt458_device::map)).umask32(0xff);

    //map(0x01ff1000, 0x01ff1001).w() // graphics register?
    //map(0x01ff0080, 0x01ff0081).w() // graphics register?
}
```

Es decir: el autor de MAME vio esas escrituras, no identificó el registro y lo dejó sin
implementar. EP/IX 2.1.1 (1993) lo usa; RISC/os 4.52 (1991) no.

### ★ rc2030 llega MUCHO más lejos
Con la consola serie y el kernel cargado desde la distribución:
```
>> boot -f dksd(,1,8)sash2
108464+26084+257920 entry: 0xa0300000
MIPS Standalone Shell Version 4.32 MIPS OPT Sat Feb 29 16:58:16 PST 1992 marker
sash: boot -f dksd(,1,2)epix2.1.1/1/unix.i2000_std root=sdc0d0s1
1804464+222688+642304 entry: 0x80050010
```
y el kernel **sí dialoga con el IOP: 2 432 IOCBs y subiendo** (en rs2030 eran **0**). Es la
prueba de que el camino gráfico del rs2030 es lo que bloqueaba al kernel. Después también se
arrastra, así que queda al menos un segundo problema por delante.

Dos detalles del rig para rc2030: necesita su propio `rc2030.zip` (copia de `rs2030.zip`), y
la entrada va por el **terminal serie**, no por el teclado AT → `natkeyboard:post()` funciona
tal cual y **no pierde ni mayúsculas ni paréntesis** (`KBD=nat` en `type2.lua`). El arranque
en frío tarda ~250 s emulados en llegar al `>>`.

### Prueba anterior en rc2030 (servidor, sin gráficos)
`rc2030` necesita su propio `rc2030.zip` (copia de `rs2030.zip`). Da consola serie con el
autotest del IOP (`SCSI Test...Passed`, `Kick Start the R2000`) y llega a **452 IOCBs** con
sondeo de SCSI0..SCSI6, pero la salida del monitor del R2000 va por **tty1** (`m_tty[1]`
→ "terminal" en `rc2030()`), que es una segunda pantalla que el script de capturas todavía no
fotografía. Pendiente: capturar ambas pantallas para poder teclear en el monitor del R2000.

## 7. Sesión rc2030 — dónde muere exactamente

Con la NVRAM caliente por máquina (`rig/nvram-good-rc2030`, restaurada por `run.sh`) y la
secuencia de dos pasos, un arranque bueno llega hasta aquí:

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

y a partir de ahí el kernel entra en un **bucle infinito de reintento**, visible en el log de
IOCB (PC del kernel `8017070C`):

```
iocb SCSI0 command 0x0200   ← operación SCSI a la unidad 0
iocb UART0 command 0x0003   ← imprime el error por consola
...  (1215 UART0, 523 UART1, 499 SCSI1, 51 SCSI0)  ...
```

O sea: **no está colgado, está fallando**. Cada operación SCSI del kernel falla, imprime
`SCSI 0L0: POLLED timeout` y reintenta; el "arrastre" de la emulación es ese torrente de texto.

### Por qué falla el kernel y no el PROM
El PROM y `sash` **sí** leen del SCSI (cargan un kernel de 1,8 MB desde la unidad 1 sin
problema): hacen E/S simple, polled, sin desconexión. El driver del kernel de EP/IX (1993) usa
el camino completo del chip. Y `src/devices/machine/aic6250.cpp` dice de sí mismo:

```
 * Status: very WIP, enough to load RISC/os on MIPS Rx2030 driver, but many
 * unimplemented and incorrect behaviours.
 * TODO
 *   - fix problems with ATN
 *   - 16 bit DMA odd address start and HBV/LBV selection
 *   - disconnect/reselect          ← no implementado
 *   - phase checks
```

### Segundo síntoma, mismo origen: el autotest del IOP falla ~50 % de las veces
```
SCSI Test...: SCSI Power Up Failure: dma count 0 bit invalid
...Failed, error= ffff
```
Traza de registros (con `#define VERBOSE (LOG_GENERAL|LOG_REG|LOG_STATE|LOG_SCSI)` en
aic6250.cpp): arbitración ganada → `selection: complete` → `phase COMMAND REQ` →
`scsi_signal_reg_w 0x80` (espera fase COMMAND) → **`dma_cntrl_w 0x03`** (arranca el DMA de los
bytes de comando) → y el bit `R07R_DMA_BYTE_CNT_ZERO` (status_reg_0 bit 0, derivado de
`!m_dma_count`) no queda como el firmware espera → aborta y hace reset del chip.
Que sea **intermitente** apunta a carrera en la máquina de estados del DMA, no a lógica fija.
Nota: `m_offset_count_zero` (bit 0x20 de fifo_status) se asigna `true` en dos sitios y **nunca
se actualiza** — stub, posible pista adicional.

### Conclusión
El medio y el sistema operativo están bien; lo que falta es **emulación**. El bloqueo es el
modelo del AIC-6250 de MAME, que da justo para lo que hace RISC/os y se queda corto para EP/IX.
Arreglarlo es trabajo de dispositivo MAME con la hoja de datos
`bitsavers.org/pdf/adaptec/asic/AIC-6250_1988.pdf` (la que cita el propio fichero).

### Bloqueo actual
Tras el banner, el probe de E/S da `SCSI 0L0: POLLED timeout` y la emulación se arrastra
(9:45 de CPU real para ~240 s emulados). Sospecha principal: el AIC6250 de MAME está
declarado en su propia cabecera como *"very WIP, enough to load RISC/os on MIPS Rx2030
driver, but many unimplemented and incorrect behaviours"*, con **disconnect/reselect sin
implementar** (`src/devices/machine/aic6250.cpp`). RISC/os 4.52 (driver de 1991) no lo usa;
EP/IX 2.1.1 (1993) probablemente sí. Pendiente de confirmar con la corrida instrumentada.

## 8. Sesión del datasheet — BUG DE MAME ENCONTRADO Y ARREGLADO

Hoja de datos: `bitsavers.org/pdf/adaptec/asic/AIC-6250_1988.pdf` → `doc/aic6250.txt`
(extraída con `pdftotext -layout`).

### 8.1 El bug: el contador de bytes de DMA es de 24 bits, MAME lo trata como 32

La hoja de datos es explícita: *"24-Bit DMA Byte Counter"*, *"The 24-bit counter allows data
transfers up to 16 Mbytes without a DMA wrap"* (registros 00-02). Y sobre el bit de estado:
*"DMA BYTE COUNT ZERO: When this bit is found to be 1, the DMA Byte Count Registers
(Registers 00-02) are all zero"* (status register 0, bit 0).

En MAME, `m_dma_count` es un `u32` que:
- **nunca se inicializa** (solo aparece en `save_item`), y
- se carga byte a byte con máscaras que solo limpian su propio byte:
  `m_dma_count &= ~0x0000ff;` → **los bits 24-31 no se tocan jamás**.

Resultado: los 8 bits altos se quedan con lo que hubiera en la memoria recién reservada del
objeto. Traza del fallo (`log-cf1.log`), con un comando SCSI de 6 bytes:

```
[:aic6250] dma_cntrl_w 0x03
[:aic6250] dma transfer from memory, count 1392508934      ← 0x53000006
```

`0x53000006`: los 24 bits bajos son 6 (correcto), el `0x53` de arriba es basura. Como el
contador nunca llega a cero, el bit DMA BYTE COUNT ZERO no se enciende nunca y la
transferencia no termina → el diagnóstico de arranque del IOP del Rx2030 aborta con
`SCSI Test...: SCSI Power Up Failure: dma count 0 bit invalid`. Que la basura varíe entre
ejecuciones es justo lo que producía la **intermitencia ~50 %**.

**Fix** (`aic6250.h.diff` + parte de `aic6250.cpp.diff`): máscaras de 24 bits en los tres
setters y `m_dma_count = 0` en `device_start()`.

**Verificación**: 8 arranques seguidos de `rc2030`, capturas **byte a byte idénticas**
(md5 `71fad366835c463435e892eee633c4b9`), todas con `SCSI Test...Passed` y monitor. Antes:
~50 % de fallos. Sin regresión: RISC/os 4.52 sigue arrancando a `exedra Console login:`.

### 8.2 Segundo parche: las condiciones de transferencia del datasheet

`DMA TRANSFER - ASYNCHRONOUS SCSI`, iniciador: el chip activa ACK cuando **la fase coincide
con la esperada, REQ está activo, el contador no es cero y la FIFO no está llena/vacía**;
además *"the AIC-6250 will stop the memory prefetch when the number of bytes in the FIFO, plus
the number of bytes already transferred on the SCSI bus, sums to the total transfer length"*.

MAME solo comprobaba la FIFO (su propio `FIXME` lo decía) y hacía prefetch hasta llenar la
FIFO o bajar de 8 bytes. Parcheado en `DMA_IN`/`DMA_OUT` y en `back_w`. No cambia el
comportamiento observado, pero elimina violaciones de protocolo latentes (ACK antes de REQ,
bytes sobrantes de un prefetch anterior) y es lo que dice la hoja de datos.

### 8.3 Lo que sigue fallando
Con ambos parches, el kernel de EP/IX sigue en su bucle: `SCSI0 0x0200` → `UART0 0x0003`
(mensaje de error) → reintento → y finalmente `SCSI0 0x0205` (reset de bus, que es el
`scsi: attention: bus reset for operation timeout` de la consola).

Dato nuevo y útil: **RISC/os usa exactamente los mismos códigos de IOCB** (0x0200 11 899
veces, más 0x0100 y 0x0500) y funciona. O sea que la diferencia no está en el código de
comando sino en **los parámetros del IOCB** (CDB, dirección de búfer, longitud).

Siguiente paso concreto: ampliar el log de IOCB de `mips_i2000.cpp` para volcar el bloque de
parámetros de cada IOCB de SCSI (CDB + dirección + longitud) y comparar RISC/os contra EP/IX.
Es instrumentación de bajo volumen — la traza completa del AIC-6250 no sirve: genera cientos
de MB porque registra cada byte y cada transición REQ/ACK del bus.

## 9. Volcado y comparación de los IOCB

Parche `patch-iocb-params.py` sobre `mips_i2000.cpp`: para los IOCB de SCSI (índices 7..14)
vuelca los 32 bytes del bloque de parámetros además del código de comando. Bajo volumen, a
diferencia de trazar el AIC-6250.

Estructura deducida (little-endian, la del V50):

| offset | contenido |
|---|---|
| 0-1 | tipo/flags de petición |
| 2-3 | comando (0x0200 en todos los casos) |
| 4-7 | puntero (no es una dirección de RAM legible: volcarla da ceros) |
| 8-11 | longitud de la transferencia |
| 12.. | lista de números de página (para la MMU del IOP) |

Comparación **dentro del mismo arranque**:

```
sash → SCSI1 (FUNCIONA, carga el kernel de 1,8 MB)
  04 00 | 00 02 | a4 07 3c 00 | 00 20 00 00 | 20 03 00 00 | 21 03 00 00 | 22 03 00 00 | 00...
  tipo=4  cmd=0x0200  ptr=0x3c07a4  len=0x2000 (8192)  paginas: 0x320 0x321 0x322

kernel EP/IX → SCSI0 (FALLA, bucle de reintento)
  00 00 | 00 02 | 80 05 3c 00 | 18 00 00 00 | 9c 09 00 00 | 00 00 00 00 | ...
  tipo=0  cmd=0x0200  ptr=0x3c0580  len=0x18 (24)  paginas: 0x99c
```

Longitudes del kernel en peticiones sucesivas: 0x14, 0x18, 0x1c, 0x20, 0x24 (20, 24, 28, 32,
36 bytes) — transferencias pequeñas y variables, no lecturas de bloques de disco.

**La diferencia está en el campo tipo (bytes 0-1): 4 en las que funcionan, 0 en las que
fallan.** El código de comando es idéntico en ambas.

## 10. El transporte SCSI está bien — prueba definitiva

Ejecutado en sash el paso literal de las release notes, que **lee de la unidad 1 y escribe en
la unidad 0**:

```
sash: cp -b 16k dksd(,1,2)epix2.1.1/1/miniroot dksd(,,1)
..........................................................
19922944 (0x1300000) bytes copied
sash:
```

**19,9 MB copiados sin un solo error**, en las dos unidades, a través del IOP y del AIC-6250
parcheado. Y después la secuencia completa del manual (sash → cp → `boot -f
dksd(,1,2)epix2.1.1/1/unix.i2000_std root=sdc0d0s1`) vuelve a terminar en el mismo bucle de
reintento del kernel.

Conclusión: **no es el disco, ni el volume header sintetizado, ni el miniroot, ni el
transporte SCSI**. Es cómo el kernel de EP/IX formula la petición (tipo 0) frente a cómo la
formula el firmware del PROM (tipo 4).

Siguiente paso natural: desensamblar el manejador de IOCB de SCSI en el firmware del IOP
(el V50 de `rs2030.zip`, mapeado en 0x80000-0xbffff del espacio del IOP) para ver qué hace
con el campo de tipo, igual que se hizo con el 6509 en el proyecto CBM-II. Alternativa: mirar
el driver SCSI de EP/IX en el propio medio (`unix.i2000_std` no está stripped) y ver qué
estructura rellena.

## 11. Desensamblado del kernel (`unix.i2000_std`)

`unix.i2000_std` es MIPSEB ECOFF **sin strip**: 5296 símbolos externos. `ecoff.py` parsea la
cabecera simbólica (HDRR, magic 0x7009) y desensambla con capstone (MIPS32 big-endian).
Secciones: `.text` 0x80050000 (1 604 464 B), `.rdata` 0x801d7b70, `.data` 0x801db550,
`.sdata` 0x8020b080, `.bss` 0x8020ec90. `$gp = 0x80213070`.

Comandos: `ecoff.py sections | syms <regex> | which <hex> | xrefs <sym> | dis <sym> [n] |
disat <hex> [n]`.

### 11.1 La ABI del IOP, desde el propio kernel
`iopb` (0x8020ead8) es una tabla de 24 entradas de 16 bytes. Del desensamblado de
`iop_poke`, `iop_wait` e `iop_setbuf`:

| offset | campo | quién lo toca |
|---|---|---|
| +0x0 | parámetro de comando | `iop_poke`: `sw $a2, ($s0)` |
| +0x4 | resultado | `iop_wait`: `lw $t7, 4($s0)` → lo devuelve al llamador |
| +0x8 | semáforo de comando (halfword) | `iop_poke`: `sh 0xff, 8($s0)` |
| +0xa | **semáforo de respuesta** (halfword) | `iop_wait`: lo sondea |
| +0xc | puntero al búfer | `iop_setbuf`: `sw $a1, 0xc($t9)` |

`iop_poke(idx, modo, cmdparam, chan)`: valida idx<24, espera a que se libere el semáforo de
comando (modo 1 = no bloquea, 3 = spin, otro = `sleep`), escribe el cmdparam, pone el semáforo
a 0xff, **espera el bit 0x40 de `0xa2000003`** y escribe un 4 ahí (el timbre).
`cmdparam = (dirección física del bloque) − 0x1000`, que es exactamente como lo decodifica MAME.

### 11.2 Qué es `0x8017070C`
`ecoff.py which 8017070C` → **`iop_poke+0x180`**, y la instrucción es literalmente:

```
80170708  jal   0x8016fe38   <ssplx>
8017070c  sb    $t7, 3($t9)        ; $t7 = 4, $t9 = 0xa2000000  → toca el timbre
```

Es decir, **el kernel toca el timbre del IOP correctamente**. Lo que nunca ocurre es que el
IOP ponga el semáforo de respuesta en +0xa.

### 11.3 Quién falla
`ecoff.py xrefs iop_poke` → el único llamador SCSI es **`isdedtinit`** (0x80178204), el probe de
dispositivos del driver `isd` (el de bajo nivel del i2000: `isdopen/isdstrategy/isdintr/
isd_low_scsi/isd_syncmode/isd_newproms/isd_un/isd_tab`). El probe hace:

```
addiu $a0, 7            ; IOCB 7 = SCSI0
jal   iop_alloc         ; reserva 0x60 bytes de área compartida
sb    $t1, ($v0)        ; byte 0 = codigo de comando
sw    $t2, 8($v0)       ; longitud/flags
and   $s0, $s7, 0x1fffffff ; KSEG0 → física
addiu $s0, $s0, -0x1000    ; → cmdparam
jal   iop_poke
```

y **justo después arma un watchdog**:

```
801787fc  lw   $t5, -0x5778($gp)   ; isd_newproms
8017883c  jal  0x8007a070 <timeout>
80178848  sw   $v0, 0x28($s0)      ; guarda el id del timeout
```

Ese `timeout()` es el que produce el `SCSI 0L0: POLLED timeout` y dispara el reintento. El bucle
observado es exactamente: poke → nadie responde → watchdog → mensaje → reintento.

### 11.4 La forma de la petición
El byte 3 del bloque de comando es un **campo de flags por bits**, puesto condicionalmente:

```
80178790  andi $v0, $v0, 0x20      ; bit de capacidad del dispositivo
80178794  beqz $v0, 0x801787c0
8017879c  lw   $t8, ($s1)
801787a4  ori  $t9, $t8, 4         ; bit 2 en una palabra de estado
801787ac  lbu  $t0, 3($s2)
801787b4  ori  $t1, $t0, 1         ; bit 0 en el byte de flags del comando
801787bc  sb   $t1, 3($s2)
```

Descartado que venga del INQUIRY del disco emulado: en `src/devices/bus/nscsi/hd.cpp` el byte 7
de la respuesta (sync/wide/linked/cmdque) **nunca se rellena**, queda a 0.

Las longitudes de las peticiones que fallan (20, 24, 28, 32, **36**) son tamaños de respuesta de
probe — 36 es la longitud estándar de un INQUIRY. O sea: **el kernel se queda atascado
sondeando los dispositivos**, antes de leer un solo bloque de datos.

### 11.5 Lo que queda
El siguiente eslabón es el **firmware del IOP** (V50, ROM de `rs2030.zip` mapeada en
0x80000-0xbffff del espacio del IOP): hay que ver por qué su manejador de IOCB de SCSI atiende
los comandos del PROM (código 1 y 2 con flags 4) y no completa los del kernel (código 2 con
flags 0). Ahora está bien acotado: se sabe qué campos mirar (+0/+4/+8/+0xa/+0xc de la entrada
IOCB, y el bloque en `0x1000 + cmdparam`) y qué comandos comparar.

## 12. Desensamblado del firmware del IOP (NEC V50)

`mkiop.py` reconstruye la imagen de 256 KB desde las cuatro PROM con el entrelazado de
`ROM_START(i2000)`: u139/u140 = bytes par/impar de la mitad baja, u142/u141 = par/impar de la
alta. Se mapea en 0x80000-0xbffff con espejo en 0xc0000-0xfffff. Vector de reset en
rom 0x3fff0 = `jmp far 0xec00:0x0010`; el arranque pone **DS = ES = SS = 0** (la RAM del IOP)
y copia sus datos a RAM. Desensamblador: `iopdis.py` (capstone x86 16 bits).

### 12.1 ★ Quién imprime el error
El kernel de EP/IX contiene `POLLED time out` (dos palabras) y el firmware del IOP
`SCSI %dL%d: POLLED timeout` (una palabra, rom 0x26371). **En pantalla sale la de una
palabra** ⇒ quien reporta el fallo es **el firmware del IOP**, no EP/IX. Es decir: el IOP
recibe el comando, intenta la operación y se rinde él.

### 12.2 Las rutinas de acceso al chip
Buscando `mov dx,0x80` / `mov dx,0x82` (los puertos del AIC-6250 en `iop_io_map`) aparecen
las dos primitivas:

```
f7623  aic_read(reg):   mov ax,[bp+4]; mov dx,0x80; out dx,al; mov dx,0x82; in al,dx; ret
f7637  aic_write(reg,v): mov ax,[bp+4]; mov dx,0x80; out dx,al; mov ax,[bp+6]; ...
```

`iopcalls.py` encuentra 34 llamadas a la primera y 95 a la segunda, todas entre 0xf4100 y
0xf6c90: ese es el driver SCSI del firmware.

### 12.3 ★★ El bucle que se rinde — y por qué sash sí funciona
```
f69e3  mov ax,9  ; call aic_read     ; registro 9 = SCSI signal
f69ed  test al,2                     ; bit 1 = REQ
f69f1  mov ax,0xf; call aic_read     ; registro 0x0f = SCSI LATCH DATA  ← dato byte a byte
f6a12  or  byte [0x4441],0x80        ; bit 7 del control register 1 ...
f6a1d  mov ax,8  ; call aic_write    ; ... = R08W_AUTO_SCSI_PIO_REQ    ← ¡PIO AUTOMÁTICO!
...
f6aac  mov ax,8  ; call aic_read     ; registro 8 = STATUS REGISTER 1
f6ab6  test al,8                     ; bit 3 = COMMAND DONE
f6aa1  cmp word [bp-6],0x32          ; contadores de reintento 0x32 / 0x3e8
```

**El firmware atiende estas peticiones con el modo Auto PIO del chip** (byte a byte por el
registro 0x0f, sondeando Command Done), no con DMA. Y ahí está la asimetría que llevábamos
toda la sesión persiguiendo: **las lecturas masivas de sash usan la ruta DMA (que funciona) y
las peticiones del kernel usan la ruta Auto PIO**, que en el modelo de MAME es la menos
desarrollada (su único comentario es `// TODO: test expected phase`).

### 12.4 Comprobado en ejecución
Instrumentando **solo** los estados Auto PIO (`patch-autopio-log.py`, volumen mínimo frente a
LOG_STATE, que imprime una línea por byte de cada DMA y genera cientos de MB), la traza
confirma la correspondencia una a una:

```
[:] iocb SCSI0 command 0x0200 param 0x234: ... (':cpu' (8017070C))
[:aic6250] AUTOPIO start (dma_cntrl 0x00)
[:aic6250] AUTOPIO req seen, in
[:aic6250] AUTOPIO in 0x02
[:aic6250] AUTOPIO done
```

4120 transferencias Auto PIO en la corrida. La ruta **sí completa** cada byte (start → req →
in → done), pero **lo que se lee son ceros** (`AUTOPIO in 0x00`, alguno `0x02`) y sólo salen
un par de bytes por comando, todos en dirección *in* — nunca *out*, o sea que el CDB no llega
a enviarse por esta vía.

### 12.5 Siguiente paso
Añadir la **fase del bus SCSI** a esas líneas de traza (una línea más en `AUTO_PIO_IN/OUT`) y
comparar con una operación buena de sash: hay que ver en qué fase se están leyendo esos ceros
y por qué la secuencia no avanza a mandar el CDB. El `// TODO: test expected phase` de
`case AUTO_PIO:` es el sospechoso natural — MAME no comprueba que la fase coincida con la
esperada antes de hacer el handshake.

## 13. ★★★ EL MINIROOT DE EP/IX ARRANCA

### 13.1 La traza con fase: los comandos del kernel **sí funcionan**
Añadiendo la fase del bus a la traza (`patch-phase-log.py`), un comando bueno de sash se ve así:

```
DMA start from memory count 6 bus COMMAND expect COMMAND    ← CDB
DMA out done bus DATA IN expect COMMAND
DMA start to memory count 36 bus DATA IN expect DATA IN     ← datos
DMA in done bus STATUS expect DATA IN
AUTOPIO ... bus STATUS expect STATUS      in 0x00           ← estado GOOD
AUTOPIO ... bus MESSAGE IN expect MESSAGE IN  in 0x00       ← comando completo
```

y **los del kernel son idénticos**: mismas fases, `bus == expect` siempre, estado 0x00. O sea
que la hipótesis del Auto PIO roto era falsa: la ruta funciona.

### 13.2 Dónde se rompe de verdad
Contando peticiones: **16 atendidas por el chip, 28 sin ninguna actividad del chip**. La
transición es exacta:

```
8576: DMA start from memory count 6 bus COMMAND expect COMMAND
8577: DMA out done bus STATUS expect COMMAND       ← salta a STATUS sin fase de datos
8580: AUTOPIO in 0x02 bus STATUS expect STATUS     ← ★ estado 0x02 = CHECK CONDITION
...a partir de aquí el IOP no vuelve a tocar el chip para esa unidad
```

Y lo que se repetía en el log no eran peticiones nuevas: era **el mismo IOCB atascado** con su
semáforo sin limpiar, re-registrado cada vez que el kernel tocaba el timbre para otra cosa
(imprimir por UART0).

### 13.3 El comando culpable
Registrando los bytes que salen en fase COMMAND (`patch-cdb-log.py`):

```
x5  status=0x00  CDB 00 00 00 00 00 00   TEST UNIT READY
x1  status=0x00  CDB 12 01 80 00 10 00   INQUIRY EVPD pagina 0x80
x1  status=0x02  CDB 1a 00 38 00 1c 00   MODE SENSE(6) pagina 0x38  ← RECHAZADO
```

`0x1a` = MODE SENSE(6), **página 0x38** (la página de caché del Common Command Set),
longitud 28. `src/devices/bus/nscsi/hd.cpp` implementa las páginas 00, 01, 02, 03, 04, 08 y
30; la 0x38 cae en `default: fail = true` → `scsi_status_complete(SS_CHECK_CONDITION)`.
La cuenta cuadra exacta: cabecera 4 + descriptor de bloque 8 + página de 16 = **28**, o sea
que el driver espera una página 0x38 con longitud 14.

### 13.4 El fix y el resultado
`hd.cpp.diff`: añadir el `case 0x38` con longitud de página 0x0e. Con eso:

```
Total real memory  = 16777216
start I/O probe
I/O probe complete                        ← el probe COMPLETA
Root on dev 0x840001, Dump on dev 0x840001
Root fstype ffs                           ← raíz montada (el miniroot en swap)
New swplo: 38912  swap size: 344K bytes
Miniroot run level 1                      ← ★★ EL MINIROOT ARRANCA
erase=^W, kill=^U, interrupt=^C           ← ★★★ su .profile, shell listo
```

9 215 comandos SCSI completos en la corrida: **8 185 WRITE(6) y 1 000 READ(6)** además del
probe. EP/IX 2.1.1 está haciendo E/S de disco de verdad.

Detalle del rig: en `rc2030` MAME solo conecta terminal a `tty1`; la consola del kernel sale
por el otro puerto, así que hay que arrancar con **`-tty0 terminal`** y capturar las dos
pantallas (`type2.lua` ya itera `manager.machine.screens`).

### 13.5 Siguiente paso
Teclear `inst` en el shell del miniroot: es el instalador, con `Pkg=/epix2.1.1` montado desde
la distribución y `Pkgroot=/mnt` sobre el disco destino, seleccionando los subpaquetes
`rs2030` + `usr` + `bsd43` + `cmplrs`.

## 14. ★★★ EL INSTALADOR `inst` CORRE

### 14.1 rs2030 también arranca
Con el fix de la página 0x38, **`rs2030` arranca igual de bien que `rc2030`**: el bloqueo de
esa máquina era el mismo problema de SCSI, no el registro gráfico sin implementar de
`0x01ff1000` (esa escritura es benigna). Y es la máquina buena para trabajar, porque la consola
del kernel sale en la pantalla gráfica y el teclado ya funciona:

```
Miniroot run level 1
erase=^H, kill=^U, interrupt=^C
#
```

En `rc2030` la consola del kernel y el teclado quedan en puertos serie distintos
(`natkeyboard` se ata a `:tty0:terminal:keyboard` y el kernel imprime en el otro), así que
tecleando no se llega al shell — por eso conviene usar `rs2030`.

### 14.2 La receta de instalación
De las release notes (§ del CD-ROM), adaptando el dispositivo a nuestra unidad 1:

```
# From=cd
# CDpath=sdc0d1s2          (por defecto seria sdc0d2s2)
# Product=epix2.1.1
# inst
```

`inst` monta él solo la distribución en `/relroot`; no hace falta `mount` a mano. El nodo
`/dev/dsk/sdc0d1s2` ya existe en el miniroot.

### 14.3 El diálogo, hasta donde va
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
Is this correct (y n) [y]?                ← aquí va ahora
```

Secuencia de tecleo que reproduce lo anterior (tiempos emulados, `rs2030`):
```
45:boot -f dksd(,1,8)sash2
110:boot -f dksd(,1,2)epix2.1.1/1/unix.i2000_std root=sdc0d0s1
420:From=cd   430:CDpath=sdc0d1s2   440:Product=epix2.1.1   455:inst
600:<CR>      660:y                 1040:y
```

### 14.4 Coste de iteración
Cada respuesta nueva obliga a repetir el arranque entero (~10 min de reloj: PROM, sash, kernel,
miniroot, y volver a recorrer el diálogo). Para seguir conviene o bien acumular respuestas por
lotes en `CMDS`, o bien probar un savestate de MAME justo tras el prompt del miniroot.

## 15. ★★★ LA INSTALACIÓN CORRE: mkfs, fsck y extracción de paquetes

Diálogo completo recorrido (todos los tiempos son segundos emulados en `rs2030`):

| t | respuesta | pregunta |
|---|---|---|
| 600 | `<CR>` | Local package root [/relroot]? |
| 660 | `y` | Is the information above correct? |
| 1040 | `y` | Install ALL subpackages (y n) [n]? |
| 1120 | `y` | timezone CST6CDT correcta? |
| 1145 | `y` | reloj correcto? |
| 1170 | `y` | instalar sash en el volume header? |
| 1750 | `6` | ¿en qué partición va /usr? (951 MB) |
| 1830 | `y` | **Initialize filesystems (y n) [y]?** |
| 1900+ | `<CR>`×6 | aceptar los valores por defecto siguientes |

**Aviso importante**: tras elegir la partición de `/usr` la pregunta NO es la del swap que
muestra el transcript de las release notes (ese es un *update*), sino
**`Initialize filesystems (y n) [y]?`**. Contestar `n` ahí (mi primer intento) hace que el
montaje falle con `Couldn't mount /dev/root: Invalid argument` e `inst` aborta ordenadamente
al shell — sin dañar nada, pero hay que repetir.

Con `y`, la instalación hace el trabajo de verdad:

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

`mkfs.ffs` + `fsck` sobre el disco destino y extracción de los subpaquetes, **incluido
`rc2030`** (el kernel y los devices de nuestra máquina) y `cmplrs` (el compilador C).

La extracción de los ~30 subpaquetes no cabe en una corrida corta: hay que lanzar con
`SNAP_UNTIL` grande (≥14000 s emulados, ~1 h de reloj) para que termine de una vez, porque
cortar a mitad deja el disco a medias y obliga a repetir `inst` desde el principio.

## 16. ★★★ PROYECTO COMPLETO — EP/IX 2.1.1 instalado, autónomo y con prompt limpio

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

### 16.1 Hacerlo autónomo
La instalación dejó todo menos el kernel (`comply: missing file: unix.i2000_std`). Se resuelve
desde dentro del propio sistema, sin repetir el `inst` de 5 horas:

```
epix # mount -r /dev/dsk/sdc0d1s2 /mnt
epix # cp /mnt/epix2.1.1/1/unix.i2000_std /unix.i2000_std
epix # ln /unix.i2000_std /unix
epix # ls -l /unix /unix.i2000_std
-rw-r--r--   2 root  other  4550656 Aug 23 04:10 /unix
-rw-r--r--   2 root  other  4550656 Aug 23 04:10 /unix.i2000_std
epix # umount /mnt ; sync
```

Y a partir de ahí arranca **solo con su disco**, sin la distribución:

```
>> boot                          (carga el sash que inst puso en el volume header)
sash: boot -f dksd(,0,0)unix     (el kernel instalado, particion 0)
```

### 16.2 Prompt limpio (desactivar rpc.mountd)
El diluvio de `mountd: couldn't register MOUNTPROG` al arrancar es NFS sin red; init lo
reintenta, se rinde con *"Command is respawning too rapidly"* y deja el ruido en pantalla.
Se quita poniendo la acción del inittab en `off`:

```
epix # cp /etc/inittab /etc/inittab.orig
epix # sed s\|respawn:/usr/etc/rpc.mountd\|off:/usr/etc/rpc.mountd\| /etc/inittab.orig > /etc/inittab
epix # grep mountd /etc/inittab
m2:234:off:/usr/etc/rpc.mountd -f `sed -n 1p /etc/rpc.mountd.conf`
epix # init q
```

Resultado: `OSI daemons:.` → `The system is ready.` → login, sin una sola línea de MOUNTPROG.

**Gotcha de tecleo**: pasar comillas por el teclado emulado es incómodo; usar `sed` con
delimitador `|` **escapado con backslash** (`s\|a\|b\|`) evita las comillas por completo.
Script listo: `rig/clean.sh`.

### Ficheros
- `hd.cpp.diff` — MODE SENSE página 0x38 (+ `hd.cpp.pristine`)
- `patch-phase-log.py`, `patch-cdb-log.py`, `cdbstats.py` — la instrumentación de esta fase
- `mkiop.py` — reconstruye la ROM del IOP; `iopdis.py` — desensamblador x86-16;
  `iopcalls.py` — busca llamadas cercanas; `iopref.py` — busca referencias a cadenas
- `patch-autopio-log.py` — instrumenta solo la ruta Auto PIO
- `ecoff.py` — parser ECOFF + desensamblador MIPS (necesita `pip3 install capstone`)
- `aic6250.h.diff`, `aic6250.cpp.diff` — los parches contra MAME 0.288
- `aic6250.h.pristine`, `aic6250.cpp.pristine` — originales para revertir
- `patch-aic6250.py`, `patch-aic6250-count.py` — aplican los parches (idempotentes, fallan si
  el bloque no coincide)
- `doc/aic6250.txt` — hoja de datos en texto
- `rig/selftest.sh` — mide la tasa de éxito del autotest SCSI (N arranques cortos + md5)
- `rig/catchfail.sh` — repite arranques hasta capturar una traza del fallo

## Herramientas escritas en esta sesión (en `<path>\epix\`)
- `vh.py` — parsea el volume header SGI y la tabla de particiones
- `ffs.py` — lector de solo lectura de FFS 4.2BSD big-endian: `ls`, `tree`, `cat`, `get`, `extract`
- `fs.py` — localiza superbloques FFS en las particiones
- `extract_vh.sh`, `getkernels.sh` — extraen standalone programs y kernels a `epix/vh/` y `epix/boot/`

Gotcha WSL: llamar a `wsl -d Ubuntu-22.04 -- bash -lc '...'` desde Git Bash destroza las rutas
`/mnt/...`; usar **ficheros de script** y prefijar `MSYS_NO_PATHCONV=1`.
