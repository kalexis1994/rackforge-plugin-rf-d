# Receta ejecutable, export de J7 y escucha finita

## Interfaz pública

[`conditioned_recipe`](../crates/rf-d-circuit/src/conditioned_recipe.rs)
publica una receta de diagnóstico con historia propia por **decay y
resolución**. Cuatro combinaciones ON/OFF,1/2 µs; todos los parámetros,
cargas, reloj y propuesta entrante están declarados. La biblioteca conserva
las ecuaciones del conjunto229, motor temporal y Workspace admitidos.
El ejemplo usa directamente la biblioteca y no importa `tests/support` o
un kernel de `tools` durante el render.

Tres eventos, en reloj exacto: KEY0/abierto→KEY10 V/cerrado→KEY0/abierto.
Los CV del oscilador permanecen fijos. Es un gatillo eléctrico de contorno,
sin notas MIDI, asignación ADSR digital o cero impuesto a la salida.
`Recipe::apply` conserva458 campos HIGH/LOW y rechaza reloj/decay incorrectos.
Esta receta no admite otros presets ni arranque desde silencio.

## Resultado numérico

| Decay | h máximo µs | Accepted | Endpoints finos |
| --- | ---: | ---: | ---: |
| ON | 2 | 3020 | 6040 |
| ON | 1 | 3704 | 7408 |
| OFF | 2 | 2987 | 5974 |
| OFF | 1 | 3674 | 7348 |

[Campaña final](../evidence/voice_conditioned_recipe_native02.json):26770
endpoints; todos los calendarios STEP, LTE, intentos, propuestas y cinco
observables coinciden por bits con los exports admitidos. Comparación de48
estados completos (21984 campos HIGH/LOW) y133870 campos observables.
ON1 se repite por bytes:3704 accepted/7408 endpoints adicionales.
El observador reducido no exporta todos los estados entre cortes ni solves
activos; no se reejecuta un grafo independiente de ecuaciones en este bloque.

Tres tests Rust nuevos y cuatro previos de memoria/heap reejecutados con
la biblioteca final, cada harness con replay. **255 tests Rust cubiertos**:
7 ejecutados y248 heredados, sin afirmar una reejecución de toda la suite.
Dos tests Python propios comprueban voltaje constante en bordes/interior,
clocks inválidos y clipping del adaptador. La CLI produce exactamente el
WAV publicado y rechaza una salida existente sin modificar WAV/sidecar.

Workspace3.378.208 bytes, Engine/Checkpoint4.800 bytes; cero heap en las
9 aceptaciones/3 rechazos de procesamiento del harness reejecutado.
El ejemplo offline sí hace I/O. Stack32 MiB experimental y memoria de
objetos siguen separados de uso máximo de stack y deadlines del plugin.

## Fallos conservados

1. Harness pidió Debug al agregado de parámetros: E0277 y replay idéntico.
   Comparar sus cinco campos completos evita modificar la biblioteca.
   [Reparación](../evidence/voice_conditioned_recipe_test_repair01.json).
2. Los workers de test tenían stack por defecto, independiente del linker:
   overflow/replay conservados. Activar RUST_MIN_STACK32 MiB usa el presupuesto
   previamente declarado. [Recibo](../evidence/voice_conditioned_recipe_stack_repair01.json).
3. La primera receta usó historia2 µs para1 µs. Mismo calendario pero floats
   distintos: rechazo, replay de adaptador y replay del mismo ejecutable
   conservados. [Corrección documentada](RECETA_CONDICIONADA_HISTORIAS.md).
   Añadir historias finas ya publicadas y cambiar únicamente su selector;
   no ajustar cargas o gates para aceptar cercanía.

Dos bibliotecas nuevas incluyen el prototipo rechazado y la receta corregida.
Sin cache Cargo, SPICE o dependencias Rust nuevas. Outputs aceptados/rechazados
conservados dentro de32 MiB y reserva1 GiB.
[Auditoría de fuentes/privados y recursos](../evidence/voice_conditioned_recipe_reference01.json).

## WAV y duración realmente simulada

