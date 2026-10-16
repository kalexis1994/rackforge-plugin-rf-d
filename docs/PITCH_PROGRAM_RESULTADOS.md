# Programa experimental de frecuencia y KEY

[Contrato](PITCH_PROGRAM_PROTOCOLO.md),
[ley de fase](../crates/rf-d-circuit/src/pitch_phase_source.rs),
[programa](../crates/rf-d-circuit/src/pitch_program_schedule.rs),
[productor](../crates/rf-d-circuit/src/pitch_program_producer.rs),
[derivación de variantes](../tools/prepare_pitch_program.py),
[banco](../tools/pitch_program_probe.rs),
[recibo admitido](../evidence/pitch_program_native03.json) y
[QA](../evidence/pitch_program_tests01.json).

## Qué se admite

Un adaptador en Hz del ciclo nominal CA3046/SVC-204D existente, con
fase continua, KEY independiente y unión real a la cadena cargada.
No se modifica el motor nominal activo ni su render o escucha admitida.
El ciclo conserva DRIVE/TRI, DC, reset e interpolación de la referencia;
la red original R6/R45 y BUS se resuelve en cada etapa, sin fuente ideal
de voltaje sobre J7, ganancia nueva o condensadores reiniciados.

Transponer el ciclo es una aproximación experimental. La forma interna,
respuesta al BUS y carga dinámica del VCO físico pueden depender del CV
y de la frecuencia. Este ensayo no identifica esas dependencias ni valida
una ley de teclado/MIDI, trims, modulación o tres osciladores. La física
de la red resistiva de salida y la precisión numérica de la cadena son
claims separados de esa incertidumbre del generador reducido.

## Contrato y memoria

Program fija hasta ocho eventos inmutables de frecuencia Hz y KEY, con
resolución de microsegundo entero y final de grilla 125 us hasta 301 ms.
Inicialmente f0/KEY OFF para conservar el DC; dominio de frecuencia de
la API [f0/2,2 f0]. La cadena se ensaya en f0,1.5 f0,0.5 f0; no se
atribuye el contraste de esa escena a cada punto del dominio de la API.
f0=410.801335673881 Hz, tomado de la referencia nominal, sin ajuste a 440 Hz.

Cada segmento usa phi(t)=phi_e+(t-e) f. Al retunear se calcula phi_e con
la ley anterior; KEY solo conserva la ley y todos sus bits. La ley inicial
repite exactamente (t-epoch) f0. Newton consulta una función inmutable por
tiempo absoluto: evaluaciones repetidas/fuera de orden o pasos rechazados
no avanzan un acumulador de fase. El paso se corta en eventos y grilla;
el lado izquierdo termina con su ley y el siguiente comienza con la nueva.

El productor retiene el Accepted completo si falta espacio. Las pausas
forzadas en KEY/retunes conservan estado/etapas/incrementos/contadores y
se reanudan con cuota cero/Clone/workspace nuevo. No hay proyección de
HIGH/LOW, reset de fase o redisparo del contorno en los dos retunes.
El programa permanece fijo mientras exista un Accepted pendiente.

Las seis variantes se derivan mediante reemplazos acotados verificables:
parámetro de fase, enlace de fuente, inicializador/lector y planificación
de eventos. Solver, Newton, estimador, cargas, polinomio de lectura, FIR
y latencia son los admitidos. Sus fuentes originales siguen intactos.
sizeof productor=36776 bytes; programa=400 ya
incluido; workspace=279824 separado. Heap cero en procesamiento
y clones. No es una prueba de pico total de stack, coste total o deadlines.

## Identidad nominal y fase

4097 tiempos con BUS variable conservan por bits las cuatro corrientes,
16 admitancias, tensiones internas y potencia frente al observador nominal.
Balance de corrientes y tangente conservativa pasan; se conserva la red
resistiva original. Las consultas por fase a las tres frecuencias mantienen
el balance. Decimal100 en 99 observaciones del programa da error máximo
1.720575e-15 ciclos sin envolver y
1.720575e-15 ciclos de fase, gate 1e-12.
Cada retune conserva la fase por bits. Reiniciar la época falla el control
negativo (>1e-3 ciclos), sin cambiar gates para acomodarlo.

