# Plan vigente de RF-D

2026-10-09. Prioridad: completar una voz de circuito utilizable con evidencia
proporcionada al alcance. [Objetivo documental](OBJETIVO.md): CA3046 nominal;
[sin acceso fÃ­sico permanente](VALIDACION_SIN_HARDWARE.md).

## 1. CampaÃ±a monolÃ­tica cerrada

El candidato activo de seis correcciones pasÃ³ controles y cuatro escenas
cortas de 40 ms. Su extensiÃ³n serial de 350 ms quedÃ³
[rechazada y auditada](VOZ_SERIAL_CAMPANA_RESULTADOS.md): Gear125 completÃ³;
Gear500/Gear250/Trap125 abortaron a 136,630269/150,293268/15,940421 ms.
Cuatro procesos desde DC propio, todos los exports/recibos archivados y
ningÃºn error de recursos o almacenamiento. Tres parejas no medidas.

Se preservan fuentes, gates, fallos y datos completos/parciales. No lanzar
otra ampliaciÃ³n de correcciones lineales ni relajar tolerancias sin causa
contrastada. La audiciÃ³n del adaptador largo sigue sin admisiÃ³n.

## 2. VCO1 nativo con carga elÃ©ctrica cerrada

Ya existe el [orÃ¡culo funcional VCO1](VCO1_RESULTADOS_CIRCUITO.md). El
[puerto cargado directo](MEZCLADOR_DIRECTO_RESULTADOS.md)
entrega corrientes, tangentes y estados provisionales de la cadena ON/C27
hasta J7. Usarlo para conectar el generador y conservar la carga en ambos
lados; no reemplazar ese cierre por una suma de voltajes.

Aplicar el [protocolo previo nativo](VCO1_NATIVO_PROTOCOLO.md): revisiÃ³n, formas de onda,
CV/trims, parÃ¡metros de laboratorio, discretizaciÃ³n, memoria y retornos.
Contrastar oscilaciÃ³n, amplitud/offset, reset, frecuencia y source current
con las referencias ya existentes, incluyendo escenas reservadas. Confirmar
sÃ³lo el estado conjunto final; fallo sin publicar cargas parciales.

La entrada Q29/C27 directa pasÃ³ 12 escenas/192 pasos y doce puertos
cargados a 500/250/125 ns, ademÃ¡s de 64 pasos en la zona anterior. Los
nuevos mÃ³dulos admiten 125 ns..1 ms; los anteriores siguen desde 0.5 Âµs.
La [depleción BE/BC y GS/GD](VCO_CARGA_JUNTURA_RESULTADOS.md) pasó
1280 vectores independientes y derivadas. El [BJT nominal](VCO_BJT_NOMINAL_RESULTADOS.md)
ya incluye transporte/difusión y sustrato explícito a TEMP=TNOM=25 °C:
1536 vectores y doce escenas independientes ngspice. El
[JFET nominal](VCO_JFET_NOMINAL_RESULTADOS.md) pasó 2028 vectores y doce
escenas propias: inversión del canal y cargas GS/GD físicas. El
[741 completo](VCO_741_NATIVO_RESULTADOS.md) conserva sus 37 incógnitas,
tres capacitores y dos inductores: 60 stamps y seis DC propios. Ahora
el [ensamblaje VCO1 completo](VCO1_STAMP_RESULTADOS.md) ya reúne las
134 incógnitas, ambos E402 en fuente común, Schmitt/reset, waveformers,
panel y referencia −4 V. Pasó 40 casos y las 134×134 derivadas. El [Newton conjunto](VCO1_NEWTON_RESULTADOS.md) ya resuelve dos DC
condicionados y seis continuaciones libres cortas/224 pasos conservando
historia y candidato atómicos. El [arranque propio](VCO1_ARRANQUE_RESULTADOS.md)
pasa diez raíces desde semilla de circuito y contraste independiente.
Los pasos fijos 500/250/125ns se rechazan durante el reset; subpasos en
laboratorio completan 30ms pero fallan periodicidad. El [stamp de subpasos
y controlador](VCO1_SUBPASOS_RESULTADOS.md) pasan sus tests, pero la campaña
se rechaza por estancamiento local de la representación binary64.
Los [incrementos/memoria compensada](VCO1_INCREMENTOS_RESULTADOS.md) pasan
50 raíces y recuperan el antiguo piso. La nueva campaña se detiene a
2,434 ms por LTE: Decimal100 confirma 2,013 µV en el colector de Q6,
gate 2 µV. La grilla privada más fina encuentra un segundo piso en el 741;
analizar su dinámica e integración, conservando los gates; después
verificar ciclos completos/refinamiento/calibración;
seguir con carga activa;
transferir R6/R45 antes de acoplar al mixer que posee esas cargas.

Primer alcance: VCO1 y cadena con controles impuestos. No declarar tres
osciladores, contorno completo o otra poblaciÃ³n fÃ­sica por ese prototipo.


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

El [puerto exacto del 741](VCO1_741_CONDENSACION_RESULTADOS.md) ya
reconstruye las 134 incógnitas desde 70 exteriores y pasa nueve pares
condicionales de raíces Decimal100. La memoria de L2 explica más del
99,98 % del error full−end en la base Q2 de ambos pisos SDIRK. La
condensación no cambia ese rechazo. Siguiente: puerto dinámico conservando
el aporte derivativo de modo común, y error exterior frente a tarjeta
completa antes de una simplificación. Sin nueva grilla o trayectoria.

El [Radau cargado](VCO1_RADAU_RESULTADOS.md) recupera ambos pisos
SDIRK y completa 1 µs más dos perfiles de 3 ms, con el siguiente reset
observado. Conserva tarjetas/cargas/memorias y gates; 72 etapas y 144
identidades locales contrastadas. Siguiente: arranque propio, varios
períodos, corrientes de ciclo y refinamiento; el método sigue en laboratorio.

## 3. Completar comportamiento de voz

- Integrar el contorno de volumen y su gatillo conservando las cargas del
  [puerto C2/reset](PUERTO_CONTORNO_CADENA_71.md); usar los diagnÃ³sticos y
  rechazos del biestable para definir la polÃ­tica siguiente.
- Derivar el contorno de filtro y sus controles con fuentes/documentos propios.
- Osciladores 2/3, ruido, modulaciÃ³n, teclado/glide/ruedas y entrada externa.
- Completar OFF y taper del mezclador y acotar dispersiÃ³n/hipÃ³tesis fÃ­sicas.
  Mantener R61=200 Î© y 200 kÎ© como escenarios separados hasta nueva evidencia.

## 4. Escucha y producto

Una escucha debe identificar quÃ© genera la seÃ±al, nodo/carga de salida,
voltiosâ†’audio, resampling, cobertura y limitaciones. Conservar el alcance de
los WAV anteriores: la escucha de salida con seno impuesto no es la voz VCO.
El adaptador de nota larga congelado requiere su banco completo admitido.

Con la voz funcional: escenas musicales fijadas, diferencias de audio y
costos por bloque en plataformas RackForge. Promover optimizaciones sÃ³lo
conservando sonido/error y memoria; heap cero no sustituye deadlines.
DespuÃ©s cerrar estado/parametrizaciÃ³n, MIDI/host, UI y paquete RF-D.

## Reglas de avance

No repetir bancos heredados si sus algoritmos/inputs estÃ¡n idÃ©nticos y la
QA declara la herencia. AÃ±adir pruebas para el circuito que cambiÃ³ y su
integraciÃ³n; separar conformance, fÃ­sica, escucha y RT. Una campaÃ±a pendiente
permite avanzar bloques independientes con contratos y gates propios.

