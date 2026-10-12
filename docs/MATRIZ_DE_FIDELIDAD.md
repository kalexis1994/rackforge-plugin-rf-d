# Matriz de fidelidad vigente

2026-10-09. [Perfil CA3046 documental nominal](OBJETIVO.md); no hay acceso
físico presente o futuro. Los parámetros activos, tolerancias y población
vintage conservan sus incertidumbres. Equivalencia numérica con un oráculo
no significa identidad sonora con el hardware.

| Bloque | Topología / cálculo disponible | Implementación o contraste actual | Brecha siguiente |
|---|---|---|---|
| Teclado/glide/ruedas | Alcance del manual y controles de laboratorio | Fuentes impuestas | Leyes eléctricas y comportamiento mono/legato |
| VCO1 | CA3046, convertidor, Schmitt/reset, ondas y panel trazados | [Primer ciclo nativo con carga activa](VOZ_PRIMER_CICLO_RESULTADOS.md), parámetros condicionados y refinamiento | Periodicidad asentada; panel/CV/rieles completos |
| Cargas de juntura VCO | Leyes de las tarjetas condicionadas | [Depleción nativa](VCO_CARGA_JUNTURA_RESULTADOS.md), Q/C/ΔQ/I/G y derivadas en 1280 casos | Transporte/difusión, térmica y BJT/JFET completos |
| BJT de VCO | Subset condicionado de las tarjetas NPN/PNP | [Stamp de cuatro terminales](VCO_BJT_NOMINAL_RESULTADOS.md), transporte/difusión/depleción a 25 °C; 1536 vectores y doce probes SPICE | No identifica población física; JFET/741 e integración pendientes |
| JFET de VCO | Una mitad E402 nominal, B=1, cargas GS/GD físicas | [Stamp de tres terminales](VCO_JFET_NOMINAL_RESULTADOS.md), 2028 vectores, inversión y doce probes SPICE | Fuente común de ambas mitades en el circuito, 741 e integración; matching físico no identificado |
| LM741 de VCO | Macromodelo TI nominal y defaults ngspice a 25 °C | [Stamp completo de 37 incógnitas](VCO_741_NATIVO_RESULTADOS.md), cinco memorias, 60 stamps y seis raíces independientes | Newton y trayectoria propios, integración VCO; no equivalencia física del integrado |
| Puerto LM741 | Mismo macromodelo nominal, memoria por candidato | [Solver dinámico cargado](VCO_741_PUERTO_RESULTADOS.md), nueve trayectorias/672 pasos y 371 solves locales SPICE; cinco tangentes | Acoplamiento real en VCO; LTE/continuo y RT no admitidos |
| VCO2/VCO3 | Alcance documental | Sin núcleo nativo de voz admitido | Derivación y bancos propios |
| Ruido/modulación | Hipótesis/manual | Sin cálculo completo admitido | Topología, espectro y destinos |
| Mezclador ON | Cinco rutas y contactos límite de la red nominal | [837 casos con C27](MEZCLADOR_C27_RESULTADOS.md); [puerto directo 5×5 a 125 ns](MEZCLADOR_DIRECTO_RESULTADOS.md) | Generadores con impedancia real, OFF y taper |
| Ladder/VCAs/salida | Q29/Q30, ladder, recuperación, C10, dos VCAs y ruta J4/J5/J7 | [Entrada directa ON/C27 nativa](MEZCLADOR_DIRECTO_RESULTADOS.md), ambos R61, 12 escenas/192 pasos y zona previa; algoritmos anteriores conservados | Controles y fuentes completos; población física y RT |
| Contorno de volumen | Gatillo, seguidor y cargas documentados; laboratorio con rechazos conservados | [Puerto C2/reset cargado](PUERTO_CONTORNO_CADENA_71.md); C2/reset aún impuestos en el nativo de 71 nodos | Conmutación estable e integración del contorno completo |
| Contorno de filtro | Alcance y puntos de entrada documentados | Frontera impuesta | Circuito y banco propios |
| Voz nativa conjunta | VCO1, BUS/C27 y cadena hasta J7 con controles impuestos | [Dos perfiles de5,25 ms](VOZ_PRIMER_CICLO_RESULTADOS.md), resets, balances y refinamiento | Arranque DC conjunto, asentamiento, contornos, fuentes restantes y RT |
| Voz SPICE conjunta | VCO1 y cadena con contorno de laboratorio | [Cuatro escenas cortas admitidas](VOZ_SEIS_ACTIVO_RESULTADOS.md); [largo rechazado y auditado](VOZ_SERIAL_CAMPANA_RESULTADOS.md), una de cuatro completa | Contrastes largos sin medir; causas de abortos pendientes |
| Audio / producto | Escuchas de alcance parcial conservadas | Sin voz nativa instalable admitida | Voz completa, adaptador de escucha, deadlines, host y paquete |

