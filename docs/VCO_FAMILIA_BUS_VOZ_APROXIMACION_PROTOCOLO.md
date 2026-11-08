# Reloj variable con detección de aproximación

2026-11-07. Conservar la voz H128, el solver Radau, las
cargas de los dos contornos y las tolerancias del
[reloj validado](VCO_FAMILIA_BUS_VOZ_RELOJ_PROTOCOLO.md).

Medir la separación absoluta de los colectores de cada
biestable. Compararla con la separación de la historia
inicial. Cuando la separación cae por debajo de tres
cuartos de los 9,3 V de alimentación del contorno y se
ha cerrado más de VT/16, limitar la propuesta al reloj
intermedio. Comprobar la señal al inicio y en ambas
etapas. Un ensayo que cruza esa condición con un paso
más grueso se vuelve a resolver desde el mismo estado.
VT y la alimentación proceden del modelo del circuito.
Las fracciones son márgenes numéricos ensayados a partir
del contraste anterior. La regla no usa el tiempo de
conmutación de la referencia.

Fuera de esa región usar bases de 8, 16 o 32 subpasos.
En la región intermedia probar bases de 64 y 128. Mantener
el guard de movimiento y cambio de orden, el paso fino
y los rechazos de Newton del reloj anterior. Seleccionar
por reserva la primera pareja que cumpla los gates, con
prioridad al paso intermedio más grande y luego al paso
más grande de la región estable. Repetir sin cambios
los rechazos.

Exigir los mismos gates nodales, de fase, corrientes y
J7, y el mismo intervalo fino y sentido de inversión.
Repetir la auditoría de R59/R60, C27, R21 y del Jacobiano
cargado. Como contraste adicional, repetir la rama
positiva con fase inicial 0,125 ciclos. Resolver un
control de 512 subpasos desde esa misma historia y fase.
Aplicar los gates antes del contraste de coste.

Tras pasar ambas reservas y el contraste adicional,
comparar con el reloj variable previo de 64/32 en el
mismo binario fijado a CPU lógica 9. Hacer dos pares
por reserva con orden invertido. Medir el solver y
el tiempo de CPU del hilo. El banco físico de 128
frames requiere margen de 1,333 ms.

## Retención después de la inversión

La anticipación inicial conservó la conmutación pero
excedió el límite nodal positivo en la muestra de la
inversión. Ensayar la misma regla con una retención
del reloj intermedio desde el final del paso que
observa la inversión hasta el siguiente reloj entero
de muestra. Se activa por el cambio de orden calculado
en cualquiera de los dos pares. El límite de movimiento,
el paso fino y el guard de Newton siguen aplicándose.
Usar la misma escalera, reservas y contraste de fase.
