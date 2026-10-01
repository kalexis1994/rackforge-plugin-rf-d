# Observación entre muestras de BDF2

## Pregunta y contrato

La [primera consulta conservativa](BIESTABLE_PREFIJO_Y_CONSULTA_TEMPORAL.md)
detectó dos casos distintos: interpolación lineal dominante en un punto
del trigger y diferencia entre trayectorias persistente en la transición.
Se amplía ese diagnóstico a B3 y la [tercera malla C3](BIESTABLE_TERCERA_MALLA_BDF2.md).

Los tiempos fijos se declaran en el productor antes de medir:

- Cada 25 µs desde 25 µs hasta 3 ms.
- Cada 0,5 µs en 2,4..2,5 ms, alrededor de la conmutación observada previamente.
- Hasta 32 puntos medios por política, escogidos por posiciones equiespaciadas
  en el orden de los intervalos aceptados, excluyendo el puente inicial.
- Los instantes de máximo interpolado del prefijo hasta 2,3 ms y de la
  comparación completa B3/C3; se agregan automáticamente y no reemplazan
  la rejilla fija.

Se usa la unión ordenada de tiempos, sin alinear eventos ni retimar las
trayectorias. Los tiempos fuera de la cobertura común se excluyen y se
registran inicio/fin y lista completa. El gate diagnóstico muestreado
permanece **1 mV máximo en los 94 nodos**. Pasarlo no demuestra un límite
continuo ni modifica el gate de la comparación completa original.

## Consulta con dos historiales

En un extremo aceptado se conserva el estado guardado. Para un instante
interior se restaura el estado aceptado inmediatamente anterior junto a
su precedente, y se resuelve un intervalo BDF2 parcial hasta el destino.
Se usan el mismo circuito y KEY=10 V. Ambos historiales entrantes permanecen
intactos; la consulta no publica memoria para el siguiente intervalo.
El arranque sólo se observa en su extremo aceptado, fuera del puente del
salto de fuente inicial.

Decimal80 verifica dQ/dt desde ambos historiales reales, C10/R, KCL <10 pA
y error de rama <10 fV. Se conserva el candidato completo, su índice de
anclaje, hash entrante y diagnósticos. Se mide también la diferencia de los
94 nodos contra la interpolación lineal usada en los informes de malla.
Los errores de consulta se guardan; no se sustituyen por valores interpolados
para convertir un fallo en una medida válida.

El intervalo parcial no pasa por la aceptación adaptativa BE/BDF2. Por ello
el resultado sigue siendo una observación provisional, aunque satisfaga
las ecuaciones discretas de carga. Los dos instantes máximos se repiten con
Jacobiano totalmente FD: gate de diferencia <10 nV y KCL <10 pA. Ambos métodos
comparten las leyes espaciales; FD verifica derivadas, no el circuito físico.

## Resultado y límites operativos

Se conservan **386 instantes y 772 consultas**. 633 consultas son válidas;
139 fallan: 129 agotan line search y 10 encuentran matriz singular.
Todas las fallidas intentan intervalos entre 2,7105e−20 y 1,4615e−16 s,
por debajo del mínimo de 1 ps de las trayectorias. La rejilla fija y los
extremos acumulados no siempre representan el mismo tiempo binario;
un instante nominalmente coincidente puede quedar unos ULP después
del extremo y pedir un paso impropio. Tres consultas subpicosegundo sí
resuelven; ese éxito aislado tampoco extiende el dominio declarado.

| Observación | Resultado |
| --- | ---: |
| Prefijo interpolado B3/C3, máximo a 0,575 ms | 1,20117 mV, nodo 93 |
| Consulta de ese mismo instante, máximo en 94 nodos | 9,88374 µV |
| Pico completo interpolado B3/C3 | 0,126367797 V |
| Consulta de ese pico al mismo reloj | 0,126367839 V |
| Máxima diferencia interpolación/consulta B3 en puntos válidos | 4,86156 mV |
| Máxima diferencia interpolación/consulta C3 en puntos válidos | 1,07737 mV |

Las dos últimas diferencias aparecen a 2,422 ms. Los cuatro contrastes FD
en ambos máximos pasan: diferencia máxima 0,5583 pV y KCL <10 pA.
Los cruces interpolados de C3 adelantan a B3 aproximadamente 14,578 ns
en ATTACK_OUT y 22,850 ns en RESET_COLLECTOR; siguen siendo observaciones
muestreadas sin cota temporal.

Sólo **290/386** tiempos tienen ambas consultas válidas, y **13/99** en
el prefijo. Por ello el gate diagnóstico del prefijo permanece fallido
aunque las diferencias de los puntos válidos sean menores que 1 mV.
El gate completo también falla por su pico. No se ocultan los puntos
sin solve ni se sustituyen por interpolación.

La primera ejecución completó el cálculo pero falló al serializar un
booleano de NumPy. `evidence/loudness_latch_bdf_sampling_attempts.json`
conserva su hash de fuente retirado y la incidencia. La segunda ejecución
normaliza tiempos/validez a tipos Python nativos, verifica fuentes antes
y después y guarda todos los resultados sin pérdidas. La regresión recibe
explícitamente un tiempo NumPy y verifica que pueda serializarse.

## Evidencia y reproducción

Productor: `tools/loudness_latch_bdf_sampling.py`.

Datos: `evidence/loudness_latch_bdf_sampling.json.gz`.

Resumen: `evidence/loudness_latch_bdf_sampling_summary.json`.

`python tools/loudness_latch_bdf_sampling.py`

`python -m unittest discover -s tests -p test_loudness_latch_bdf_sampling.py -v`

Las regresiones reconstruyen cada consulta, verifican cargas, residuos,
serialización y anclajes, recalculan la selección de tiempos y conservan
el gate original. Los hashes de fuentes y de las dos trayectorias se
contrastan antes/después; el almacenamiento comprimido se verifica sin
pérdidas. Los cruces ATTACK_OUT=4 V ascendentes y RESET_COLLECTOR=0,5 V
descendentes se conservan con todos sus intervalos muestreados, sin elegir
un evento conveniente.

## Alcance pendiente

Una rejilla finita y consultas sin publicación no dan una cota entre
observaciones. Los instantes de cruce siguen interpolados y su incertidumbre
temporal no está acotada. No hay solución exacta independiente del DAE,
identificación física de cargas, conmutación vintage admitida ni audio.
El siguiente corte limita el dominio de las consultas a 1 ps y, cuando
el residuo temporal es menor, parte de un anclaje aceptado anterior mediante
dos pasos provisionales. Debe conservar el tiempo pedido y registrar toda
la memoria intermedia; no basta redondear al extremo cercano para admitir
un solve al mismo instante.

La observación debe servir para decidir el siguiente control de malla;
no sustituye una trayectoria que conserve memoria y pase refinamiento.