El [VCO1 nativo ensamblado](VCO1_STAMP_RESULTADOS.md) conserva 134
incógnitas, dos 741 completos, BJT/JFET, Schmitt/reset y cargas del panel.
40 casos y todas las derivadas admiten el stamp, con arranque DC C1=0
condicionado y snapshots SPICE. No admite DC libre, arranque calibrado
rechazado, arranque propio, ciclos completos o refinamiento nativo.
El [Newton conjunto](VCO1_NEWTON_RESULTADOS.md) pasa dos DC condicionados
y seis continuaciones libres de 8 us/224 pasos desde semillas importadas
de laboratorio; no identifica periodos o eventos de reset.
El [arranque propio posterior](VCO1_ARRANQUE_RESULTADOS.md) sí pasa diez
raíces desde circuito e incidencias independientes. Los ciclos de paso
fijo se rechazan en el reset. La copia privada con subpasos completa 30ms,
pero no pasa dispersión entre períodos y no es producción admitida.
El [stamp de subpasos/control temporal](VCO1_SUBPASOS_RESULTADOS.md)
verifica48 stamps y28 raíces disponibles;20 raíces independientes fallan.
La campaña del controlador se rechaza por precisión de representación,
con KCL fuera de gate y corrección menor que1ULP en la referencia −4V.

El [bloque de incrementos](VCO1_INCREMENTOS_RESULTADOS.md) recupera
50 raíces con memoria hi/lo y referencia completa Decimal100. El
controlador mantiene los gates y transporta ambas componentes. Campaña
rechazada a 2,434338 ms por LTE confirmado en Q6 (2,013 µV > 2 µV).
No admite ciclo completo/refinamiento; sigue grilla más fina. Pila de
laboratorio 8 MiB declarada; heap cero no admite RT.


El [diagnóstico de grilla más fina](VCO1_RESET_GRILLA_RESULTADOS.md)
recupera el intervalo inicial, pero conserva otro rechazo temporal en
XIC3.7 tras 188,881 ns de continuación condicional y 32.300 pasos.
22 raíces coinciden con Decimal100. Analizar dinámica/discretización
741 antes de extender otra grilla o banco; código de producción intacto.

El [ensayo SDIRK y descriptor local](VCO1_SDIRK_RESULTADOS.md)
contrasta etapas/cargas, pero ambos recorridos quedan rechazados por LTE
confirmado en XIC3.7. Modos rápidos coincidentes≈7,629 fs/0,370 ps, sin
certificación global. Cerrar subdivisiones; derivar contrato del puerto741
contra tarjeta completa antes de modificar sus dinámicas o integración.

## Estado de la nota larga

El [preflight02](../evidence/voice_serial_preflight02.json) admitió recursos,
no el circuito. Gear500/Gear250/Trap125 se detuvieron a
136,630269/150,293268/15,940421 ms; Gear125 completó 350 ms. La
[auditoría final](VOZ_SERIAL_CAMPANA_RESULTADOS.md) conserva los cuatro recibos y
archivos. Banco rechazado, tres parejas no medidas y ningún error de
recursos/almacenamiento. Los prefijos no cubren tiempo ausente.

