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

La [QA vigente](evidence/cutoff_ab_tests01.json) conserva
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
[QA vigente](evidence/cutoff_ab_tests01.json).


## Q25/Q15 cargados en la voz — 2026-10-12

[Cierre229](docs/VOZ_BIESTABLE_CARGADO_RESULTADOS.md) conecta el biestable
con carga intrínseca compatible, C2 y el gatillo hasta J7. Los tres terminales
Q25/Q15 dejan de ser fuentes ideales; C4 conserva sus dos placas internas.
Cuatro perfiles de10 µs,18320 ecuaciones,3840 pasos y40 restores completos.
La malla inicial se rechaza;15.625/7.8125 ns pasan el gate2 µV con1.553 µV
máximo en los finales comparados. Hipótesis de dispositivos explícitas,
ventana local; ADSR completo, contorno de filtro y RT siguen pendientes.
[QA](evidence/cutoff_ab_tests01.json).


## Contorno229 con contacto sostenido — 2026-10-12

[Control temporal adaptativo](docs/VOZ_CONTORNO_ADAPTATIVO_RESULTADOS.md)
para el circuito cerrado: cuatro perfiles de102 µs, S sostenido50 µs y
liberación50 µs.3226 avances/6452 finos,32976 ecuaciones independientes,
20 restores completos y8 rollbacks. Dos límites de paso coinciden en
los12 cortes con≈.154 nV máximo; C2 responde desde las corrientes reales.
Ventana corta con historia precargada; nota/ADSR completo y RT pendientes.
[QA](evidence/cutoff_ab_tests01.json).


## Contorno cargado durante el reset del VCO — 2026-10-12

[Ventana229 de3.004 ms](docs/VOZ_CONTORNO_RESET_RESULTADOS.md): S sostenido
1.5 ms y liberación1.5 ms, ON/OFF y límites h2/1 µs. Un reset por perfil
con VCO/BUS/filtro/VCAs/J7 y contorno en el mismo solve.35724 ecuaciones,
25152 finos,24 restores de prefijo y balances de carga; diferencia máxima
.1404 µV en los cortes comparados. Historia entrante conservada por bits.
Ciclo completo entre dos resets, contorno desde silencio y RT pendientes.
[QA](evidence/cutoff_ab_tests01.json).


## Ciclo del VCO con contorno229 y C7 cargado — 2026-10-12

[Continuación hasta11.442 ms](docs/VOZ_CONTORNO_CICLO_RESULTADOS.md) conserva
cada historia propia y completa un ciclo transitorio entre dos resets
con VCO/BUS/filtro/VCAs/J7 y contorno activos. La apertura con C7 cargado
refuta el predictor anterior: fallo/replay preservados, una condición
numérica reparada sin modificar ecuaciones ni gates. Cuatro perfiles
admitidos, 26770 finos y 38472 ecuaciones;
unión exacta, refinamiento y balances pasan.
Siguiente: medir y acelerar el solve contra esta referencia para alcanzar
un contorno de duración musical. Contorno desde silencio, otras cargas
de placa2, contorno de filtro, fidelidad física y RT pendientes.
[QA](evidence/cutoff_ab_tests01.json).


## Reuso del trial de Newton — 2026-10-12

[Cache local exacta](docs/NEWTON_REUSO_RESULTADOS.md) conserva stamp y corrección
del trial ya aceptado. Benchmark de84 pares: mediana pareada
1.6693×, 760→460 ensamblados y696→396 solves.
Cuatro trayectorias completas coinciden por bytes con la referencia:
26770 finos, 24 restores, 368 avances repetidos, mismos gates y cargas.
Sin nueva duración o audio; 38472 ecuaciones heredadas por identidad.
Siguiente: reducir costo del sistema lineal contra esta referencia exacta.
Deadlines, contorno desde silencio y duración musical siguen pendientes.
[QA](evidence/cutoff_ab_tests01.json).


## LU con extensión contigua — 2026-10-13

