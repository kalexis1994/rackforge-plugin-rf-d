# Cierre de carga de los contornos del RF-D

El solver cargado de 118 nodos sirve como referencia
numérica para esta escena nominal. El banco conserva
los dos terminales del tramo de audio y evalúa los
retornos de R59 y R60 por separado. C18 queda en el
contorno de filtro. El piloto audible usa su propia
polarización. [Protocolo](VOZ_REDUCIDA_CONTORNOS_PROTOCOLO.md)

El cierre afín separa 54 nodos interiores de contorno,
62 nodos interiores de audio y dos terminales
compartidos. Sus stamps recompuestos coincidieron
exactamente en 16 anclas, incluidas las transiciones
de KEY y ambos lados de la inversión. El cierre de
cuatro incógnitas Radau pasó 64 direcciones
reservadas contra la resolución densa de 236
incógnitas. La peor diferencia nodal fue 0,209 fV.
Las diferencias máximas de R59 y R60 fueron
3,07e−21 A y 3,00e−20 A, respectivamente. El peor
residual backward normalizado con el piso de
resolución fue 7,90e−12.

Los recibos 01–03 conservan el error de convención
de KEY en el borde de muestra y el diagnóstico del
residual relativo en filas casi sin excitación.
El recibo 04 conserva la primera pasada dinámica.
El mapa completamente afín perdió la inversión.
Con los dos contornos activos, Newton sin
amortiguar salió del dominio de una juntura.
[Diagnóstico de los puertos](../evidence/rf_d_reduced_contour_ports04.json)

Con amortiguación y el VCO afín, el híbrido
reprodujo la inversión en el intervalo de referencia
319096–319104 y mantuvo los retornos dentro de
tolerancia. El peor desvío nodal alcanzó 37,7 mV en
BUS. Al evaluar H128 con su tabla original y la fase
Radau real, el peor desvío bajó a 2,41 mV, en el
colector de Q28. Ese error todavía excedió el límite
nodal. [VCO afín](../evidence/rf_d_reduced_contour_ports05.json),
[H128 activo](../evidence/rf_d_reduced_contour_ports06.json)

Con H128 y las junturas del ladder activas, el
híbrido quedó a 1,19 veces el límite nodal de la
muestra 79. Agregar recuperación y los VCA de
señal redujo el peor error de la ventana 77–79 a
2,69 µV. La inversión ocurrió en los mismos ocho
ticks. El residuo en el cierre de la voz quedó por
debajo de 1 pA. [Comparación de junturas](../evidence/rf_d_reduced_contour_ports07.json)

La misma selección pasó las ventanas independientes
15–18 y 95–98 que contienen los bordes de KEY. Pasó
también 76–81, que amplía la inversión y su
recuperación. En esa ventana el mayor error nodal
fue 9,51 µV y el de J7, 7,03 µV. En todas las
ventanas pasaron ambos retornos. No hubo una
inversión extra del biestable de filtro.
[Reservas independientes](../evidence/rf_d_reduced_contour_ports08.json)

Con el mapa de historia precalculado, las reservas
volvieron a pasar. El bloque negativo autónomo de
128 muestras pasó completo, con 0,569 nV de peor
error nodal. El bloque positivo con una sola
linealización pasó hasta la muestra 44. En la 45
llegó a 39,44 µV en el nodo 110, emisor de la rama
PNP del amplificador de auriculares. El desvío fue
1,19 veces el límite y el de J7 llegó a 22,14 µV.
R59 y R60 seguían dentro de tolerancia. El siguiente
contraste es conservar las junturas de esa rama
antes de probar una renovación del mapa.
[Trayectorias continuas](../evidence/rf_d_reduced_contour_ports09.json)

El híbrido sigue en el banco de laboratorio. Para
medir 128 frames efectivos en RackForge queda cerrar
la trayectoria positiva y llevar el acoplamiento al
motor de audio con un reloj de coste acotado.

## Junturas de salida

Q16/Q11, Q10 y CR1/CR2 de placa 3 se sumaron
como restos exponenciales al mapa afín. El
contraste de cuatro perturbaciones contra el
stamp completo dio errores máximos de 0,142 fA
y 5,50 fS. En la ventana de inversión ampliada
el error nodal bajó de 9,51 µV a 1,29 µV.

Con esa variante, el bloque negativo volvió a
pasar completo y el positivo avanzó hasta la
muestra 64 dentro del límite. En la 65, el nodo
101, a la salida de C2, alcanzó 25,41 µV de
error y usó 1,00058 veces su tolerancia. Los
retornos siguieron dentro del límite y el
desvío en J7 quedó por debajo de 0,584 µV en
las 65 muestras evaluadas.
[Trayectoria con auriculares activos](../evidence/rf_d_reduced_contour_ports10.json)

Al agregar las junturas de la conversión de
placa 4, las ocho perturbaciones de salida
dieron un máximo de 0,142 fA en el resto de
corriente y 9,41 fS en el Jacobiano. Volvieron
a pasar el cierre de puertos, los bordes de
KEY y la ventana ampliada de recuperación.

| Contraste continuo | Rama negativa | Rama positiva |
| --- | ---: | ---: |
| Muestras dentro del límite | 128/128 | 128/128 |
| Error nodal máximo | 0,569 nV | 0,256 nV |
| Error máximo de R59 | 1,09e−21 A | 8,05e−21 A |
| Error máximo de R60 | 4,47e−19 A | 4,47e−19 A |
| Error máximo en J7 | 6,03 fV | 3,01 pV |

En el bloque positivo, la inversión de volumen
conservó el intervalo 319096–319104 y su sentido.
El biestable de filtro conservó su estado. J7 pasó
los tres límites de audio con RMS relativo de
7,31e−10, pico relativo de 7,72e−10 y desvío medio
de 0,195 pV. El recorrido usó una sola linealización,
29 dispositivos activos de audio y la misma malla
fina que la referencia.
[Bloques completos](../evidence/rf_d_reduced_contour_ports11.json)

El contraste queda cerrado para la escena nominal
del solver. La medición a 128 frames efectivos en
RackForge requiere implementar el acoplamiento en
el motor y validar el reloj de ejecución.