El [diagnóstico Gear500](../evidence/voice_serial_prefix_nominal50001.json)
y la [auditoría decimal](../evidence/voice_serial_prefix_decimal01.json)
conservan reloj y 15 vectores bit a bit frente al candidato anterior;
las otras tres columnas difieren hasta 4,24×10⁻²² V. No hay identidad bit a
bit global ni causa de aborto demostrada. El mensaje de Q7 no diagnostica
por sí solo todo el sistema.

## Cómo interpretar las admisiones

- **Topología:** conexiones y valores respaldados para la revisión declarada.
- **Cálculo:** pasa los escenarios/gates de su protocolo con hipótesis explícitas.
- **Nativo:** implementación y memoria contrastadas para ese subconjunto.
- **Audio externo:** requiere procedencia y condiciones comparables; permanece abierto.
- **RT/producto:** deadline, recursos y flujo de host deben medirse; permanecen abiertos.

La [QA reciente](../evidence/voice_vco1_newton_tests01.json) cubre 220,
con tres ejecuciones nuevas y 217 heredadas. No convierte los nominales
BJT/JFET en parámetros de un instrumento real. R61=200 Ω/200 kΩ sigue siendo
una discrepancia documental; α no identifica taper y ramas omitidas no
representan contactos OFF. Mantener manuales/audio/binarios en local ignorado.

El [historial de esta matriz](MATRIZ_DE_FIDELIDAD_HISTORICA_2026-10-07.md)
conserva todos los estados y resultados anteriores. El
[snapshot por hash](../evidence/voice_documentation_snapshot01.json)
respalda esa copia exacta; ningún algoritmo, dato numérico o gate cambia.

## Puerto 741 exacto — 2026-10-08

[Contrato y resultados](VCO1_741_CONDENSACION_RESULTADOS.md): eliminación
exacta de interiores en Newton, 12 sistemas y nueve pares de raíces
cargadas Decimal100. Retiene cinco terminales/memorias, retornos y
reconstrucción completa; no suprime dinámica ni cambia producción.
La alimentación dinámica de la base Q2 por L2 explica más del 99,98 %
de la diferencia full−end en los dos pisos SDIRK; explicación local,
no causalidad de todo el reset ni identificación física del integrado.
Mantener rechazos temporales, ciclos/refinamiento/frecuencia, carga activa,
física y RT abiertos. [QA](../evidence/voice_vco1_741_condensation_tests01.json)
hereda 235 tests; cero nuevos o reejecutados. Publicación distingue
repeticiones y raíces de laboratorio de tests unitarios.

## Radau cargado — 2026-10-08

[Etapas acopladas y resultados](VCO1_RADAU_RESULTADOS.md): discretización
distinta sobre las mismas cargas/tarjetas. Pasa 48 raíces iniciales y
recupera ambos pisos SDIRK; continuación de 1 µs y dos perfiles de 3 ms
completos atraviesan el siguiente reset. 72 etapas seleccionadas y 144
identidades de base Q2/L2 contrastadas. No son una trayectoria completa
independiente, arranque propio, periodicidad/frecuencia refinada o física.
Producción intacta; heap/RT y voz completa pendientes. [QA](../evidence/voice_vco1_radau_tests01.json)
hereda 235 tests y conserva todos los rechazos anteriores; cero nuevos
tests unitarios/ejecuciones heredadas y cero SPICE/audio nuevos.

## Ciclos propios Radau y escucha nativa â€” 2026-10-08

[Dos recorridos de30 ms](VCO1_RADAU_CICLOS_RESULTADOS.md) desde arranque propio,
C4=10 pF nominal, pasan periodicidad/corrientes/refinamiento y conformidad
con Gear/Trap archivados.16 comparaciones de etapas reales; diagnÃ³stico
Newton:18 comparaciones independientes/14 etapas Ãºnicas, con fallo y replay.
235 tests Rust heredados por identidad. Cuatro WAV del VCO nativo: ciclo real
repetido, sin filtro/VCA y sin simular toda la duraciÃ³n. ProducciÃ³n/RT abiertos.