El [historial del plan](PLAN_HISTORICO_2026-10-07.md) conserva los estados
anteriores, prioridades y enlaces por bytes exactos. El
[registro de snapshot](../evidence/voice_documentation_snapshot01.json)
preserva su procedencia. No se eliminan fallos o evidencia del laboratorio.

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

## Cierre conjunto local — 2026-10-08

El [stamp de200 incógnitas](VOZ_BUS_CONJUNTO_RESULTADOS.md) cierra eléctricamente
VCO1, BUS/C27 y cadena hasta J7 con carga única del panel. Ocho etapas
contrastadas; siguiente bloque: motor conjunto con LTE, rollback e historia
propia corta. No ampliar campañas largas antes de ese contrato temporal.

## Motor temporal conjunto — 2026-10-08

[Cuatro continuaciones de2 µs](VOZ_MOTOR_TEMPORAL_RESULTADOS.md) controlan
error temporal, restauración exacta y rechazo atómico con historia posterior
generada por el solve conjunto. Siguiente: primer reset/ciclo con carga activa,
trazas y contraste de refinamiento antes de escucha. Arranque conjunto DC
propio, contornos completos y tiempo real siguen pendientes.

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

## Modos locales y recursos — 2026-10-09

[Excitación y observación de los 18 modos](VOZ_MODOS_RESULTADOS.md): 27
soluciones complejas contrastadas y ocho escalones analíticos. El modo de
265 ms es débil en BUS→J7; no adoptar su tiempo como warmup de la voz.
Los siguientes bancos parten de la nueva raíz conjunta condicionada y deben
medir carga/estado por ciclo. Compresión transparente de 626 archivos de
cache conservó todos los hashes y recuperó ≈129 MiB; mantener el guard de
1 GiB y los checkpoints. Sin nueva admisión de ciclos/audio ni cambio físico.

## Prefijo desde raíz conjunta — 2026-10-09

[500 µs a dos resoluciones](VOZ_PREFIJO_CONDICIONADO_RESULTADOS.md)
completados: 6015 intervalos, 12.030 medios endpoints, dos restores exactos,
4800 ecuaciones independientes y refinamiento de 200 coordenadas a dos
relojes comunes. Raíz high/low idéntica; sin cambio de física ni gates.
C27 cambia +0,255 mV en este prefijo; no hubo reset ni admisión de
periodicidad. Continuar desde los checkpoints finales hasta los ciclos,
con balance de carga/estado a la misma fase. Sin nuevo audio ni RT.

## Ciclos desde raíz conjunta y siguiente bloque — 2026-10-09

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

## Semillas con cargas prescritas — 2026-10-09

[Condicionador conjunto de laboratorio](VOZ_CARGAS_SEMILLA_RESULTADOS.md)
admitido: 218 incógnitas, dos objetivos y dos guesses; 872 ecuaciones de
acondicionamiento/9600 dinámicas contrastadas. Memoria 0 conserva 18 cargas;
memoria 1 conserva 17 y cambia C27 por una hipótesis guiada por media saw.
Cuatro liberaciones de 2 µs, refinamiento y restores exactos pasan.

Siguiente: ciclos desde estas semillas, con ledger de corrientes, carga
por fase, media panel y J7. Contrastar la reducción de deriva antes de
corregir o elegir memoria. La cuadratura de endpoints orienta el objetivo,
sin admitir periodicidad. No prolongar un warmup fijo sin evidencia.
248 tests Rust heredados; sin nuevos tests Rust, audio, SPICE o RT.
[QA actual](../evidence/voice_joint_charge_seed_tests01.json).

## Ciclos de las semillas con cargas — 2026-10-09

[Cuatro perfiles hasta 5,25 ms](VOZ_CICLOS_SEMILLAS_RESULTADOS.md), dos
memorias/dos resoluciones, 19200 ecuaciones y 96 corrientes de terminales
nuevas contrastadas. Endpoints de 2 µs idénticos por bytes; ocho restores
exactos. Las medias Radau y balances C27 se cierran con los estados reales.

Siguiente: corregir memoria usando corrientes medias y las 18 cargas,
contrastar la trayectoria y exigir periodos consecutivos antes de escucha.
Menor deriva de C27 no acredita las demás cargas ni asentamiento de J7.
Mantener cada historia, su fuente y gates. Sin warmup fijo, ajuste de
componentes o nuevos tests Rust/audio/SPICE/RT.
[QA actual](../evidence/voice_joint_seed_cycles_tests01.json).

## Respuesta de cargas y cierre conjunto — 2026-10-09

[Banco de las 18 cargas](VOZ_CARGAS_RESPUESTA_RESULTADOS.md): S de rango
18 en ambas memorias, 32700 ecuaciones de inicialización y 9600 dinámicas
nuevas. Derivadas centrales a ±125/62,5 µV admitidas con gates originales;
rechazos de perturbación, decoder, import y disco preservados.
Dos objetivos corregidos cierran el circuito y se liberan a 2 µs a dos
resoluciones, con cuatro restores exactos.

Siguiente: ciclos propios de estos objetivos a dos resoluciones; medir
18 cargas, salida y periodos consecutivos. La matriz estática no es
Jacobiano del mapa periódico ni la predicción una mejora ya medida.
[QA actual](../evidence/voice_joint_charge_response_tests01.json).

## Ciclos propios de la corrección conjunta — 2026-10-09

[Cuatro perfiles a dos resoluciones](VOZ_CICLOS_CORREGIDOS_RESULTADOS.md)
completos, 19200 ecuaciones nuevas contrastadas, ocho restores exactos y
cuatro prefijos de 2 µs bit exactos. La comparación reporta las 18 cargas,
J7 y la predicción estática con mejoras/empeoramientos, sin convertir
refinamiento en periodicidad. Siguiente: evaluar cargas restantes y periodos
consecutivos de una historia. Sin cambiar componentes ni elegir por amplitud.
[QA vigente](../evidence/voice_joint_corrected_cycles_tests01.json).

## Dependencia del paso respecto de su memoria — 2026-10-10

[Tangente absoluta de etapas](VOZ_TANGENTE_HISTORIA_RESULTADOS.md)
contrastada en 48 pasos/9600 columnas y 432 direcciones. Solves nuevos a
perturbaciones escaladas, con gates originales y cuatro rechazos/replays
preservados. Siguiente: propagación con RHS múltiples y calendario fijo,
contraste de historias propias, luego dependencia del tiempo/fase del retorno.
La selección adaptativa de paso y el mapa periódico siguen pendientes.
[QA actual](../evidence/voice_history_tangent_tests01.json).

## Propagación de memoria en calendarios registrados — 2026-10-10

[Doce ventanas contrastadas](VOZ_PROPAGACION_HISTORIA_RESULTADOS.md),
768 pasos, nueve RHS compartidos y 27648 solves de historias propias.
Jacobiano independiente propagado, continuidad y observaciones por bits.
Siguiente: retorno completo y derivada del tiempo/fase antes de corregir
memoria periódica. Calendario adaptativo y asentamiento siguen abiertos.
[QA actual](../evidence/voice_history_propagation_tests01.json).

## Tiempo del reset observado y estado en fase — 2026-10-10

