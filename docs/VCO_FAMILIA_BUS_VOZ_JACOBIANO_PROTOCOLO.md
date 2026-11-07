# Jacobiano directo y sustitución acotada de la voz cargada

2026-11-07. Control con búsqueda lineal ligera, reutilización
de Newton, LU contiguo y FMA de la prueba anterior. Usar la
misma H128, ambos estados iniciales, pasos, fuentes, eventos
y criterios del residual. Mantener separados los tiempos
de etapa completa, etapa ligera y resolución lineal.
[Control](VCO_FAMILIA_BUS_VOZ_ARMADO_RESULTADOS.md)

Construir el Jacobiano de audio directamente en la matriz
de 68 nodos de la etapa. Las primeras 66 filas y columnas
retienen sus operaciones y su contraste de finitud. Se
conservan los contactos R21, BUS y C10 y los aportes de
carga que se incorporan después. Contrastar las tres
posiciones de R21 en etapas de ambas historias.

Para las sustituciones del LU, retener la primera entrada
inferior no nula y el extremo superior ya calculado para
la fila pivote. Medir los extremos después del intercambio
y con el relleno actual. Las operaciones retenidas siguen
en el mismo orden. Los ceros omitidos actúan sobre un
operando finito. Reproducir el tramo original si el
acumulador es −0 para conservar el signo. Si la dirección
deja de ser finita, rechazar el sistema como singular.

Probar pivotes intercambiados, bordes, ambos signos de
cero, overflow, una matriz singular y la recuperación
sobre el mismo workspace. Exigir igualdad bit a bit con
el control en las matrices, direcciones y diagnósticos
de los contrastes eléctricos. Verificar los 129 relojes
de ambas reservas y los intervalos de conmutación. Aplicar
los mismos límites de Newton, backward, KCL, C27 y puerto.

Perfilar cuatro variantes en tres recorridos alternados
de las ventanas existentes. Tras pasar reservas, comparar
la variante y el control en las continuaciones de 128
muestras, fuera del host. El banco físico requiere que el
tiempo observado deje margen para 1,333 ms.

## Contraste separado de los bordes externos

Si acotar las sustituciones da resultados dispares,
comparar el mismo LU contiguo con la actualización de
bordes omitida únicamente cuando el factor vale cero.
Guardar el factor con su signo antes de decidir. Antes de
su eliminación, los elementos de borde se inicializan
a +0 o a un coeficiente no nulo, y cada actualización
resta un producto redondeado. Dos valores finitos
distintos representables no pueden tener una diferencia
menor que el mínimo subnormal. Un cero resultado de esa
resta es +0 bajo redondeo al más cercano. La operación
con producto ±0 deja el mismo coeficiente y signo. Los
factores de columnas anteriores se conservan tal como
fueron calculados. Los controles de finitud de la fila
pivote, los factores y la dirección siguen activos.

Repetir las cuatro variantes y los mismos contrastes
de reservas y bordes para aislar este efecto del cambio
en las sustituciones.