El render resuelve **8.438→11.442 ms**, una ventana propia de3.004 ms ya
admitida. J7 se exporta en voltios con sus cargas resueltas. La CLI observa
esa interpolación lineal mediante sinc18 kHz, Blackman±32/Fs y cuadratura
Gauss8/16; extensión constante sólo en bordes de convolución. Escala fija
0.01 V/FS, mono PCM16/48 kHz, sin normalización, clipping, DC removal, fades
o repetición. No es un resampler admitido para DSP en tiempo real.

| Adaptación, para ON y OFF | Frames | Duración WAV | Interpretación |
| --- | ---: | ---: | --- |
| Tiempo nativo | 144 | 3 ms | Fragmento corto del circuito, cola4 µs omitida |
| Microscopio100× | 14419 | 300.395833 ms | Mismas tensiones con tiempo/frecuencia100×más lentos |

Los300 ms del microscopio **no** son duración adicional del circuito,
envolvente original o una nota musical. El sidecar declara duración
simulada, mapeada, WAV y truncamiento. La cuadratura pasa≤0.25 LSB y≤1 LSB
PCM; derivación repetida idéntica y roundtrip de todo el payload PCM16.
[Escucha y hashes de los cuatro archivos locales](../evidence/voice_conditioned_recipe_listening01.json),
[CLI/adapter tests](../evidence/voice_conditioned_recipe_cli01.json).

## Reproducir sin referencias privadas

Ejecutar desde la raíz del repo con Rust GNU x86_64 y NumPy (versiones exactas
de esta medición en los recibos). Elegir una carpeta nueva: el ejemplo y la
CLI preservan salidas previas. Los estados sintéticos están en la biblioteca;
no hacen falta PDFs, capturas o checkpoints de `references-local`.

```powershell
$recipeRustc = "$env:USERPROFILE\.rustup\toolchains\stable-x86_64-pc-windows-gnu\bin\rustc.exe"
$env:PATH = "C:\msys64\mingw64\bin;C:\msys64\ucrt64\bin;$env:PATH"
New-Item -ItemType Directory -Path tmp/receta-usuario
& $recipeRustc --edition=2021 --crate-name rf_d_circuit --crate-type rlib -C opt-level=2 -C strip=symbols crates/rf-d-circuit/src/lib.rs -o tmp/receta-usuario/librf_d_circuit.rlib
& $recipeRustc --edition=2021 -C opt-level=2 -C strip=symbols -C 'link-arg=-Wl,--stack,33554432' crates/rf-d-circuit/examples/conditioned_render.rs --extern rf_d_circuit=tmp/receta-usuario/librf_d_circuit.rlib -o tmp/receta-usuario/render.exe
& ./tmp/receta-usuario/render.exe on 1 tmp/receta-usuario/on
python -B tools/conditioned_render_cli.py --trace tmp/receta-usuario/on/j7.bin --output tmp/receta-usuario/on/j7.wav
python -B tools/conditioned_render_cli.py --trace tmp/receta-usuario/on/j7.bin --output tmp/receta-usuario/on/j7-tiempo100.wav --stretch 100
```

[Ejemplo Rust completo](../crates/rf-d-circuit/examples/conditioned_render.rs)
y [CLI WAV](../tools/conditioned_render_cli.py). `off` y `2` seleccionan las
otras historias; ningún evento puede cruzarse por un advance sin partir
el calendario. Los scripts de campaña/auditoría históricos son registros
de esta medición con carpetas exclusivas, no el comando de uso habitual.

## Admisión y próximo cierre

[QA](../evidence/voice_conditioned_recipe_tests01.json): receta pública y render
offline admitidos para esta ventana, con historias, puertos/cargas y alcance
de escucha explícitos. No acredita parecido físico, periodicidad asintótica,
voz completa, arranque desde silencio o deadlines.

Siguiente: una ventana propia más larga con el gatillo sostenido y luego
liberado, desde la historia correspondiente a cada resolución. Observar J7
y contorno durante varios ciclos, conservando resets, estado229 y balances.
El objetivo es obtener una escucha útil del circuito a tiempo nativo;
la duración mayor requiere trayectoria nueva y su contraste temporal.
