# Corpus del prefijo dirigido y cierres con enteros grandes

El [productor](../tools/loudness_latch_bdf_static_precision_directed_prefix_inputs.py)
reúne el prefijo dirigido y la repetición aislada de dos cierres enormes,
con sus recibos primarios. Helpers, pruebas y recibos se congelan en
`02dfb01`; corpus y resumen, en `dbfae2e`, antes de validar.

Se recuperan **535 entradas de 94 informes**, con **130 hashes propios**
(94 informes y 36 helpers), tres excepciones históricas LF→CRLF y trece
versiones históricas de tests fallidos. La política de lectura/registro
de enteros sin límite decimal es explícita. No se modifica un input previo.

## Intentos conservados

Diez regresiones del prefijo pasan al primero en **504,8150407 s**.
Cuatro de los cierres grandes pasan al primero en **42,0994302 s**.
Sus fuentes permanecen idénticas antes/después. El corpus conserva ambos
informes, incluidos los fallos de registro originales de 4300 dígitos.
La repetición recupera ambos presupuestos y rechaza el radio 10 µV.

La primera validación del corpus falla en una aserción que conservaba el
nombre del resumen anterior. Su recibo y fuente exacta se fijan en
`74ae782`, antes de corregir el test en `95a8776`. El segundo intento
falla al comprobar versiones históricas contra un recibo que aún no
contenía el intento en ejecución. Se preserva en `6a4264c`; la corrección
`7c33a5b` verifica directamente las fuentes UTF-8 y hashes de ambos fallos,
sus snapshots y blobs Git. Datos y helpers permanecen intactos.

El [recibo del corpus](../evidence/loudness_latch_bdf_static_precision_directed_prefix_inputs_validation.json)
retiene las dos fuentes fallidas propias, además de las trece históricas
dentro del corpus: quince fuentes distintas verificables en total. El
corpus no incluye su propio recibo de manera recursiva. La nueva prueba
comprueba sus intentos anteriores sin asumir que un intento pendiente
ya fue guardado.

Las dos pruebas del corpus pasan en el **tercer intento, 120,2588294 s**,
con snapshots idénticos. En total, **16 pruebas nuevas aceptadas**: diez del
prefijo, cuatro del registro y dos de recuperación. Los dos primeros
intentos propios permanecen completos; no se repite el experimento
numérico ni se cambia el corpus al corregir estas comprobaciones.

## Archivo y alcance

[Datos](../evidence/loudness_latch_bdf_static_precision_directed_prefix_inputs.json.gz):
390166 bytes, SHA comprimido
`bb1bc6259e6be63ed47f1ba8e8b3fb3a26af06103191e65a637fd41dcded705f`,
canónico `8867c794cde8ebfa56f9f85301b64e5f0d0c9f0c023280f4706337db681ae1e8`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_directed_prefix_inputs_summary.json).

La auditoría final verifica las 535 entradas y 130 hashes desde Git,
las trece fuentes históricas y ambas correcciones propias. Productor,
helper y protocolo del prefijo coinciden con `a3489f8`; datos con
`16e5053`. El productor de enteros coincide con `2d961a5`, sus datos con
`59a0630`. Atributos Git, fuentes de acción y evidencia del corte anterior
coinciden con `7b1c571`. El corpus permanece en `dbfae2e` durante todas
las correcciones. Cero archivos congelados o gates modificados.

Recuperar bytes no prueba portabilidad de otro BLAS o SO ni identifica
una placa vintage. Se admiten sólo seis intervalos nominales hasta
≈6,25 µs, error nodal ≤0,754 µV. Trayectoria completa, 1 mV global,
parámetros físicos, audio, motor nativo y deadline siguen abiertos.
