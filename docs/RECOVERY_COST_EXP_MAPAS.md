# Contraste de los mapas exponenciales

Previo a corregir la comprobación, 2026-11-06. El test de identidades
heredado de una sola entrada en voltios se aplicó a trece columnas con
unidades distintas y cancelación. En la columna de corriente, restar
pesos/h menos forcing deja ~-3.89e-7 tras operandos del orden de 1e10;
la diferencia observada es5.63e-6, y el escalado por el resultado casi
nulo falla. El recibo conserva el error y el replay idéntico.

No cambiar los mapas ni los gates físicos. Medir el error hacia atrás de
la identidad por magnitudes de los operandos antes de cancelar, con el
gate1e-10, y añadir una exponencial independiente de matriz aumentada
por Taylor/escalado/cuadrado en los tres puntos de producción. Normalizar
columnas de fuerza en ese cálculo, recuperar unidades antes de comparar.
Exigir1e-10 relativo a la norma de cada mapa de referencia independiente.
Esto separa el error de la comprobación cancelante de un mapa incorrecto.

El primer cociente hacia atrás, componente a componente, también rechazó
una fila casi desacoplada: escala1.51e-6 en esa fila frente a1.47e7 para
su columna. Se conservó su replay. La norma final es infinito por columna
de entrada, no un cociente por cada entrada casi nula. Las comprobaciones
de mapas independientes, nodos, puertos y etapas siguen siendo obligatorias.
