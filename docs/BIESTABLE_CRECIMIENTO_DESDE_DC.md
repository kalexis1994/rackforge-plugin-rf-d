# Crecimiento BDF2 desde DC: E4G8

## Protocolo declarado antes de medir

Las [ventanas con memoria E4](BIESTABLE_VENTANAS_DE_CRECIMIENTO.md) motivan
un contraste completo desde DC. Se integra una ruta nueva **E4G8** hasta
3 ms. Sólo cambia el umbral de error para duplicar la propuesta: **0,125**
frente al 0,25 de E4. Es una sensibilidad al controlador con tolerancias
fijas, no una tercera política de refinamiento.

Se conservan circuito sintético `finite_transit`, 94 nodos, R61=200 Ω,
BUS=0 V y KEY 0→10 V en t=0. Se usa exactamente la política E4: error
absoluto nodal/juntura 10 nV, relativo 10⁻⁸, incremento de juntura 12,5 mV,
producto modal 0,025, paso máximo 100 µs, mínimo de intervalo real 1 ps y
presupuesto de 12000 intentos. El macro con dos medios requiere ≥2 ps;
la razón de BDF2 y cada crecimiento siguen limitados a 2.

El arranque conserva BE completo frente a BE medio+BDF2 medio solamente
mientras falta el historial previo; publica los dos estados finos. Después
se publica BDF2 completo y se guardan dos medios BDF2 provisionales al mismo
destino binario. No se divide Richardson ni se reinicia memoria tras rechazo.
Los otros dos criterios para crecer siguen en la mitad de sus gates.

Cada publicación y medio guardado debe satisfacer carga sobre historial real,
KCL <10 pA, error de rama <10 fV y restauración exacta. Las fuentes y los
informes anteriores se fijan por SHA antes/después y permanecen intactos.
Se preservan todos los rechazos y cualquier cobertura incompleta.

`python tools/loudness_latch_bdf_growth_dc.py`

## Observación declarada

Se contrasta E4G8 con **E4** y, separadamente, con **D4**. Ambos contrastes
mantienen el reloj original, excluyen puentes del salto de fuente inicial y
conservan el gate de 1 mV. La comparación interpolada es un diagnóstico.
La segunda etapa consulta cada máximo interpolado por nodo (94), la rejilla
fija heredada de 25 µs y 0,5 µs entre 2,4–2,5 ms, 32 medios estratificados
por ruta y el máximo interpolado global. Se deduplican tiempos exactamente.

Se usa el observador conservativo existente, con anclaje anterior y dos
pasos provisionales cuando el resto solicitado sería menor que 1 ps.
Se repite FD en el pico interpolado y en el pico de la selección consultada;
se distinguen registros repetidos de casos distintos. Las consultas no
modifican la trayectoria publicada ni acotan su máximo continuo.

`python tools/loudness_latch_bdf_growth_dc_sampling.py`

## Costo y alcance

Se separan intentos, rechazos, intervalos publicados y medios provisionales.
Se registra tiempo de integración Python fuera de audio, en una ejecución;
no se compara como benchmark con tiempos antiguos ni como deadline.
Incluso si estos contrastes pasan, no hay solución exacta independiente,
refinamiento a tolerancia más estricta, identificación física o audio admitido.
El gate fallido D4/E4 de 7,81 mV permanece en su informe original.

Resultados y regresiones se añadirán cuando termine el experimento.