[Reducción de trabajo](docs/LU_EXTENSION_RESULTADOS.md) de eliminación con
pivotes/criterios originales. Lista indexada conservada como hipótesis
no elegida; extensión contigua confirmada con mediana pareada
1.0908× y37.72% menos actualizaciones.
84 pares y8 regresiones del solver; cuatro perfiles conservan40 archivos
por bytes,26770 finos y24 restores.38472 ecuaciones heredadas, sin
reejecutarlas. Sin duración o audio nuevos, ni admisión RT.
Siguiente: condensación de bloques dinámicos preservando puertos y masa.
[QA](evidence/cutoff_ab_tests01.json).


## Condensación dinámica de LM741 — 2026-10-13

[Prototipo de Schur](docs/SCHUR_DINAMICO_RESULTADOS.md) elimina128
correcciones interiores y resuelve330 exteriores, conservando las458
coordenadas de las dos etapas, puertos, masa e historia HIGH/LOW.
84 pares/38472 ecuaciones nuevas pasan el grafo independiente;
396 correcciones,1680 memorias y2016 corrientes pasan sus comparaciones.
Mediana pareada1.1342×; nueve regresiones de estructura/rechazo.
El gate residual mixto sigue rechazado en20 solves Schur y24 de referencia:
sistema J/b completo, fuentes y replay exacto preservados. Sin admisión
para trayectorias, duración/audio nuevos o RT.
Siguiente: refinamiento acotado sobre el sistema fallido, conservando
factores, puertos y gate; después banco y recorrido si pasan.
[QA de alcance](evidence/cutoff_ab_tests01.json).


## Schur refinado con residuo compensado — 2026-10-13

[Refinamiento acotado](docs/SCHUR_REFINADO_RESULTADOS.md) conserva factores del mismo J, reconstruye
458 correcciones y mantiene puertos, masa e historia. Tres refinamientos
como máximo, sin fallback ni tolerancias nuevas; sólo20 de396 solves
requieren una corrección adicional.181368 filas lineales únicas y38472
ecuaciones nuevas pasan Decimal100, junto con memorias y corrientes.
Doce regresiones cubren estructura, no finitos, capacidad y presupuesto.
El soporte exacto reproduce toda la traza y raíces por bytes.
Precisión pasa; utilidad de costo pendiente (medianas0.9083×/0.9496×).
Sin campaña temporal, duración/audio nuevos o RT.
Siguiente: perfilar preparación, sustituciones y residuo antes de otra
variante; abrir trayectoria sólo después de pasar precisión y costo.
[QA](evidence/cutoff_ab_tests01.json).


## Perfil de costo y variantes no elegidas — 2026-10-13

[Medición por fase](docs/SCHUR_COSTO_RESULTADOS.md) conserva84 pares por bits en una copia
privada: preparación82.47%, residuo0.70% del solve observado.
Tres hipótesis pasan candidatos pero fallan utilidad: medianas
0.8535×/0.9149×/0.9392×. Preservar todas; no elegir por el mejor intento.
Las dos últimas conservan396 trazas J/b/correcciones por bytes;
181368 filas y38472 ecuaciones independientes heredadas, sin reauditar.
21 regresiones incluyen ceros con signo, subnormales y no finitos.
Fallo de compilación/replay y reparación de tipo explícita conservados.
Sin campaña temporal, duración/audio nuevos o RT. Siguiente: construcción
y factorización en ubicación final, con precisión y costo antes de promover.
[QA](evidence/cutoff_ab_tests01.json).


## Schur en sitio y ciclo condicionado admitido — 2026-10-13

[Workspace local](docs/SCHUR_EN_SITIO_RESULTADOS.md) llena/factoriza interiores64 y exterior330
en sus destinos, conservando458 correcciones, puertos, masa e historia.
Banco1.0086× y confirmación única1.0133× con el mismo ejecutable;
396 trazas por bits,26 regresiones incluyendo recuperación del workspace.
Cuatro recorridos propios pasan38472 ecuaciones nuevas y comparaciones
de229 coordenadas al mismo reloj frente a LU (máximo8.52e-13 V).
26770 finos,24 restores,368 avances repetidos,16 corrupciones y8 rollbacks.
Admitido para la ventana condicionada3.004 ms; sin duración/audio nuevos,
contorno desde silencio, identificación física o RT. Siguiente: otra
reducción estructural conservando puertos/cargas para duración musical.
[QA](evidence/cutoff_ab_tests01.json).


