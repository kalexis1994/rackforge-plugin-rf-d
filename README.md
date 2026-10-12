# RF-D

RecreaciÃ³n de circuito del Minimoog Model D clÃ¡sico para RackForge, bajo
[RACE](https://github.com/kalexis1994/rackforge-race/blob/main/README.md). Primer perfil: placa osciladora CA3046
nominal documentada; [revisiÃ³n y alcance](docs/OBJETIVO.md). No hay ni habrÃ¡
un instrumento fÃ­sico de referencia. La equivalencia numÃ©rica de un modelo
no acredita identidad sonora con una unidad vintage.

## Estado actual — 2026-10-12

| Ruta | Resultado disponible | Alcance pendiente |
|---|---|---|
| Cargas BE/BC y GS/GD | [Primitiva nativa](docs/VCO_CARGA_JUNTURA_RESULTADOS.md), 1280 vectores y derivadas | Transporte/difusión, binding térmico y dispositivos completos |
| BJT NPN/PNP de VCO | [Transporte y cargas nativos](docs/VCO_BJT_NOMINAL_RESULTADOS.md), 1536 vectores y doce escenas SPICE | Parámetros físicos, otras temperaturas y trayectoria estacionaria |
| JFET E402 de VCO | [Canal y cargas de una mitad](docs/VCO_JFET_NOMINAL_RESULTADOS.md), 2028 vectores y doce escenas SPICE | Parámetros físicos, otras temperaturas y trayectoria estacionaria |
| LM741 de VCO | [Stamp completo](docs/VCO_741_NATIVO_RESULTADOS.md), 37 incógnitas, cinco memorias, 60 vectores y seis DC propios | Parámetros físicos y trayectoria VCO estacionaria |
| Puerto LM741 | [Newton y cinco derivadas cargadas](docs/VCO_741_PUERTO_RESULTADOS.md), seis DC, nueve trayectorias/672 pasos y 371 intervalos SPICE | Cierre activo con mixer y deadlines |
| VCO1 nativo ensamblado | [Circuito completo de 134 incógnitas](docs/VCO1_STAMP_RESULTADOS.md), 40 casos, Jacobiano completo y contactos exactos | Arranque propio, ciclos completos y carga activa |
| VCO1 arranque propio | [Diez raíces propias](docs/VCO1_ARRANQUE_RESULTADOS.md), semilla de circuito y contraste independiente | Reset/refinamiento temporal: pasos fijos rechazados; carga activa |
| VCO1 motor portable | [Arranque/checkpoint y cuatro tests nativos](docs/VCO1_PORTABLE_RESULTADOS.md), 26 comparaciones de etapas y heap cero | Referencia nominal; carga conjunta, stack/deadline y host pendientes |
| VCO1 Radau nominal | [Dos recorridos propios de30 ms](docs/VCO1_RADAU_CICLOS_RESULTADOS.md), periodicidad/refinamiento y escucha nativa aislada | CV/trims reservados, C4=100 pF, carga activa y producciÃ³n/RT |
| VCO1 puerto 741 exacto | [70 incógnitas exteriores, 12 sistemas y nueve pares de raíces](docs/VCO1_741_CONDENSACION_RESULTADOS.md) | Laboratorio Decimal100; error dinámico del puerto y reset temporal pendientes |
| VCO1 integración/rigidez | [SDIRK contrastado y modos rápidos locales](docs/VCO1_SDIRK_RESULTADOS.md) | Dos continuaciones rechazadas; contrato exacto cerrado localmente en el bloque del puerto |
| VCO1 grilla de reset | [22 raíces contrastadas y segundo piso temporal](docs/VCO1_RESET_GRILLA_RESULTADOS.md) | Prefijo privado de 189 ns; analizar dinámica/integración 741 antes de ampliar |
| VCO1 incrementos/memoria | [50 raíces y 897.800 derivadas; precisión recuperada](docs/VCO1_INCREMENTOS_RESULTADOS.md) | Reset rechazado por error temporal a 2,434 ms; grilla más fina |
| VCO1 subpasos/control temporal | [48 stamps y 28 raíces locales; controlador atómico](docs/VCO1_SUBPASOS_RESULTADOS.md) | Referencia histórica: límite de representación recuperado localmente en el bloque de incrementos |
| VCO1 Newton conjunto | [Dos DC condicionados y seis continuaciones/224 pasos](docs/VCO1_NEWTON_RESULTADOS.md), memoria atómica | Semilla propia, ciclos completos, refinamiento y carga activa |
| VCO1 de referencia | [Circuito funcional, convergencia y calibraciÃ³n](docs/VCO1_RESULTADOS_CIRCUITO.md) | Trayectoria nativa de ciclos completos y carga activa; osciladores 2/3 |
| Mezclador ON y C27 | [Puerto dinÃ¡mico con memoria](docs/MEZCLADOR_C27_RESULTADOS.md), 837 casos nodales | OFF, taper e impedancias reales de generadores |
| Entradaâ†’ladderâ†’VCAsâ†’J7 | [Entrada directa nativa](docs/MEZCLADOR_DIRECTO_RESULTADOS.md), 12 escenas/192 pasos a 500/250/125 ns | Contornos y generadores todavÃ­a impuestos |
| Carga vista por las fuentes | [Puerto directo 5Ã—5 a 125 ns](docs/MEZCLADOR_DIRECTO_RESULTADOS.md), candidatos y tangentes | Cerrar VCO real con estas corrientes y tangentes |
| Contorno de volumen | [Puerto C2/reset y cadena cargada](docs/PUERTO_CONTORNO_CADENA_71.md), laboratorio de conmutaciÃ³n | IntegraciÃ³n estable del contorno completo y contorno de filtro |
| Voz monolÃ­tica SPICE | [Banco corto admitido](docs/VOZ_SEIS_ACTIVO_RESULTADOS.md); [largo rechazado](docs/VOZ_SERIAL_CAMPANA_RESULTADOS.md) | Nota larga completa con sus tres contrastes |
| Producto | NÃºcleos y herramientas de laboratorio | Voz nativa completa, recursos, MIDI/host y paquete instalable |

El [cierre eléctrico conjunto](docs/VOZ_BUS_CONJUNTO_RESULTADOS.md) une VCO1 y
la cadena hasta J7: cuatro pasos y ocho etapas contrastadas localmente.
Ese banco comprueba pasos locales; la continuación está en el motor siguiente.

El [motor temporal conjunto](docs/VOZ_MOTOR_TEMPORAL_RESULTADOS.md) admite
cuatro continuaciones de2 µs, control LTE, restore exacto y rollback.
El [primer ciclo con carga activa](docs/VOZ_PRIMER_CICLO_RESULTADOS.md)
ya pasa dos perfiles de5,25 ms: dos resets, un ciclo transitorio, balances
y refinamiento al mismo reloj. Conserva dos pausas administrativas y sus
continuaciones exactas; no admite aún una nota asentada.

La [inicialización conjunta condicionada](docs/VOZ_INICIALIZACION_RESULTADOS.md)
ya resuelve DC con C1=0 desde dos semillas y libera dos perfiles de2 µs.
Contrasta400 ecuaciones DC,4800 dinámicas y la transferencia local BUS→J7.
C27 cambia≈0,9305 V respecto de la memoria histórica; los modos locales
alcanzan≈265 ms. Los [ciclos de esta nueva raíz](docs/VOZ_CICLOS_CONDICIONADOS_RESULTADOS.md)
completan dos perfiles de5,25 ms con refinamiento y cargas observadas;
la periodicidad aún queda abierta. El ciclo anterior conserva su historia.

La [QA vigente](evidence/voice_contour_engine_tests01.json) conserva
248 tests Rust heredados por identidad y el nuevo banco de trayectorias. La
[cadena con cargas explícitas](docs/CADENA_CARGA_RADAU_RESULTADOS.md) pasa
72 etapas y 180 corrientes, con medios pasos de7,629 ps; fuentes impuestas.
El
[motor portable de referencia](docs/VCO1_PORTABLE_RESULTADOS.md) incorpora
arranque, checkpoints y rollback; heap cero medido, deadline pendiente. Radau
completa dos recorridos propios nominales de30 ms y pasa periodicidad,
balance/refinamiento y cuatro comparaciones con Gear/Trap archivados.
Contrasta16 etapas reales y el rechazo Newton local; no son tests Rust.
Ya hay escucha del VCO nativo aislado: repite un ciclo real del perfil125,
sin filtro/VCA. ProducciÃ³n, ciclos asentados de voz, CV/trims y RT siguen abiertos.

La campaÃ±a serial de 350 ms comenzÃ³ tras pasar el
[preflight02](evidence/voice_serial_preflight02.json). Gear500 y Gear250
se detuvieron a 136,630269 y 150,293268 ms; Trap125 a 15,940421 ms.
Gear125 completÃ³ 350 ms. Los cuatro exports quedaron archivados y auditados;
las tres parejas no se midieron por falta de escenas completas. El
[banco largo queda rechazado](docs/VOZ_SERIAL_CAMPANA_RESULTADOS.md). No hay audio nuevo.

El [seguidor de volumen cargado](docs/VOZ_SEGUIDOR_RESULTADOS.md) ya
sustituye la fuente de2 V por Q3/Q2/CR6 dentro de la voz VCO1→J7:
205 incógnitas, doce perfiles de2 µs,9840 ecuaciones contrastadas y
corrientes C2/reset explícitas. C2 y reset siguen impuestos; contorno
completo, integración adaptativa205 y filtro-contour pendientes.

Los [controles temporales C2/reset](docs/VOZ_SEGUIDOR_CONTROL_RESULTADOS.md)
ya conservan la memoria205 durante cinco tramos de10 µs totales por
perfil:8200 ecuaciones, balances C18/C27 y veinte restores con replay
completo de tramo por bits. C2/reset todavía son fuentes ideales; el
próximo cierre incorpora C2 y su red de carga/descarga.

C2 ya es un [estado dinámico conectado](docs/VOZ_C2_CARGA_RESULTADOS.md):
217 incógnitas con ataque/decay/sustain, CR4/CR9 y carga real del seguidor.
Cuatro perfiles de50 µs pasan17360 ecuaciones, balances C2/C18/C27,
ON/OFF y40 restores completos de tramo. Los terminales del biestable
siguen impuestos; su integración causal permanece pendiente.

El [gatillo común cargado](docs/VOZ_GATILLO_CARGADO_RESULTADOS.md) ya
cierra Q12/Q20, C7/C4 y la carga real de RESET_DRIVER dentro de225
incógnitas:18000 ecuaciones, cinco balances y40 restores completos de tramo.
Q25/Q15 siguen como fronteras explícitas; su conmutación causal permanece
pendiente. Teclado y S-trigger se reciben como estímulos del circuito.

## Siguiente trabajo

1. Integrar el [motor portable VCO](docs/VCO1_PORTABLE_RESULTADOS.md) tras
   cerrar el stamp y la carga conjunta. Ampliar CV/trims reservados
   y C4=100 pF antes de promover calibración u otro perfil.
2. La [condición inicial conjunta](docs/VOZ_INICIALIZACION_RESULTADOS.md)
   ya completó sus ciclos propios. Contrastar una inicialización para
   régimen oscilatorio y reducir la deriva medida, con carga por ciclo,
   niveles/offset de J7 y coste antes de ampliar o escuchar.
   Los controles permanecen impuestos; la escala local no es una cota global.
3. Cerrar contornos, controles y fuentes restantes; despuÃ©s comprobar la voz,
   plazos y adaptadores de escucha/host para su alcance declarado.

## DocumentaciÃ³n y verificaciÃ³n

- [Contrato de plugins RackForge](https://github.com/kalexis1994/rackforge/blob/main/docs/PLUGIN_DEVELOPMENT.md).
- [Plan vigente](docs/PLAN.md) y [matriz de fidelidad](docs/MATRIZ_DE_FIDELIDAD.md).
- [Fuentes](docs/FUENTES.md), [revisiones](docs/REVISIONES.md) y
  [validaciÃ³n sin hardware](docs/VALIDACION_SIN_HARDWARE.md).
- [Bloques](docs/BLOQUES.md), [hallazgos](docs/HALLAZGOS.md) y
  [escenas de captura](docs/CAPTURAS.md).

Regresiones pÃºblicas de los dos cierres nativos recientes:

```powershell
$env:RUST_MIN_STACK = "8388608"
$env:RUSTFLAGS = "-C link-arg=-Wl,--stack,8388608" # toolchain GNU de los recibos
cargo test --offline --locked -p rf-d-circuit --test vco1_increment --test vco1_increment_no_alloc --test vco1_increment_adaptive --test vco1_increment_adaptive_no_alloc
```

Los recibos de producciÃ³n registran compiler, flags, outputs y hashes.
Sus herramientas preservan intentos: una repeticiÃ³n debe preparar un recibo
nuevo, sin sobrescribir una campaÃ±a congelada. Heap cero no prueba RT.

El objetivo musical es una voz mono para bajos, leads y articulaciÃ³n en vivo.
Presets/MIDI y automatizaciÃ³n son adaptadores de RackForge; no representan
memoria del instrumento clÃ¡sico. AÃºn no hay paquete RF-D instalable ni
admisiÃ³n de fidelidad fÃ­sica o deadline de la voz.

## Historial y material local

El [historial de esta portada](README_HISTORICO_2026-10-07.md) conserva
exactamente los estados anteriores y sus enlaces. Los
[snapshots](evidence/voice_documentation_snapshot01.json) no cambian cÃ³digo,
modelos, datos o gates; cada resultado histÃ³rico conserva su protocolo.

Manuales, esquemas, fuentes originales, WAV y binarios privados se conservan
en directorios locales ignorados. No se incluyen en Git o el paquete.
RF-D no implica afiliaciÃ³n con Moog Music.

La [QA de publicaciÃ³n](evidence/voice_vco1_increment_tests01.json) verifica
inputs protegidos, nuevos tests y archivos privados. El
[snapshot previo](evidence/voice_lm741_port_documentation01.json) conserva
las tres portadas anteriores por bytes exactos. El rechazo largo sigue vigente.

[Modos de carga: excitación y observación](docs/VOZ_MODOS_RESULTADOS.md),
27 contrastes complejos y diagnóstico de energía. El modo local más lento
no fija el tiempo de arranque de la voz. ≈129 MiB recuperados por compresión
transparente sin borrar evidencia. Diagnóstico local, sin bound global.

[Prefijo conjunto desde DC condicionado](docs/VOZ_PREFIJO_CONDICIONADO_RESULTADOS.md):
500 µs en dos perfiles, 4800 ecuaciones contrastadas, checkpoints y restores
exactos. La continuación de esa historia está completada abajo.

[Ciclos desde raíz conjunta](docs/VOZ_CICLOS_CONDICIONADOS_RESULTADOS.md):
dos perfiles de5,25 ms, 68558 intervalos,9600 ecuaciones nuevas contrastadas
y dos seams exactos. Cargas y J7 aún derivan entre cruces; siguiente:
inicialización para régimen oscilatorio. Sin nuevo audio ni admisión de RT.

[Condicionador de cargas de cadena](docs/VOZ_CARGAS_SEMILLA_RESULTADOS.md):
218 incógnitas, dos memorias/dos guesses, 872 ecuaciones de inicialización
y 9600 dinámicas contrastadas. Conserva 18 cargas históricas o retargetea
solo C27; libera cuatro perfiles de 2 µs con restores exactos. Laboratorio,
sin cambio de física. Siguiente: ciclos propios y deriva, antes de escucha.

[Ciclos de dos memorias de carga](docs/VOZ_CICLOS_SEMILLAS_RESULTADOS.md):
cuatro perfiles de 5,25 ms, 137193 intervalos y 19200 ecuaciones nuevas
contrastadas; ocho restores exactos y reproducción de 2 µs por bytes.
Ledger Radau de medias del panel/C27 y 18 cargas por fase. Periodicidad
asentada aún pendiente; sin nuevo audio, cambio de física o admisión de RT.

[Corrección conjunta de 18 cargas](docs/VOZ_CARGAS_RESPUESTA_RESULTADOS.md):
36 columnas de respuesta contrastadas, perturbación refinada conservando
el rechazo original, dos memorias nuevas con cierre no lineal y cuatro
liberaciones de 2 µs. Mejora de deriva periódica aún no medida.

[Ciclos de las memorias corregidas](docs/VOZ_CICLOS_CORREGIDOS_RESULTADOS.md):
cuatro trayectorias de 5,25 ms, 137176 intervalos y 19200 ecuaciones nuevas
contrastadas; ocho restores exactos y reproducción de 2 µs por bytes.
Comparación propia de las 18 cargas y J7. Asentamiento todavía pendiente.

[Tangente temporal de historia](docs/VOZ_TANGENTE_HISTORIA_RESULTADOS.md):
48 pasos contrastados, 9600 columnas Hx, 432 direcciones y 1728 solves
perturbados. Reproducción por bytes de las raíces anteriores; cuatro
rechazos con replay conservados. Respuesta local a h fijo, aún no mapa periódico.

[Propagación temporal de memoria](docs/VOZ_PROPAGACION_HISTORIA_RESULTADOS.md):
12 ventanas/768 pasos, 6912 direcciones y 27648 solves de historias propias.
Contraste independiente y continuidad exacta; nueve RHS por factorización.
Admisión limitada al calendario fijo de esas ventanas; retorno completo pendiente.
[QA vigente](evidence/voice_history_propagation_tests01.json).

[Derivada del cruce y proyección de fase](docs/VOZ_EVENTO_HISTORIA_RESULTADOS.md):
ocho brackets, 72 direcciones y 576 solves nuevos de historias propias.
Contraste independiente del tiempo relativo y del estado sobre la sección.
Retorno de periodo completo y calendario adaptativo siguen pendientes.
[QA vigente](evidence/voice_history_event_tests01.json).

[Intervalo completo entre resets](docs/VOZ_INTERVALO_RETORNO_RESULTADOS.md):
22356 pasos reproducidos, cuatro historias completas de C27 y contraste
del periodo y deriva de las 18 tensiones de memoria. 15 operadores
independientes seleccionados; sólo la dirección 139 tiene FD completa.
[QA vigente](evidence/voice_return_interval_tests01.json).

[Base condicionada de las semillas corregidas](docs/VOZ_BASE_CARGAS_CORREGIDAS_RESULTADOS.md):
36 columnas, 146 raíces y 288 pasos perturbados. Propagación independiente
de la base por los dos primeros pasos de cada memoria; control explícito
frente a la inyección aislada de C27. Falta el retorno completo desde estas raíces.
[QA vigente](evidence/voice_charge_basis_tests01.json).

[Retorno desde la raíz condicionada](docs/VOZ_RETORNO_CONDICIONADO_RESULTADOS.md):
42544 pasos base y 170176 solves perturbados de C27 desde sus propias
raíces. Ambos tiempos de reset, periodo y deriva en fase contrastados;
20 operadores independientes para las 18 columnas. FD completa sólo C27.
[QA vigente](evidence/voice_conditioned_return_utf8_tests01.json).

[Primera corrección dinámica de memoria](docs/VOZ_CORRECCION_DINAMICA_RESULTADOS.md):
una dirección combinada contrastada con cuatro FD completas y un candidato
propio. Ratio L2 de deriva 0.00218670557; ratio máximo 0.00199744081.
Rango 16, 212720 solves, 40000 ecuaciones y prefijos seriales por bits.
Admisión del candidato en este dominio: True.
[QA vigente](evidence/voice_dynamic_direction_tests01.json).

[Candidato dinámico con calendario propio](docs/VOZ_CANDIDATO_CICLOS_RESULTADOS.md):
dos perfiles de10,25 ms, cuatro resets y tres retornos por perfil;
14400 ecuaciones independientes, estados al mismo reloj y seis restores
por bits. Persistencia de la mejora bajo criterio previo: True.
No acredita periodicidad asintótica; siguiente bloque: controles/cargas.
[QA vigente](evidence/voice_candidate_cycles_tests01.json).

[Apertura del cutoff de la cadena](docs/VOZ_APERTURA_CUTOFF_RESULTADOS.md):
tres DC archivados, G/C contrastadas y cuatro armónicos con BUS ideal.
Abrir0,5→1 eleva |J7/BUS| unas 53.75 veces en la fundamental.
Diagnóstico de pequeña señal; siguiente: control temporal con carga propia.
[QA vigente](evidence/voice_cutoff_opening_tests01.json).

[Control temporal de cutoff con carga real](docs/VOZ_CUTOFF_TEMPORAL_RESULTADOS.md):
cuatro perfiles de250 µs, C18/cola/J7, 28800 ecuaciones y ocho restores.
J7 cambia≈2,7 mV, cargas entrantes intactas y caso nominal por bits a2 µs.
Siguiente: continuar los perfiles abiertos hasta resets completos.
[QA vigente](evidence/voice_cutoff_temporal_tests01.json).

[Cutoff abierto con ciclos propios de VCO/filtro/VCA](docs/VOZ_CUTOFF_CICLOS_RESULTADOS.md):
dos perfiles hasta5,25 ms desde el prefijo propio, dos resets por perfil,
55200 ecuaciones y balances de carga/medias. Escucha de inspección admitida:
True; réplica de un intervalo, escala explícita80×.
No acredita voz completa, periodo asintótico o RT.
[QA vigente](evidence/voice_contour_engine_tests01.json).


## Q25/Q15 cargados en la voz — 2026-10-12

[Cierre229](docs/VOZ_BIESTABLE_CARGADO_RESULTADOS.md) conecta el biestable
con carga intrínseca compatible, C2 y el gatillo hasta J7. Los tres terminales
Q25/Q15 dejan de ser fuentes ideales; C4 conserva sus dos placas internas.
Cuatro perfiles de10 µs,18320 ecuaciones,3840 pasos y40 restores completos.
La malla inicial se rechaza;15.625/7.8125 ns pasan el gate2 µV con1.553 µV
máximo en los finales comparados. Hipótesis de dispositivos explícitas,
ventana local; ADSR completo, contorno de filtro y RT siguen pendientes.
[QA](evidence/voice_contour_engine_tests01.json).


## Contorno229 con contacto sostenido — 2026-10-12

[Control temporal adaptativo](docs/VOZ_CONTORNO_ADAPTATIVO_RESULTADOS.md)
para el circuito cerrado: cuatro perfiles de102 µs, S sostenido50 µs y
liberación50 µs.3226 avances/6452 finos,32976 ecuaciones independientes,
20 restores completos y8 rollbacks. Dos límites de paso coinciden en
los12 cortes con≈.154 nV máximo; C2 responde desde las corrientes reales.
Ventana corta con historia precargada; nota/ADSR completo y RT pendientes.
[QA](evidence/voice_contour_engine_tests01.json).
