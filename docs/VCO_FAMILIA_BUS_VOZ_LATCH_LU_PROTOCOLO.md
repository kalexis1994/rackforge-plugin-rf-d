# Carga de junturas y filas activas del LU

2026-11-07. Control del banco H128 con Jacobiano directo,
búsqueda ligera, FMA y borde con factor cero omitido.
Mantener pasos, históricos HIGH/LOW, parámetros de
junturas, fuentes y cuatro puertos de Schur.
[Control](VCO_FAMILIA_BUS_VOZ_JACOBIANO_RESULTADOS.md)

La evaluación de carga y capacitancia de ambos extremos
ya comprueba dominio y finitud. Reutilizar esa validación
antes de integrar la juntura. Conservar las ramas de la
integral, el empalme y el orden del residual y la
tangente. Reutilizar la misma exponencial del voltaje
anterior en el término de baja inyección. Contrastar
ambos sentidos del empalme, continuidad, HIGH/LOW y
rechazos de dominio frente al controlador original.

Registrar las filas no nulas de la columna actual
mientras se escoge el pivote. Tras el intercambio,
traducir los dos índices afectados y actualizar sólo
esas filas. Cada fila de interior y su borde son
independientes para el pivote actual. Mantener el
recorrido de columna, regla de desempate, escalas,
división, actualización de cada coeficiente, productos
redondeados y actualización posterior de puertos.
Contrastar intercambios con diagonal nula o no nula,
relleno, ceros con signo y rechazos seguidos de reintento.

Reservas de 129 relojes bit a bit con 64 y 512 subpasos
por muestra. Conservar la auditoría de R59/R60, R21, KCL,
C27, Jacobiano cargado y el intervalo del biestable.
Contrastar los factores y la carga por separado usando
tres recorridos alternados de cuatro variantes. Ventanas
positivas en 52–57, 76–81 y 96–101 muestras desde el
inicio. Mantener la ventana negativa 15–20. Comparar el
coste del banco de 128 muestras después de las reservas.
El banco físico requiere margen de 1,333 ms.

## Confirmación tras la discrepancia de coste

La primera comparación de bloques va con la variante
antes del control. Cuando el perfil por ventanas y el
bloque completo den resultados distintos, repetir con el
control primero. Fijar únicamente los procesos del banco
a la CPU lógica 9, previamente usada por el laboratorio.
Comprobar la máscara heredada en cada ejecutable. Medir
también el tiempo de CPU del hilo de las continuaciones,
que incluye auditoría y registro, además del reloj de
pared alrededor del solver. Conservar la primera prueba.

Repetir ambas reservas con control, combinación y LU
aislado. Mantener cuatro variantes en el perfil de
ventanas y los mismos gates eléctricos.
