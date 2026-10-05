# Corpus de continuación curva y manifiesto completo

El [protocolo](BIESTABLE_PREFIJO_CURVO_PROTOCOLO.md) y productor se fijan
en `0814518` antes de medir. Cada soporte tiene un archivo completo con
fuentes, historias reconstruidas, interfaz y todos sus certificados.
El manifiesto liga ruta exacta, reloj, selección, bytes, SHA comprimido y
SHA canónico. Los destinos existentes se rechazan para preservar intentos.

La validación primaria reproduce referencias, RHS de 119 ecuaciones,
recintos del descriptor medio, inversas, tasas, acciones y cierres de cada
soporte. Comprueba transporte de 22 errores, reloj real, selección y parada
por hueco o límite. Incluye soluciones cuadráticas exactas con tres
duraciones y ambos signos, RC y conservación de endpoints, y rechazos de
archivos con ruta, bytes, SHA o identidad alterados. Las consultas
Decimal100 separan el redondeo del observador de las cotas racionales.

El [productor del corpus](../tools/loudness_latch_bdf_static_precision_curved_prefix_inputs.py)
añade el recibo anterior del corpus, manifiesto nuevo, recibo primario y
todos los archivos por soporte. Mantiene las excepciones históricas CRLF
y las fuentes fallidas identificadas. El test recupera cada blob y verifica
sus bytes antes de conservar sólo su SHA para comparaciones posteriores;
esa política evita retener todo el corpus binario simultáneamente.

El resultado certifica un prefijo nominal respecto a referencias explícitas;
no prueba otro SO/BLAS, sonido vintage, cobertura completa o audio nativo.
Gates y evidencia anteriores se conservan.

## Intento primario interrumpido y corrección del lector

El primer intento se interrumpe por decisión del agente tras **90,7530536 s**
al detectar que la prueba de almacenamiento pasa el resumen JSON plano
al lector del productor, que sólo acepta gzip. No se publica un conteo
de pruebas terminadas: `reported_tests=null`, `completed_suite=false`.
El recibo conserva comando completo, exit code, stdout/stderr parciales,
fuente UTF8 exacta, SHA y entradas antes/después idénticas. También registra
la causa verificada de la interrupción y el proceso hijo identificado.

`7d76e8a` archiva ese recibo antes de corregir; `b6f6eec` cambia una sola
línea de la prueba a json.loads del resumen UTF8. Productor, protocolo,
archivos numéricos, manifiesto, validator, circuito y gates quedan intactos.
Esta versión interrumpida se recupera por separado de las dieciséis fuentes
fallidas históricas, con su estado explícito y sin fingir una suite completa.

Las seis pruebas primarias pasan en la segunda corrida, **766,1438986 s**,
con entradas idénticas antes/después. Reproducen las ocho referencias,
64 inversas, 6336 consultas de tasa, 512 acciones y todos los cierres,
además del manifiesto, sus destinos e identidad. El recibo aceptado y
helper/tests/validator del corpus se fijan en `b8617c2` antes de generar
el archivo ampliado.

## Corpus completo y publicación

El corpus se congela en `be32885` antes de validar. Recupera **600 entradas
de 112 informes** y verifica **151 hashes propios** (112 informes y
39 helpers), con tres excepciones LF→CRLF. Sus **17 fuentes anteriores**
se desglosan en dieciséis versiones fallidas históricas y la versión de
esta validación interrumpida. Cada una mantiene fuente exacta, SHA, comando,
recibo e índice de intento; el recibo propio identifica la interrupción.

Las dos pruebas del corpus pasan al primer intento en **73,1705622 s**.
Son **ocho pruebas nuevas aceptadas**: seis primarias en la segunda corrida
tras una interrupción conservada, y dos archivísticas al primero. Ambos
recibos mantienen entradas idénticas antes/después. No se repite la medición
numérica para corregir el lector del test.

[Recibo primario](../evidence/loudness_latch_bdf_static_precision_curved_prefix_validation.json),
[recibo del corpus](../evidence/loudness_latch_bdf_static_precision_curved_prefix_inputs_validation.json),
[archivo](../evidence/loudness_latch_bdf_static_precision_curved_prefix_inputs.json.gz)
y [resumen](../evidence/loudness_latch_bdf_static_precision_curved_prefix_inputs_summary.json).

Corpus: 418694 bytes, SHA comprimido
`48a2949dc0814f30c124e87f6c9747d63d181f790f1392f1c7b8a5acecb50928`,
canónico `2a06dc2981a4f3e075b913d41211fb12c8c505b341c5ec02167f0092450f346a`.

Productor/protocolo corresponden a `0814518`; manifiesto, ocho archivos y
resumen, a `25a09e8`; test corregido, a `b6f6eec`; fuentes del corpus,
a `b8617c2`; corpus/resumen, a `be32885`. Atributos Git, integrador y
fuentes numéricas anteriores siguen en su revisión `f57dcef`. Las pruebas
recuperan todos los blobs con sus excepciones y verifican los hashes.
No quedan cachés de Python. La reconstrucción de bytes no prueba otro
SO/BLAS, fidelidad física o audio nativo.

Se admite el prefijo nominal de dieciséis soportes hasta ≈125 µs, con
error acumulado ≤0,793 µV respecto a sus referencias por tramos. La parada
es por límite declarado, no por un hueco encontrado. Los soportes posteriores,
meta global 1 mV, voz, audio nativo y deadline mantienen sus gates.