[Ocho cruces locales](VOZ_EVENTO_HISTORIA_RESULTADOS.md) contrastan
el término de tiempo y la proyección de 72 direcciones, con 576 pasos
perturbados propios. El control positivo demuestra el efecto de omitir
el término temporal. Siguiente: propagación entre retornos y respuesta
respecto de las cargas iniciales, antes de corregir memoria periódica.
El observador interpolado no admite evento continuo ni adaptación.
[QA actual](../evidence/voice_history_event_tests01.json).

## Un intervalo completo: respuesta de C27 — 2026-10-11

[Periodo y deriva observados](VOZ_INTERVALO_RETORNO_RESULTADOS.md):
22356 pasos y 89424 solves perturbados, cuatro historias completas de
139, con ambas proyecciones. 15 operadores independientes; no propagación
independiente de todo el intervalo. Siguiente: construir el dominio de
cargas iniciales y contrastar perfiles antes de corregir memoria periódica.
[QA actual](../evidence/voice_return_interval_tests01.json).

## Base de cargas en las semillas corregidas — 2026-10-11

[36 columnas y liberación inicial](VOZ_BASE_CARGAS_CORREGIDAS_RESULTADOS.md)
contrastadas con 146 raíces propias y 288 pasos perturbados. El adaptador
de 18 RHS reproduce dos lotes de nueve por bits. La columna condicionada
de C27 difiere de la inyección unitaria 139. Siguiente: propagar desde
estas raíces hasta ambos resets y medir la dependencia de la deriva.
[QA actual](../evidence/voice_charge_basis_tests01.json).

## Raíz condicionada hasta ambos resets — 2026-10-11

[Retorno de C27](VOZ_RETORNO_CONDICIONADO_RESULTADOS.md): 42544 pasos
desde el origen y cuatro historias completas (170176 solves), con cinco
raíces auditadas y 20 operadores independientes. Siguiente: admitir las
direcciones necesarias mediante FD completa antes de corregir la deriva
dinámica y contrastar perfiles. Memoria periódica y adaptación pendientes.
[QA actual](../evidence/voice_conditioned_return_tests01.json).

## Primera dirección dinámica — 2026-10-12

[FD completa y candidato propio](VOZ_CORRECCION_DINAMICA_RESULTADOS.md):
rango 16, seis raíces, 212720 solves y 40000 ecuaciones independientes.
Ratio L2 0.00218670557; máximo 0.00199744081.
Siguiente: ciclos posteriores, calendario propio adaptativo y contraste
de perfil antes de adoptar una inicialización estable de la voz.
[QA actual](../evidence/voice_dynamic_direction_tests01.json).

## Candidato adaptativo y retornos posteriores — 2026-10-12

[Cuatro resets, dos resoluciones](VOZ_CANDIDATO_CICLOS_RESULTADOS.md),
10,25 ms, tres retornos por perfil, 14400 ecuaciones y seis restores por bits.
Persistencia de mejora en esta duración: True.
Siguiente: avanzar controles/cargas funcionales; no exigir una cota global
de asentamiento para iniciar un banco corto de otra frontera identificada.
[QA actual](../evidence/voice_candidate_cycles_tests01.json).

## Apertura del cutoff — 2026-10-12

[Diagnóstico de nivel DC/AC](VOZ_APERTURA_CUTOFF_RESULTADOS.md): el panel
puede abrir la transferencia sin cambiar componentes. Próximo bloque:
control temporal corto con cargas entrantes, caso nominal por bits y
refinamiento; después ampliar a una escena audible con nivel observado.
[QA actual](../evidence/voice_cutoff_opening_tests01.json).

## Control temporal de cutoff — 2026-10-12

[Cuatro perfiles de250 µs](VOZ_CUTOFF_TEMPORAL_RESULTADOS.md) con VCO/carga
conjunta. C18/cola y J7 responden; 28800 ecuaciones, balances y refinamiento.
Continuar desde los dos checkpoints abiertos propios hasta resets completos;
no recondicionar las memorias para sustituir la respuesta al cambio de panel.
[QA actual](../evidence/voice_cutoff_temporal_tests01.json).

## Cutoff abierto hasta resets completos — 2026-10-12

[Dos continuaciones propias](VOZ_CUTOFF_CICLOS_RESULTADOS.md) completan5,25 ms
totales, con prefijo heredado por bytes, dos resets y55200 ecuaciones.
Admisión de escucha de inspección del intervalo: True.
Continuar controles/contornos y otras fuentes sobre esta referencia;
conservar niveles físicos y separar adaptación de escucha, fidelidad y RT.
[QA actual](../evidence/voice_cutoff_cycles_tests01.json).

## Seguidor de volumen en la voz — 2026-10-12

[Cierre205 de laboratorio](VOZ_SEGUIDOR_RESULTADOS.md): Q3/Q2/CR6→R59→Q18
con VCO1 real, doce trayectorias de2 µs, refinamiento y9840 ecuaciones.
Conserva por bits400 coordenadas entrantes;72 corrientes de endpoints
contrastadas. Siguiente: cambios temporales C2/reset con memoria y restore,
luego contorno causal completo. No admite ADSR, adaptación205, hardware,
RT o nuevo audio. [QA](../evidence/voice_loudness_tests01.json).

## Fuentes C2/reset con memoria — 2026-10-12

[Dos continuaciones205 de10 µs](VOZ_SEGUIDOR_CONTROL_RESULTADOS.md):
cinco tramos,8200 ecuaciones, balances C18/C27 y veinte restores completos
de tramo por bits. Checkpoint conserva reloj, fuentes y410 componentes;
60 corrientes de endpoints contrastadas. Sigue: incorporar el estado C2
con carga/descarga y puerto de reset antes del biestable causal completo.
Sin audio nuevo, ADSR, adaptación205, hardware o RT.
[QA actual](../evidence/voice_loudness_control_tests01.json).

## C2 dinámico y red de carga/descarga — 2026-10-12

[Cierre217](VOZ_C2_CARGA_RESULTADOS.md): C2 deja de ser fuente ideal,
con Q16/Q17/Q18/Q19, panel eléctrico, CR9 y decay final ON/OFF. Cuatro
perfiles de50 µs,17360 ecuaciones, balances C2/C18/C27 y40 restores.
Condición inicial de C2 declarada;410 coordenadas de voz heredadas por bits.
Siguiente: biestable/gatillo causal con los tres puertos cargados.
Sin ADSR completo, audio nuevo, adaptación217, identificación física o RT.
[QA](../evidence/voice_c2_charge_tests01.json).

## Gatillo común cargado y memorias — 2026-10-12

[Cierre225](VOZ_GATILLO_CARGADO_RESULTADOS.md): Q12/Q20 y C7/C4 reciben
la carga de C2; RESET_DRIVER deja de ser fuente ideal. Cuatro perfiles de
10 µs,18000 ecuaciones, balances C2/C18/C27/C7/C4 y40 restores.
Fallo Newton/replay y adaptador de C4 preservados, mismos gates.
Siguiente: Q25/Q15 con carga no lineal y continuidad/refinamiento causal.
Sin latch completo, audio nuevo, adaptación225, identificación física o RT.
[QA](../evidence/voice_trigger_charge_tests01.json).


## Biestable cargado en la voz — 2026-10-12

