# Refinamiento temporal por movimiento del biestable

El banco ejecutó la voz H128 a 48 kHz con CV de placa
fijo a −1,6 V y las mismas historias iniciales de ambas
reservas. El calendario local usa el movimiento de los
colectores que calcula el solver en cada etapa Radau.
Reduce el paso si ese movimiento supera VT/32 o si
cambia el orden de los colectores. El paso fino es el
del control de 512 subpasos. La regla conserva los
estados HIGH/LOW, las ecuaciones y las cargas.
[Protocolo](VCO_FAMILIA_BUS_VOZ_RELOJ_PROTOCOLO.md)

## Reservas

Se probaron los techos de paso desde el más grueso.
La rama positiva con base de 32 subpasos reprodujo el
intervalo de conmutación y alcanzó 1,573 veces el límite
nodal. El replay reprodujo el resultado. Con base de
64 subpasos, el máximo bajó a 0,3004 del límite y el
peor error en R59/R60 usó 6,86e−6 de su tolerancia.
El RMS relativo de J7 fue 6,16e−9. La inversión de
volumen conservó su sentido en el intervalo entre
77,904296875 y 77,90625 muestras.

La rama negativa pasó con base de 32 subpasos. El peor
nodo usó 4,77e−5 de su tolerancia y se conservó el orden
de los colectores de ambos contornos. Las dos reservas
pasaron las comprobaciones de fase, J7, C27, Jacobiano
cargado, R21 y corriente en ambos retornos. La auditoría
local incluyó la inversión del biestable.

En la muestra 78, el nodo 16 fue el más cercano a su
límite en ambos recorridos positivos. Su error bajó
de 40,93 µV a 7,82 µV al cambiar la base de 32 a 64.
El peor error nodal negativo fue 1,09 nV en el nodo 37
de la muestra 8.

## Coste confirmado

| Reserva | Pasos fijos | Pasos aceptados | Tiempo fijo | Reloj variable | Factor |
| --- | ---: | ---: | ---: | ---: | ---: |
| Positiva | 65.536 | 10.997 | 37,102 s | 7,034 s | 5,27× |
| Negativa | 8.192 | 4.096 | 4,945 s | 2,497 s | 1,98× |

Comparación de 128 muestras con CPU lógica 9 y el
mismo binario. El reloj de pared acumula los intentos
de Newton, incluidos los que el guard divide. El
tiempo de CPU del hilo, que incluye el controlador,
auditoría y registro, pasó de 37,203 a 7,109 s en la
rama positiva y de 4,984 a 2,516 s en la negativa.
La repetición reprodujo el calendario y los estados.
En la rama positiva hubo 2.798 pasos del tamaño fino
y tres divisiones disparadas por el guard de movimiento.
No hubo rechazos de Newton en las variantes elegidas.

El reloj variable queda en el banco nativo. El coste
todavía supera el margen de 1,333 ms y los dos pases
físicos siguen pendientes. Se retiraron los ejecutables
y tablas temporales.
[Mediciones](../evidence/vco_family_voice_bus_clock01.json),
[auditoría](../evidence/vco_family_voice_bus_clock_tests01.json)
