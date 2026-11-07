# H128 en el dominio cargado del BUS

2026-11-07. Se amplió la familia estacionaria CA3046 a
BUS de −1 a +1 V. Los ocho nodos originales conservan
sus coeficientes, con el tramo central entre −0,125 y
+0,125 V. Se añadieron ocho ciclos de entrenamiento
y se reservaron seis combinaciones CV/BUS independientes
del ajuste. Dos corridas adicionales contrastaron
método y paso en −1,6 V de CV y −0,91 V de BUS.
[Protocolo](VCO_FAMILIA_BUS_VOZ_PROTOCOLO.md),
[reserva estacionaria](../evidence/vco_family_voice_bus_model01.json)

| Magnitud máxima en reserva | Observación | Límite |
| --- | ---: | ---: |
| Frecuencia | 0,08533 cent | 1 cent |
| DC de sierra, triángulo y pulso | 14,57 µV | 5 mV |
| Norma armónica 1–8 de las ondas | 0,01228 % | 2 % |
| IC1_SUM DC o norma 1–8 | 23,47 pV | 10 µV |
| Corriente DC o norma 1–8 del panel | 0,2572 nA | 2 nA |

La tabla periódica Hermite de 4096 fases reduce la consulta
de la sierra a interpolaciones locales. En 1300 consultas,
el error frente a la suma H128 fue de hasta 0,648 µV y
0,0301 nA en el puerto. Se rechazaron ocho entradas fuera
de dominio. R6/R45 se evaluaron una sola vez. Las corrientes
de terminal conservaron KCL y disipación de la red.

## Unión con las cargas

Se eliminan las dos incógnitas de fase por paso Radau.
La frecuencia depende del BUS en cada etapa. Al sustituir
las fases en el residual aparecen cuatro derivadas de BUS
que se incorporan al Jacobiano, con contraste por diferencias
centradas. La carga de C27 sigue entre BUS y BASE_Q29.
El stamp de la cadena conserva el gatillo, C2, C5, las
memorias de junturas y los retornos R59/R60 de ambos contornos.

Las dos ramas arrancan con historias HIGH/LOW retenidas.
La negativa usa el DC monofónico y aplica KEY en las
muestras 16–95. La positiva parte de la historia cargada
a 6 ms del circuito conjunto y libera KEY. Ambas usan CV
de placa fijo a −1,6 V, sin mapeo MIDI adicional.
[Historias de referencia](../evidence/recovery_engine128_mono_tests01.json),
[circuito conjunto](VOZ_DOS_CONTORNOS_RESULTADOS.md)

En las etapas reservadas, las filas de corriente frente al
stamp denso original quedaron dentro de 20 pA y las filas
de carga conservaron el resultado. El balance de C27 se
reconstruyó con sus diferencias de potencial. La primera
liberación a 32 subpasos rechazó un paso Newton y el replay
lo reprodujo. La bisección acotada completó la trayectoria.
El contraste 32/64 aún discrepó 1,101 mV en el nodo 25 al
conmutar el biestable. A 128/256, el peor error nodal quedó
en 1,78 veces el límite. Se conservaron ambas parejas y
sus replays.
[Recibos originales en archivo sin pérdida](../evidence/vco_family_voice_bus_receipts01.tar.xz)

La pareja 256/512 conservó la liberación dentro del gate.
Se reutilizó el recorrido de 256 con el mismo núcleo,
tabla, compilador, biblioteca e historia. En el peor
reloj común, la diferencia fue 7,20 µV en C2, 20,6 nV
en C5 y 1,95 pV en BUS. El mayor error nodal de esa rama
alcanzó 0,9125 del límite. La rama negativa pasó con
32/64 subpasos. Se conservaron ambos retornos cargados
y el contraste de J7 al mismo reloj.
[Auditoría](../evidence/vco_family_voice_bus_tests01.json)

## Coste

| Rama y subpasos por muestra | Tiempo de solver para 128 muestras |
| --- | ---: |
| Negativa, 32 | 5,930 s |
| Negativa, 64 | 10,829 s |
| Positiva, 256 | 28,841 s |
| Positiva, 512 | 55,848 s |

El banco midió el solver nativo de la voz cargada con
bloques nominales de 2,667 ms. Las dos reservas cargadas
son continuaciones a CV fijo. El margen de 1,333 ms queda
rechazado por coste y los dos pases físicos siguen
pendientes. Las reservas del núcleo de recuperación y el
FIR anteriores permanecen ligadas a sus paquetes. Se
retiraron los binarios, tablas y exportaciones temporales
después de auditar los recibos.
