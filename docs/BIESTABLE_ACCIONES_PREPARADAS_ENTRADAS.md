# Corpus de preparación exacta de acciones

El [protocolo](BIESTABLE_ACCIONES_PREPARADAS_PROTOCOLO.md), productor y helper
se congelan en `5bdff2b` antes de medir. Control original intacto; banco fijo
de 64 macroceldas, 32 pares AB y 32 BA, una preparación y una pasada.
Todos los presupuestos y 512 subcertificados por helper se comparan en bytes
con la acción completa archivada. Cada muestra conserva orden, reloj wall/CPU,
longitudes, SHA, archivo tipado, trial, RHS y macrocelda. El gate no compara
sólo los picos. No hay cambios de fuente o discrepancias durante la medición.

## Fuentes y validación primaria

Datos, siete pruebas y validator se congelan en `49363c7`. El primer intento
completa las siete pruebas en **234,8189175 s**; seis pasan, incluida la
reproducción completa de las 64 acciones. El test pequeño de cancelación
esperaba un polinomio nulo de un coeficiente. El control conserva tres ceros,
es decir, el grado del polinomio de entrada. No es una discrepancia entre
helpers: la comparación con el control pasa antes de esa expectativa.

El fallo y fuente exacta, SHA, comando, stdout/stderr, exit=1 y snapshots se
conservan en `1f52617`, antes de corregir. La expectativa se congela en
`3f87d87`; no se cambia helper, productor, aritmética, banco o tiempos.
**Las siete pruebas pasan al segundo en 234,6799164 s**. Ambas ejecuciones
conservan los bytes antes/después. No se repite el ensayo de tiempos.

Las pruebas reproducen todos los presupuestos y certificados, rechazan
cambios de contexto/integridad y formas inválidas, verifican falta de alias,
signo, restos independientes y duración/polinomios nuevos. Comprueban el
ledger de tiempos, costes incluidos, archivos completos y alcance temporal.
[Recibo primario](../evidence/loudness_latch_prepared_action_validation.json).

## Corpus ampliado

Recibo aceptado, collector, dos tests y validator se congelan en `bdbf244`.
El corpus se congela en `8b372c4` antes de validar. Recupera **657 entradas
de 138 informes**, con **180 hashes propios** (138 informes y 42 helpers).
Conserva las tres excepciones históricas LF→CRLF y **18 fuentes de tests**:
diecisiete fallidas y una interrumpida. La nueva fuente fallida se contrasta
con el blob de Git del HEAD señalado por su recibo antes de conservar su SHA.

El collector incluye los 17 artefactos de la continuación, su linaje completo,
recibos anteriores, nuevo banco y recibo primario. Una versión fallida no
sustituye las fuentes actuales. Los informes y gates numéricos históricos,
atributos Git e integrador se conservan. Python se ejecuta con -B.

[Corpus](../evidence/loudness_latch_prepared_action_inputs.json.gz),
[resumen](../evidence/loudness_latch_prepared_action_inputs_summary.json) y
[recibo del corpus](../evidence/loudness_latch_prepared_action_inputs_validation.json).

Las dos pruebas del corpus pasan al segundo en **82,5034305 s**, con todos
los hashes antes/después iguales. El primer intento, **16,9951456 s**, falla
por una comprobación del nuevo recibo aplicada también al recibo histórico
aceptado de continuación. Ese fallo propio queda en `8af29db`, con fuente
UTF-8, SHA, comando, stdout/stderr, exit=1 y snapshots. `3fbee62` congela la
corrección tipada antes de repetir; no se regenera el corpus ni el banco.
Esta fuente propia se conserva en el recibo adicional; las 18 fuentes del
archivo generado corresponden al linaje anterior y al fallo primario nuevo.

**Nueve pruebas nuevas aceptadas**, siete primarias y dos archivísticas;
ambas suites al segundo. Los dos fallos de fixtures se conservan. El ensayo
de tiempos sólo tiene una pasada, sin nuevos fallos numéricos o cambios de
gates. La auditoría recupera íntegramente los 657 blobs y fuentes declaradas.

Archivo: **437424 bytes**, SHA comprimido
`ce3cdd24ea402a7cdb7b3b7854233e86bb75e593adfd7b4857ba94e4f7f17c28`;
canónico `a036630615099a3f100f77f91b61ae0b09e5b6d752500b3c42e29390e3a45346`.

Preparación offline nominal. Se conservan 24 soportes hasta ≈225 µs y la
cota acumulada ≤0,793 µV. Identificación física, parecido sonoro, cobertura
completa, 1 mV global, voz, audio nativo y deadline siguen abiertos.
