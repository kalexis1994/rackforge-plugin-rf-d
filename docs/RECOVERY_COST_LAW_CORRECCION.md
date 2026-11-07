# Evitar cancelación en el cambio de rama

Previo a corregir y medir coste, 2026-11-06. La primera variante conjunta
pasa las trayectorias, pero rechaza el gate Decimal5e-15 junto al umbral
.001: la rama expm1(z)-z pierde cifras al restar números cercanos. El
fallo y su repetición con la misma fuente quedan en joint01/02, incluido
el stream de leyes y su replay idéntico. No se rebaja el gate.

Extender la evaluación estable a |z|<.125 con Horner de grado12, sumando
z^k/k!,k=2..12, y compartir expm1=z+defecto en esa rama. Resto exacto
<=exp(.125)*.125^13/13! <3.4e-22 antes del redondeo. La otra rama conserva
una expm1 compartida. Es evaluación numérica de la misma ley, sin cambiar
IS, beta, temperatura, matrices, residual, memoria, integrador o puertos.

Ampliar el contraste Decimal con .125 y ambos vecinos de bits, positivo
y negativo, además del antiguo umbral y toda la rejilla. Mantener los
gates del protocolo y publicar qué variante llegó a banco de coste.
