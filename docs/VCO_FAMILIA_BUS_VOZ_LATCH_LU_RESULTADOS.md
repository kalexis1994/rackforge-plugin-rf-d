# Carga de junturas y filas activas del LU

Continuaciones de la voz H128 a 48 kHz con CV de placa
fijo a −1,6 V. El control conserva el Jacobiano directo,
la búsqueda ligera, FMA y la omisión de bordes con
factor cero.
[Protocolo](VCO_FAMILIA_BUS_VOZ_LATCH_LU_PROTOCOLO.md)

El cambio de junturas reutiliza la validación de los
extremos ya evaluados antes de calcular el incremento
de carga. Mantiene el empalme, la integral de C(v), el
estado HIGH/LOW y las derivadas. El LU registra qué filas
tienen coeficiente no nulo mientras busca el pivote.
Tras intercambiar filas, traduce esos índices y conserva
las operaciones de cada fila y de su borde.

## Reservas

Las continuaciones reprodujeron bit a bit los 129
relojes, con las 118 coordenadas HIGH/LOW, la fase, J7
y los retornos R59/R60. El orden de colectores del
filtro se mantuvo. La inversión de volumen ocurrió en
el mismo sentido entre 77,904296875 y 77,90625 muestras
desde el inicio. La auditoría de Jacobiano cargado,
correcciones de ambos retornos, KCL, C27 y puerto
incluyó el paso de la inversión.

Pasaron 90 contrastes de etapa en las tres posiciones
de R21. Los fixtures de juntura reprodujeron 162
combinaciones, incluidos los vecinos del empalme en
ambos sentidos, y seis rechazos. Los fixtures lineales
reprodujeron ocho direcciones, incluidos intercambios
con el coeficiente inicial nulo y no nulo, dos rechazos
y la recuperación del mismo workspace.

## Primera comparación

Las ventanas positivas de cinco muestras mostraron
ahorros en el LU aislado de 5,4 % antes, 8,8 % durante
y 6,2 % después de la liberación. La etapa completa
aislada bajó 1,6 % durante la liberación y subió 4,1 %
en la ventana posterior. El recorrido completo, con
la combinación antes del control y sin fijar CPU,
subió de 39,257 a 39,862 s en la reserva positiva.
Se conservan los resultados y el contraste posterior
invierte el orden y fija la afinidad del banco.
[Primer recibo](../evidence/vco_family_voice_bus_latch_lu01.json)

## Repetición con afinidad

La repetición usó la CPU lógica 9, con el control
primero y comprobación de afinidad en los tres
ejecutables de las reservas. Los tiempos son de pared
alrededor del solver. Cada fila corresponde a una
continuación de 128 muestras por variante, sin
instrumentación dentro del solver.

| Reserva | Control | LU aislado | Combinación | Ahorro combinado |
| --- | ---: | ---: | ---: | ---: |
| Positiva, 512 subpasos | 38,746 s | 36,829 s | 36,735 s | 5,2 % |
| Negativa, 64 subpasos | 5,320 s | 4,995 s | 4,938 s | 7,2 % |

En la rama positiva, el LU aislado explica la mayor
parte de la diferencia observada frente al control.
La repetición queda limitada a este banco. La
discrepancia con el primer recorrido forma parte
de la evidencia.

El tiempo de CPU del hilo en la rama positiva, que
incluye auditoría y registro, bajó de 38,844 a 36,875 s.
La rama negativa pasó de 5,328 a 4,953 s. Esta medida
confirma el sentido de la diferencia del reloj de pared
en la repetición.

| Ventana positiva | Etapa completa aislada | LU aislado |
| --- | ---: | ---: |
| Antes de la liberación, 52–57 | 1,3 % | 8,5 % |
| Durante la liberación, 76–81 | 1,6 % | 10,7 % |
| Después de la liberación, 96–101 | 1,4 % | 8,0 % |

Ahorros de las medianas en tres recorridos alternados.
Cada uno de los tres pares por ventana positiva tuvo
menor coste en la sección del cambio aislado y cerró
en el mismo estado y fase.

La variante queda en el banco nativo. Los dos pases
físicos de 128 frames quedan pendientes porque el
tiempo observado supera 1,333 ms. Se retiraron binarios
y tablas temporales.
[Repetición](../evidence/vco_family_voice_bus_latch_lu02.json),
[auditoría](../evidence/vco_family_voice_bus_latch_lu_tests01.json)
