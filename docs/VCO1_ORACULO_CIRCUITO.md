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

## Banco congelado de convergencia

Se extiende la duración de la escena a **30 ms** y se observa periodicidad
tras **15 ms**, para incluir al menos dos ciclos también con teclado -1 V.
[Auditoría de retornos](VCO1_AUDITORIA_RETORNOS.md) establece la topología
vigente; las dos corridas anteriores permanecen rechazadas.

El banco contiene 14 escenas: ambos C4 en Gear2 a 500/250/125 ns y
Trapezoidal2 a 125 ns; teclado -3.1/-1.1 V; pulso superior 4 con contactos
inferiores 10/11/12; triángulo superior 1 con entrada de ancho abierta 8.
No asignar estas combinaciones a leyendas mecánicas sin corroboración.

Criterios adicionales fijados antes de medir: dispersión relativa de
periodos <=1e-5, dirección creciente de frecuencia por CV y ancho de
pulso decreciente por contactos 10→11→12, todos dentro de (0,1). Balance
integrado de corrientes Qa/Q10 sobre dos ciclos frente a delta de carga
C1, discrepancia <=0.002 de la carga de Qa transportada; excluye corriente
mínima/carga de puerta de Q7 y error de cuadratura. Es una observación
finita de conservación, no un certificado entre muestras. El pico por
fase se informa como diagnóstico y no tiene gate que pueda ocultar deriva
de frecuencia. Se conservan las observaciones completas de cada método.

```powershell
python -B tools/vco1_circuit_probes.py --bank convergence-v1
python -B -m unittest discover -s tests -p 'test_vco1*.py' -v
```

## Corrección de lectura del duty y escucha

El primer banco conserva un rechazo de su validador: interpretó la
fracción del estado negativo como ancho HIGH. En 20B el estado bajo es
negativo; el ancho alto es **1 - duty_negativo**. Se corrige sólo esa
interpretación, preservando trazas, circuitos, tolerancias y fallo original.
La validación siguiente recompone métricas desde los 14 exports privados
completos y registra que hubo cero nuevos solves.

El adaptador de escucha usa el último ciclo estacionario medido, integra
exactamente su interpolación lineal no uniforme para obtener coeficientes
Fourier y conserva sólo armónicos debajo de 0.45 Fs a 48 kHz. Quita DC,
aplica **8 V por full scale** fijo y fades de 10 ms; no normaliza por pico.
Estos procesos pertenecen al monitor, no al circuito. El WAV repite el
ciclo estacionario reconstruido; no es una simulación SPICE de toda su
duración ni la voz completa con mixer/filtro/VCA. Sus archivos son locales.

```powershell
python -B tools/validate_vco1_circuit_bank.py
python -B tools/render_vco1_circuit.py
```
