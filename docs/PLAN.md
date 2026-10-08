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
Derivar coordenadas de incremento/memoria capacitiva sin relajar gates,
y verificar ciclos completos/refinamiento/calibración;
seguir con carga activa;
transferir R6/R45 antes de acoplar al mixer que posee esas cargas.

Primer alcance: VCO1 y cadena con controles impuestos. No declarar tres
osciladores, contorno completo o otra poblaciÃ³n fÃ­sica por ese prototipo.

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
