# Controlador E4G8 con Newton compensado: protocolo previo

Tras archivar la equivalencia de los 6.486 intervalos impuestos (`bb2358f`),
ejecutar **una trayectoria adaptativa nueva** desde DC hasta 3 ms con
`increment-pair/compensated-static-J66/v1`. KEY 0→10 V, BUS=0, r61=200 Ω,
modelo Q25/Q15 `finite_transit` escala 1. No hay hardware de referencia.

## Cambio y controles fijados

Copiar explícitamente el driver E4G8 congelado y cambiar sólo la construcción
`BdfNetwork` por `CompensatedBdfNetwork`. Antes de ejecutar, comprobar igualdad
del AST de ambos drivers tras normalizar exclusivamente ese identificador;
exigir exactamente una sustitución. No parchear globals ni clases históricas.
Mantener los mismos objetos de funciones de arranque, estimador, publicación,
cálculo modal, límites y Policy. No cambiar el Jacobiano compartido del guard
modal: este experimento sustituye sólo J de Newton.

Mantener Policy E4: voltajes/junturas absolutos y relativos 10⁻⁸;
incremento máximo de juntura 0,0125 V; producto modal máximo 0,025;
h máximo 100 µs, mínimo 1 ps, 12.000 intentos; crecimiento de error 0,125.
La política conserva arranque BE-completo contra BE-medio/BDF2-medio,
BDF2-completo contra dos medios provisionales, publicación del completo,
restricciones de dominio y crecimiento ≤2. Sin factor Richardson.

El driver conserva rechazo, reducción del intervalo, final y presupuesto
originales. Es reducción propia del controlador fijado, sin añadir
recuperación por otra semilla, raíces alternativas o reset. Archivar todos
los pasos publicados, sombras, predictores de arranque, rechazos y mensajes
disponibles. KCL, corrección, publicación, restauración e historiales
conservan sus gates previos; ninguna diferencia de referencia los relaja.

## Contrastes registrados

1. Estado DC completo nuevo frente al E4G8 archivado: igualdad canónica.
2. Proyecciones de ensayos aceptados (inicio, h, cantidad de pasos) y
   rechazados (tiempo, h, razón): igualdad exacta, conservando ambas listas
   incluso si cambian. No imponer ahora el reloj guardado.
3. Reloj, intervalos, fuentes y método publicados: igualdad exacta. Si
   coincide, comparar todos los 94 nodos compensados y 25 memorias bajo
   **10 nV absoluto**; cargas con escala 10⁻¹² C/V exclusivamente numérica.
   Si difiere, no hacer correspondencia por índice ni retimar para aprobar.
4. Si el reloj coincide con el experimento de reloj fijo, verificar igualdad
   canónica de cada estado publicado con ese candidato. Las sombras
   provisionales no deben contaminar su memoria aceptada.
5. Repetir sólo el comparador lineal histórico contra D4 y E4, gate **1 mV**,
   como diagnóstico separado. Conservar máximos, final, dominio y fallos;
   no presentarlo como consultas independientes ni cota entre muestras.

Contar ensayos/intervalos publicados y provisionales por separado. El conteo
y tiempo de laboratorio no prueban deadline. Identificar fuentes/datos
antes/después, driver y AST, todas las salidas y gates abiertos. Equivalencia
del controlador significa reproducir su conducta bajo este experimento;
no prueba que estime correctamente el error temporal global. Física,
audio, mapa espacial independiente y cota temporal permanecen pendientes.

`python tools/loudness_latch_bdf_static_precision_adaptive.py`