Siguiente: motor portable, CV/trims reservados/C4=100 pF y dominio temporal
comÃºn con la cadena. El VCO usa mÃ­nimos por debajo125 ns; resolver esa brecha
antes del mixer activo y transferir R6/R45 una sola vez. No relajar gates o
duplicar cargas. [QA](../evidence/voice_vco1_radau_cycles_tests01.json) conserva
rechazos y snapshots, verifica checkpoints/trazas reversibles y regenera PCM.
La validaciÃ³n nominal no identifica una unidad vintage.

## Motor portable de referencia — 2026-10-08

[VCO1 portable](VCO1_PORTABLE_RESULTADOS.md) incorpora arranque propio,
reloj u64, checkpoint completo y aceptación atómica con corrientes Radau.
Cuatro tests nuevos pasan; 26 comparaciones de etapas con Decimal heredado,
12 corrientes y heap cero medido. 235 tests heredados; 239 cubiertos.
Kernel y leyes mantienen identidad; no se repitieron los dos bancos largos.
No acredita deadline, voz completa o física.

Próximo cierre: dominio de paso y carga conjunto con mixer/ladder/VCAs,
sin duplicar R6/R45 ni imponer un piso de125 ns al VCO.
[QA](../evidence/voice_vco1_portable_tests01.json).

## Cadena Radau con carga explícita — 2026-10-08

[68 tensiones y memoria hi/lo](CADENA_CARGA_RADAU_RESULTADOS.md), BUS/C10
explícitos, leyes anteriores conservadas. Doce escenas y 72 etapas propias
del oráculo pasan contra el nativo, 180 corrientes, 221.952 entradas de
Jacobiano y ocho casos estructurales de contacto. Cuatro tests nuevos;
243 cubiertos con 239 heredados. Medios pasos de7,629 ps contrastados
localmente y heap cero en operaciones medidas; sin SPICE/audio/RT nuevos.

Siguiente: stamp conjunto VCO/cadena y transferencia única de R6/R45;
el VCO todavía no recibe la carga activa de este banco. Las fuentes
continúan impuestas y no se admite una trayectoria larga conjunta.
[QA](../evidence/voice_chain_charge_tests01.json).

## Cierre VCO1/cadena local — 2026-10-08

[Cuatro pasos acoplados](VOZ_BUS_CONJUNTO_RESULTADOS.md), ocho etapas y
1.600 residuos independientes en candidatos nativos. Panel y C27 con dueño
único; sin fuente ideal en BUS. No son raíces independientes ni trayectoria
con error temporal admitido. Historia inicial condicionada; fidelidad y RT
pendientes.

## Motor temporal conjunto — 2026-10-08

[Motor condicionado](VOZ_MOTOR_TEMPORAL_RESULTADOS.md): cuatro perfiles
de2 µs/80 intervalos; LTE y refinamiento al mismo reloj pasan.24 etapas
seleccionadas verificadas por residuos independientes en puntos nativos.
Heap cero en dos rutas medidas, stack32 MiB y sin admisión RT. No se
admiten primer reset/ciclo, nota musical, arranque DC conjunto ni fidelidad.

## Primer ciclo conjunto con carga activa — 2026-10-08

[Dos perfiles hasta5,25 ms](VOZ_PRIMER_CICLO_RESULTADOS.md), dos resets y
un ciclo transitorio VCO1→BUS→ladder/VCAs→J7. LTE, balances C1/BUS y
refinamiento de200 coordenadas en21 relojes pasan;60 etapas contrastadas,
12000 residuos,60 corrientes terminales. Dos pausas administrativas quedan
conservadas y se retoman por bits sin duplicar prefijos.248 tests Rust
heredados, sin pruebas Rust, audio o SPICE nuevos.

