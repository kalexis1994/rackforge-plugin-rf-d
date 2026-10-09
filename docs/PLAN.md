# Plan vigente de RF-D

2026-10-08. Prioridad: completar una voz de circuito utilizable con evidencia
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
