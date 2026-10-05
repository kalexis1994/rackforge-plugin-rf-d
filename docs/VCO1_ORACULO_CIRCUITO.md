# VCO 1 CA3046: oráculo de circuito acoplado

## Identidad y fuente

Placa CA3046 SVC-9 Fig. 9-3, PDF p. 5, panel Fig. 9-17, p. 19;
descripción funcional SVC-204D §2.16, pp. 14–15. Se reutilizan los grafos
cotejados, sin sustituir rampa, reset o formadores por ondas analíticas.
La netlist resuelve simultáneamente Qa/Qb/Qc, IC1/IC3, R42, R78 (incluido
220 ohm + 10 nF), C1/C2, Q7/Q8/Q9/Q4/Q3, Q5/Q6/Q10, Q2/Q1 y Q11/Q12.
Las ramas resistivas del panel y el cursor R6 cargan los nodos reales.

La referencia -4 V se resuelve con R166/R174/C14 y la carga Q4/IC3 de VCO1.
Las otras dos secciones no están pobladas en este corte: su corriente neta
es una frontera explícita `external_neg4_load_a`, no una referencia fija
ni la alimentación compartida completa. Los rieles +/-10 y -5 V se imponen.
El bus del mixer se impone y la corriente de R45 vuelve al oscilador.
Es una frontera de laboratorio, pendiente de conexión al filtro real.

## Dispositivos y unidades

[evidence/vco1_laboratory_devices.json](../evidence/vco1_laboratory_devices.json)
registra todos los parámetros de las tarjetas. BJTs: subconjunto
Gummel–Poon NG-46 pp. 138–145 con carga BE/BC, beta directo e inverso
finitos y saturación, pero IS/betas/capacidades/tiempos son hipótesis de
laboratorio, compartidas; no parámetros de fabricante de los dispositivos
Moog. VAF=IKF=0 desactiva Early/alta inyección. Q5/Q6 conservan el conflicto
2N4402/2N3906: una tarjeta PNP común no contrasta esos dos candidatos.

JFET: NG-46 pp. 152–154, ec. 7.25 con B=1. DS-E402-S77, PDF p. 114,
impresa 3-81, aporta IDSS 0.5–5 mA, corte -1…-4.5 V y capacitancias
Ciss=4.5 pF/Crss=1.2 pF típicas a VDS=20 V, VGS=0. Se eligen
IDSS=2 mA y VTO=-2.5 V dentro de esos intervalos; lambda=.003/V y PB=1 V
son hipótesis. Derivación: BETA=IDSS/[VTO²(1+20 lambda)], CGS=Ciss-Crss,
CGD=Crss sqrt(1+20/PB). Las curvas y el sesgo real no quedan identificados.

IC1/IC3 utilizan el macromodelo oficial National/TI LM741 SNOM211B,
con terminales +entrada, -entrada, +riel, -riel, salida. Permanece privado.
Su hash se exige antes del solve. Conserva dinámica y límites de salida;
no demuestra identidad del 741 instalado en un ejemplar histórico.
C4 se ejecutará en perfiles separados de 10 y 100 pF.

## Protocolo antes de medir

Fuentes/modelo/protocolo quedan confirmados antes de correr la netlist.
ngspice46 se verifica por el SHA ya registrado en FUENTES. Cada intento
usa un nombre nuevo y conserva deck, log, export completo y recibo de
fuentes antes/después, incluso al fallar. Ningún intento sustituye otro.

Escena inicial: las seis líneas de control a -2.1 V, R11=500 ohm,
R8=0.5, contacto superior 3 (sierra), inferior 10 (masa), nivel eléctrico
0.5, mixer 0 V y carga adicional -4 V nula. Son estímulos de laboratorio,
no posiciones del panel ni una nota MIDI. Inicialización .ic C1=0 V,
con polarización DC restringida; después ningún reset impuesto.

Primero verificar arranque sostenido durante 15 ms, al menos dos periodos
tras 5 ms, exports finitos/completos y pasos efectivos no mayores al máximo.
Después comparar máximos de paso 500/250/125 ns y Gear2/Trapezoidal2;
frecuencia dentro de 1 cent y excursiones de salida dentro de 5 mV entre
los dos refinamientos más finos. Si hay discontinuidad, informar también
la diferencia por fase sin usarla como error absoluto en el mismo reloj.
Estos criterios son de convergencia del prototipo; no cambian los gates
históricos del biestable ni certifican error entre muestras.

Medir corriente de Qa/Q10, rampa, colector Q3, 9B/21B/20B, referencia -4 V,
Qb, IC1/IC3 y cursor. Explorar teclado +/-1 V, perfiles C4 y posiciones
eléctricas del selector. No usar extremos rotulados en el manual para
forzar amplitudes o conmutación en la netlist.

## Ejecución

```powershell
python -B tools/vco1_circuit_reference.py --label initial-gear500
```

La comparación portable, antialias, mezcla real, tres osciladores,
calibración física y deadline siguen abiertos. Una oscilación obtenida
aquí se denomina oráculo condicionado; no voz RF-D terminada.
