# Biestable: tiempos observados y diferencias de forma

## Alcance

Postproceso del [barrido compensado A2/B2](BIESTABLE_BARRIDO_COMPENSADO.md),
sin ejecutar nuevos solves, editar historiales ni desplazar las trayectorias
publicadas. `tools/loudness_latch_transition_observations.py` identifica los
cruces ascendentes de ATTACK_OUT y descendentes del colector Q25 mediante
interpolación lineal de muestras aceptadas.

El informe `evidence/loudness_latch_transition_observations.json` guarda
todos los cruces, extremos de cada intervalo, voltajes y pendiente muestreada.
No selecciona un evento cuando hay varios cruces. Sus umbrales en V son
observables diagnósticos dentro del rango simulado; no calibraciones vintage.
Un intervalo entre dos muestras no es una cota demostrada del instante de
cruce de una solución continua.

## Resultado al mismo reloj

| Evento | A2 (ms) | B2 (ms) | B2−A2 (µs) |
| --- | ---: | ---: | ---: |
| ATTACK_OUT sube por 2 V | 2,422335029 | 2,420018526 | −2,316503 |
| ATTACK_OUT sube por 4 V | 2,424602551 | 2,422282769 | −2,319783 |
| ATTACK_OUT sube por 8 V | 2,426524556 | 2,424206732 | −2,317824 |
| Q25 colector baja por 4 V | 2,436416637 | 2,434095654 | −2,320983 |
| Q25 colector baja por 0,5 V | 2,447235948 | 2,444641045 | −2,594903 |
| Q25 colector baja por 0,05 V | 2,447466051 | 2,444871903 | −2,594148 |

La subida de ATTACK_OUT precede a la parte final de la caída del colector.
El adelanto observado de B2 es ~2,32 µs en ATTACK_OUT y ~2,59 µs en la
caída final de Q25. La caída interpolada 0,5→0,05 V tarda **230,103 ns**
en A2 y **230,858 ns** en B2. Hay, por tanto, varios momentos pertinentes
de la trayectoria; no se describe todo el error con un único instante de
conmutación.

## Alineación únicamente diagnóstica

Se comparan dos ventanas relativas de ±10 µs, cada una anclada en un
observable de 4 V que tiene un único cruce en ambas trazas. Se interpola
en la unión de sus tiempos relativos; los archivos originales conservan
sus tiempos absolutos.

| Ancla | Puntos | Diferencia máxima de nodo en ventana alineada |
| --- | ---: | ---: |
| Subida ATTACK_OUT por 4 V | 154 | 61,5079 mV, ATTACK_OUT |
| Caída Q25 colector por 4 V | 874 | 126,224 mV, RESET_COLLECTOR |

El desfase es pertinente al comparar la región de subida rápida; permanecen
diferencias de forma en ambas ventanas. La alineación no reemplaza el
contraste al mismo tiempo, que sigue fallando con **5,146985 V** máximos y
**6,4488 mV** finales frente a su gate de 1 mV. Ninguna ventana admite
refinamiento temporal, conmutación física o audio.

## Regresión y siguiente bloque

Tres pruebas reproducen el informe y hashes, verifican los extremos de todos
los cruces, conservan cruces múltiples, rechazan una dirección ambigua y
contrastan un desplazamiento temporal sintético conocido sin alterar su forma.

`python tools/loudness_latch_transition_observations.py`

`python -m unittest discover -s tests -p test_loudness_latch_transition_observations.py -v`

Siguiente bloque: medir el error acumulado de C2/junturas antes de cada región
rápida con otra malla y otro integrador, manteniendo los límites de publicación
y el criterio al mismo reloj. Los tiempos aquí observados son del modelo
sintético; no son tiempos de un Model D físico identificado.
