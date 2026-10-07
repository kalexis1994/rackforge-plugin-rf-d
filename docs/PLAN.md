# Plan vigente de RF-D

2026-10-07. Prioridad: completar una voz de circuito utilizable con evidencia
proporcionada al alcance. [Objetivo documental](OBJETIVO.md): CA3046 nominal;
[sin acceso físico permanente](VALIDACION_SIN_HARDWARE.md).

## 1. Campaña monolítica cerrada

El candidato activo de seis correcciones pasó controles y cuatro escenas
cortas de 40 ms. Su extensión serial de 350 ms quedó
[rechazada y auditada](VOZ_SERIAL_CAMPANA_RESULTADOS.md): Gear125 completó;
Gear500/Gear250/Trap125 abortaron a 136,630269/150,293268/15,940421 ms.
Cuatro procesos desde DC propio, todos los exports/recibos archivados y
ningún error de recursos o almacenamiento. Tres parejas no medidas.

Se preservan fuentes, gates, fallos y datos completos/parciales. No lanzar
otra ampliación de correcciones lineales ni relajar tolerancias sin causa
contrastada. La audición del adaptador largo sigue sin admisión.

## 2. VCO1 nativo con carga eléctrica cerrada

Ya existe el [oráculo funcional VCO1](VCO1_RESULTADOS_CIRCUITO.md). El
[puerto cargado de cinco fuentes](MEZCLADOR_PUERTO_CARGADO_RESULTADOS.md)
entrega corrientes, tangentes y estados provisionales de la cadena ON/C27
hasta J7. Usarlo para conectar el generador y conservar la carga en ambos
lados; no reemplazar ese cierre por una suma de voltajes.

Aplicar el [protocolo previo nativo](VCO1_NATIVO_PROTOCOLO.md): revisión, formas de onda,
CV/trims, parámetros de laboratorio, discretización, memoria y retornos.
Contrastar oscilación, amplitud/offset, reset, frecuencia y source current
con las referencias ya existentes, incluyendo escenas reservadas. Confirmar
sólo el estado conjunto final; fallo sin publicar cargas parciales.

Primero verificar la entrada Q29/C27 mediante stamp directo y extender
su dominio contra un oráculo completo a 500/250/125 ns. El adaptador vigente
admite desde 0.5 µs; todavía no se extiende por este protocolo.

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
