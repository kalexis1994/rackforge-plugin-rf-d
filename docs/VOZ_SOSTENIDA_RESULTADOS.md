# Trayectoria sostenida y liberación: 12.004 ms propios

## Escena resuelta

El [ejemplo público](../crates/rf-d-circuit/examples/sustained_voice.rs) usa
la biblioteca admitida, estados propios ON por resolución y todas las cargas
de la receta previa. Reposo4 µs desde8.438 ms, KEY10 V/contactocerrado durante
8 ms y KEY0/contactoabierto durante4 ms. Final20.442 ms. No cambia CV, circuito,
fuentes de alimentación o tarjetas; la respuesta proviene de la red.

| h máximo µs | Accepted | Endpoints finos | Resets | Restores | Accepted reproducidos |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 11142 | 22284 | 5 | 10 | 156 |
| 1 | 13967 | 27934 | 5 | 10 | 156 |

[Campaña](../evidence/voice_sustained_native01.json):538.576 s, con compilación
del caller y observación. No es una medición de velocidad comparativa o RT.
Sin biblioteca/cache Cargo/SPICE nuevos. El scratch y motor son los públicos.

## Grafo, relojes y cargas

[Auditoría independiente](../evidence/voice_sustained_reference01.json):
**32.976 ecuaciones no lineales nuevas**,144 candidatas seleccionadas de
coarse/mid/end en bordes de fase, resets y la antigua frontera9.942 ms.
Grafo original, FD y cargas de juntura Decimal100; no llama al solver Rust
para comprobar esas ecuaciones. Selección explícita, no todos los estados
internos de los25109 accepted. Todos sus relojes/LTE/intentos/propuestas
y KCL de BUS se auditan, además de los pares seleccionados.

Comparar los229 estados en43 relojes comunes pasa el gate2 µV/2 nA original:
máximo observado0.290208 µV y ratio0.145104. Cinco resets en cada perfil,
tres durante el gatillo; brackets e interpolación coinciden dentro de10 ns.
Nueve balances orientados por fase y total pasan1 pA·duración, con ΔQ
recomputado a precisión100. Las integrales de todas las etapas son nativas;
no se presentan como cuadratura independiente de cada etapa.

Los exports del prefijo hasta9.942 ms coinciden por bytes con el laboratorio:
STEP, OBS, siete estados completos y cinco triples seleccionados por perfil.
No recondicionar o sustituir la historia para alargar la ventana. Desde esa
frontera el gatillo continúa8 ms en total, con su estado/propuesta aceptados.

## Replay sin acumular la trayectoria

Hasta tres motores sombra reproducen16 accepted por checkpoint de fase,
interior o reset, y el prefijo disponible si termina la fase. Comparar todos
los bits de Pair, observables y checkpoint, con Workspace compartido
serialmente. **312 accepted reproducidos,20 restores**. El máximo observado
fue un probe activo; la capacidad está limitada a tres por código.
No guardar un Vec de todos los Accepted del recorrido más largo.

Ocho corrupciones y cuatro rollbacks se comprueban. El caller offline sigue
haciendo heap/I/O; no mide heap, uso máximo de stack o deadline del plugin.
255 tests Rust y dos definiciones Python anteriores se heredan por identidad,
sin reejecutarlos. Dos checks de integración de la CLI se ejecutan.

## Escucha nativa y decisión sobre repetir ciclos

[Tres WAV locales](../evidence/voice_sustained_listening01.json): dos nativos
1/2 µs,576 frames/12 ms, y microscopio100×,57619 frames/1.200395833 s.
**12.004 ms realmente simulados** por perfil; cola4 µs omitida en el WAV
nativo. Los1.2 s del microscopio alteran tiempo/frecuencia, sin trayectoria
eléctrica adicional. No hay loop, DC removal, normalización, fades o clipping.
Sinc18 kHz/Blackman, escala fija0.01 V/FS y bordes constantes sólo para filtrar.

La diferencia nativa entre resoluciones es0.200599 µV y1 LSB; cuadratura8/16
y roundtrip de todo el PCM pasan. La [CLI](../tools/sustained_render_cli.py)
produce el mismo WAV por bytes y rechaza WAV/sidecar existentes sin cambiarlos.
[Integración](../evidence/voice_sustained_cli01.json).

El oscilador mide410.801787 Hz en los últimos ciclos sostenidos. J7 cambia
**0.338393 mV**, aproximadamente16.56 % del RMS AC, entre esos dos ciclos;
el seam es0.317139 mV. Supera los límites previos5 µV/2 %. La propuesta de
repetición se rechaza: no se crea una escucha de1.5 s mediante un loop.
Una frecuencia coincidente no implica una salida asentada.

[Diagnóstico separado](../evidence/voice_sustained_diagnostic01.json): cambio
de media−52.9226 µV; la diferencia después de centrar cada ciclo sigue siendo
0.344569 mV. Ese centrado sólo se aplica al diagnóstico, sin alterar el WAV
o las tolerancias. La deriva observada no se explica sólo por la media DC.

## Memorias después de quitar el gatillo

En la traza fina, C2 pasa3.746799→3.962159 V durante los4 ms posteriores al
evento KEY0/contactoabierto: aumenta0.215359 V. C7 baja3.350885→1.818436 V;
reset_driver9.3→0.120801 V. Q25/Q15 y C4 continúan evolucionando. La fuente
se ha liberado, pero ese nombre de fase no prueba que C2 haya empezado a
descargar. No es evidencia de comportamiento correcto o incorrecto del
Model D físico ni una causa identificada del circuito.

Siguiente: continuar la liberación desde cada checkpoint propio, observar
la conmutación Q25/Q15, C7/C4 y cuándo cambia de signo la pendiente de C2.
Contrastar esa respuesta con el recorrido del esquema/condiciones de control
antes de juzgarla. No añadir un reset de envolvente digital para corregirla.

## Reproducir

Usar los comandos Rust GNU/stack32 MiB de
[la receta pública](RECETA_CONDICIONADA_RESULTADOS.md#reproducir-sin-referencias-privadas),
compilando este ejemplo con la misma rlib. Elegir una carpeta nueva:

```powershell
& $recipeRustc --edition=2021 -C opt-level=2 -C strip=symbols -C 'link-arg=-Wl,--stack,33554432' crates/rf-d-circuit/examples/sustained_voice.rs --extern rf_d_circuit=tmp/receta-usuario/librf_d_circuit.rlib -o tmp/receta-usuario/sustained.exe
& ./tmp/receta-usuario/sustained.exe 1 tmp/receta-usuario/sostenido
python -B tools/sustained_render_cli.py --source tmp/receta-usuario/sostenido/selected.txt --output tmp/receta-usuario/sostenido/j7.wav
```

`2` elige su historia propia y otra resolución. El ejemplo no necesita
referencias privadas para inicializar. `--stretch 100` produce el microscopio
rotulado, con sidecar y duración explícitos. OFF queda admitido sólo en su
ventana anterior; este experimento más largo es ON.

[QA](../evidence/voice_sustained_tests01.json) protege la colección anterior,
datos y fuentes nuevas. Admisión limitada a esta escena/ventana; sin contorno
desde silencio, periodicidad asintótica, fidelidad física, voz completa o RT.