[Cierre229](VOZ_BIESTABLE_CARGADO_RESULTADOS.md): Q25/Q15, R38/R39/R56 y
cargas de juntura compatibles liberan SET_BASE/Q25 colector/RESET_BASE.
C4 conserva historia y matriz de dos terminales;450 componentes heredadas
por bits. Cuatro perfiles de10 µs,18320 ecuaciones,3840 pasos y40 restores.
Malla inicial rechazada, refinamiento15.625/7.8125 ns admitido en los finales.
Siguiente: trayectoria de ataque/sustain/liberación con el circuito cerrado.
Cargas omitidas de otros dispositivos explícitas; sin ADSR completo,
contorno de filtro, audio nuevo, identificación física o RT.
[QA](../evidence/voice_latch_charge_tests01.json).


## Control temporal229 y S sostenido — 2026-10-12

[Motor adaptativo](VOZ_CONTORNO_ADAPTATIVO_RESULTADOS.md) continúa el
contorno cerrado: reposo2 µs, S sostenido50 µs, liberación50 µs.
Cuatro perfiles ON/OFF y máximos250/125 ns, misma semilla por escena.
32976 ecuaciones,3226 accepted/6452 finos,20 restores y8 rollbacks.
C2 carga y descarga desde el circuito, con balances y comparación en12
relojes por escena. No se modifican dispositivos o memoria entrante.
Siguiente: milisegundos y resets del VCO antes de una nota completa.
Sin Note On completo por KEY, ADSR asentado, audio nuevo, hardware o RT.
[QA](../evidence/voice_contour_engine_tests01.json).


## Milisegundos de contorno229 y reset — 2026-10-12

[Ventana cargada](VOZ_CONTORNO_RESET_RESULTADOS.md) de3.004 ms por perfil:
reposo4 µs, S sostenido1.5 ms, liberación1.5 ms; ON/OFF y límites2/1 µs.
Un reset del VCO por perfil con contorno/cadena activos;35724 ecuaciones,
12576 accepted/25152 finos,24 restores de prefijos de hasta16 accepted.
Balances y cortes al mismo reloj pasan, sin cambiar dispositivos/gates.
Siguiente: ciclo entre dos resets y extensión de la carga/liberación.
Sin replay completo de estos tramos nuevos, contorno desde silencio,
periodicidad asintótica, audio nuevo, identificación física o RT.
[QA](../evidence/voice_contour_reset_tests01.json).


## Ciclo del VCO con contorno229 y C7 cargado — 2026-10-12

[Continuación hasta11.442 ms](VOZ_CONTORNO_CICLO_RESULTADOS.md) conserva
cada historia propia y completa un ciclo transitorio entre dos resets
con VCO/BUS/filtro/VCAs/J7 y contorno activos. La apertura con C7 cargado
refuta el predictor anterior: fallo/replay preservados, una condición
numérica reparada sin modificar ecuaciones ni gates. Cuatro perfiles
admitidos, 26770 finos y 38472 ecuaciones;
unión exacta, refinamiento y balances pasan.
Siguiente: medir y acelerar el solve contra esta referencia para alcanzar
un contorno de duración musical. Contorno desde silencio, otras cargas
de placa2, contorno de filtro, fidelidad física y RT pendientes.
[QA](../evidence/voice_contour_cycle_tests01.json).


## Reuso del trial de Newton — 2026-10-12

[Cache local exacta](NEWTON_REUSO_RESULTADOS.md) conserva stamp y corrección
del trial ya aceptado. Benchmark de84 pares: mediana pareada
1.6693×, 760→460 ensamblados y696→396 solves.
Cuatro trayectorias completas coinciden por bytes con la referencia:
26770 finos, 24 restores, 368 avances repetidos, mismos gates y cargas.
Sin nueva duración o audio; 38472 ecuaciones heredadas por identidad.
Siguiente: reducir costo del sistema lineal contra esta referencia exacta.
Deadlines, contorno desde silencio y duración musical siguen pendientes.
[QA](../evidence/newton_reuse_tests01.json).


## LU con extensión contigua — 2026-10-13

[Reducción de trabajo](LU_EXTENSION_RESULTADOS.md) de eliminación con
pivotes/criterios originales. Lista indexada conservada como hipótesis
no elegida; extensión contigua confirmada con mediana pareada
1.0908× y37.72% menos actualizaciones.
84 pares y8 regresiones del solver; cuatro perfiles conservan40 archivos
por bytes,26770 finos y24 restores.38472 ecuaciones heredadas, sin
reejecutarlas. Sin duración o audio nuevos, ni admisión RT.
Siguiente: condensación de bloques dinámicos preservando puertos y masa.
[QA](../evidence/voice_lu_extent_tests01.json).


## Condensación dinámica de LM741 — 2026-10-13

[Prototipo de Schur](SCHUR_DINAMICO_RESULTADOS.md) elimina128
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
[QA de alcance](../evidence/voice_dynamic_schur_tests01.json).


## Schur refinado con residuo compensado — 2026-10-13

[Refinamiento acotado](SCHUR_REFINADO_RESULTADOS.md) conserva factores del mismo J, reconstruye
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
[QA](../evidence/voice_schur_refined_tests01.json).


## Perfil de costo y variantes no elegidas — 2026-10-13

[Medición por fase](SCHUR_COSTO_RESULTADOS.md) conserva84 pares por bits en una copia
privada: preparación82.47%, residuo0.70% del solve observado.
Tres hipótesis pasan candidatos pero fallan utilidad: medianas
0.8535×/0.9149×/0.9392×. Preservar todas; no elegir por el mejor intento.
Las dos últimas conservan396 trazas J/b/correcciones por bytes;
181368 filas y38472 ecuaciones independientes heredadas, sin reauditar.
21 regresiones incluyen ceros con signo, subnormales y no finitos.
Fallo de compilación/replay y reparación de tipo explícita conservados.
Sin campaña temporal, duración/audio nuevos o RT. Siguiente: construcción
y factorización en ubicación final, con precisión y costo antes de promover.
[QA](../evidence/voice_schur_cost_tests01.json).


## Schur en sitio y ciclo condicionado admitido — 2026-10-13

[Workspace local](SCHUR_EN_SITIO_RESULTADOS.md) llena/factoriza interiores64 y exterior330
en sus destinos, conservando458 correcciones, puertos, masa e historia.
Banco1.0086× y confirmación única1.0133× con el mismo ejecutable;
396 trazas por bits,26 regresiones incluyendo recuperación del workspace.
Cuatro recorridos propios pasan38472 ecuaciones nuevas y comparaciones
de229 coordenadas al mismo reloj frente a LU (máximo8.52e-13 V).
26770 finos,24 restores,368 avances repetidos,16 corrupciones y8 rollbacks.
Admitido para la ventana condicionada3.004 ms; sin duración/audio nuevos,
contorno desde silencio, identificación física o RT. Siguiente: otra
reducción estructural conservando puertos/cargas para duración musical.
[QA](../evidence/voice_schur_inplace_tests01.json).


## Contorno cargado condensado — 2026-10-13

[Reducción estructural](SCHUR_CONTORNO_RESULTADOS.md) incorpora 58 correcciones de contorno a los
128 interiores LM741: exterior 330→272 y reconstrucción completa de 458,
con 229 estados HIGH/LOW, R59/Q18, masas e historia conservados.
Costo pareado 1.0229× y confirmación 1.0251× frente al Schur admitido.
181.368 filas lineales nuevas, 38.472 ecuaciones de banco y otras 38.472
temporales pasan Decimal100; 35 regresiones con replay pasan.
Cuatro perfiles/26770 finos conservan restores, eventos y balances.
Admisión limitada al ciclo condicionado de 3.004 ms, sin duración/audio
nuevos, contorno desde silencio, identificación física o RT.
Siguiente: cadena con BUS/base Q18 retenidos, exterior potencial 140;
soporte inspeccionado, invertibilidad y utilidad pendientes. [QA](../evidence/voice_schur_contour_tests01.json).