## Contorno cargado condensado — 2026-10-13

[Reducción estructural](docs/SCHUR_CONTORNO_RESULTADOS.md) incorpora 58 correcciones de contorno a los
128 interiores LM741: exterior 330→272 y reconstrucción completa de 458,
con 229 estados HIGH/LOW, R59/Q18, masas e historia conservados.
Costo pareado 1.0229× y confirmación 1.0251× frente al Schur admitido.
181.368 filas lineales nuevas, 38.472 ecuaciones de banco y otras 38.472
temporales pasan Decimal100; 35 regresiones con replay pasan.
Cuatro perfiles/26770 finos conservan restores, eventos y balances.
Admisión limitada al ciclo condicionado de 3.004 ms, sin duración/audio
nuevos, contorno desde silencio, identificación física o RT.
Siguiente: cadena con BUS/base Q18 retenidos, exterior potencial 140;
soporte inspeccionado, invertibilidad y utilidad pendientes. [QA](evidence/cutoff_ab_tests01.json).


## Cadena filtro/VCA condensada — 2026-10-13

[Partición cargada](docs/SCHUR_CADENA_RESULTADOS.md) retiene BUS/base Q18 en ambas etapas y reduce
exterior272→140. Reconstruye458 correcciones y conserva229 estados
HIGH/LOW, masas, cargas y puertos compartidos con el contorno.
Medianas1.0299×/1.0265× frente al Schur con contorno;
181.368 filas lineales,38.472 ecuaciones de banco y otras38.472 temporales
nuevas pasan Decimal100;45 regresiones/replay. Cuatro recorridos con
26770 finos conservan balances, eventos y restores. Admisión condicionada
a3.004 ms, sin duración/audio nuevos o RT. Perfil privado por bits:
linearize≈50.3% del step, solve≈27.3%.
Siguiente: ensamblaje Radau en ubicación final, con J/b/raíces por identidad.
[QA](evidence/cutoff_ab_tests01.json).


## Ensamblaje Radau en ubicación final — 2026-10-13

[Dos buffers de Stamp](docs/RADAU_EN_SITIO_RESULTADOS.md) se llenan por &mut y permutan referencias
después de aceptar, conservando J, masa, puertos, rechazos y estado229
HIGH/LOW.84 raíces/1834 campos por bits e iteraciones/trials idénticos.
Mediana pareada1.4004×:≈28.6% menos tiempo en el banco,
sin confirmación adicional según contrato.396 trazas lineales y40 exports
temporales por bytes;181.368 filas y dos bancos de38.472 ecuaciones heredados,
sin reauditar.11 regresiones, cuatro recorridos propios y26770 finos pasan.
Admisión limitada al ciclo condicionado3.004 ms; sin duración/audio nuevos
o RT. Siguiente: integración portable229 y contrato de ownership/memoria.
[QA](evidence/cutoff_ab_tests01.json).


## Conjunto229 público y workspace propio — 2026-10-13

[Biblioteca Rust](docs/CONJUNTO_PORTABLE_RESULTADOS.md) exporta conditioned_voice/conditioned_engine:
229 estados HIGH/LOW, puertos/cargas y controlador originales. Caller dueño
del Workspace, checkpoint separado de scratch y confirmación atómica.
Workspace3.378.208 bytes; Engine/Checkpoint4.800. Cero asignaciones en9
llamadas aceptadas y3 rechazadas;4 tests nuevos,248 heredados (252 cubiertos).
84 raíces y40 exports temporales por bytes;396 matrices guardadas reproducidas,
sin presentarlas como solves activos observados. Filas y ecuaciones heredadas
por identidad. Cuatro recorridos públicos/26770 finos admitidos para3.004 ms.
Biblioteca nueva, sin cache Cargo, duración/audio nuevos o RT. Siguiente:
receta pública de historia/controles y render offline condicionado. [QA](evidence/cutoff_ab_tests01.json).


