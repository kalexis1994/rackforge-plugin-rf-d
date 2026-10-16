# Entrada de render offline de la escena admitida

[Contrato previo](NOMINAL_RENDER_PROTOCOLO.md),
[sesión/sink](../crates/rf-d-circuit/src/nominal_render.rs),
[entry point nativo](../tools/nominal_render_main.rs),
[herramienta](../tools/render_nominal.py),
[ensayo admitido](../evidence/nominal_render_native02.json) y
[QA](../evidence/nominal_render_tests01.json).

## Uso

Desde la raíz de RF-D:

```powershell
python -B tools/render_nominal.py
```

Compila con el compiler y rlib locales congelados, resuelve su propio DC
y renderiza la escena de 300 ms, con soporte eléctrico hasta 301 ms.
El único destino es artifacts/rf-d-nominal-current.wav, fuera de Git.
Ctrl+C solicita cancelación entre cuotas; se conserva el WAV anterior.
La cuota por defecto es 128 invocaciones adaptativas; --quota acepta
1..4096. No son milisegundos de CPU ni un deadline. DC y el solve actual
no se interrumpen desde dentro. Sigue siendo un render de laboratorio,
sin MIDI, panel tocable o tiempo real.

## Perfil fino y archivo conservados

La escucha anterior usa máximo full 1 us. El productor previo propone
hasta 2 us; RenderSession reutiliza su seam interno para limitar a 1 us
la propuesta entregada al mismo voice::advance. No cambia el motor,
estados, estimador, puertos, cargas o FIR. El control independiente del
prefijo y el estado final de la nota completa verifican esa composición.
No se usa la proximidad entre perfiles 2/1 us como igualdad de archivos.

J7 a 384 kHz y FIR 769 taps hacia 48 kHz. Separar índice de fuente y
momento de disponibilidad, que tiene 1 ms adicional. Se integra el futuro
real, se exportan 14400 frames del cuerpo semiabierto y se conserva el
punto 14400 como ancla. Sin flush con ceros, normalización, fade o dither.
WAV IEEE float32 mono, 1 V=1 FS, header fmt/fact/data idéntico al previo.

## Sesión, progreso y cancelación

RenderSession posee el productor y su Accepted pendiente, fase, contador
de observados, cuerpo/ancla y llamadas pump. Expone tiempos calculado,
consumido y objetivo por separado, más invocaciones/pasos/frames. pump
no hace heap, IO o logging. La inicialización DC queda fuera de la cuota.
El workspace se presta como scratch, sin cambiar la memoria del circuito.

La cancelación pasa a fase terminal antes de otro pump: cero nuevos
solves, entregas o escrituras de salida, conservando estado y pendiente.
Un Clone permite mantener otra rama activa en memoria. No hay checkpoint
persistente o reanudación desde disco. Una sesión completa sigue completa
aunque después llegue una petición de cancelar.

WavSink hace IO fuera de pump. Preflight del bloque por orden, índices,
finito y nivel; convierte a float32 con buffer fijo. Un write parcial o
flush fallido es terminal y no se reintenta sobre un stream ambiguo.
finish exige todo el cuerpo; el ancla no se entrega como frame adicional.

La herramienta exige tmp/lab-current vacío, adquiere un lock exclusivo,
rechaza enlaces y registra sólo sus archivos propios para limpieza. Un
área ocupada se conserva. Native escribe un provisional con create_new;
sólo después de COMPLETE, conteos, contenedor y SHA admitido se publica
con os.replace en el mismo volumen. Fallo/cancelación conserva el destino.
El protocolo de flag se comprueba antes/después del DC y entre cuotas;
no se presenta como cancelación instantánea o prueba de un deadline.

## Ensayos y fallo conservado

[Primer intento](../evidence/nominal_render_native01.json) y replay fallan
por exigir 10151 pasos en los primeros 10 ms, extrapolados de los 301151
de la nota completa. Ese supuesto de conteo era incorrecto: las reducciones
en KEY no se distribuyen uniformemente. Las muestras ya comparadas no
fallaron. Se guardan fuentes, inputs y replay antes de la
[corrección](../evidence/nominal_render_count_correction01.json).

El ensayo admitido sustituye esa constante por una integración independiente
0–10 ms con el planificador previo de máximo 1 us. Ambos recorren 10109
pasos; 236 HIGH/LOW finales y Pipeline idénticos por bits. Newton <=1 pA/
2 nV y estimador <=1, sin cambiar los gates del motor. Las 433 lecturas
float64 coinciden por bits con el prefijo fino archivado. El WAV transitorio
de 9 ms exporta 432 frames y coincide con un header/payload independiente;
el ancla es el punto 432. Una rama se cancela en el primer Accepted
pendiente de KEY, se mantiene intacta y terminal; otra se reanuda con
workspace nuevo y cuota cero. Progreso monótono y final idempotente.

Tres tests Rust nuevos cubren cuerpo/ancla/cancelación, preflight y cuerpo
obligatorio, y fallos inyectados de write parcial/flush. Los siete tests
anidados anteriores se filtran. Se ejecutan los tres nuevos dos veces
al reparar el oráculo: seis invocaciones, tres definiciones, 264 tests
anteriores heredados y 267 cubiertos en QA.

El wrapper se ejecuta con cancelación antes del DC y después del primer
progreso; en ambos casos termina sin publicación y deja el WAV intacto.
Proceso fallido y error de publicación se inyectan sin volver a integrar
la nota larga. Área ocupada y cuatro cuotas inválidas se rechazan antes
de compilar. No se atribuye a estas inyecciones una trayectoria física.

El recorrido real completo atraviesa cold_start, productor fino, escritor,
validación y publicación. 301151 Accepted, 115585 entradas, 14401 puntos
observados, 14400 frames exportados. Los 236 HIGH/LOW finales coinciden
por bits con el FINAL fino archivado. El archivo publicado conserva:

```text
SHA256 de9b9bed0e2842baa3d2a6df725281aa68a157cf35f675cc40dab84daf57b92f
57656 bytes / 14400 frames / 48 kHz / mono IEEE float32
```

El [primer cierre de QA](../evidence/nominal_render_qa_failure01.json)
y su replay también se conservan: faltaba el placeholder en staging tras
un error del adaptador de preparación al leer UTF-8 como cp1252. Se corrige
la lectura explícita y la preparación, sin modificar el render admitido,
la referencia o los gates numéricos. Es un fallo de metadatos del cierre.

## Alcance y siguiente unión

Heap cero medido en pump/Clone del prefijo real. sizeof de sesión =
36392 bytes, sink = 24 bytes y workspace = 279824 bytes separado;
no son pico total de stack.
El escritor y el wrapper sí hacen IO y asignaciones fuera del core.
No hay un nuevo benchmark RT o auditoría de ecuaciones originales;
la evidencia eléctrica previa se hereda por identidad y control de bits.

Una trayectoria larga nueva comprueba el ciclo completo. Hay dos prefijos
admitidos (sesión/control) y dos prefijos fallidos (intento/replay), más
una cancelación parcial real. Los tres WAV transitorios de prefijo y
los provisionales de cancelación se retiran; sólo se conserva el único
WAV actual, idéntico al previo. Sin nuevos inputs sonoros privados,
cache, Cargo o rlib. tmp/lab-current queda vacío al terminar.

Siguiente: fijar una primera entrada musical de nota/frecuencia para la
fuente VCO nominal, preservando puertos/cargas/fase y distinguiendo ese
adaptador del VCO físico completo. Priorizar una secuencia audible de
notas con control verificable antes de más infraestructura de exportación.
No extender los claims de esta escena a controles o dominios no ensayados.