## Cadena filtro/VCA condensada — 2026-10-13

[Partición cargada](SCHUR_CADENA_RESULTADOS.md) retiene BUS/base Q18 en ambas etapas y reduce
exterior272→140. Reconstruye458 correcciones y conserva229 estados
HIGH/LOW, masas, cargas y puertos compartidos con el contorno.
Medianas1.0299×/1.0265× frente al Schur con contorno;
181.368 filas lineales,38.472 ecuaciones de banco y otras38.472 temporales
nuevas pasan Decimal100;45 regresiones/replay. Cuatro recorridos con
26770 finos conservan balances, eventos y restores. Admisión condicionada
a3.004 ms, sin duración/audio nuevos o RT. Perfil privado por bits:
linearize≈50.3% del step, solve≈27.3%.
Siguiente: ensamblaje Radau en ubicación final, con J/b/raíces por identidad.
[QA](../evidence/voice_schur_chain_tests01.json).


## Ensamblaje Radau en ubicación final — 2026-10-13

[Dos buffers de Stamp](RADAU_EN_SITIO_RESULTADOS.md) se llenan por &mut y permutan referencias
después de aceptar, conservando J, masa, puertos, rechazos y estado229
HIGH/LOW.84 raíces/1834 campos por bits e iteraciones/trials idénticos.
Mediana pareada1.4004×:≈28.6% menos tiempo en el banco,
sin confirmación adicional según contrato.396 trazas lineales y40 exports
temporales por bytes;181.368 filas y dos bancos de38.472 ecuaciones heredados,
sin reauditar.11 regresiones, cuatro recorridos propios y26770 finos pasan.
Admisión limitada al ciclo condicionado3.004 ms; sin duración/audio nuevos
o RT. Siguiente: integración portable229 y contrato de ownership/memoria.
[QA](../evidence/voice_radau_inplace_tests01.json).


## Conjunto229 público y workspace propio — 2026-10-13

[Biblioteca Rust](CONJUNTO_PORTABLE_RESULTADOS.md) exporta conditioned_voice/conditioned_engine:
229 estados HIGH/LOW, puertos/cargas y controlador originales. Caller dueño
del Workspace, checkpoint separado de scratch y confirmación atómica.
Workspace3.378.208 bytes; Engine/Checkpoint4.800. Cero asignaciones en9
llamadas aceptadas y3 rechazadas;4 tests nuevos,248 heredados (252 cubiertos).
84 raíces y40 exports temporales por bytes;396 matrices guardadas reproducidas,
sin presentarlas como solves activos observados. Filas y ecuaciones heredadas
por identidad. Cuatro recorridos públicos/26770 finos admitidos para3.004 ms.
Biblioteca nueva, sin cache Cargo, duración/audio nuevos o RT. Siguiente:
receta pública de historia/controles y render offline condicionado. [QA](../evidence/voice_conditioned_portable_tests01.json).


## Receta propia y render offline condicionado — 2026-10-13

[Receta ejecutable](RECETA_CONDICIONADA_RESULTADOS.md): cuatro historias
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
[QA](../evidence/voice_conditioned_recipe_tests01.json).


## Gatillo sostenido y liberación: 12.004 ms propios — 2026-10-13

[Trayectoria ON](VOZ_SOSTENIDA_RESULTADOS.md) conserva historias propias
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
[QA](../evidence/voice_sustained_tests01.json).


## Liberación restaurada y conmutación observada

Continuación ON desde20.442 ms por8 ms, propios1/2 µs; sin nuevo evento.
458 valores HIGH/LOW y propuesta4096 ticks conservados por bits. Q25/Q15
cruzan y dC2/dt pasa negativa; corriente de ataque/decay/seguidor explica
el signo.19236 ecuaciones independientes,28 estados229 comunes y6 resets;
balances9 por fase/total/unión20.004 ms.14 restores/224 accepted reproducidos.
WAV960 frames/20 ms y CLI con tres comprobaciones ejecutadas. Sin rlib/cache
Cargo/SPICE nuevos;255 tests Rust heredados. Revisión de PDF originales y
errata Figure9-7/página9-5; no cambios de tarjetas, topología o tolerancias.
Ver [resultados y reproducción](VOZ_LIBERACION_RESULTADOS.md).
Siguiente: extender descarga y explorar su control decay con historias propias,
manteniendo puertos/cargas; obtener duración útil sin inventar un loop.


## Control eléctrico de decay, admitido en una escena cargada

Familia pública decay_voice/decay_engine: resistor de panel ensamblado
directamente, sin cambios a fuentes nominales. Ocho accepted de tres motores/
bibliotecas coinciden por bytes a100 kΩ. API set_decay_ohm cambia sólo R;
12 inválidos/2 restores inválidos rechazados.28.442→44.442 ms a1 kΩ desde
cada checkpoint propio;24732 ecuaciones/21 relojes229,
14 resets y9 balances de carga pasan.36.004 ms reales unidos, WAV36 ms;
CLI/PCM/sidecar y dos seams.255 tests Rust heredados, no reejecutados.
Compilación rechazada/replay conservados; falta de argumento del observador
reparada sin gates nuevos. [Resultados y reproducción](DECAY_CONTROL_RESULTADOS.md).
Siguiente: duración de escucha útil y costo del motor de la voz, manteniendo
puertos/cargas y contraste contra esta referencia antes de optimizar.


## Ensamblaje por cuadrantes y política estructural por CSR

Familia block_decay_voice/engine, nominales anteriores intactos. Pivotes
nulos no mejoran y cuadrantes públicos1 no pasan costo; ambos conservados.
Cuadrantes+CSR real pasan mediana0.800968 y política209764
posiciones.16.468.764 campos de stamp por bits;8721 Accepted
pareados en público,12 estados458 y9 balances Decimal100. Prefijo4 ms propio
identico;8244 ecuaciones independientes heredadas, ninguna reejecutada.
255 tests Rust heredados; sin Cargo/cache/SPICE/audio/duración nuevos.
[Resultados y reproducción](VOZ_COSTO_BLOQUES_RESULTADOS.md).
Siguiente: más duración real y señales observables, con esta familia y el
contraste de cargas/control. No ampliar certificados sin necesidad de señal.


La [liberación extendida con el motor público](VOZ_LIBERACION_EXTENDIDA_RESULTADOS.md)
añade32 ms reales: historia unida68.004 ms y dos WAV nativos68 ms, sin loop.
KEY/S/R heredados, unión completa3728 bytes;8 avances completos coinciden
con el ensamblado original. 41220 ecuaciones nuevas,
41 relojes229, balances y replay acotado pasan. C2 final0.880011 V,
no silencio completo admitido. CLI reproducible y cuatro checks.
Sin biblioteca/cache nuevas, fidelidad física, heap/deadline nuevos o RT.


El [banco ampliado y perfil actual](VOZ_CEROS_RESULTADOS.md) contrasta
168 pares y35471184 campos de stamp. Dos recorridos de ceros conservan
bits,1280 fixtures LU y seis errores, pero fallan utilidad5 %:
ratio1.000029624 con104488 bytes extra y0.977922929 sin
scratch extra. No se promueven. Perfil actual exacto: initialize55.13 %
incluye parts42.37 %, solve37.09 %; relojes anidados, sin ganancia inferida.
La voz pública y audio68 ms permanecen idénticos. Siguiente: ensamblado y
parts/copia de estados, conservando puertos, cargas y contraste completo.


