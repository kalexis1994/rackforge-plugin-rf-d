# Solver SIMD y margen por callback

2026-11-07. Mantener el FIR contiguo y el banco ASIO a 48 kHz.
Primero recorrer la excitación del invitado sin cronometrar y
contabilizar evaluaciones de Newton por bloque. Vincular cada fila
del perfil con los callbacks previos de 128 frames por ordinal.
Comparar el máximo y la distribución de trabajo del solver en los
bloques dentro y fuera de 1.333 ms. La coincidencia temporal de
los ciclos de CPU se evalúa aparte.

Probar SIMD en el polinomio de las 12 leyes y en filas independientes
del solver y los puertos. Mantener el umbral de cada ley, la ruta
escalar de `exp_m1`, el pivoteo, el orden de productos y sumas por
fila y el criterio de convergencia. Mantener FIR, excitación, ABI,
reloj, política de audio y el resto del host.

Antes de ASIO, exigir igualdad bit a bit con el escalar en las
reservas nominales y de estrés de los tres puntos. Repetir malla
de leyes, endpoints, contraste de 250 ns y fragmentación del FIR.
En ASIO conservar los 2048 frames del banco, alternancia y avance
de 128, cero asignaciones, avisos, fallos de slot y pérdidas de
plazo. Exigir 1.333 ms en todas las filas, incluida la preparación
del primer callback, y la repetición larga para confirmar margen.
Conservar los rechazos y sus replays sin alterar las cotas.

Si la primera variante sigue fuera de margen, especializar el paso
nominal y devolver sólo los puertos en la ruta de audio. Vectorizar
la corrección impar conservando los dos productos de cada término
y sus restas en el mismo orden. Verificar paso a paso los bits del
estado y los puertos de esa ruta frente al inspector, antes de
repetir el banco a 128 frames.

Probar el solve par con almacenamiento por columnas si persisten
los picos. Vectorizar factores y actualizaciones de filas, con el
mismo pivote y la misma sustitución hacia atrás. La comparación de
la traza completa bit a bit permite referir las reservas anteriores
sin duplicar sus datos. Cotejar también la compilación Wasm con
una sola unidad de generación de código y LTO completo si hace
falta confirmar el efecto del código generado.

Medir acumuladores SIMD locales explícitos en los mapas de 4, 12
y 18 filas. Cada acumulador mantiene el orden escalar de su fila.
Los recibos de las variantes y sus replays quedan acotados a
5 MiB, sin duplicar las reservas en las variantes finales.
[Protocolo previo](RECOVERY_ENGINE128_BROADCAST_PROTOCOLO.md)