Siguiente: inicialización y controles de cadena, niveles BUS/J7, offset
y periodicidad asentada antes de escucha. Arranque DC propio conjunto,
contornos completos, nota musical, fidelidad vintage y tiempo real siguen
pendientes. Los límites anteriores describen sus bancos históricos.
[QA vigente](../evidence/voice_joint_cycles_tests01.json).

## Condición inicial conjunta y escalas locales — 2026-10-09

[DC condicionado con C1=0](VOZ_INICIALIZACION_RESULTADOS.md), dos semillas
y liberación2 µs/14+20 intervalos.400 ecuaciones DC y4800 de etapas pasan
con referencia independiente en puntos nativos. La memoria C27 difiere
≈0,9305 V respecto del lift histórico. La ganancia local BUS→J7 a410,8 Hz
es≈0,00448 V/V;18 modos de carga incluyen escalas hasta≈265 ms. Son
diagnósticos de cadena con BUS impuesto, sin cota global de asentamiento.

Siguiente: ciclos desde esta condición inicial, periodicidad/carga por
ciclo y niveles de J7 antes de escucha. El ciclo5,25 ms conserva su
semilla histórica. No se admite DC libre, encendido físico, contornos
completos, nota asentada, fidelidad o RT.248 tests Rust heredados,
sin tests Rust/audio/SPICE nuevos.
[QA vigente](../evidence/voice_joint_startup_tests01.json).

## Diagnóstico local de excitación y observación — 2026-10-09

[Excitación y observación de los 18 modos](VOZ_MODOS_RESULTADOS.md): 27
soluciones complejas contrastadas y ocho escalones analíticos. El modo de
265 ms es débil en BUS→J7; no adoptar su tiempo como warmup de la voz.
Los siguientes bancos parten de la nueva raíz conjunta condicionada y deben
medir carga/estado por ciclo. Compresión transparente de 626 archivos de
cache conservó todos los hashes y recuperó ≈129 MiB; mantener el guard de
1 GiB y los checkpoints. Sin nueva admisión de ciclos/audio ni cambio físico.

## Prefijo conjunto admitido — 2026-10-09

[500 µs a dos resoluciones](VOZ_PREFIJO_CONDICIONADO_RESULTADOS.md)
completados: 6015 intervalos, 12.030 medios endpoints, dos restores exactos,
4800 ecuaciones independientes y refinamiento de 200 coordenadas a dos
relojes comunes. Raíz high/low idéntica; sin cambio de física ni gates.
C27 cambia +0,255 mV en este prefijo; no hubo reset ni admisión de
periodicidad. Continuar desde los checkpoints finales hasta los ciclos,
con balance de carga/estado a la misma fase. Sin nuevo audio ni RT.

## Ciclos condicionados y brecha de asentamiento — 2026-10-09

[Ciclos desde500 µs hasta5,25 ms](VOZ_CICLOS_CONDICIONADOS_RESULTADOS.md)
completados en ambos perfiles con seams, cargas y reloj preservados.
9600 ecuaciones nuevas,48 corrientes terminales y200 coordenadas contrastadas
al mismo reloj. Dos resets por perfil y un periodo observado entre ellos;
KCL/balance/refinamiento pasan, pero los18 capacitores y J7 muestran deriva.

Siguiente: contrastar una inicialización para régimen oscilatorio con carga
y restauración algebraica. La raíz DC condicionada válida no acredita ese
régimen. Conservar ambas historias, no relajar tolerancias ni extender
un warmup fijo sin causa contrastada. Luego contornos, controles y fuentes
restantes, escenas reservadas y coste/host para el alcance de escucha.
Sin nuevos tests Rust/audio/SPICE ni admisión de encendido/fidelidad/RT.
[QA actual](../evidence/voice_joint_conditioned_cycles_tests01.json).

## Inicialización con carga prescrita — 2026-10-09

