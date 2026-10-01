# Máximos consultados con historial común

## Selección previa y memoria

La consulta del máximo interpolado del [historial común](BIESTABLE_HISTORIAL_COMUN.md)
dio 2,12 mV. Para no confundir ese único punto con el máximo de la región,
se declara observar **el máximo interpolado de cada uno de los 94 nodos**,
la rejilla anterior retenida dentro de la cobertura común y los instantes
máximos de ambos contrastes, condicional y desde DC. No se selecciona un
subconjunto favorable ni se alinea la transición.

Se usa la unión de 332 tiempos válidos entre el primer extremo común y
3 ms. Cada consulta mantiene el reloj pedido y restaura dos historiales;
los restos menores que 1 ps usan el [anclaje anterior con dos intervalos](BIESTABLE_DOMINIO_DE_OBSERVACION.md).
No se publica memoria provisional en ninguna trayectoria. La topología,
R61/BUS/KEY y las hipótesis de carga permanecen iguales al experimento base.

## Resultado

Las **664 consultas** resuelven sin fallos y conservan KCL de carga <10 pA,
ecuación de rama <10 fV e historial serializado completo.

| Observación condicional | Máximo | Instante | Nodo |
| --- | ---: | ---: | --- |
| Unión interpolada de ambas mallas | 28,945598 mV | 2,422167969 ms | 67, ATTACK_OUT |
| Consulta de ese mismo punto | 2,122804 mV | 2,422167969 ms | 67, ATTACK_OUT |
| Máximo de la nueva rejilla consultada | **26,790648 mV** | **2,442481232 ms** | **66, ATTACK_GATE_LOWER** |

Los cuatro contrastes totalmente FD en ambos máximos pasan <10 nV;
la diferencia más grande es 1,03 pV. Se verifica dQ/dt de cada paso FD
desde su memoria real. Compartir las leyes del circuito no crea una
referencia espacial independiente.

El **gate condicional de 1 mV sigue fallando**, incluso al resolver al
mismo instante en la región rápida. El valor de 2,12 mV del punto dominado
por interpolación no describe el peor punto de la rejilla. El nuevo
máximo consultado tampoco constituye una búsqueda exhaustiva del máximo
continuo ni una cota del DAE exacto.

El máximo original desde DC de 126,37 mV conserva su propio fallo; la
memoria común sólo condiciona el nuevo experimento. No se atribuye un
porcentaje causal a un único nodo del prefijo ni se suman diferencias máximas.

## Evidencia y regresión

Productor: `tools/loudness_latch_bdf_common_sampling.py`.

Datos: `evidence/loudness_latch_bdf_common_sampling.json.gz`.

Resumen: `evidence/loudness_latch_bdf_common_sampling_summary.json`.

`python tools/loudness_latch_bdf_common_sampling.py`

`python -m unittest discover -s tests -p test_loudness_latch_bdf_common_sampling.py -v`

Cinco pruebas recalculan todos los máximos por nodo y la selección temporal,
reconstruyen cada consulta/publicación y memoria intermedia, repiten FD,
recalculan el gate y verifican hashes, cobertura y almacenamiento sin pérdidas.
No se admiten refinamiento global, conmutación física ni audio.

## Próximo corte

El [estimador BDF2 por doble paso](BIESTABLE_ESTIMADOR_BDF2_DOBLE_PASO.md)
prepara el control de discrepancia local con ambas rutas del mismo integrador.
Necesita un barrido desde DC con dos políticas y el gate global original,
además de conservar estos contrastes condicionados y todos los fallos previos.
