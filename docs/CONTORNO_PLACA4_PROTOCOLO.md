# Contorno de volumen cargado por filtro y ambos VCA

Fecha: 2026-10-06. Primera unión SPICE del grafo de contorno completo
con placa 4 y sus cargas, incluyendo memoria Gummel–Poon condicionada.
La unión simultánea VCO/placa 4 sigue nominal; sus tres controles
rechazados y los dos diagnósticos nuevos conservan su estado abierto.

## Fuentes y revisión independiente

SVC-9 PDF p. 9, Fig. 9-7: se revisó nuevamente la hoja completa y el
detalle de contorno/gatillo. Panel en p. 19 Fig. 9-17; decay final en
p. 17 Fig. 9-15; componentes pp. 26–27 tabla 7-6. Placa 4 p. 13
Fig. 9-11. El [grafo existente](../evidence/loudness_contour_graph.json)
conserva sus conflictos de designador y valores candidatos.

Conexiones comprobadas: R36 parte del colector Q20 (TRIGGER_COLLECTOR),
no del colector Q12 (RESET_DRIVER); R28/C4 sí parten de Q12 hacia
base Q25. R56 une colector Q25 y base Q15. R38 une colector Q15 y
base Q25. Q18 de contorno tiene base en R44 y emisor en sustain.
La descripción antigua de reset común confundía el origen de R36;
el grafo ya tenía la conexión correcta. Se corrige sólo esa descripción.

## Circuito y fronteras

Diez BJT del contorno/gatillo más 25 BJT de placa 4. C2=10 microfarad,
C4=10 nF y C7=100 nF mantienen sus nodos originales. Se usan las mismas
tarjetas BJT con carga de juntura y tránsito que la placa 4. Los diodos
de contorno conservan las hipótesis anteriores: n=1.5, Is=1e-8 A para
la familia Ge, 1e-12 A para Si; almacenamiento no identificado y omitido.
No se afirma modelo de fabricante ni se añade lógica ADSR o reset digital.

Pin 7 de placa 2 comparte nodo con pin 9 de placa 4: se elimina la
fuente de contorno impuesta, y R59=68 kohm carga el seguidor con la
corriente de base real de Q18. Todo se resuelve simultáneamente.
La base Q21 del segundo VCA sigue a 2 V; no se cierra su circuito de jack.
El filtro recibe senoide de laboratorio 440 Hz, 0.1 V pico, fuente de
1 kohm. No se resuelve el VCO ni se hereda el gate de su unión.

Alimentación de contorno impuesta 9.3 V; Q26, riel bruto +15 V y carga
del contorno de filtro sobre gatillo/reset quedan abiertos. S-trigger
abierto, teclado PWL: 0→10 V desde 10 ms, 10→0 V desde 200 ms,
ambas transiciones de 10 microsegundos. Son fronteras temporales del
laboratorio, no tiempos medidos de teclado. El circuito no cambia de
fase por un temporizador. No se imponen voltajes de capacitor, estado
del biestable o salida de envolvente.

## Banco congelado

Diez escenas de 350 ms. Nominal: ataque 10 kohm, decay 100 kohm,
sustain inferior 2500 ohm; decay final ON; resistor a Q12 10 kohm,
pullup de reset 3300 ohm. Gear2 con pasos máximos 8/4/2 microsegundos,
Trap2 con 2 microsegundos. Se conservan Sparse, bypass=0, itl4=100,
reltol=1e-7, abstol=1e-13 A, vntol=1e-8 V y gmin=1e-12 S.

Escenas reservadas a 2 microsegundos: ataque 1000 ohm, decay 10000 ohm,
sustain inferior 1000 ohm, decay final OFF, resistor Q12 4700 ohm y
pullup reset 1000 ohm. Se cambia un control por escena.

Tres contrastes 8→4, 4→2 y Gear2→Trap2/2 microsegundos:
máxima diferencia de C2, salida de contorno y salida principal <=5 mV
en grilla común de 20 microsegundos, sin alineación de eventos ni
normalización. RMS de salida en ventanas reposo 2–8 ms, ataque 20–80 ms,
tecla sostenida 120–190 ms y release 230–340 ms: <=1% + 10 microvolt.
No se interpreta esa grilla como cota continua o certificación del reset.

Además, defecto máximo **acumulado** de carga de C2 del contorno y de
C2 de salida <=0.1 nC, integrado sobre todo el reloj no uniforme,
incluidos eventos. Se conserva orientación, rutas de ataque/decay,
corriente a seguidor y CR4 cuando decay final está OFF. La medición
requiere posiciones interiores de ataque/decay; no admite por este
banco topes de potenciómetro. Topes cero del generador se unen exactamente.

Los niveles, picos y cambios con controles se reportan, sin introducir
un objetivo de duración o amplitud después de medir. Todo fallo conserva
fuente, deck, log, export y reloj; fuentes estables y escena completa
son obligatorios. Aceptar este banco sólo cierra la referencia numérica
bajo estas fronteras. Voz con VCO, filtro-contorno, parámetros físicos,
estabilidad continua, ruta portable y deadlines permanecen abiertos.

## Adaptación de escucha prevista

Una escucha posterior exige auditoría del banco completo. Escenas nominal
2 microsegundos, ataque 1000 ohm y decay final OFF: usar los 350 ms
medidos completos de salida principal; no repetir un ciclo. Adaptar reloj
no uniforme por interpolación lineal a 384 kHz, FIR simétrico 1025 taps,
Kaiser beta=8.6, cutoff=21600 Hz, DC global retirada y delay compensado,
padding reflejado, decimación a 48 kHz, PCM16 mono, 8 V/full scale fijo
y fades de 10 ms. Rechazar señal no finita, cantidad de frames incorrecta
o clipping. No se normaliza por escena. Montaje: tres notas de 0.35 s
con dos pausas de 0.15 s; 1.35 s total. El input es una senoide impuesta,
no audio de VCO resuelto bajo carga. La duración limitada y fades no
acreditan que haya terminado el release natural.
