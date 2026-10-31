# Nivel, cutoff y memoria entre puntos locales

Protocolo previo, 2026-10-31. Continuar CHARGE_REDUCED sin alterar datos,
gates, voz, escucha o entradas admitidas. Perfil R61=200/L1 únicamente;
no extender automáticamente R61=200000. Mismos componentes SVC-9,
puerto OSC1 (BUS-.5*U)/39250, loudness1/2=2 V, range=.1 y resto fijo.

Preparar tres DC/G/M independientes con cutoff .49/.50/.51 (fracción
desde -10 V de PanelBoundary, sin convertirla en Hz). Condensación18/50
con la incidencia anterior, todos los capacitores conservados. Sin
interpolar matrices o ajustar con trayectorias reservadas.

Mapa reservado de nivel: U=a*(sin(2*pi*137*t)+.3*sin(2*pi*1103*t)),0..4 ms,
a=.01/.1/1 V en los tres puntos,500/250 ns. Mantener los gates:68 nodos
1 uV, corriente BUS2 nA, J7 RMS .001, pico .003, media1 uV, fallback
absoluto1 nV cerca de cero. Informar aceptación/rechazo por punto/nivel;
un fallo del aproximado no es fallo de ejecución del oráculo. Conservar
el caso y replay numérico idéntico de las reservas que rechacen dominio.

Ensayo dinámico: input a=.01 V, cutoff inicial.50, cambios a.51/.49/.50
en1/2/3 ms, hasta4 ms. Referencia corta exactamente en eventos, con el
punto derecho gobernando las etapas posteriores. Las cargas y corriente
integradas no se reinicializan. Exportar DC HIGH/LOW de los tres puntos.

Familia candidata: estado persistente de voltajes absolutos de18
capacitores HIGH/LOW. Para cada punto q_delta=Qstate/C - q_dc; avanzar
con el mapa local y volver a sumar q_dc con compensación. Cambiar índice
no cambia Qstate/C, ni fase de la entrada. La salida suma DC y conserva
alimentación directa. Los rieles fijos/offsets de capacitor se declaran
aparte; coordenadas A*x omiten constantes de riel que no cambian aquí.
El estado inicial es DC preparado, no capacitores físicamente descargados.

Comparar primero Python/familia al mismo paso del oráculo y luego384 kHz.
Gates anteriores sin relajarlos. Un reset a DC al cambiar punto debe
ser detectado por balance de cargas aunque parezca mejorar el error.
Conservar rechazo del candidato si pierde algún gate. Una guarda de
amplitud y un selector discreto no certifican todo gesto de cutoff.

Rust/Python: <=1e-11 V nodal/estado, <=1e-15 A de puerto; negativos
conservan estado por bits, incluyendo ceros con signo. Medir familia
con cambios discretos más FIR48 kHz,1200 bloques128, primero incluido;
sin IO/reloj/heap/locks en procesamiento. Objetivo50% de2.6667 ms,
ningún deadline observado >100%; no admisión de voz completa o WCET.

Almacenar sólo puertos completos y estados seleccionados cada64 pasos,
extremos/eventos/peor error, después de métricas en rejilla completa.
Un tmp/lab-current, export transitorio por proceso<=32 MiB y240 s;
recibos<=12 MiB sin QA. Retirar cada export después de su SHA y métricas;
no prometer recuperar la rejilla ausente. Compiler/rlib congelados,
sin Cargo/cache/SPICE/WAV ni otras carpetas de muestras.