[Condicionador de laboratorio](VOZ_CARGAS_SEMILLA_RESULTADOS.md):
218 incógnitas restauran algebraicos a fase retenida y conservan 18 cargas
históricas o 17 con C27 retargeteado explícitamente. 872 ecuaciones iniciales
y 9600 dinámicas contrastadas; cuatro perfiles de 2 µs y restores exactos.
La física temporal no cambia. Pendientes ciclos propios y periodicidad;
media saw de endpoints y sesgo de entrada 6 son hipótesis de semilla.
No se admite arranque físico, contornos completos, audio nuevo, fidelidad
vintage o RT. 248 tests heredados sin reejecutarlos.
[QA vigente](../evidence/voice_joint_charge_seed_tests01.json).

## Ciclos propios de dos memorias — 2026-10-09

[Cuatro perfiles de 5,25 ms](VOZ_CICLOS_SEMILLAS_RESULTADOS.md) admitidos:
dos memorias/dos resoluciones, 19200 ecuaciones y 96 corrientes nuevas
contrastadas. Reproducción bit exacta de 2 µs y ocho restores; medias
Radau de saw/BUS/entrada 6 y balances de carga del panel/C27 cerrados.
18 cargas por fase y J7 medidos. Pendientes memoria periódica y periodos
consecutivos; no se admite escucha de voz completa, encendido físico,
fidelidad vintage o RT. Física intacta; 248 tests Rust heredados sin
reejecutarlos. [QA vigente](../evidence/voice_joint_seed_cycles_tests01.json).

## Respuesta estática y memorias corregidas — 2026-10-09

[Respuesta de las 18 cargas](VOZ_CARGAS_RESPUESTA_RESULTADOS.md) admitida
con contraste independiente y perturbación refinada. Cuatro raíces
corregidas/872 ecuaciones y cuatro liberaciones de 2 µs/9600 ecuaciones
dinámicas nuevas, cuatro restores exactos. Respuesta de fase retenida,
no del mapa periódico. Pendiente deriva de ciclos propios y periodos
consecutivos. Sin fidelidad vintage, encendido físico, nuevo audio o RT.
Física y biblioteca intactas; 248 tests heredados por identidad.
[QA vigente](../evidence/voice_joint_charge_response_tests01.json).

## Ciclos de dos objetivos corregidos — 2026-10-09

[Trayectorias propias completas](VOZ_CICLOS_CORREGIDOS_RESULTADOS.md), dos
memorias/dos resoluciones, 19200 ecuaciones y 96 corrientes nuevas
contrastadas. Ocho restores, cuatro prefijos bit exactos, ledgers propios
de panel/C27 y contraste de 18 cargas/J7 con sus historias anteriores.
No acredita periodos consecutivos asentados, encendido físico, fidelidad
vintage, nuevo audio o RT. Física intacta, 248 tests Rust heredados.
[QA actual](../evidence/voice_joint_corrected_cycles_tests01.json).

## Respuesta temporal local de memoria — 2026-10-10

[Hx y respuestas de etapa](VOZ_TANGENTE_HISTORIA_RESULTADOS.md), 48 pasos,
9600 columnas/432 direcciones contrastadas. 48 reproducciones bit exactas
de los pasos admitidos y 1728 solves perturbados; biblioteca física intacta.
No admite propagación periódica, elección adaptativa de paso, nueva memoria
asentada, fidelidad física, audio o RT. 248 tests Rust heredados.
[QA vigente](../evidence/voice_history_tangent_tests01.json).

## Composición temporal de historia — 2026-10-10

[Propagación de nueve direcciones](VOZ_PROPAGACION_HISTORIA_RESULTADOS.md)
en 12 ventanas/768 pasos del calendario real. Dos escalas centrales con
historias propias y Jacobianos independientes; 24 pasos seleccionados y
768 observaciones finales reproducidos por bits. Biblioteca/física intactas.
No acredita periodo completo, calendario adaptativo, derivada de tiempo de
evento, fidelidad física, audio o RT. 248 tests heredados por identidad.
[QA vigente](../evidence/voice_history_propagation_tests01.json).