El [ensamblado directo público](VOZ_ENSAMBLADO_RESULTADOS.md) evita
el contenedor200 y su copia a229, conservando constructor, validaciones,
sumas, masa, contorno y puertos.71019312 campos Parts/stamp por bits en168
pares; API pública ratio0.895860583 y workspace3378208 igual.
6464 Accepted completos/12 rejillas y nueve balances
coinciden en4 ms propios por resolución,68.442→72.442 ms; kernel ratio
0.920475855. 2748 ecuaciones originales
heredadas por identidad,0 nuevas. Fallos de binding/replays conservados.
Sin duración/WAV nuevos, heap/deadline o RT. Siguiente duración útil propia.


La [cola propia con ensamblado directo](VOZ_COLA_LARGA_RESULTADOS.md)
añade 64 ms eléctricos: historia de 132.004 ms y dos WAV de 132 ms, 6336 muestras.
Receta y 3728 bytes de unión idénticos; ocho avances comparados por bits.
76944 ecuaciones originales seleccionadas nuevas,
81 relojes de 229 estados, balances de carga y replay acotado pasan. C2 final
0.850987312 V; no silencio asintótico inferido.
CLI con diez entradas/código identificados y cuatro integraciones.
Sin biblioteca/cache nuevas, fidelidad física o RT. Siguiente escena útil de voz.


El [retrigger con memoria propia](VOZ_RETRIGGER_RESULTADOS.md)
añade 16,004 ms: segundo gatillo de 8 ms y liberación de 8 ms sin borrar cargas.
Dos eventos por resolución conservan 458 HIGH/LOW, resistencia, clock y propuesta;
16 Accepted posteriores pareados por bits con block, además de ocho de unión.
43968 ecuaciones seleccionadas nuevas, 22 relojes de
229 estados y nueve balances por fase/total/unión pasan. Dos WAV reales de 148 ms,
17 entradas/código identificados y cuatro integraciones CLI. Sin fidelidad física
o RT; la historia inicial sigue condicionada. [QA](../evidence/voice_retrigger_tests01.json).


El [cutoff cargado de panel](VOZ_CUTOFF_RESULTADOS.md) añade 16,004 ms:
α1→0,5→1 sin modificar KEY/CV ni borrar cargas. Codec completo RFCTF001 de
3736 bytes; 16 Accepted tras eventos y ocho de unión coinciden con block.
32976 ecuaciones seleccionadas nuevas con el panel
de cada fase, 22 relojes de 229 estados y nueve balances por fase/total/unión.
Dos WAV reales de 164 ms, 24 entradas identificadas y cuatro checks CLI.
Contorno de filtro pin16 sigue impuesto; sin Hz calibrados, fidelidad física o RT.
[QA](../evidence/voice_cutoff_tests01.json).


El [A/B de cutoff desde el mismo estado](VOZ_CUTOFF_AB_RESULTADOS.md)
compara α1/0,5 durante 8 ms con 458 HIGH/LOW, clock/propuesta y controles comunes.
Rama abierta nueva: 13740 ecuaciones seleccionadas;
cerrada: 13740 heredadas, sin reejecución. Once clocks229, balances/replay
pasan; cuatro WAV de 8 ms sin concatenación o normalización. RMS cerrado/abierto
1.02668585 (0.228751 dB), ventana con DC/transitorios. Siete entradas/código y
cuatro checks CLI. La historia/WAV continuo de 164 ms sigue sin prolongarse.
Sin Hz calibrados, contorno de filtro completo, fidelidad física o RT.
[QA](../evidence/cutoff_ab_tests01.json).


## 2026-10-14 — Seguidor del contorno de filtro cargado

Q22/Q21 complementario y R17/R74 con Q26/Q28 en un puerto de nueve nodos
y ocho terminales. 60 DC y 96 pasos locales de 1 mV admitidos, 32 clocks
comunes, 1520 filas originales y Jacobiano completo. El estrés de 2,15 V
queda rechazado por refinamiento a 8/4 µs, con fuentes/replay preservados.
La receta C11 se vincula al estado; 24 rechazos y 96 candidatos/replays pasan.
No integrar aún en la voz. Cerrar después temporizador C5, biestable y Q4
con la corriente de entrada de este puerto y el gatillo compartido; revisar
C12 opcional y alimentación. Resolver ataque/decay continuo antes de
refinamiento a gran señal y unión TAIL/ladder.
[Resultados](CONTORNO_FILTRO_PUERTO_RESULTADOS.md),
[QA](../evidence/filter_contour_port_tests01.json).


## 2026-10-14 — C5 continuo y gatillo de ambos contornos

C5/Q1/Q4 dejan de ser fuentes impuestas; Q12/Q20 reciben las cargas de
ambos contornos, con R32/R37/C1/CR1/CR2. 54 nodos, dos recetas opcionales,
teclado/S separados y máximos 8/4 µs: ocho trayectorias de 36 ms,
liberación y retrigger, memoria conservada y refinamiento admitido.
Escena eléctrica fija de panel; no extender la cobertura a todos los controles.
La dinámica de KEY depende de R60/C7; no asumir fase instantánea desde
el evento de fuente. Preservados fallo/replay y reparación del auditor.
Conectar ahora TAIL y volumen con placa 4 para medir una voz funcional.
Usar este núcleo como referencia y derivar un motor viable por bloques,
con error/cargas medidos; prioridad a señal audible antes de más certificados
locales. [Resultados](C5_GATILLO_COMPARTIDO_RESULTADOS.md),
[QA](../evidence/c5_trigger_tests01.json).


## Cierre de cargas de ambos contornos — 2026-10-14

Completada la [unión de ambos contornos con cadena](CONTORNOS_CADENA_RESULTADOS.md):
118 nodos, Q26/Q28 y C18 compartidos, VCA_BASE/TAIL internos, dos escenas
de 36 ms y referencia original de 119 nodos admitidas. Prioridad siguiente:
unir el VCO real al BUS de esta red, obtener una trayectoria audible y
medir reducción del circuito frente a la referencia. Panel general y RT abiertos.


## VCO real con ambos contornos — 2026-10-14

Completada la [voz de 250 incógnitas](VOZ_DOS_CONTORNOS_RESULTADOS.md):
BUS único, VCO real, ambos contornos cargados y J7; 8 ms en dos resoluciones
y original de 251 nodos admitidos. Ya no se impone una onda al filtro.
Prioridad siguiente: reducción del costo con puertos/cargas conservados y
error respecto de esta voz, duración suficiente para escuchar una nota.
No agregar certificados locales como condición previa a ese avance.


## Costo y duración de voz — 2026-10-14

[Orden y memoria del solver](VOZ_COSTO_RESULTADOS.md) admitidos en la voz
cargada: ~37 % menos costo lineal en el banco, Parts conservados por bits,
trayectoria ampliada a 24 ms en dos resoluciones y prefix antiguo contrastado.
Export local breve de J7 sin repetir ciclos. Prioridad siguiente: reducción
mayor del modelo contra esta referencia, con error musical/de puertos
medido, para una nota sostenida y un motor utilizable. RT sigue pendiente.


## 2026-10-14 — Nota corta y presupuesto temporal observable

