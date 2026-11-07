# Coste de la voz H128 con ambos contornos cargados

2026-11-07. Continuaciones de 128 muestras a 48 kHz con
CV de placa fijo a −1,6 V. Se conservaron las historias
HIGH/LOW, el BUS cargado y la temporización de KEY del
[banco de partida](VCO_FAMILIA_BUS_VOZ_RESULTADOS.md).

## Perfil y descarte

En ventanas de cinco muestras que incluyeron KEY y la
liberación, el armado de etapas completas consumió entre
45 y 46 % del tiempo, y la resolución lineal entre 34 y
36 %. El último estado de cada ventana coincidió con el
archivado. El armado sin Jacobiano consumió entre 13 y 15 %.

La duplicación adaptativa de pasos conservó la rama
negativa con un error nodal de 0,000275 del límite y
consumió 25,754 s. En la rama positiva agotó las 80
iteraciones de Newton en la muestra 77, en el mínimo de
la rejilla. El replay sin cambios reprodujo la salida y
el fallo. Se descartó para la voz cargada.
[Recibo del perfil y del descarte](../evidence/vco_family_voice_bus_cost01.json)

## Pasos fijos y equivalencia

La variante reutiliza el punto ya resuelto de la
búsqueda lineal cuando satisface ambos límites de Newton
y queda presupuesto de iteraciones. El banco habilitó
FMA para las operaciones explícitas de suma y producto
compensado. Se midieron juntos ambos cambios. El control
se recompiló con el mismo GNU O3 y sin instrumentación
interna. Se conservaron las leyes, los pasos Radau y
los límites de Newton y Schur.
[Protocolo](VCO_FAMILIA_BUS_VOZ_COSTO_PROTOCOLO.md)

Las 129 lecturas de cada reserva coincidieron bit a bit
con la referencia en los 118 nodos HIGH/LOW, la fase,
J7 y los retornos R59/R60. El biestable de volumen
invirtió su estado en el mismo subpaso y en el mismo
sentido, entre 77,904296875 y 77,90625 muestras desde el
inicio. El orden de los colectores del filtro se mantuvo.
La auditoría del stamp denso incluyó ese subpaso. La
diferencia máxima en las filas de corriente fue 3,31 aA.
Las filas de carga coincidieron y el balance de C27
difirió como máximo 3,39 zA. El error de la derivada de
BUS utilizó hasta 0,001082 del límite.

| Rama | Subpasos por muestra | Control | Variante | Ahorro observado |
| --- | ---: | ---: | ---: | ---: |
| Negativa | 64 | 6,209 s | 5,876 s | 5,4 % |
| Positiva | 512 | 45,344 s | 42,749 s | 5,7 % |

Son tiempos del solver nativo fuera del host, un
recorrido por rama y variante. La compilación candidata
requiere FMA y su ejecución verificó esa capacidad. La
variante queda en el laboratorio. Ambas ramas exceden
el margen de 1,333 ms para 128 frames, por lo que los
dos pases físicos quedan pendientes. Se retiraron los
binarios y tablas regenerables del laboratorio.
[Mediciones](../evidence/vco_family_voice_bus_reuse01.json),
[auditoría](../evidence/vco_family_voice_bus_reuse_tests01.json)