## Observador de reset y fase local — 2026-10-10

[Tiempo y estado interpolados](VOZ_EVENTO_HISTORIA_RESULTADOS.md), ocho
brackets/72 direcciones y 576 solves propios contrastados. 16 pasos y
57600 coordenadas de sensibilidad reproducidos por bits. Física intacta.
No acredita periodo completo, evento continuo, calendario adaptativo,
memoria periódica, fidelidad, audio ni RT. 248 tests Rust heredados.
[QA vigente](../evidence/voice_history_event_tests01.json).

## Respuesta de C27 entre dos resets — 2026-10-11

[Recorrido completo a calendario fijo](VOZ_INTERVALO_RETORNO_RESULTADOS.md):
22356 pasos por bits, cuatro historias/89424 solves propios para 139.
Periodo, deriva en fase y las 18 tensiones de capacitores contrastados.
Las otras ocho columnas son recurrencia nativa con operadores seleccionados.
No admite raíz condicionada de cargas, mapa de Poincaré, adaptación,
memoria periódica asentada, fidelidad, audio ni RT. 248 tests heredados.
[QA vigente](../evidence/voice_return_interval_tests01.json).

## Base de memoria condicionada en las semillas corregidas — 2026-10-11

[36 columnas, 146 raíces y 288 pasos propios](VOZ_BASE_CARGAS_CORREGIDAS_RESULTADOS.md).
Raíces/corrientes y cuatro fixtures reproducidos por bits; oráculo de base
y propagación de cuatro pasos. Control positivo distingue C27 condicionada
de inyección 139. No admite retorno completo desde la raíz, asentamiento,
mapa periódico, adaptación, fidelidad, audio ni RT. 248 tests heredados.
[QA vigente](../evidence/voice_charge_basis_tests01.json).

## Retorno del dominio condicionado — 2026-10-11

[C27 desde su raíz hasta dos resets](VOZ_RETORNO_CONDICIONADO_RESULTADOS.md):
42544 pasos base, cuatro raíces propias y 170176 solves perturbados.
20 operadores/8000 ecuaciones y ambos tiempos/estados de evento contrastados.
FD completa sólo objetivo 5, memoria 0/calendario 125 ns. Falta admitir
las demás direcciones y la corrección dinámica. No admite Poincaré,
asentamiento, adaptación, fidelidad física o RT; 248 tests heredados.
[QA vigente](../evidence/voice_conditioned_return_tests01.json).

## Dirección dinámica y resultado no lineal — 2026-10-12

[Una combinación de objetivos](VOZ_CORRECCION_DINAMICA_RESULTADOS.md)
admitida por FD completa a dos tamaños. Cinco historias propias y seis
raíces, 40000 ecuaciones y 640000 coordenadas de prefijos por bits.
Mejora del candidato a=1 en este dominio: True.
No acredita todas las columnas, periodicidad, adaptación, fidelidad o RT.
[QA vigente](../evidence/voice_dynamic_direction_tests01.json).

## Candidato dinámico con calendario propio — 2026-10-12

[Dos perfiles adaptativos](VOZ_CANDIDATO_CICLOS_RESULTADOS.md) hasta10,25 ms;
ocho resets/seis intervalos, estados al mismo reloj, balances de carga,
14400 ecuaciones y seis restores por bits. Persistencia del criterio de
mejora: True. Sin cota asintótica, audio o RT.
[QA vigente](../evidence/voice_candidate_cycles_tests01.json).

## Diagnóstico de nivel y control del panel — 2026-10-12

[Tres puntos DC y AC de68 nodos](VOZ_APERTURA_CUTOFF_RESULTADOS.md),
G por FD a1/2 µV, C por incidencias, 48 solves/24 transferencias.
BUS ideal y pequeña señal; no acredita el nivel de una nota no lineal
ni trayectoria/audio nuevos. [QA vigente](../evidence/voice_cutoff_opening_tests01.json).
