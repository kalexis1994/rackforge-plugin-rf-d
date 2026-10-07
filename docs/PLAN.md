# Plan vigente de RF-D

2026-10-07. Prioridad: completar una voz de circuito utilizable con evidencia
proporcionada al alcance. [Objetivo documental](OBJETIVO.md): CA3046 nominal;
[sin acceso físico permanente](VALIDACION_SIN_HARDWARE.md).

## 1. Terminar la campaña monolítica ya iniciada

El candidato activo de seis correcciones pasó controles y cuatro escenas
cortas de 40 ms. El productor serial está ejecutando las cuatro notas de
350 ms desde DC propio, con ON a 10 ms y OFF a 200 ms. Recursos admitidos
por [preflight02](../evidence/voice_serial_preflight02.json), XZ, un worker y
7200 s máximos por escena. Sus fuentes y helpers permanecen congelados.

Gear500/Gear250 ya conservan abortos a 136,630269/150,293268 ms. Gear125
sigue en ejecución; Trap125 queda pendiente. Al terminar, auditar cada
recibo y restauración, relojes, balances y tres parejas con los gates originales.
Si el banco falla, publicar el rechazo y delimitar el siguiente experimento;
no ampliar correcciones o relajar tolerancias sin una causa contrastada.

## 2. VCO1 nativo con carga eléctrica cerrada

Ya existe el [oráculo funcional VCO1](VCO1_RESULTADOS_CIRCUITO.md). El
[puerto cargado de cinco fuentes](MEZCLADOR_PUERTO_CARGADO_RESULTADOS.md)
entrega corrientes, tangentes y estados provisionales de la cadena ON/C27
hasta J7. Usarlo para conectar el generador y conservar la carga en ambos
lados; no reemplazar ese cierre por una suma de voltajes.

Fijar un protocolo del núcleo VCO antes de medir: revisión, formas de onda,
CV/trims, parámetros de laboratorio, discretización, memoria y retornos.
Contrastar oscilación, amplitud/offset, reset, frecuencia y source current
con las referencias ya existentes, incluyendo escenas reservadas. Confirmar
sólo el estado conjunto final; fallo sin publicar cargas parciales.

Primer alcance: VCO1 y cadena con controles impuestos. No declarar tres
osciladores, contorno completo o otra población física por ese prototipo.

## 3. Completar comportamiento de voz

- Integrar el contorno de volumen y su gatillo conservando las cargas del
  [puerto C2/reset](PUERTO_CONTORNO_CADENA_71.md); usar los diagnósticos y
  rechazos del biestable para definir la política siguiente.
- Derivar el contorno de filtro y sus controles con fuentes/documentos propios.
- Osciladores 2/3, ruido, modulación, teclado/glide/ruedas y entrada externa.
- Completar OFF y taper del mezclador y acotar dispersión/hipótesis físicas.
  Mantener R61=200 Ω y 200 kΩ como escenarios separados hasta nueva evidencia.

## 4. Escucha y producto

Una escucha debe identificar qué genera la señal, nodo/carga de salida,
voltios→audio, resampling, cobertura y limitaciones. Conservar el alcance de
los WAV anteriores: la escucha de salida con seno impuesto no es la voz VCO.
El adaptador de nota larga congelado requiere su banco completo admitido.

Con la voz funcional: escenas musicales fijadas, diferencias de audio y
costos por bloque en plataformas RackForge. Promover optimizaciones sólo
conservando sonido/error y memoria; heap cero no sustituye deadlines.
Después cerrar estado/parametrización, MIDI/host, UI y paquete RF-D.

## Reglas de avance

No repetir bancos heredados si sus algoritmos/inputs están idénticos y la
QA declara la herencia. Añadir pruebas para el circuito que cambió y su
integración; separar conformance, física, escucha y RT. Una campaña pendiente
permite avanzar bloques independientes con contratos y gates propios.

El [historial del plan](PLAN_HISTORICO_2026-10-07.md) conserva los estados
anteriores, prioridades y enlaces por bytes exactos. El
[registro de snapshot](../evidence/voice_documentation_snapshot01.json)
preserva su procedencia. No se eliminan fallos o evidencia del laboratorio.