## Receta propia y render offline condicionado — 2026-10-13

[Receta ejecutable](docs/RECETA_CONDICIONADA_RESULTADOS.md): cuatro historias
propias ON/OFF por resolución1/2 µs, controles/cargas explícitos y ejemplo
Rust sin referencias privadas. Exporta J7 en voltios usando biblioteca y
Workspace públicos. Cuatro calendarios,26770 endpoints y48 estados completos
coinciden por bits; replay ON a 1 µs. Se ejecutan 7 tests Rust (3 nuevos/4 previos),
248 heredados y2 tests Python. CLI WAV y sidecar reproducibles; cero heap
medido nuevamente en las rutas del harness, sin admisión de deadline.

Cuatro WAV de ventana3.004 ms: tiempo nativo3 ms y microscopio100×,
300.396 ms mapeados. Sin repetición, normalización o circuito adicional;
el microscopio altera tiempo/frecuencia. Rechazo de historia2 µs aplicada
a1 µs conservado con replay, corregido con sus estados propios ya públicos.
Siguiente: gatillo sostenido/liberación en una ventana propia más larga
y escucha útil a tiempo nativo, con contraste temporal.
[QA](evidence/cutoff_ab_tests01.json).


## Gatillo sostenido y liberación: 12.004 ms propios — 2026-10-13

[Trayectoria ON](docs/VOZ_SOSTENIDA_RESULTADOS.md) conserva historias propias
1/2 µs,229 estados, puertos y cargas.8 ms de gatillo y4 ms después de
liberarlo;25109 accepted/50218 finos.32976 ecuaciones nuevas y43 relojes
comunes pasan; prefijo hasta9.942 ms por bytes.312 accepted reproducidos
desde20 checkpoints, con hasta3 motores sombra y sin acumular Accepted.

Dos WAV nativos12 ms y microscopio100× de1.2 s, sin circuito adicional.
El gate de repetición rechaza la deriva de J7 (0.338 mV); no se genera un loop.
C2 todavía crece durante4 ms después de KEY0, con C7/C4/biestable en evolución;
es una observación del modelo, sin causa física adjudicada. Siguiente:
seguir la liberación propia, observar conmutación/descarga y revisar su
recorrido de control.255 tests Rust heredados, sin reejecución o deadline.
[QA](evidence/cutoff_ab_tests01.json).


La [liberación restaurada](docs/VOZ_LIBERACION_RESULTADOS.md) añade8 ms propios
sin nuevo gatillo: unión20.004 ms y12 ms después de KEY0. Q25/Q15 conmutan y
C2 comienza a descargar aproximadamente4.0907 ms después de KEY0; balance
de corrientes comprobado, sin reset digital.19236 ecuaciones nuevas,28 relojes
comunes229 y seis resets pasan.224 accepted reproducidos desde14 checkpoints.
Dos WAV nativos960 frames/20 ms, sin loop; CLI rechaza estados incompatibles
en la unión. Tres checks de integración;255 tests Rust heredados, no reejecutados.
[Revisión documental](docs/VOZ_LIBERACION_REVISION.md) conserva fuentes y
registra errata de localizador. La descarga sigue incompleta; próximo bloque:
su evolución y controles de decay para una escucha más larga. Sin fidelidad
física, contorno desde silencio o RT admitidos.


