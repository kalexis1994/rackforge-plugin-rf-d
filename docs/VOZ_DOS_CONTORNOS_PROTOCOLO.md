# VCO real con ambos contornos y cadena cargada

Protocolo previo, 2026-10-14. Revisión nominal CA3046, sin unidad física.
Fuentes SVC-9 Fig.9-3 p.5, Fig.9-7 p.9, Fig.9-11 p.13, Fig.9-8 p.10
y Fig.9-17 p.19; hipótesis y valores heredados de los núcleos admitidos.

## Cierre

250 incógnitas: VCO 134 menos corriente de fuente ideal BUS, cadena con
ambos contornos 118 menos BUS compartido. Original 251, con cursor Amount.
BUS pertenece al VCO y recibe C27 y la reacción del ladder. OSC1 ON,
alpha 0.5, sierra del panel original; demás fuentes OFF. Retirar OSC1 de
OnMixer y toda sinusoide impuesta. Q26/Q28/C18 y el gatillo permanecen
únicos. Panel fijo de CONTORNOS_CADENA_PROTOCOLO, C11/C12 OFF, segundo
VCA con 2 V impuestos. CV documentales del VCO -2.1 V, trims R8=0.5 y
R11=500 ohm; C4=10 pF, dispositivos nominales a 298.15 K. No MIDI calibrado.

DC propio con RAMP_C1=0 V impuesto sólo durante inicialización. Registrar
su corriente; liberar esa restricción al integrar. Semillas de los bloques
aislados son aproximaciones numéricas, no una historia admitida de la unión.
Mantener todos los capacitores y junturas durante cada trial. La frecuencia,
formas y reset deben emerger del circuito, sin reloj de oscilador impuesto.

## Banco

Ventana inicial 8 ms desde la nueva raíz; KEY=0 V hasta 1 ms, 10 V hasta
6 ms, luego 0 V. Sin contacto S. Comparar máximos de medio paso 2/1 us,
con tiempos enteros del VCO, observaciones comunes cada 125 us y fuente
constante dentro de cada tramo KEY. Radau dos etapas y step doubling.
Gates heredados: residual nodal 0.1 pA, MNA 10 pV; corrección 2 nV o
2 pA para incógnitas de corriente. LTE VCO 2 uV/2 nA; LTE cadena/contornos
0.2 uV + 2e-7 |V|. Historia fija y publicación atómica de toda la red.

Solver: Schur dinámico de dos LM741 (64 incógnitas por bloque de dos etapas)
y toda la cadena/contornos (234); puertos BUS de ambas etapas. Exterior 138.
Ninguna rama se descarta; guardas de estructura y refinamiento lineal
heredados con gate 1e-11. Comparar solución lineal y residuo original en
candidatos seleccionados; esta partición nueva no hereda admisión automática.

Original Decimal100 VCO más red original de cadena y Amount. Auditar DC
condicionado y parejas seleccionadas con historia fija, filas de corriente
y voltaje separadas. Gates originales 20 pA/0.2 nV para MNA, corrección
1 uV/1 nA; FD de la cadena 2 nS + 2e-5 |J|, memoria de junturas independiente.
Refinamiento al mismo reloj: nodos VCO 20 uV + 2e-6 |V|, corriente 2 nA;
cadena/contornos 20 uV + 2e-6 |V|, R59/R60 2 nA + 2e-5 |I|.
Balance BUS seleccionado 20 pA. Un prefijo no admite la ventana completa.

Conservar fuentes, datos parciales y replay sin cambios antes de reparar.
Límites: 1 GiB libre, 32 MiB nuevos, compilación 120 s, 600 s por perfil,
300 s por auditor. Sin Cargo ni recompilación de la biblioteca. Exportar
audio sólo desde una trayectoria completa admitida, con duración real y
adaptación explícita; 8 ms no se presentan como nota larga. Fidelidad física,
panel general, MIDI y tiempo real quedan fuera de este banco.
