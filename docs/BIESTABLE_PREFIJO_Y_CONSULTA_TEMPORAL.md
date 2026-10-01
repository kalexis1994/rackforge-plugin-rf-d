# Prefijo, tiempos y consulta conservativa al mismo instante

## Alcance

El [barrido BDF2](BIESTABLE_BARRIDO_BDF2.md) reduce la discrepancia entre
políticas, pero sigue fallando el máximo de trayectoria. Este diagnóstico
lee los informes completos de Euler y BDF2 sin modificar sus estados,
tiempos, rechazos ni gates. Código: `tools/loudness_latch_bdf_prefix_audit.py`;
informe: `evidence/loudness_latch_bdf_prefix_audit.json`.

El prefijo llega a 2,3 ms, antes de los cruces ascendentes de ATTACK_OUT
por 4 V de todas las trazas. Se comparan los 94 nodos en la unión temporal,
con interpolación lineal y exclusión del puente de fuente inicial hasta
25 µs. El gate del prefijo es 1 mV, fijado antes de medir. También se guardan
observaciones a 0,1/1/2/2,3 ms para C2, bases/colectores, salida y trigger.

## Sensibilidad observada antes de la transición

| Comparación entre políticas del mismo método | Máximo de nodos en prefijo | Nodo limitante | Máximo de C2 |
| --- | ---: | --- | ---: |
| Euler A2/B2 | 5,27865 mV | TRIGGER_COLLECTOR | 112,791 nV |
| BDF2 A3/B3 | 3,75244 mV | TRIGGER_COLLECTOR | 50,2158 nV |

Los máximos interpolados de prefijo fallan 1 mV. C2 tiene una diferencia
mucho menor que la del trigger; no basta medir sólo su capacitor grande
para describir el error de todo el circuito. Estas son sensibilidades de
malla sobre un modelo compartido, no errores frente a una solución exacta.

Los cruces **interpolados** muestran B−A:

| Evento | Euler | BDF2 |
| --- | ---: | ---: |
| ATTACK_OUT sube por 4 V | −2,319783 µs | −62,031 ns |
| Q25 colector baja por 0,5 V | −2,594903 µs | −101,998 ns |

Los tiempos interpolados no tienen una cota de precisión continua. La
reducción observada del desfase tampoco admite por sí sola el refinamiento.

## Resolver el punto que limita el prefijo

El máximo interpolado BDF2 está en 0,5875 ms. Se conserva el extremo
aceptado de B3 y se consulta A3 en ese mismo instante mediante un nuevo
paso BDF2 de **37,5 µs** desde sus dos historiales aceptados anteriores.
La consulta conserva ambos estados entrantes y queda sin publicar.
No se sustituye el historial ni se retima la trayectoria original.

| Dato al mismo instante | Resultado |
| --- | ---: |
| Diferencia interpolada original de TRIGGER_COLLECTOR | 3,75244 mV |
| Diferencia de TRIGGER_COLLECTOR con consulta de circuito | 36,4195 µV |
| Diferencia máxima de los 94 nodos con consulta | 39,4267 µV |
| Cambio máximo interpolación→consulta en A3 | 3,78886 mV |
| KCL directa del candidato provisional | 4,20727 pA |

Aquí la comparación lineal entre muestras aporta casi toda la separación
observada. La consulta sigue siendo una aproximación BDF2 desde los estados
guardados, no una solución continua exacta ni una nueva trayectoria admitida.
Un punto consultado no verifica todos los otros tiempos del prefijo:
el gate original queda conservado como fallido.

## Comprobar también el máximo de la transición

Se repite la consulta al mismo tiempo en **2,442553711 ms**, el máximo
del barrido completo. Se conserva el extremo aceptado A3 y se resuelve
B3 desde sus dos estados anteriores con h≈1,525879 ns.

| Dato | Resultado |
| --- | ---: |
| Diferencia interpolada original, ATTACK_GATE_LOWER | 0,563356642 V |
| Diferencia con consulta del circuito al mismo tiempo | 0,563357660 V |
| Cambio por consulta | 1,01847 µV |
| KCL directa de esa consulta | 0,0815 pA |

La interpolación tiene poca influencia en este pico: la discrepancia grande
permanece al resolver ambos candidatos al mismo instante. El gate de 1 mV
de la trayectoria sigue fallando. Ninguna consulta admite conmutación física,
audio o proximidad a un Model D vintage.

## Regresión y siguiente gate

Tres pruebas contrastan interpolación con un desplazamiento sintético conocido,
reproducen observaciones/hashes y ambas consultas, verifican dQ/dt directo,
C10/R, snapshots previos intactos y repetición FD completa de las consultas
parciales. Los datos originales de ambos barridos conservan sus hashes.

`python tools/loudness_latch_bdf_prefix_audit.py`

`python -m unittest discover -s tests -p test_loudness_latch_bdf_prefix.py -v`

Siguiente gate: malla BDF2 más exigente y criterio de observación temporal que
controle también el error entre muestras. Conservar el pico consultado, los
fallos originales y las cargas no identificadas al contrastar otra integración
o un oráculo espacial independiente.