El [control eléctrico de decay](docs/DECAY_CONTROL_RESULTADOS.md) expone
PANEL_R16 en ohmios en la voz cargada.100 kΩ reproduce ocho accepted completos
por bits entre rlib antigua, nominal nueva y motor controlado. Un evento1 kΩ
conserva458 HIGH/LOW, cargas, fuentes, reloj y propuesta.16 ms adicionales,
C2 final1.499697 V;24732 ecuaciones nuevas,
21 relojes229 y14 resets pasan. Dos WAV nativos36 ms reales, sin loop;
CLI y sidecar declaran el evento. Rechazos de control/restore atómicos.
Sin mapa de perilla, calibración física o RT; siguiente duración útil y
eficiencia conservando el circuito y la señal.


La [familia de costo reducido](docs/VOZ_COSTO_BLOQUES_RESULTADOS.md) conserva
ecuaciones, puertos y cargas: Jacobiano por cuadrantes y validación de
conexiones desde CSR real.16.468.764 entradas y209.764 posiciones de política
coinciden;8721 avances completos por bits en la API pública.
Banco público: mediana0.800968×baseline, sin RT admitido.
Pivotes nulos y primera versión pública se conservan rechazados por costo.
Prefijo4 ms idéntico a la referencia;9 balances y checkpoints pasan. No
duración/audio nuevos; siguiente: render propio más largo con esta familia.


La [liberación extendida con el motor público](docs/VOZ_LIBERACION_EXTENDIDA_RESULTADOS.md)
añade32 ms reales: historia unida68.004 ms y dos WAV nativos68 ms, sin loop.
KEY/S/R heredados, unión completa3728 bytes;8 avances completos coinciden
con el ensamblado original. 41220 ecuaciones nuevas,
41 relojes229, balances y replay acotado pasan. C2 final0.880011 V,
no silencio completo admitido. CLI reproducible y cuatro checks.
Sin biblioteca/cache nuevas, fidelidad física, heap/deadline nuevos o RT.


El [banco ampliado y perfil actual](docs/VOZ_CEROS_RESULTADOS.md) contrasta
168 pares y35471184 campos de stamp. Dos recorridos de ceros conservan
bits,1280 fixtures LU y seis errores, pero fallan utilidad5 %:
ratio1.000029624 con104488 bytes extra y0.977922929 sin
scratch extra. No se promueven. Perfil actual exacto: initialize55.13 %
incluye parts42.37 %, solve37.09 %; relojes anidados, sin ganancia inferida.
La voz pública y audio68 ms permanecen idénticos. Siguiente: ensamblado y
parts/copia de estados, conservando puertos, cargas y contraste completo.


El [ensamblado directo público](docs/VOZ_ENSAMBLADO_RESULTADOS.md) evita
el contenedor200 y su copia a229, conservando constructor, validaciones,
sumas, masa, contorno y puertos.71019312 campos Parts/stamp por bits en168
pares; API pública ratio0.895860583 y workspace3378208 igual.
6464 Accepted completos/12 rejillas y nueve balances
coinciden en4 ms propios por resolución,68.442→72.442 ms; kernel ratio
0.920475855. 2748 ecuaciones originales
heredadas por identidad,0 nuevas. Fallos de binding/replays conservados.
Sin duración/WAV nuevos, heap/deadline o RT. Siguiente duración útil propia.


La [cola propia con ensamblado directo](docs/VOZ_COLA_LARGA_RESULTADOS.md)
añade 64 ms eléctricos: historia de 132.004 ms y dos WAV de 132 ms, 6336 muestras.
Receta y 3728 bytes de unión idénticos; ocho avances comparados por bits.
76944 ecuaciones originales seleccionadas nuevas,
81 relojes de 229 estados, balances de carga y replay acotado pasan. C2 final
0.850987312 V; no silencio asintótico inferido.
CLI con diez entradas/código identificados y cuatro integraciones.
Sin biblioteca/cache nuevas, fidelidad física o RT. Siguiente escena útil de voz.


El [retrigger con memoria propia](docs/VOZ_RETRIGGER_RESULTADOS.md)
añade 16,004 ms: segundo gatillo de 8 ms y liberación de 8 ms sin borrar cargas.
Dos eventos por resolución conservan 458 HIGH/LOW, resistencia, clock y propuesta;
16 Accepted posteriores pareados por bits con block, además de ocho de unión.
43968 ecuaciones seleccionadas nuevas, 22 relojes de
229 estados y nueve balances por fase/total/unión pasan. Dos WAV reales de 148 ms,
17 entradas/código identificados y cuatro integraciones CLI. Sin fidelidad física
o RT; la historia inicial sigue condicionada. [QA](evidence/cutoff_ab_tests01.json).


