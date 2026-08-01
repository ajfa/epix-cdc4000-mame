# Notas del proyecto: EP/IX 2.1.1 en MAME

Resumen de lo que costó llegar aquí, por si hay que rehacerlo o depurar algo.

## El medio

`CDC EP-IX 2.11.7z` contiene `cdc_epix_2.1.1.iso`, que **no es un ISO9660**:
es una imagen de disco con cabecera de volumen SGI/MIPS (magic `0x0BE5A941`).
La partición 2 (bloque 9880, 568 MB) es un FFS big-endian montado como
`/usr/netinstall`, con la distribución completa: kernels de toda la gama CDC
4000 (`unix.i2000_std` para RC2030/RS2030, `unix.r3030_std`, `unix.r6000_std`…),
`sash.2030`, un `miniroot` de 19,9 MB, compilador C, utilidades BSD 4.3 y SVR4.

El `pkginfo` declara `subpackage=rc2030/rs2030` como objetivo de primera clase,
que es justo la máquina que MAME emula sin marcas de "no funciona".

## Arranque e instalación

Receta de las release notes del propio EP/IX, adaptada a nuestra unidad:

```
>> boot -f dksd(,1,8)sash2
sash: cp -b 16k dksd(,1,2)epix2.1.1/1/miniroot dksd(,,1)
sash: boot -f dksd(,1,2)epix2.1.1/1/unix.i2000_std root=sdc0d0s1
# From=cd
# CDpath=sdc0d1s2
# Product=epix2.1.1
# inst
```

Respuestas del instalador, en orden: `<CR>` (raíz del paquete), `y` (info
correcta), `y` (instalar todos los subpaquetes), `y` (zona horaria), `y`
(reloj), `y` (sash a la cabecera de volumen), `6` (partición de `/usr`),
**`y` (inicializar filesystems)**, y `<CR>` para el resto.

⚠ Tras elegir la partición de `/usr` la pregunta **no** es la del swap que
muestra el transcript de las release notes (ese es de una instalación *update*),
sino `Initialize filesystems (y n) [y]?`. Contestar `n` ahí hace que falle el
montaje y `inst` aborta.

La extracción de los ~30 subpaquetes tarda unas 5 horas de reloj: corre a ~0,78x
tiempo real, muy por debajo del ~250% de las fases ligeras.

## Después de instalar

`comply` avisa de que falta `/unix`: el kernel no se copia solo. Se arregla
desde dentro del sistema ya arrancado, sin repetir la instalación:

```
epix # mount -r /dev/dsk/sdc0d1s2 /mnt
epix # cp /mnt/epix2.1.1/1/unix.i2000_std /unix.i2000_std
epix # ln /unix.i2000_std /unix
epix # umount /mnt ; sync
```

Y para un arranque sin ruido de NFS (`mountd: couldn't register MOUNTPROG`):

```
epix # cp /etc/inittab /etc/inittab.orig
epix # sed s\|respawn:/usr/etc/rpc.mountd\|off:/usr/etc/rpc.mountd\| /etc/inittab.orig > /etc/inittab
epix # init q
```

(el `sed` usa `|` escapado con backslash como delimitador para no necesitar
comillas, que son incómodas de teclear a través del teclado emulado).

## rc2030 frente a rs2030

Las dos arrancan. `rs2030` es la cómoda: la consola del kernel sale en la
pantalla gráfica y el teclado AT funciona. En `rc2030` la consola del kernel y
el teclado quedan en puertos serie distintos (MAME ata el teclado natural a
`:tty0:terminal:keyboard` y el kernel imprime por el otro), así que no se puede
teclear al shell sin enredar.

## Herramientas incluidas (`tools/`)

- `mkdisks.sh`, `mktarget.py` — crean los CHD y preparan el disco destino
  (cabecera de volumen + miniroot en la partición de swap).
- `ffs.py` — lector de solo lectura de FFS 4.2BSD big-endian: `ls`, `tree`,
  `cat`, `get`, `extract`. Sirve para mirar dentro de las imágenes sin montarlas.
- `vh.py`, `chdinfo.py`, `fsfree.py` — cabecera de volumen SGI, cabecera CHD y
  espacio libre de los filesystems.
- `ecoff.py` — parser de la tabla de símbolos ECOFF MIPS + desensamblador
  (necesita `pip3 install capstone`). Con esto se localizó `iop_poke` y la ABI
  de IOCBs del kernel.
- `mkiop.py`, `iopdis.py`, `iopcalls.py` — reconstruyen la ROM del IOP (NEC V50)
  desde las cuatro PROM y la desensamblan; así se encontró que el firmware
  atiende las peticiones con el modo Auto PIO del AIC-6250.
- `patch-*.py` — los parches de MAME, incluidos los de instrumentación que se
  usaron para depurar (volcado de IOCBs, trazas de fase del bus SCSI, CDB).
