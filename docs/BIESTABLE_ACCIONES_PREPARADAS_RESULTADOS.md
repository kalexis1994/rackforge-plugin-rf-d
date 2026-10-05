# Acciones preparadas: igualdad completa y coste medido

El [protocolo](BIESTABLE_ACCIONES_PREPARADAS_PROTOCOLO.md), helper y productor
se congelan en `5bdff2b` antes de medir. El helper original queda como control.
Banco: 64 macroceldas de soportes 16–23, width=8 y trial=1, pertenecientes a
la [continuación compartida](BIESTABLE_CONTINUACION_COMPARTIDA_RESULTADOS.md).
Una sola pasada alterna 32 pares AB y 32 BA, sin elegir muestras después.

## Preparación e identidad

Se restauran X, D y E a tuplas de Fraction sin alias mutables. Se calculan una
vez q, cotas por fila y factores DX, |DX|, row*q/(1-q), row/(1-q), respetando
la asociación racional original. La identidad de entrada incluye todo el
recinto, radio, dominios y flags; la identidad del estado incluye todos sus
campos derivados. Ambas se verifican antes de cada budget.

Cada RHS, polinomio firmado, resto independiente, duración y partición se
procesa por macrocelda. Bernstein, primera corrección, cola, intersección,
redondeos dirigidos de 256 bits, normas nodales y de las 22 memorias conservan
el orden y los resultados completos del helper anterior. No se prepara un
resultado de una acción para usarlo en otra.

Identidad del contexto:
`c70353a83e3bddab60e24da964b96b304322d6c1dd8268a6fcc9c83fa7062f46`.
Estado:
`0895ceb0fb387e21647e31be2ae16ee260c110992c8dc95da7e93c6ed635f154`.

## Resultado y tiempos

**64/64 presupuestos completos idénticos en bytes canónicos** entre control,
variante y archivo original. Cada helper calcula **512 subcertificados** con
119 ecuaciones. Se comparan directamente los bytes antes de registrar SHA y
longitudes; no sólo los picos. Los certificados completos originales están
en los artefactos tipados, identificados por ruta, SHA, trial y macrocelda.
No hay discrepancias que archivar ni cambios en las fuentes durante el banco.

| Medida wall | Control | Variante preparada |
| --- | --- | --- |
| 64 llamadas, total | 286,7196643 s | 216,5439470 s |
| Mediana por llamada | 4,4794752 s | 3,3923911 s |
| Pares AB, 32 llamadas | 143,4860994 s | 108,1252986 s |
| Pares BA, 32 llamadas | 143,2335649 s | 108,4186484 s |
| Preparación única | — | 0,2413868 s |
| Total con preparación | 286,7196643 s | 216,7853338 s |

**24,39 % menos wall** y razón control/(variante+preparación) **1,322597**
en esta pasada. CPU total del control: 285,984375 s; variante: 215,890625 s,
más 0,234375 s de preparación. El ledger conserva cada muestra, orden,
longitud, SHA y las mediciones wall/CPU sin reducirlas a estos agregados.

Incluye verificación de identidad por llamada, compilación, acciones y normas.
Excluye lectura de archivos, compresión y comparación/serialización canónica
externa en ambos temporizadores. Las conversiones internas que forman los
certificados sí se pagan. Python 3.12.10, NumPy 2.5.2, Windows 11 y procesador
AMD64 Family 25 Model 33; aritmética exacta de Fraction. Una pasada en este
equipo no estima distribución de rendimiento, ahorro nativo o deadline.

## Archivo, reproducción y alcance

[Datos](../evidence/loudness_latch_prepared_action_benchmark.json.gz) y
[resumen](../evidence/loudness_latch_prepared_action_benchmark_summary.json).
Archivo comprimido: **80906 bytes**, SHA
`902f5391ba55e600ca68f1838a248b6e070765424b76c111d1ffa7e937ae37a8`;
canónico `512718318c8e533198339ff7d9cf42229a5606c384f7ca5810b463d730c84c9d`.
Datos, siete tests y validator se congelan en `49363c7` antes de validar.
[Corpus y recibos](BIESTABLE_ACCIONES_PREPARADAS_ENTRADAS.md): nueve pruebas
nuevas aceptadas, siete primarias y dos archivísticas; ambas suites al segundo.
Dos fallos de fixtures quedan conservados; no se repite el ensayo de tiempos.

Se conservan **24 soportes hasta ≈225 µs**, acumulado **≤0,793 µV**;
no se amplía la cobertura temporal ni se renuevan inversas o tasas.
Es una preparación del laboratorio offline nominal, con parámetros sintéticos.
1 mV global, cobertura completa, identificación física, voz, audio nativo y
deadline siguen abiertos. Próximo:
[continuación con preparación explícita](BIESTABLE_CONTINUACION_PREPARADA_PLAN.md).
