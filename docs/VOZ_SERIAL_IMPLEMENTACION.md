# Implementación serial con archivos reversibles

2026-10-07. Materializa el [protocolo congelado](VOZ_NOTA_LARGA_ARCHIVO_PROTOCOLO.md).
No modifica helpers, controles, exports o recibos históricos. La preparación
del productor no significa que el banco eléctrico ya se haya ejecutado.

## Producción y recursos

`tools/voice_serial_long.py --preflight N` conserva un nuevo recibo numerado.
Rechaza sobrescribir intentos anteriores. Recalcula presupuesto desde los
controles admitidos; el primer codec que cabe en orden gzip9→XZ6/CRC64 queda
seleccionado. El margen sigue en 2 GiB, y las densidades siguen siendo estimaciones.

Con `--run`, requiere además QA serial admitida y espacio actual suficiente
para el codec elegido. Usa el runner binario congelado y su carpeta nueva
`active-six-binary-long01`, inicialmente inexistente. No reubica históricos.
Orden: Gear500, Gear250, Gear125, Trap125; 7200 s por proceso, desde DC propio.
Antes de cada escena suma archivos futuros, el mayor intermedio pendiente y
el margen. Los archivos ya retenidos consumen disponibilidad actual: no se
cuentan otra vez como escrituras futuras. Un rechazo eléctrico no cancela
las escenas independientes. Un fallo de almacenamiento detiene producción
y conserva los artefactos; faltas de recursos dejan escenas pendientes.

## Archivo y restauración

`tools/voice_serial_archive.py` admite cuatro nombres de escena y sufijos
exactos dentro de una carpeta directa. Rechaza redirecciones, links y
archivos con hardlinks. Cada archivo nuevo se coteja con su recibo original,
se comprime a una ruta exclusiva y se restaura por streaming hasta EOF.
SHA256 y tamaño deben coincidir. Antes de retirar el raw nuevo se registra
el manifiesto y se verifican de nuevo las identidades. Sólo se retira esa
ruta exacta; se conservan deck, log, recibo y contenedor. No se barre una carpeta.

La restauración usa la ruta raw original de esta campaña porque la auditoría
nativa congelada exige esa ruta. Nunca sobrescribe un raw existente. Controla
el tamaño descomprimido durante la lectura; sólo tras verificar identidad
entrega el archivo al consumidor. El array nativo tiene buffer propio.
Cuando termina correctamente la observación, vuelve a verificar identidades
y retira el temporal. Error de decode, consumidor o cambio de datos lo
conserva para diagnóstico y bloquea otro intento sobre la misma ruta.

Si hay una interrupción entre retiro y manifiesto final, la identidad de
archivo sigue disponible en el contenedor pero el manifiesto no está admitido.
No se reanuda silenciosamente: se conserva el intento y debe registrarse su
recuperación explícita. Los recibos originales no se reescriben para indicar
la representación archivada; el manifiesto aporta ese vínculo.

## Observación y alcance

Se restaura una escena por vez y se audita su comando, fuentes, runtime,
flags, reloj y export con `run_identity`. Después se aplican medidas y tres
contrastes largos congelados. Para una pareja, se libera el temporal izquierdo
antes de restaurar el derecho; ambos arrays propios pueden coexistir en RAM.
Se verifica espacio de restauración antes de observar el banco.

Sólo cuatro coberturas completas, tres contrastes medidos/admitidos y balances
admitidos, sin errores de recursos/archivo, permiten admisión local. Un aborto
del solver se conserva archivado pero no completa ventanas; una escena no
ejecutada por recursos no es un fallo eléctrico. Un intento sin recibo final
conserva hashes de artefactos y marca el inicio de proceso como desconocido.
No se adjudican solves nuevos a esa ambigüedad como si estuvieran confirmados.

El control de almacenamiento copia exports ya medidos a una campaña nueva,
archiva/retira sólo esas copias y verifica restauración completa. Los originales
quedan intactos. No añade solves, audio, fidelidad física o admisión RT.