Nominal real 0–10 ms, KEY ON 1 ms, máximo 1 us: variante y control anterior
independiente completan 10109 pasos cada uno. DC, 236 HIGH/LOW, Accepted
completos, coarse/fine, etapas, incrementos, h/error e iteraciones/intentos
son idénticos por bits. También los 3841 RAW y 433 AA8 respecto del
prefijo fino archivado. No se repite la nota larga de 301 ms.

## Secuencia y refinamiento

Escena de 24 ms: KEY ON 1 ms; f0→1.5 f0 a 6.25 ms y →0.5 f0 a
12.5 ms, manteniendo KEY; OFF 18.75 ms. Cuerpo de salida 0–23 ms y
soporte físico hasta 24 ms: 9217 RAW y 1105 puntos a 48 kHz, incluido
el ancla. Valores e índices coinciden por bits con el batch FIR anterior.
Fronteras de eventos y puertos antes/después coinciden; no hay un retune
oculto dentro de un paso. Los snapshots conservan todas las memorias.

El [primer intento](../evidence/pitch_program_native01.json) y su replay
fallan en el banco de pausas: un bloque podía saltar el índice elegido
para forzar capacidad cero. La [corrección](../evidence/pitch_program_capacity_correction01.json)
limita el consumidor hasta la próxima frontera, sin cambiar el motor.
También se conserva el [error previo del generador](../evidence/pitch_program_preparation_failure01.json)
y replay: escape de newline en el adaptador, anterior a cualquier solve.

El [par 2/1 us](../evidence/pitch_program_native02.json) pasa las uniones
pero falla el error RMS de retune_up: 0.112353 % frente a 0.1 %. Conservar
su repetición de análisis y la [decisión de refinamiento](../evidence/pitch_program_refinement_decision01.json).
El contraste 1/0.5 us previsto pasa los mismos gates; perfil fino seleccionado
0.5 us para esta secuencia. No generalizar el máximo de la nota fija.

| Ventana, par 1/0.5 us | RMS relativo | Máximo/pico | Media absoluta |
| --- | ---: | ---: | ---: |
| whole | 0.017778 % | 0.045770 % | 0.009654 uV |
| first | 0.004387 % | 0.006093 % | 0.000208 uV |
| retune_up | 0.055032 % | 0.076379 % | 0.160056 uV |
| retune_down | 0.006207 % | 0.013051 % | 0.100782 uV |
| release | 0.002625 % | 0.002682 % | 0.139036 uV |

Gates: RMS <=0.1 %, máximo/pico <=0.3 %, media <=1 uV; pre-KEY absoluto
<=1 uV. Newton <=1 pA/2 nV y estimador <=1 en ambos perfiles. Separadamente,
192/384 kHz sobre cada historia pasa RMS <=0.01 %, máximo/pico <=0.03 %
y media <=0.1 uV. Máximo RMS relativo de tasa observado 9.089684e-08.
No es una demostración de ausencia universal de alias o de fidelidad física.

Cuatro tests nuevos: continuidad/pureza de fase, entradas inválidas,
validación de programa y frontera derecha. Se ejecutan en tres intentos:
12 invocaciones de cuatro definiciones; seis tests anidados se filtran.
Se heredan 267 tests anteriores y se cubren 271. Se conservan fuentes,
inputs, fallos y replays; ninguna fila original nueva se declara por
sólo conservar las ecuaciones. Dos perfiles controlados nuevos admitidos,
con dos recibos previos fallidos y sus replays diferenciados.

## Almacenamiento y continuación

Compiler/rlib congelados. Sin nuevo WAV, cache, Cargo, biblioteca o input
sonoro privado. El único WAV previo permanece por SHA; tmp/lab-current
queda vacío. Los recibos contienen sólo datos acotados para reproducir
los controles; no carpetas de muestras. El motor nominal activo conserva
su origen y los perfiles anteriores conservan su alcance.

Siguiente: unir este programa al render offline para una secuencia de
duración musical, con etiqueta de transposición experimental y un único
resultado regenerable. Mantener aparte el contraste de curvas CV/forma/
carga del VCO físico, necesario para promoverlo a emulación general.
