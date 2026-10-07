# Export nativo y archivo reversible: resultados

2026-10-07. Ejecución del [control binario previsto](VOZ_NOTA_LARGA_EXPORT_BINARIO_PROTOCOLO.md)
y de la [preparación de archivo serial](VOZ_NOTA_LARGA_ARCHIVO_PROTOCOLO.md).

## Control eléctrico y de representación

Una ejecución nueva de build11, seis correcciones activas, Gear2/500 ns,
desde DC propio, completa 40 ms con **191714 filas y 19 columnas**:
reloj y dieciocho voltajes. Sólo se añade el export binario después del
ASCII; la auditoría reproduce la reversibilidad de ese cambio y las
identidades de fuentes, ejecutable, runtime y ausencia de observadores.

El [control](../evidence/voice_native_control01.json) conserva la misma
trayectoria ASCII del banco corto: **cero diferencias de bits**. El binario
restaurado coincide con ese ASCII en los **3642566 valores**, incluidos
ceros firmados, sin interpolar, diezmar ni redondear. Tiempo de laboratorio:
244,16 s. La [auditoría](../evidence/voice_native_control_validation01.json)
reproduce el control y el inventario compilado sin SPICE ni compilaciones nuevas.

| Representación del control completo | Bytes | Verificación |
| --- | ---: | --- |
| ASCII nuevo | 91448055 | Bits idénticos al ASCII corto anterior |
| Nativo binary64 | 29141351 | Bits idénticos al ASCII nuevo |
| gzip nivel 9 | 20473174 | SHA256/tamaño del archivo nativo restaurado idénticos |
| XZ preset 6, CRC64 | 16234580 | SHA256/tamaño del archivo nativo restaurado idénticos |

La cabecera nativa ocupa 823 bytes. El payload conserva orden, nombres,
unidades y 191714×19×8 bytes. El soporte de alias de **corrientes** se
prueba con fixtures sintéticos; este control vivo no exporta corrientes.
El lector sólo admite el ABI medido little endian/binary64 y un único
plot real Transient Analysis con reloj completo y estricto.

## Fallo de adaptación conservado y QA

El primer lector mantenía un `np.memmap` abierto y produjo dos errores
WinError 32 al limpiar fixtures en Windows. Se preservan el
[primer intento](../evidence/voice_native_parser_rejection01.json), con
snapshot exacto de fuentes y resumen observado, y el
[replay sin cambios](../evidence/voice_native_parser_rejection02.json),
con stdout/stderr completos. Ambos fallan 2/10; no son fallos del solver.

La reparación sustituye sólo la lectura por un buffer propio `np.fromfile`.
Se conservan los tests y gates. Diez regresiones cubren layout, unidades,
conteos, duplicados, truncamiento, bytes extra, reloj, finitud, ceros
firmados, un bit distinto y reversibilidad de los decks corto/largo.
Tres adicionales cubren ambos codecs, identidad errónea, truncamiento,
codec inválido y prohibición de sobrescribir o cambiar el original.

La [QA nativa](../evidence/voice_native_tests01.json) ejecuta diez y hereda
140 por identidad de entradas: 150 cubiertas. La
[QA de archivo](../evidence/voice_archive_tests01.json) ejecuta tres y
hereda esas 150: **153 cubiertas, 13 ejecutadas en este corte**. La herencia
no se presenta como ejecución nueva. Fuentes medidas y recibos anteriores
quedan congelados; las tres portadas de estado son las únicas actualizadas
entre las 250 entradas de la QA anterior.

## Recursos largos y siguiente frontera

El [preflight binario](../evidence/voice_binary_long_preflight01.json)
requiere 3846373308 bytes y observa 3600785408: **rechaza**.
La [preparación de archivo](../evidence/voice_archive_control01.json)
comprime el mismo control, conserva ambos originales y verifica todos
los bytes restaurados hasta EOF. Su
[auditoría independiente](../evidence/voice_archive_control_validation01.json)
reproduce identidad y aritmética. No se retira ningún archivo.

El presupuesto serial suma los cuatro archivos estimados, el mayor raw
intermedio y 2 GiB; incluye las dos representaciones al verificarlo.

| Codec | Requeridos | Disponibles al medir | Recursos |
| --- | ---: | ---: | --- |
| gzip9 | 3905525222 | 3565645824 | Rechazados |
| XZ6/CRC64 | 3658422626 | 3549667328 | Rechazados |

El mejor presupuesto queda **108755298 bytes** sobre la disponibilidad
registrada. Las densidades de compresión y filas×8,75 son estimaciones,
no cotas de escenas futuras. El espacio puede cambiar. No se inicia el
banco largo con seis: sigue **no medido**, no rechazado eléctricamente.
El runner paralelo conserva su preflight fallido y no constituye una
implementación del plan serial; su ejecución queda cerrada por ese gate.

Siguiente paso: disponibilidad suficiente y un preflight nuevo; materializar
el productor serial con recibos de archivo/restauración antes de las cuatro
escenas de 350 ms, ON 10 ms/OFF 200 ms, y sus tres contrastes originales.
Se mantienen build11, modelos, ventanas y gates. Este corte añade un solve
SPICE corto, cero compilaciones y cero solves largos. No genera audio nuevo
ni acredita fidelidad física o tiempo real.