El [cutoff cargado de panel](docs/VOZ_CUTOFF_RESULTADOS.md) añade 16,004 ms:
α1→0,5→1 sin modificar KEY/CV ni borrar cargas. Codec completo RFCTF001 de
3736 bytes; 16 Accepted tras eventos y ocho de unión coinciden con block.
32976 ecuaciones seleccionadas nuevas con el panel
de cada fase, 22 relojes de 229 estados y nueve balances por fase/total/unión.
Dos WAV reales de 164 ms, 24 entradas identificadas y cuatro checks CLI.
Contorno de filtro pin16 sigue impuesto; sin Hz calibrados, fidelidad física o RT.
[QA](evidence/cutoff_ab_tests01.json).


El [A/B de cutoff desde el mismo estado](docs/VOZ_CUTOFF_AB_RESULTADOS.md)
compara α1/0,5 durante 8 ms con 458 HIGH/LOW, clock/propuesta y controles comunes.
Rama abierta nueva: 13740 ecuaciones seleccionadas;
cerrada: 13740 heredadas, sin reejecución. Once clocks229, balances/replay
pasan; cuatro WAV de 8 ms sin concatenación o normalización. RMS cerrado/abierto
1.02668585 (0.228751 dB), ventana con DC/transitorios. Siete entradas/código y
cuatro checks CLI. La historia/WAV continuo de 164 ms sigue sin prolongarse.
Sin Hz calibrados, contorno de filtro completo, fidelidad física o RT.
[QA](evidence/cutoff_ab_tests01.json).


El [puerto del contorno de filtro](docs/CONTORNO_FILTRO_PUERTO_RESULTADOS.md)
cierra Q22/Q21, Amount cargado y Q26/Q28: nueve nodos/ocho terminales,
60 DC y 96 pasos locales de 1 mV; 1520 filas originales, 45084 entradas
FD y 9984 tangentes. Conserva C11/C18, topes exactos, masa y 24 rechazos
atómicos. La gran discontinuidad C5 0,85→3 V sigue rechazada por
refinamiento; el puerto local no acredita contorno completo o voz integrada.
Módulo de laboratorio compilado contra biblioteca congelada, fuera de lib.rs.
[QA actual](evidence/filter_contour_port_tests01.json). Próximo cierre: C5
continuo, biestable y carga del gatillo compartido. Sin audio nuevo o RT.


[C5 y gatillo compartido](docs/C5_GATILLO_COMPARTIDO_RESULTADOS.md) cierran
ambos contornos en 54 nodos con carga real de Amount/Q26/Q28. Ocho recorridos
de 36 ms, liberación/retrigger, 86228 Accepted; 40920 filas originales,
576 clocks y balances pasan. C5/C2 conservan memoria; 40 restores locales
y 320 rechazos del checkpoint. Escena fija de panel, rieles/VCA/TAIL impuestos,
sin nuevo audio o plugin tocable. Próximo cierre: placa 4 y voz funcional,
con el circuito detallado como referencia para reducir costo.
[QA actual](evidence/c5_trigger_tests01.json).


## Ambos contornos con cargas de filtro y VCA

[La unión de 118 nodos](docs/CONTORNOS_CADENA_RESULTADOS.md) cierra R59,
TAIL y Q26/Q28 con ambos contornos, ladder, dos VCA y J7. Dos trayectorias
de 36 ms, 21250 Accepted, 14518 filas originales y 139240 entradas FD
pasan. Entrada eléctrica sinusoidal impuesta; VCO real y tiempo real
siguen pendientes. [QA](evidence/dual_chain_tests01.json).


## Voz con VCO real y ambos contornos

