# Entradas históricas: bytes de Git y del checkout

## Diferencia comprobada

La comparación directa de las entradas congeladas con `git show HEAD:ruta`
falla para **tres JSON históricos**. Git guarda LF y el checkout Windows
usado por los productores contiene CRLF. Los SHA de los informes identifican
correctamente esos bytes de entrada, pero no coinciden con el blob sin
materializar. Las tres diferencias son exactamente expansión LF→CRLF;
no cambian los JSON canónicos ni los datos numéricos.

| Archivo | Bytes usados en Windows | Alcance |
| --- | --- | --- |
| `evidence/loudness_contour_graph.json` | 10.263 | Grafo histórico |
| `evidence/loudness_latch_bdf_doubling_probes.json` | 1.703.094 | Sondas históricas |
| `evidence/loudness_latch_rejection_audit.json` | 60.742 | Rechazo histórico |

Se auditan las **49 entradas distintas** de los informes de ventanas,
suplemento FD y sensibilidad FD, fijando los blobs de `02fb815`. Las otras
46 entradas coinciden en bytes con Git. Los cuatro nuevos resúmenes/recibos
de ventanas y sensibilidad ya preservan sus bytes exactos al commitear.
No se normalizan los archivos históricos ni se reescriben informes previos.

## Archivo y reconstrucción

La [auditoría empaquetada](../evidence/loudness_latch_bdf_checkout_audit.json.gz)
conserva las tres fuentes UTF-8 completas con sus CRLF, SHA de entrada y
SHA del blob Git, revisión, pertenencia a informes y la comparación directa
fallida. Es lossless: 311.702 bytes, SHA256 comprimido
`01f321fe2b512280bc433d0cb226209732dfff4dff919602113e7a639ce50ad9`.
Su [resumen](../evidence/loudness_latch_bdf_checkout_audit_summary.json)
conserva las identidades sin repetir las fuentes completas.

`recover_historical_input(blob, archived)` en
[el auditor](../tools/loudness_latch_bdf_checkout_audit.py) devuelve los bytes
exactos archivados sólo si el blob y el archivo coinciden con ambos SHA,
la diferencia es exclusivamente LF→CRLF y sus JSON canónicos coinciden.
Un blob desconocido o cualquier cambio de datos se rechaza. La función
no escribe al disco ni modifica un checkout.

Para reconstruir las entradas en otro sistema, partir de la revisión fijada
y materializar esas tres fuentes archivadas **en un checkout aislado de
reproducción**, verificando los SHA antes de correr los productores. Una
lectura del blob Git sin ese paso no equivale a las entradas Windows.
La auditoría prueba reconstrucción de bytes, no ejecución numérica en Linux
ni portabilidad de BLAS, Python o de un compilador.

## Regresiones

`python tools/validate_bdf_checkout_audit.py`

El [recibo](../evidence/loudness_latch_bdf_checkout_audit_validation.json)
registra **2/2 pruebas** por intento, comandos/salida/exit codes y
entradas sin cambios. Reconstruye las 49 entradas desde los blobs fijados,
verifica todos sus SHA originales y rechaza cambios de datos o identidades.
Los productores previos y sus tres informes permanecen intactos; no se
repite el experimento ni se modifica un gate numérico.

El HEAD contextual del productor y primer intento es `02fb815`; el segundo
intento de validación parte de `3ba7b82`. El archivo del auditor se identifica además
por sus bytes SHA y queda archivado en el commit posterior. Este complemento
cierra la reconstrucción de estas entradas históricas; conserva abiertos
los mismos gates de mapa, refinamiento temporal, física y audio.

Los nuevos resúmenes/recibos de esta auditoría usan una regla `-text` local
en `evidence/.gitattributes`, conservando sus bytes LF también en futuros
checkouts Windows. La regla afecta únicamente esos nuevos JSON y deja
intactas las políticas históricas y el `.gitattributes` raíz congelado como
entrada del barrido FD. Tras fijarla se repite la validación; ambos intentos
exitosos se conservan, con la política local incluida en el segundo recibo.