[Completado](VOZ_NOTA_OBSERVABLE_RESULTADOS.md): primera política temporal
con circuito completo conserva gates Newton y reduce ~4× el costo del
banco de 24 ms. Nota propia de 100 ms, gatillo 1–75 ms, ambas memorias
y cargas hasta J7; 801 clocks y audio de duración real pasan. El prefijo
estricto compartido cubre 6 ms; refinamiento completo cubre 100 ms.
No se extiende la precisión estricta a interiores excluidos del estimador.
Prioridad: reducción espacial de VCO/741 y cadena con puerto/cargas y
error musical medidos. 553/555 s por 100 ms todavía exige esa reducción
para un motor utilizable. No agregar más certificados locales como
condición previa a esa implementación.


## 2026-10-14 — Retiro de datos y puerto R6/R45

[Limpieza](ALMACENAMIENTO_LABORATORIO.md): 22.34 GB regenerables, 110705
archivos y 10325 carpetas vacías retirados; ningún input admitido borrado.
Un área de ensayo nuevo queda vacía tras medir; no agregar clones/builds
o WAV por cada bloque. [Puerto exacto](VCO_PUERTO_PANEL_RESULTADOS.md):
cursor de R6 eliminado, corrientes de sierra/masa/BUS y gradientes completos
conservados, 70 estrellas y 1602 observaciones de voz pasan. El VCO
completo aún genera la sierra de referencia. Próximo: núcleo de fase con
forma/curva CV derivadas y contraste de reacción a la carga en este puerto.
No presentar el puerto resistivo como reducción ya completa del VCO/741.


## 2026-10-14 — VCO nominal de fase implementado

[Prototipo](VCO_FASE_NOMINAL_RESULTADOS.md): fuente periódica derivada de
circuito y red de salida de cuatro puertos. Frecuencia/fase, DC/armónicos
1–8 y reacción diferencial local al BUS pasan contra datos reservados.
~0.18 µs/muestra, cero heap medido en el núcleo; sin nuevo WAV/cache.
Siguiente bloque funcional: integrar este generador con el BUS real de
ambos contornos/ladder/VCAs y medir J7, C2/C5 y R59/R60. No ampliar
certificados del VCO nominal antes de esa unión. Curva CV, rangos,
modulación, otros selectores y arranque necesitan cobertura posterior.
La voz actual conserva su circuito de referencia y no obtiene aún este
ahorro; ni la fase periódica ni su tangente admiten fidelidad física o RT
de todo el instrumento.


## 2026-10-14 — Unión funcional del VCO periódico con la voz

[Resultados](HYBRID_VOZ_RESULTADOS.md): rama 40–100 ms con memorias
reales de ambos contornos/filtro/VCAs/J7. Se reemplaza sólo el VCO por
perfil periódico con carga de BUS; el reset obliga a corregir el perfil
52-armónicos por 901 nudos del ciclo nativo. Gates exteriores intactos;
J7 RMS 1,0672 %, pico 2,608 %, 5712 filas originales pasan. Heap cero;
28,5 s por 60 ms, sin RT ni nuevo WAV. Próximo bloque: reducir dinámica
de cadena sobre esta unión y contrastar J7/cargas/costo; luego arranque,
ataque y CV. Evitar volver a certificados aislados antes de esa función.


## 2026-10-14 — Frontera dinámica de cadena condensada

[Resultado](HYBRID_SCHUR_RESULTADOS.md): contornos y audio separados
por VCA_BASE/TAIL en ambas etapas Radau. Interiores 108/124, exterior
cuatro, estado físico completo de 118 incógnitas reconstruido. Misma
señal/cargas, 5712 filas originales y costo 0,843728 del control fresco.
El primer Schur correcto fue más lento; la versión final usa LU con
frontera y evita Jacobiano completo en trials de residual. Gates intactos.
Siguiente: reducir evaluación eléctrica de cadena sobre esta frontera
verificada, con cargas/J7/costo; luego ampliar arranque/ataque y CV.
La frontera pequeña no elimina por sí sola el costo de los stamps.


## 2026-10-15 — Evaluación de cadena preparada y compensada

[Resultados](HYBRID_STAMP_RESULTADOS.md): preparación inmutable y rutas
completo/residual, sin omitir LOW. Se conserva Jacobiano/masa y se evita
J·LOW denso usando las derivadas de dispositivos y puertos. El candidato
se valida una vez en 118 nodos antes de proyectar a los bloques. 5712
filas originales pasan; costo final 0,898562 del Schur fresco, sin
debilitar gates tras siete rechazos de costo. Margen temporal pequeño;
no implica deadline o RT. Próximo: perfilar y mejorar la representación
del sistema lineal con esta evaluación, conservando incidencias/cargas;
arranque/ataque y controles requieren bloques posteriores.


## 2026-10-15 — Recorrido contiguo de la matriz Radau

Admitido el [ensamblado por etapas](HYBRID_STAGE_RESULTADOS.md), con
11,35 % menos costo contra preparado fresco y trayectorias observadas
exactas. El perfil atribuye 3,62 s al ensamblado anterior, 1,86 s a CSR
y 4,43 s a factorización; instrumentación y benchmark se distinguen.
Siguiente: reducir materialización/inspección densa sin omitir entradas
reales, conservando puertos, backward, historia y cargas. No volver a
certificados aislados. Cadena nominal offline, sin ampliar arranque/CV/RT.


## 2026-10-15 — Representación directa del sistema temporal

Admitido [Radau directo](HYBRID_DIRECT_RESULTADOS.md), con cargas,
coeficientes, direcciones y trayectorias observadas conservados. Dos
candidatos correctos no alcanzaron el gate de costo; el conjunto final
lo pasa con 10,28 % menos costo y margen pequeño. Sin nuevo dominio
físico/RT. Continuar perfilando evaluación eléctrica/factores sobre la
unión funcional antes de elegir otra reducción; conservar historia,
puertos y cargas, sin otra secuencia de certificados aislados.


## 2026-10-15 — Mantener directo tras rechazos de factores

[Resultado](HYBRID_SUPPORT_RESULTADOS.md): reducir productos mediante
soporte pivote disperso no aceleró; tampoco el recorrido contiguo con
omisión de trabajo nulo. Ratios 1,068040 y 1,031722, ambos rechazados.
El solver directo sigue activo y se conservan fuentes/replays y nuevos
fixtures de fill-in/swaps/overflow. Siguiente: perfilar contribuciones
de evaluación eléctrica vigente (6,708 s en el perfil, sección mayor)
antes de elegir otra transformación. Conservar unión, puertos, historia
y cargas; sin ampliar arranque/CV/RT ni reiniciar certificados aislados.


## 2026-10-15 — Pasar de interfaces a reducción algebraica

Los [cuatro ensayos de interfaz](HYBRID_COMPACT_RESULTADOS.md) conservan
precisión y fallan el gate previo de costo. El directo sigue activo; no
se promueve el mejor 8,27 % retroactivamente. El [siguiente bloque](LADDER_REDUCCION_ALGEBRAICA_PLAN.md)
fija nodos 0–15 del ladder, cuatro cargas diferenciales y puertos de
entrada, TAIL y salidas con sus acoplamientos al padre. Derivar variables
algebraicas desde las mismas ecuaciones, con beta finita y reacción de
cargas; reconstruir estados y medir en la voz funcional. Sin nueva
admisión, ampliación de arranque/CV/RT o repetición de certificados aislados.


## 2026-10-15 — Ladder local reconstruido; integrar en la voz