[La unión de 250 incógnitas](docs/VOZ_DOS_CONTORNOS_RESULTADOS.md) ya resuelve
VCO1, BUS cargado, ambos contornos, ladder, dos VCA y J7. Dos escenas
de 8 ms pasan con 251 nodos originales; no hay onda de entrada impuesta.
Motor detallado de laboratorio, sin nueva escucha o RT. Prioridad: reducir
costo contra esta referencia y extender a una nota audible.
[QA](evidence/dual_voice_tests01.json).


## Costo menor y voz de 24 ms

[La variante optimizada](docs/VOZ_COSTO_RESULTADOS.md) conserva el circuito
y reduce ~37 % el costo del solver en el banco. Dos trayectorias nuevas de
24 ms pasan con referencia original, sin reset a 8 ms. Hay una ráfaga local
de J7 de 24 ms, sin repetir ciclos; es corta y tenue, no una nota sostenida.
La siguiente prioridad sigue siendo una reducción mayor y duración útil.
[QA](evidence/voice_cost_tests01.json).


## 2026-10-14 — Primera nota corta con ambos contornos

[Paso observable y nota de 100 ms](docs/VOZ_NOTA_OBSERVABLE_RESULTADOS.md):
KEY sostenido 74 ms, retirada y evolución hasta 100 ms; circuito completo
y cargas intactas. 801 clocks, refinamiento y ecuaciones originales
seleccionadas pasan. Dos WAV privados de 4800 frames con PCM idéntico,
sin ciclos repetidos. En 24 ms el banco observable cuesta aproximadamente
una cuarta parte de la referencia estricta, con error RMS J7 <0.001 %.
La nota sigue siendo offline (553/555 s por perfil); siguiente prioridad:
reducción de bloques frente a este oráculo. [QA](evidence/observed_note_tests01.json).


## 2026-10-14 — Limpieza y puerto resistivo para VCO reducido

Retirados 110705 archivos regenerables y 10325 carpetas vacías: 22.34 GB
lógicos; las 8769 entradas admitidas siguen disponibles. Nueva
[política de laboratorio](docs/ALMACENAMIENTO_LABORATORIO.md): un área
temporal, recibos compactos y retiro de ejecutables/exports tras cada banco.
[Puerto R6/R45](docs/VCO_PUERTO_PANEL_RESULTADOS.md) conserva carga de
sierra, BUS y masa; contactos extremos, Jacobiano y 1602 estados de la
voz actual pasan. Preparado para conectar el futuro VCO reducido.
[QA](evidence/lab_retention_tests01.json).


## 2026-10-14 — VCO reducido nominal con puerto cargado

[Núcleo de fase](docs/VCO_FASE_NOMINAL_RESULTADOS.md): 52 armónicos y DC
derivados del circuito, cuatro terminales de salida con BUS libre.
962 observaciones reservadas, frecuencia/fase y 72 tangentes pasan;
error de armónicos 1–8 0.797 % sierra y 0.085 % triángulo.
Tres millones de muestras: ~0.18 µs por muestra y cero heap en este
callback. La voz completa aún usa su VCO anterior; unir ahora este puerto
a la cadena y comparar J7. Sin WAV ni nuevos directorios de muestras.
[QA](evidence/vco_phase_tests01.json).


## 2026-10-14 — VCO periódico unido a la cadena real

[Unión nominal](docs/HYBRID_VOZ_RESULTADOS.md): dos ramas propias de
40–100 ms con 118 incógnitas de contornos/ladder/VCAs/J7 y puerto VCO
cargado. El reset compacto de circuito supera el rechazo inicial del
BUS sin cambiar gates: J7 RMS 1,0672 %, pico 2,608 %, cargas y C2/C5
pasan. 5712 ecuaciones originales contrastadas y heap cero medido.
28,5 s por 60 ms simulados; aún sin RT, arranque/CV generales o nuevo
WAV. Sin carpetas de muestras; área temporal vacía.
[QA](evidence/hybrid_voice_tests01.json).
