# Reducción a cargas de la cadena cargada

Protocolo previo, 2026-10-31. Primer núcleo de coste bajo derivado del
circuito: linealización local de chain_charge68, sin cambiar componentes.
No es aún el núcleo no lineal de producción ni una voz con contornos.
Mantener el solver completo y el rechazo nodal1 uV de MONO_VOICE intactos.

## Frontera y unidades

SVC-9 Fig.9-11 p.13, Fig.9-8 p.10, Fig.9-17 p.19 y las hipótesis del
grafo68 anterior. Dos escenas separadas R61=200/L1 y200000/L0; resto de
parámetros de mixer_chain_lab/controlled_boundary(0,true), sin OSC1 en
OnMixer. Puerto externo OSC1, cursor R6=.5: Ibus=(BUS-.5*U)/39250 A.
U es tensión impuesta de prueba, no VCO H128 o su dependencia de BUS.
No sumar la resistencia del puerto dos veces. DC propio para U=0 V,
VCA1/2=2 V y cutoff/range fijos anteriores. Incrementos de nodos en V,
cargas en C, G en S, M en F, B en A/V, tiempo en s.

Construir incidencia A de TODOS los capacitores de chain_charge,
incluido C10 explícito; verificar rango, no fijarlo por suposición.
q=A*x son voltajes capacitivos (la carga es diag(C)*q). Completar las
coordenadas con potenciales algebraicos z, x=T*[q,z], mediante un mapa
invertible. Congruencia T^t*G*T y T^t*M*T conserva trabajo/retornos.
Eliminar z por Schur sólo después de comprobar masa nula en sus filas.
No truncar modos, descartar capacitores pequeños o dejar puertos ideales.

Preparar fuera de audio la transición SDIRK2 L-stable de la ODE de cargas,
gamma=1-1/sqrt(2), para entrada lineal entre extremos. Reconstruir nodos
y corriente BUS desde q y U; la alimentación directa algebraica pertenece
al puerto. No reinicializar memorias al cambiar entrada. Datos generados
de G/M/DC, sin ajuste a las trayectorias reservadas.

## Contrastes y gates

- M=A^t*diag(C)*A, error máximo<=1e-20 F; T inversa<=1e-12 absoluto;
  eliminación algebraica/KCL<=1e-12 A en estados seleccionados.
- Transferencia compleja del reducido y solve directo68 a33 frecuencias
  log10(10..24000) Hz: todos los nodos <=1e-8 relativo +1e-12 V/V,
  corriente <=1e-8 relativo +1e-15 A/V. Derivar denominadores por señal.
- Mismo SDIRK discreto reducido/directo68, sin usar raíz reducida como
  semilla de un solve no lineal. Conservar carga18 y balance de puerto.
- Reserva no lineal: U=a*(sin(2*pi*137*t)+.3*sin(2*pi*1103*t)),0..4 ms,
  a=1e-5 y1e-3 V en ambas escenas; pasos500/250 ns. Misma entrada en las
  etapas reales; DC independiente del mapa reducido. Todos los nodos1 uV,
  BUS1 uV, panel2 nA, J7 RMS .001 y pico .003 con media1 uV; absoluto
 1 nV si la salida es casi cero. Si falla, conservar amplitud/gate/replay
  y declarar dominio rechazado, sin ajustar usando los casos reservados.
- Rust y Python en el mismo reloj: error <=1e-11 V de estado/nodos,
  corriente<=1e-15 A; input inválido conserva estado por bits y heap cero.

## Coste y alcance

Banco a384 kHz, salida FIR48 kHz heredada y latencia1 ms, bloques128.
Cronómetro externo, mil bloques completos como mínimo, primero incluido,
setup fuera del intervalo, sin IO/alloc/locks dentro. Objetivo<=50% de
2.6667 ms por bloque, cero deadlines observados; no WCET o admisión de
la voz completa. Declarar exactamente puertos y funciones incluidos.
Comparar coste sólo con el alcance equivalente, sin dividir tiempos de
la voz119 por el tiempo de un bloque lineal fijo para vender una mejora.

Una sola tmp/lab-current, compiler/rlib congelados, sin Cargo/cache/WAV.
Procesos<=240 s, evidencia<=16 MiB sin QA. Fuentes,8769 inputs y escucha
previos protegidos. Fallos con fuente/input/replay antes de corregir;
recibos nuevos únicos. Cerrar por separado reducción lineal, dominio
no lineal, coste de este bloque y tiempo real de la futura voz.
