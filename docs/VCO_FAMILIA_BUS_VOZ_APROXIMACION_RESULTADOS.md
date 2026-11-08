# Reloj variable con aproximación y recuperación del biestable

Banco H128 a 48 kHz, con CV de placa fijo a −1,6 V.
El control es el reloj variable anterior. Se conservaron
el solver de dos etapas, los puertos, cargas y límites
de Newton y el guard fino por movimiento.
[Protocolo](VCO_FAMILIA_BUS_VOZ_APROXIMACION_PROTOCOLO.md)

El reloj limita el paso al intermedio cuando se cierra
la separación de un par de colectores respecto de la
historia inicial. Después de observar la inversión,
mantiene ese límite hasta el próximo reloj entero de
muestra. La selección usa el estado del circuito.

## Reservas

Las seis combinaciones sin retención conservaron el
intervalo de inversión en la rama positiva, pero usaron
1,573 veces el límite nodal. Las repeticiones
reprodujeron el rechazo. La rama negativa pasó con
la pareja 8/64.
[Ensayo inicial](../evidence/vco_family_voice_bus_approach01.json)

Con retención, ambas reservas pasaron con base de 8
subpasos y reloj intermedio de 64. El máximo nodal
positivo usó 0,30035 de su límite y el negativo 0,00103.
Los retornos R59/R60, J7, la fase y las comprobaciones
de C27, R21 y del Jacobiano cargado pasaron sus gates.
En la rama positiva, el biestable invirtió en el mismo
sentido entre 77,904296875 y 77,90625 muestras, y la
retención abarcó 384 unidades de la rejilla, equivalentes
a 1,953 µs. Se conservó el orden de los colectores del
filtro. No hubo inversión en la rama negativa.

El contraste con fase inicial de 0,125 ciclos también
pasó contra su referencia fina de 512 subpasos. Conservó
el intervalo y sentido de inversión. Usó 0,30035 del
límite nodal, 8,00e−6 del límite de los retornos y
1,98e−7 de RMS relativo en J7.

## Coste después de validar las reservas

| Rama | Pasos previos | Pasos nuevos | Reloj previo | Reloj nuevo | Factor |
| --- | ---: | ---: | ---: | ---: | ---: |
| Positiva | 10.997 | 4.992 | 7,062 s | 3,237 s | 2,18× |
| Negativa | 4.096 | 1.024 | 2,476 s | 0,672 s | 3,69× |

Medianas de dos pares con orden invertido, en el mismo
binario y con afinidad a CPU lógica 9. Se cronometraron
todos los intentos del solver, incluidas las divisiones
por los guards. El tiempo de CPU del hilo, que también
incluye control de paso, auditoría y registro, bajó de
7,070 a 3,266 s en la positiva y de 2,508 a 0,711 s en
la negativa. Los pares reprodujeron las trayectorias
y los calendarios de sus respectivas variantes.

La variante se valida para estas continuaciones y el
contraste de fase a CV fijo. El coste supera el margen
de 1,333 ms y los dos pases físicos siguen pendientes.
Se retiraron los ejecutables y las tablas temporales.
[Mediciones](../evidence/vco_family_voice_bus_approach02.json),
[auditoría](../evidence/vco_family_voice_bus_approach_tests01.json)