El [bloque local](LADDER_ALGEBRAICO_RESULTADOS.md) pasa 48 etapas y sus
gates de reconstrucción, derivadas, conservación, cargas/rechazos. El bias
incluye su capacitor de 220 µF: cuatro memorias internas, siete algebraicas
y cinco puertos; ninguna memoria descartada. Siguiente: insertar esas
coordenadas en ambas etapas de la voz y reconstruir sus 118 nodos para
la auditoría original. Conservar cargas cruzadas, historial HIGH/LOW y
TAIL/VCA_BASE; validar trayectoria 40–100 ms antes del costo fresco.
El directo sigue activo; no hay admisión global o RT del kernel nuevo.


## 2026-10-15 — Unión del ladder verificada; retirar trabajo duplicado

El [candidato global](LADDER_VOZ_RESULTADOS.md) reconstruye la álgebra en
ambas etapas, conserva memorias y puertos y pasa trayectoria/auditoría
original. La salida comprueba 118 filas físicas y corrección original,
no sólo 111 coordenadas retenidas. Costo ratio 1,542441: rechazado, directo
activo. Siguiente: evaluar reacciones condensadas y padre sin estampar el
ladder dos veces ni materializar toda su proyección, preservando esta unión
como control funcional. No añadir otra secuencia de certificados locales;
volver a trayectoria, filas originales y costo fresco con los mismos gates.
Sin ampliar arranque/CV/fidelidad física/RT ni generar nuevas muestras.


## 2026-10-15 — Separación verificada; condensar la corrección física

[Resultado](SPLIT_LADDER_RESULTADOS.md): se retira el segundo stamp DC del
ladder conservando cargas y sellos del punto actual; precisión y auditoría
original pasan. El perfil del primer candidato localiza 8,648849 s en el
tramo del padre; el segundo retira su adaptador de tipos. Ambos fallan
costo frente al directo fresco, que sigue activo. Siguiente: perfilar los
solves reducido/original y preparar una sola vez el Newton actual, derivando
la corrección física completa mediante Schur con residual algebraico
remanente. Compararla con el solve original y conservar 1 pA/2 nV, estimador,
trayectorias, auditoría y costo fresco. Sin más ensayos aislados de adaptadores.


## 2026-10-15 — Corrección afín verificada; localizar costo actual

[Resultado](AFFINE_NEWTON_RESULTADOS.md): 576 direcciones y 5712 filas
originales pasan con una preparación reducida y residual algebraico real.
Retirado el solve completo adicional; costo ratio 1,607968, rechazado.
Directo activo. El perfil de llamadas anteriores mide reducido 7,005680 s
original 2,706435 s, con replays; no separa factorización. La voz candidata
usa algunos pasos de 0,25 µs y Newton sigue cerca del gate 2 nV.
Siguiente: medir evaluación residual/J, preparación Schur/CSR y solve del
candidato actual frente al directo antes de editar. Si la reconstrucción
local sigue costando más, priorizar el directo como base de ejecución y
conservar la variante condensada como referencia funcional. Mantener
cargas, puertos, precisión, auditoría y costo ≤0,90. Sin más certificados
locales aislados ni nuevas muestras.


## 2026-10-15 — Perfil medido; priorizar ensamblaje del directo

[Resultado](EXECUTION_COST_RESULTADOS.md): se perfilan directo y afín con
trayectorias idénticas a sus controles. Preparación 6,232122/12,179957 s;
solve/refinamiento después de preparar ocupan mucho menos. El candidato
de soporte actual del pivote conserva precisión exacta y falla costo:
ratio 1,054244. Descartado, directo anterior activo. No seguir variando
listados de pivote ni volver a otra condensación local sin evidencia.
Siguiente: construir el sistema directo desde incidencias del stamp actual,
con orden de acumulación DC/masa, puertos, cancelaciones y detección de
aristas nuevas preservados; evitar matrices intermedias y scans repetidos.
Fijar contrato antes de cambiar el ensamblaje, contrastar coeficientes y
volver a voz completa/auditoría/costo ≤0,90. El perfil no prueba ahorro
futuro ni RT. Sin ampliar controles, arranque o muestras.


## 2026-10-15 — Incidencias admitidas; arranque propio de la cadena

[Resultado](INCIDENCE_VOICE_RESULTADOS.md): 192 direcciones y trayectorias
idénticas, 5712 filas originales pasan. Ensamblaje desde componentes actuales,
sin J/M globales de etapa. Candidato y fachada pasan costo con controles
frescos: ratios 0,758772/0,788476. Motor nominal seleccionado mediante
active_nominal_voice.rs; el directo anterior queda como control histórico.
No atribuir el ahorro a un único cambio o afirmar RT: sigue offline.
Siguiente: fijar condiciones iniciales propias de la cadena con la fuente
periódica nominal actual, conservando cargas/trigger y sin proyectar el
estado de 40 ms de una referencia. Contrastar DC, estados y etapas con las
ecuaciones originales; luego recorrer ataque/nota completa a dos pasos.
Esto no sería arranque del VCO físico ni CV general. Mantener gates de
precisión y memoria; priorizar unión funcional antes de otra microoptimización
local o generación de muestras.


## 2026-10-15 — DC y ataque propios admitidos; lectura a reloj de audio

[Resultado](CHAIN_STARTUP_RESULTADOS.md): cold_start autónomo resuelve el
DC conjunto sin proyectar la memoria de 40 ms. Conserva cargas/trigger y
completa dos perfiles propios 0–100 ms, 8806 filas originales y control
histórico pasan; heap cero. La API repite las etapas del prototipo por bits.
Motor por incidencias activo; no se cambia factor/estimador ni se amplía
la fuente periódica a VCO físico/CV general. Dos condiciones de Newton
no prueban unicidad global de los latches.
Siguiente: definir lectura offline de J7 a un reloj de audio y contrastar
su error temporal con una referencia fina. Conservar nivel absoluto,
eventos y memoria; preparar un buffer acotado antes de exportar audio.
No confundir grilla de observación de 125 µs con audio de producción,
ni forzar pasos bajo MIN_DT para alinear muestras. Sin otra secuencia de
microoptimizaciones o acumulación de muestras.


## Lectura de J7 a 48 kHz admitida para la escena nominal

[Búfer y resultados](J7_READOUT_RESULTADOS.md): reloj racional, etapas
fine, voltios y continuidad de KEY/memorias. Pasividad exacta a 32 us;
32/8 y 4/2 us fallan precisión y conservan replays. 2/1 us pasa gates
originales; máximo nominal de 2 us. No demuestra RT o banda limitada.
Prioridad: nota offline de duración útil y conversión/antialias verificados,
luego una única exportación para escucha, conservando nivel absoluto.
Evitar otra cadena de microoptimizaciones y nuevas carpetas de muestras.


## Nota extendida y salida con antialias

[Contrato](LONG_NOTE_AA_PROTOCOLO.md), [auditoría](LONG_NOTE_AA_AUDITORIA.md)
y [resultados](LONG_NOTE_AA_RESULTADOS.md): nota 300 ms, KEY OFF 200 ms y
futuro físico hasta 301 ms para completar el FIR. Separar refinamiento
eléctrico 2/1 us de lectura 192/384 kHz, con gates por ataque/sostenido/
liberación. Conservar prefijo y memorias; comprobar respuesta, convolución,
controles negativos y ecuaciones originales. Una sola escucha regenerable
en voltios, sin carpetas de variantes. Esta referencia servirá para futuras
extensiones funcionales; no ampliar sus claims a CV general, tres VCO o RT.
