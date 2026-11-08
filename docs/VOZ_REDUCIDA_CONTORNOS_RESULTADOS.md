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
