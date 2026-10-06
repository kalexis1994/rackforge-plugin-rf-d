# Export binario nativo: control antes de cambiar el banco largo

2026-10-06. Prospectivo; no hay todavía un export binario admitido.
Sólo se aplica si el banco corto de seis pasa y su preflight de cuatro
exports ASCII más 2 GiB rechaza por almacenamiento. Conserva el
[protocolo activo](VOZ_NOTA_LARGA_SEIS_ACTIVO_PROTOCOLO.md), los gates
eléctricos y temporales y los archivos históricos.

## Fuente y cambio de frontera

El árbol auditado de build11 contiene el writer nativo de ngspice-46:

| Fuente local privada | SHA256 | Función inspeccionada |
| --- | --- | --- |
| `src/frontend/postcoms.c` | `60bcc3b4bd6e2cc4203dc8bd4f3185b27d1376e321613ce89f6c84ee1887901c` | `com_write`, selección/copia de vectores y `filetype` |
| `src/frontend/rawfile.c` | `fa5d8625a5b4168d4f928af455f685a9a7edb0ef7999af2f18853e8bf5216840` | `raw_write`, cabecera y escritura de cada `double` |

La inspección muestra una escritura real por fila/vector, con escala
primera y tipos en cabecera. Esto propone una representación más pequeña;
su equivalencia con `wrdata` queda pendiente del control medido.
No recompilar ni modificar el ejecutable, solver, dispositivos o historia.

## Control positivo obligatorio

Después de auditar el banco corto, derivar su Gear2/500 ns de 40 ms con
ON 2 ms/OFF 25 ms. Mantener el deck por bytes hasta el export, incluido
DC, vectores, tolerancias e integración. Añadir después de `wrdata` un
`write` de los mismos vectores, con `set filetype=binary`. Cambiar sólo
rutas de export y esas instrucciones posteriores al transitorio.

Un único proceso activo build11, presupuesto 900 s, debe producir ambos
exports. Limpiar todos los flags de observación y exigir el anuncio de
seis; comprobar los mismos hashes de fuente/runtime antes/después.
Conservar recibo, log y ambos formatos, incluso ante rechazo.

Exigir conjuntamente:

1. ASCII completo y exactamente igual al Gear500 recién auditado,
   con todas sus filas, reloj y dieciocho vectores; no interpolar.
2. Binario restaurado con identidad **de bits binary64** frente a ese
   ASCII, incluidos ceros con signo, todas las filas y todas las columnas.
   El SHA de archivo puede diferir por la cabecera; registrar ambos.
3. Cabecera real de transitorio, conteos y unidades válidos, escala `time`
   única, nombres de vectores únicos y mapeo explícito al orden congelado.
   Admitir una envoltura de nombre de corriente sólo si se documenta y
   corresponde exactamente a una corriente solicitada.
4. Tamaño exacto de payload `filas × columnas × 8`, sin padding ambiguo,
   múltiples plots, complejos, datos truncados o bytes adicionales.
   Declarar ABI/endian del entorno medido; no atribuir portabilidad.
5. Rechazos sintéticos para nombre/conteo/unidad incorrectos, payload
   truncado/sobrante y reloj o valores no finitos. Auditar el parser y el
   control antes de que el formato sustituya ASCII en notas largas.

## Extensión condicionada y recursos

Sólo con ese control admitido, sustituir en los cuatro decks largos el
export ASCII por `set filetype=binary` y `write` de los vectores originales.
Revertir exactamente los cambios temporales y de export para comprobar
que los bytes eléctricos permanecen intactos. Usar un runner y recibos
nuevos; los anteriores conservan su formato y lectores.

Repetir el preflight con las filas medidas de los cuatro casos cortos,
ratio 8,75, tamaño binario por fila y cabecera observada, más 2 GiB.
Declarar estimaciones, no cotas, y los 7200 s por proceso. Conservar
aborto, timeout y export parcial. El parser entrega el mismo orden de
columnas a los helpers de carga/ventanas/contrastes congelados.
Se mantienen las cuatro coberturas, tres contrastes y todos los gates.

Esta adaptación cambia almacenamiento, no precisión de la simulación.
No reduce duración, vectores o muestreo; no borra evidencia para cumplir
el presupuesto. Audio sólo después de auditar las cuatro notas admitidas.
