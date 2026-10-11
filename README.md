# RF-D

RecreaciÃƒÂ³n de circuito del Minimoog Model D clÃƒÂ¡sico para RackForge, bajo
[RACE](https://github.com/kalexis1994/rackforge-race/blob/main/README.md). Primer perfil: placa osciladora CA3046
nominal documentada; [revisiÃƒÂ³n y alcance](docs/OBJETIVO.md). No hay ni habrÃƒÂ¡
un instrumento fÃƒÂ­sico de referencia. La equivalencia numÃƒÂ©rica de un modelo
no acredita identidad sonora con una unidad vintage.

## Estado actual â€” 2026-10-10

| Ruta | Resultado disponible | Alcance pendiente |
|---|---|---|
| Cargas BE/BC y GS/GD | [Primitiva nativa](docs/VCO_CARGA_JUNTURA_RESULTADOS.md), 1280 vectores y derivadas | Transporte/difusiÃ³n, binding tÃ©rmico y dispositivos completos |
| BJT NPN/PNP de VCO | [Transporte y cargas nativos](docs/VCO_BJT_NOMINAL_RESULTADOS.md), 1536 vectores y doce escenas SPICE | ParÃ¡metros fÃ­sicos, otras temperaturas y trayectoria estacionaria |
| JFET E402 de VCO | [Canal y cargas de una mitad](docs/VCO_JFET_NOMINAL_RESULTADOS.md), 2028 vectores y doce escenas SPICE | ParÃ¡metros fÃ­sicos, otras temperaturas y trayectoria estacionaria |
| LM741 de VCO | [Stamp completo](docs/VCO_741_NATIVO_RESULTADOS.md), 37 incÃ³gnitas, cinco memorias, 60 vectores y seis DC propios | ParÃ¡metros fÃ­sicos y trayectoria VCO estacionaria |
| Puerto LM741 | [Newton y cinco derivadas cargadas](docs/VCO_741_PUERTO_RESULTADOS.md), seis DC, nueve trayectorias/672 pasos y 371 intervalos SPICE | Cierre activo con mixer y deadlines |
| VCO1 nativo ensamblado | [Circuito completo de 134 incÃ³gnitas](docs/VCO1_STAMP_RESULTADOS.md), 40 casos, Jacobiano completo y contactos exactos | Arranque propio, ciclos completos y carga activa |
| VCO1 arranque propio | [Diez raÃ­ces propias](docs/VCO1_ARRANQUE_RESULTADOS.md), semilla de circuito y contraste independiente | Reset/refinamiento temporal: pasos fijos rechazados; carga activa |
| VCO1 motor portable | [Arranque/checkpoint y cuatro tests nativos](docs/VCO1_PORTABLE_RESULTADOS.md), 26 comparaciones de etapas y heap cero | Referencia nominal; carga conjunta, stack/deadline y host pendientes |
| VCO1 Radau nominal | [Dos recorridos propios de30 ms](docs/VCO1_RADAU_CICLOS_RESULTADOS.md), periodicidad/refinamiento y escucha nativa aislada | CV/trims reservados, C4=100 pF, carga activa y producciÃƒÂ³n/RT |
| VCO1 puerto 741 exacto | [70 incÃ³gnitas exteriores, 12 sistemas y nueve pares de raÃ­ces](docs/VCO1_741_CONDENSACION_RESULTADOS.md) | Laboratorio Decimal100; error dinÃ¡mico del puerto y reset temporal pendientes |
| VCO1 integraciÃ³n/rigidez | [SDIRK contrastado y modos rÃ¡pidos locales](docs/VCO1_SDIRK_RESULTADOS.md) | Dos continuaciones rechazadas; contrato exacto cerrado localmente en el bloque del puerto |
| VCO1 grilla de reset | [22 raÃ­ces contrastadas y segundo piso temporal](docs/VCO1_RESET_GRILLA_RESULTADOS.md) | Prefijo privado de 189 ns; analizar dinÃ¡mica/integraciÃ³n 741 antes de ampliar |
| VCO1 incrementos/memoria | [50 raÃ­ces y 897.800 derivadas; precisiÃ³n recuperada](docs/VCO1_INCREMENTOS_RESULTADOS.md) | Reset rechazado por error temporal a 2,434 ms; grilla mÃ¡s fina |
| VCO1 subpasos/control temporal | [48 stamps y 28 raÃ­ces locales; controlador atÃ³mico](docs/VCO1_SUBPASOS_RESULTADOS.md) | Referencia histÃ³rica: lÃ­mite de representaciÃ³n recuperado localmente en el bloque de incrementos |
| VCO1 Newton conjunto | [Dos DC condicionados y seis continuaciones/224 pasos](docs/VCO1_NEWTON_RESULTADOS.md), memoria atÃ³mica | Semilla propia, ciclos completos, refinamiento y carga activa |
| VCO1 de referencia | [Circuito funcional, convergencia y calibraciÃƒÂ³n](docs/VCO1_RESULTADOS_CIRCUITO.md) | Trayectoria nativa de ciclos completos y carga activa; osciladores 2/3 |
| Mezclador ON y C27 | [Puerto dinÃƒÂ¡mico con memoria](docs/MEZCLADOR_C27_RESULTADOS.md), 837 casos nodales | OFF, taper e impedancias reales de generadores |
| EntradaÃ¢â€ â€™ladderÃ¢â€ â€™VCAsÃ¢â€ â€™J7 | [Entrada directa nativa](docs/MEZCLADOR_DIRECTO_RESULTADOS.md), 12 escenas/192 pasos a 500/250/125 ns | Contornos y generadores todavÃƒÂ­a impuestos |
| Carga vista por las fuentes | [Puerto directo 5Ãƒâ€”5 a 125 ns](docs/MEZCLADOR_DIRECTO_RESULTADOS.md), candidatos y tangentes | Cerrar VCO real con estas corrientes y tangentes |
| Contorno de volumen | [Puerto C2/reset y cadena cargada](docs/PUERTO_CONTORNO_CADENA_71.md), laboratorio de conmutaciÃƒÂ³n | IntegraciÃƒÂ³n estable del contorno completo y contorno de filtro |
| Voz monolÃƒÂ­tica SPICE | [Banco corto admitido](docs/VOZ_SEIS_ACTIVO_RESULTADOS.md); [largo rechazado](docs/VOZ_SERIAL_CAMPANA_RESULTADOS.md) | Nota larga completa con sus tres contrastes |
| Producto | NÃƒÂºcleos y herramientas de laboratorio | Voz nativa completa, recursos, MIDI/host y paquete instalable |

El [cierre elÃ©ctrico conjunto](docs/VOZ_BUS_CONJUNTO_RESULTADOS.md) une VCO1 y
la cadena hasta J7: cuatro pasos y ocho etapas contrastadas localmente.
Ese banco comprueba pasos locales; la continuaciÃ³n estÃ¡ en el motor siguiente.

El [motor temporal conjunto](docs/VOZ_MOTOR_TEMPORAL_RESULTADOS.md) admite
cuatro continuaciones de2 Âµs, control LTE, restore exacto y rollback.
El [primer ciclo con carga activa](docs/VOZ_PRIMER_CICLO_RESULTADOS.md)
ya pasa dos perfiles de5,25 ms: dos resets, un ciclo transitorio, balances
y refinamiento al mismo reloj. Conserva dos pausas administrativas y sus
continuaciones exactas; no admite aÃºn una nota asentada.

La [inicializaciÃ³n conjunta condicionada](docs/VOZ_INICIALIZACION_RESULTADOS.md)
ya resuelve DC con C1=0 desde dos semillas y libera dos perfiles de2 Âµs.
Contrasta400 ecuaciones DC,4800 dinÃ¡micas y la transferencia local BUSâ†’J7.
C27 cambiaâ‰ˆ0,9305 V respecto de la memoria histÃ³rica; los modos locales
alcanzanâ‰ˆ265 ms. Los [ciclos de esta nueva raÃ­z](docs/VOZ_CICLOS_CONDICIONADOS_RESULTADOS.md)
completan dos perfiles de5,25 ms con refinamiento y cargas observadas;
la periodicidad aÃºn queda abierta. El ciclo anterior conserva su historia.

La [QA vigente](evidence/voice_conditioned_return_tests01.json) conserva
248 tests Rust heredados por identidad y el nuevo banco de trayectorias. La
[cadena con cargas explÃ­citas](docs/CADENA_CARGA_RADAU_RESULTADOS.md) pasa
72 etapas y 180 corrientes, con medios pasos de7,629 ps; fuentes impuestas.
El
[motor portable de referencia](docs/VCO1_PORTABLE_RESULTADOS.md) incorpora
arranque, checkpoints y rollback; heap cero medido, deadline pendiente. Radau
completa dos recorridos propios nominales de30 ms y pasa periodicidad,
balance/refinamiento y cuatro comparaciones con Gear/Trap archivados.
Contrasta16 etapas reales y el rechazo Newton local; no son tests Rust.
Ya hay escucha del VCO nativo aislado: repite un ciclo real del perfil125,
sin filtro/VCA. ProducciÃƒÂ³n, ciclos asentados de voz, CV/trims y RT siguen abiertos.

La campaÃƒÂ±a serial de 350 ms comenzÃƒÂ³ tras pasar el
[preflight02](evidence/voice_serial_preflight02.json). Gear500 y Gear250
se detuvieron a 136,630269 y 150,293268 ms; Trap125 a 15,940421 ms.
Gear125 completÃƒÂ³ 350 ms. Los cuatro exports quedaron archivados y auditados;
las tres parejas no se midieron por falta de escenas completas. El
[banco largo queda rechazado](docs/VOZ_SERIAL_CAMPANA_RESULTADOS.md). No hay audio nuevo.

## Siguiente trabajo

1. Integrar el [motor portable VCO](docs/VCO1_PORTABLE_RESULTADOS.md) tras
   cerrar el stamp y la carga conjunta. Ampliar CV/trims reservados
   y C4=100 pF antes de promover calibraciÃ³n u otro perfil.
2. La [condiciÃ³n inicial conjunta](docs/VOZ_INICIALIZACION_RESULTADOS.md)
   ya completÃ³ sus ciclos propios. Contrastar una inicializaciÃ³n para
   rÃ©gimen oscilatorio y reducir la deriva medida, con carga por ciclo,
   niveles/offset de J7 y coste antes de ampliar o escuchar.
   Los controles permanecen impuestos; la escala local no es una cota global.
3. Cerrar contornos, controles y fuentes restantes; despuÃƒÂ©s comprobar la voz,
   plazos y adaptadores de escucha/host para su alcance declarado.

## DocumentaciÃƒÂ³n y verificaciÃƒÂ³n

- [Contrato de plugins RackForge](https://github.com/kalexis1994/rackforge/blob/main/docs/PLUGIN_DEVELOPMENT.md).
- [Plan vigente](docs/PLAN.md) y [matriz de fidelidad](docs/MATRIZ_DE_FIDELIDAD.md).
- [Fuentes](docs/FUENTES.md), [revisiones](docs/REVISIONES.md) y
  [validaciÃƒÂ³n sin hardware](docs/VALIDACION_SIN_HARDWARE.md).
- [Bloques](docs/BLOQUES.md), [hallazgos](docs/HALLAZGOS.md) y
  [escenas de captura](docs/CAPTURAS.md).

Regresiones pÃƒÂºblicas de los dos cierres nativos recientes:

```powershell
$env:RUST_MIN_STACK = "8388608"
$env:RUSTFLAGS = "-C link-arg=-Wl,--stack,8388608" # toolchain GNU de los recibos
cargo test --offline --locked -p rf-d-circuit --test vco1_increment --test vco1_increment_no_alloc --test vco1_increment_adaptive --test vco1_increment_adaptive_no_alloc
```

Los recibos de producciÃƒÂ³n registran compiler, flags, outputs y hashes.
Sus herramientas preservan intentos: una repeticiÃƒÂ³n debe preparar un recibo
nuevo, sin sobrescribir una campaÃƒÂ±a congelada. Heap cero no prueba RT.

El objetivo musical es una voz mono para bajos, leads y articulaciÃƒÂ³n en vivo.
Presets/MIDI y automatizaciÃƒÂ³n son adaptadores de RackForge; no representan
memoria del instrumento clÃƒÂ¡sico. AÃƒÂºn no hay paquete RF-D instalable ni
admisiÃƒÂ³n de fidelidad fÃƒÂ­sica o deadline de la voz.

## Historial y material local

El [historial de esta portada](README_HISTORICO_2026-10-07.md) conserva
exactamente los estados anteriores y sus enlaces. Los
[snapshots](evidence/voice_documentation_snapshot01.json) no cambian cÃƒÂ³digo,
modelos, datos o gates; cada resultado histÃƒÂ³rico conserva su protocolo.

Manuales, esquemas, fuentes originales, WAV y binarios privados se conservan
en directorios locales ignorados. No se incluyen en Git o el paquete.
RF-D no implica afiliaciÃƒÂ³n con Moog Music.

La [QA de publicaciÃƒÂ³n](evidence/voice_vco1_increment_tests01.json) verifica
inputs protegidos, nuevos tests y archivos privados. El
[snapshot previo](evidence/voice_lm741_port_documentation01.json) conserva
las tres portadas anteriores por bytes exactos. El rechazo largo sigue vigente.

[Modos de carga: excitaciÃ³n y observaciÃ³n](docs/VOZ_MODOS_RESULTADOS.md),
27 contrastes complejos y diagnÃ³stico de energÃ­a. El modo local mÃ¡s lento
no fija el tiempo de arranque de la voz. â‰ˆ129 MiB recuperados por compresiÃ³n
transparente sin borrar evidencia. DiagnÃ³stico local, sin bound global.

[Prefijo conjunto desde DC condicionado](docs/VOZ_PREFIJO_CONDICIONADO_RESULTADOS.md):
500 Âµs en dos perfiles, 4800 ecuaciones contrastadas, checkpoints y restores
exactos. La continuaciÃ³n de esa historia estÃ¡ completada abajo.

[Ciclos desde raÃ­z conjunta](docs/VOZ_CICLOS_CONDICIONADOS_RESULTADOS.md):
dos perfiles de5,25 ms, 68558 intervalos,9600 ecuaciones nuevas contrastadas
y dos seams exactos. Cargas y J7 aÃºn derivan entre cruces; siguiente:
inicializaciÃ³n para rÃ©gimen oscilatorio. Sin nuevo audio ni admisiÃ³n de RT.

[Condicionador de cargas de cadena](docs/VOZ_CARGAS_SEMILLA_RESULTADOS.md):
218 incÃ³gnitas, dos memorias/dos guesses, 872 ecuaciones de inicializaciÃ³n
y 9600 dinÃ¡micas contrastadas. Conserva 18 cargas histÃ³ricas o retargetea
solo C27; libera cuatro perfiles de 2 Âµs con restores exactos. Laboratorio,
sin cambio de fÃ­sica. Siguiente: ciclos propios y deriva, antes de escucha.

[Ciclos de dos memorias de carga](docs/VOZ_CICLOS_SEMILLAS_RESULTADOS.md):
cuatro perfiles de 5,25 ms, 137193 intervalos y 19200 ecuaciones nuevas
contrastadas; ocho restores exactos y reproducciÃ³n de 2 Âµs por bytes.
Ledger Radau de medias del panel/C27 y 18 cargas por fase. Periodicidad
asentada aÃºn pendiente; sin nuevo audio, cambio de fÃ­sica o admisiÃ³n de RT.

[CorrecciÃ³n conjunta de 18 cargas](docs/VOZ_CARGAS_RESPUESTA_RESULTADOS.md):
36 columnas de respuesta contrastadas, perturbaciÃ³n refinada conservando
el rechazo original, dos memorias nuevas con cierre no lineal y cuatro
liberaciones de 2 Âµs. Mejora de deriva periÃ³dica aÃºn no medida.

[Ciclos de las memorias corregidas](docs/VOZ_CICLOS_CORREGIDOS_RESULTADOS.md):
cuatro trayectorias de 5,25 ms, 137176 intervalos y 19200 ecuaciones nuevas
contrastadas; ocho restores exactos y reproducciÃ³n de 2 Âµs por bytes.
ComparaciÃ³n propia de las 18 cargas y J7. Asentamiento todavÃ­a pendiente.

[Tangente temporal de historia](docs/VOZ_TANGENTE_HISTORIA_RESULTADOS.md):
48 pasos contrastados, 9600 columnas Hx, 432 direcciones y 1728 solves
perturbados. ReproducciÃ³n por bytes de las raÃ­ces anteriores; cuatro
rechazos con replay conservados. Respuesta local a h fijo, aÃºn no mapa periÃ³dico.

[PropagaciÃ³n temporal de memoria](docs/VOZ_PROPAGACION_HISTORIA_RESULTADOS.md):
12 ventanas/768 pasos, 6912 direcciones y 27648 solves de historias propias.
Contraste independiente y continuidad exacta; nueve RHS por factorizaciÃ³n.
AdmisiÃ³n limitada al calendario fijo de esas ventanas; retorno completo pendiente.
[QA vigente](evidence/voice_history_propagation_tests01.json).

[Derivada del cruce y proyecciÃ³n de fase](docs/VOZ_EVENTO_HISTORIA_RESULTADOS.md):
ocho brackets, 72 direcciones y 576 solves nuevos de historias propias.
Contraste independiente del tiempo relativo y del estado sobre la secciÃ³n.
Retorno de periodo completo y calendario adaptativo siguen pendientes.
[QA vigente](evidence/voice_history_event_tests01.json).

[Intervalo completo entre resets](docs/VOZ_INTERVALO_RETORNO_RESULTADOS.md):
22356 pasos reproducidos, cuatro historias completas de C27 y contraste
del periodo y deriva de las 18 tensiones de memoria. 15 operadores
independientes seleccionados; sÃ³lo la direcciÃ³n 139 tiene FD completa.
[QA vigente](evidence/voice_return_interval_tests01.json).

[Base condicionada de las semillas corregidas](docs/VOZ_BASE_CARGAS_CORREGIDAS_RESULTADOS.md):
36 columnas, 146 raÃ­ces y 288 pasos perturbados. PropagaciÃ³n independiente
de la base por los dos primeros pasos de cada memoria; control explÃ­cito
frente a la inyecciÃ³n aislada de C27. Falta el retorno completo desde estas raÃ­ces.
[QA vigente](evidence/voice_charge_basis_tests01.json).

[Retorno desde la raÃ­z condicionada](docs/VOZ_RETORNO_CONDICIONADO_RESULTADOS.md):
42544 pasos base y 170176 solves perturbados de C27 desde sus propias
raÃ­ces. Ambos tiempos de reset, periodo y deriva en fase contrastados;
20 operadores independientes para las 18 columnas. FD completa sÃ³lo C27.
[QA vigente](evidence/voice_conditioned_return_tests01.json).
