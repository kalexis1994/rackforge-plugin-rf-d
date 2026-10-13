# Gatillo sostenido y liberación: trayectoria propia más larga

2026-10-13, base8e839b8, antes de medir. Proteger3450 fuentes/8034 privados.
Escena ON, biblioteca y circuito229 congelados; historias propias1/2 µs de
la receta pública. Misma topología CA3046, CV, panel, fuentes y cargas de
[la receta](RECETA_CONDICIONADA_RESULTADOS.md). No hay constantes eléctricas
nuevas ni ajuste de componentes a una grabación.

## Calendario experimental

Tick125 ns/65536. Inicio8.438 ms, reposo4 µs, KEY10 V/contactocerrado durante
8 ms desde8.442 ms; KEY0/contactoabierto desde16.442 ms durante4 ms.
Final20.442 ms: **12.004 ms de trayectoria**, incluidos8/4 ms sostenido/release.
Estos tiempos son estímulos de laboratorio, no controles ADSR impuestos.
Los CV del VCO permanecen fijos; la respuesta del contorno/VCA emerge de la red.

Conservar la propuesta1024 ticks e historia propia de cada resolución.
Cortes cada.3 ms y al final exacto de cada fase:1/27/14 targets,43 estados
con el inicial. Los seis grids del prefijo hasta9.942 ms y todos sus STEP,
OBS y estados deben reproducir por bits el prefijo admitido, antes de heredar
su cobertura. La fase sostenida continúa desde allí sin reiniciar memorias.

## Motor, estado y replay limitado

Ejemplo público que usa la rlib admitida; no imports de tests/support, kernel
de tools o archivos privados para inicializar. I/O sólo en el caller offline.
El motor acepta un par por llamada. Cambiar KEY/contacto en el reloj exacto
preserva458 campos HIGH/LOW; no reescribe cargas, fase digital o propuesta.

Exportar todos los endpoints y calendarios,43 estados al mismo reloj,
checkpoint3720 bytes RFHLD001 con metadata estricta y selected triples
coarse/mid/end al inicio/final de fases, resets y antiguo final sostenido9.942 ms.
Contornos/corrientes, BUS y J7 continúan con las cargas resueltas originales.

Evitar acumular Accepted de una ventana larga. Hasta tres motores sombra
reproducen los siguientes16 accepted de cada checkpoint de fase, interior o
reset, usando el mismo target, Workspace serial y fuentes. Comparar todos
los bits de Pair, observables, estado/propuesta; al final de fase sólo el
prefijo disponible. Gate explícito de capacidad3, sin heredar memoria/RT por
el tamaño de objetos o por ausencia de un Vec grande. El caller hace I/O/heap.
Cuatro corrupciones, destino inválido y presupuesto1 rechazados con rollback.

## Gates eléctricos y de refinamiento

Auditor independiente existente: grafo original, cargas de juntura Decimal100,
balances y FD de la cadena. Evaluar todos los selected triples y sus458 filas
por par; LTE recomputado desde historias completas. No sustituir el oráculo
por llamada al solver Rust. Para todos los accepted, validar clock, h, LTE,
intentos y política de propuesta; KCL del BUS≤20 pA.

Nueve integrales nativas por fase y total, pesos Radau.75/.25: C2,C18,C27,
C7,C4 y las cuatro memorias de Q25/Q15 con retornoC4 orientado. Auditor
recomputa ΔQ con Decimal100; gate1 pA·duración. No describe esa integral
nativa como cuadratura independiente de cada etapa.

Al mismo reloj, todos los229 estados1/2 µs: error≤2 µV o2 nA para coordenadas
98..132, sin cambiar tolerancias del oráculo anterior. Número de resets igual;
interpolación de su bracket: diferencia≤10 ns. Observar al menos tres resets
en la ventana y dos completos con KEY sostenido. Comparaciones de waveform
por fase son diagnósticos adicionales, no cotas continuas.

Preservar fallo y replay sin cambios antes de reparar. No continuar una escena
rechazada mediante otra raíz o historia, ni relajar gates para admitir duración.

## Escucha y recursos

WAV nativo mono48 kHz, sinc18 kHz/Blackman y cuadratura8/16 de la adaptación
ya admitida; escala fija0.01 V/FS, sin normalización, DC removal, fades o loop.
576 frames/12 ms, cola4 µs omitida. Contraste1/2 µs de audio≤2 µV y≤7 LSB;
cuadratura≤.25 LSB y≤1 LSB; payload completo PCM16 por bytes.
Microscopio100× opcional conserva su rótulo y altera tiempo/frecuencia;
no simula1.2 s de circuito. Un fragmento12 ms sigue siendo una escucha corta.

Diagnóstico de dos últimos ciclos completos sostenidos, definidos por reset
ramp<−2→≥−2 V; fase interpolada con brackets,2049 puntos. Gate para proponer
una repetición de inspección: max|ΔJ7|≤5 µV **y**≤2 % del RMS AC del último
ciclo, RMS AC≥0.1 mV; seam≤5 µV; diferencias de ciclo entre resoluciones≤2 µV.
Si falla, conservar diagnóstico sin producir un loop. Una comparación finita
de J7 no admite periodicidad del estado completo o estabilidad asintótica.

Compilación nueva del ejemplo≤120 s, sin rlib/cache Cargo nuevos. Dos perfiles
secuenciales≤1590 s cada uno, guard interno1500 s, campaña≤3300 s. Oráculo
≤600 s; disco nuevo≤96 MiB, reserva1 GiB, stack experimental32 MiB. No exigir
un replay completo de toda la duración si los restores locales pasan.
Tests históricos255 heredados por identidad; ejecutar sólo integración nueva
que resuelva un riesgo concreto. Deadline y fidelidad física permanecen abiertos.
