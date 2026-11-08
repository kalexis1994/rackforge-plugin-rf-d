# Ensamblado conjunto de las dos etapas Radau

2026-11-07. El control es la variante del banco anterior
con filas activas del LU y reutilización de la carga de
junturas. Mantener los 118 estados HIGH/LOW, los cuatro
puertos de Schur, las leyes de carga y la tabla H128.
[Control](VCO_FAMILIA_BUS_VOZ_LATCH_LU_RESULTADOS.md)

Leer una vez la fila de cada etapa fuente y emitir sus
contribuciones a ambas filas de destino. En el almacenamiento
disperso, la primera etapa escribe desde el comienzo y la
segunda desde el final. La lectura recorre cada fila en el
orden original de columnas. Las dos direcciones de escritura
comparten la capacidad de 4096 entradas. Calcular los pesos,
las escalas del LU y el piso de backward en el mismo orden
por fila. Conservar pivotes, factores, reconstrucción y
control de residuales.

Comparar bit a bit la matriz completa de 236 incógnitas en
cada auditoría de etapas, incluida la inversión del biestable.
Probar una topología sintética con soportes distintos por
etapa y cancelación diagonal, exceso de capacidad y producto
no finito, seguidos de un solve válido en el mismo workspace.
Conservar las pruebas de carga, R59/R60, R21, C27 y las
trayectorias de 129 relojes con 64 y 512 subpasos.

Fijar el banco a CPU lógica 9. Medir por separado el
ensamblado del sistema lineal y la resolución completa
en tres recorridos alternados de las cuatro ventanas
anteriores. Comparar el coste sin instrumentación
después de pasar las reservas. El banco físico requiere
margen de 1,333 ms.

## Emisión de filas mediante bits de presencia

Si el recorrido conjunto muestra resultados dispares
por ventana, ensayar por separado un cambio en el armado
del Jacobiano de cada etapa. Registrar en 118 bits las
columnas tocadas por las contribuciones reales. Emitir
en orden ascendente y omitir pares cancelados. Mantener
el operador de suma y los ceros con signo. Comprobar
capacidad antes de publicar una fila y contar pares
cancelados si la capacidad restante lo exige.

Probar contra el emisor anterior en el Jacobiano cargado
y en un caso al límite de capacidad. Repetir las ventanas
y las reservas con el orden de ejecutables invertido.
La variante por bits usa el ensamblador y el LU del
control para separar ambos efectos.
