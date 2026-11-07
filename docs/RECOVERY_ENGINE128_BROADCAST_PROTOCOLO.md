# Reservas eléctricas y picos del SIMD

2026-11-07. Mantener RackForge `37e5f803`, la ruta Wasm de
laboratorio y la ABI. Comparar SIMD por pares con una variante que
reutiliza cada entrada escalar en todos los pares de filas. Conservar
el orden de multiplicación y suma de cada fila, sin FMA ni SIMD
relajado. El núcleo conserva tablas, 18 cargas, 12 leyes, solve de
Newton y FIR.

Antes de medir ASIO, ejecutar el núcleo escalar y ambas variantes
SIMD en un banco WASI a O3. Usar las entradas congeladas de las tres
reservas nominales y de estrés de ±0.13 V. Comparar bit a bit los
68 nodos, los puertos, las cargas, las memorias, las corrientes de
defecto y el residuo del solver. Reusar las comprobaciones de rechazo
y reintento sin asignación. Aplicar las cotas existentes a la malla
de las 12 leyes, los 48 endpoints y el contraste contra las reservas
de 250 ns. El banco WASI valida el núcleo y el banco RackForge vuelve
a contrastar la salida del paquete mediante el runtime portable real.
[Cotas eléctricas](RECOVERY_COST_EXP_PROTOCOLO.md)

Repetir a 48 kHz los bancos del motor con ambas variantes, dejando
el mismo reloj, preparación, ruta ASIO, afinidad y política de audio.
Exigir 128 frames efectivos, 2048 frames bit a bit contra el nativo,
cero asignaciones del host, cero avisos y cero fallos de slot. Aplicar
el mismo máximo de 1.333 ms y plazo de 2.667 ms. Conservar la
primera serie y su replay sin cambios si se rechaza. Cotejar picos
con ciclos del hilo y tiempo fuera del render dentro de cada fila.
Los ciclos y las muestras de CPU no identifican por sí solos la
causa de la cola de latencia.

Si la variante de entrada compartida sigue fuera de margen, medirla
con el FIR por dos tramos contiguos. Reusar el candidato de FIR que
mantiene los 769 taps en el mismo orden. Antes de cronometrar,
repetir en WASI los cuatro escenarios y 48 fragmentos por escenario
del banco de equivalencia de voltajes, índices y rechazo atómico.
[Protocolo del FIR](RECOVERY_COST_FIR_PROTOCOLO.md)

Conservar el inventario de evidencia. Guardar recibos acotados antes
de retirar el target, los binarios Wasm y los intermedios del área
temporal única. El VCO y los contornos quedan sujetos al criterio
de tiempo real y permanecen fuera de esta prueba.
