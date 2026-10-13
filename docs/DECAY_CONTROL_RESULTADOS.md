# Decay eléctrico en ohmios, con la voz y sus cargas conectadas

## Nueva función pública

[decay_voice](../crates/rf-d-circuit/src/decay_voice.rs) y
[decay_engine](../crates/rf-d-circuit/src/decay_engine.rs) exponen PANEL_R16
como decay_ohm, mediante ensamblaje directo del resistor en el grafo30.
Default100 kΩ. API set_decay_ohm conserva estado HIGH/LOW, cargas, fuentes,
reloj y propuesta. Dominio finito0<R≤1 MΩ con conductancia finita;0 exige
contacto/topología propios y se rechaza. No mapa de perilla o ley logarítmica.
Procedencia y límites fijados en [el protocolo](DECAY_CONTROL_PROTOCOLO.md).

Familia derivada mediante transformación explícita de los ensambladores y
motor nominales. El código nominal anterior sigue por bytes; lib.rs añade
exports. Misma conectividad229, Schur, Newton/Radau, cargas, retornos y LTE;
único coeficiente variable: R entre Q18colector211 y C2=205. No se resta un
stamp completo ni se multiplica una envolvente digital. Las hipótesis de
semiconductores, rieles, sustain y filtro impuesto siguen vigentes.

## Regresión nominal y evento de control

Ocho accepted completos (cuatro por resolución1/2 µs) coinciden **por bytes
entre tres ejecuciones**: motor antiguo/rlib congelada, motor antiguo/rlib
nueva y motor controlado a100 kΩ/rlib nueva. Coarse/mid/end con todos los
estados e incrementos, residuos/correcciones/iteraciones/trials, observables,
calendario/LTE/intentos/propuesta y checkpoint lógico; no sólo J7.
Es regresión finita, no replay de toda la matriz histórica.255 tests Rust y
dos definiciones Python anteriores se heredan por identidad sin reejecutarlos.

Restaurar otra vez cada entrada propia28.442 ms, no el final de esos probes.
RFDCY0013728 bytes añade R y conserva el payload458f64 anterior3720 bytes.
El evento100 kΩ→1 kΩ cambia sólo sus bytes56..64, sin nuevo KEY/S-trigger,
raíz, carga o propuesta. Copia original, preevento y postevento quedan ligados
por hashes. Doce controles inválidos y dos restores inválidos se rechazan;
cuatro corrupciones y destino inválido por perfil también preservan estado.

## Trayectoria nueva

28.442→44.442 ms,16 ms nuevos a1 kΩ;20 cortes.8 ms y21 estados completos.
Parte del contorno anterior y no de silencio. Sin cambio en CV, R59, cargas
de salida J7, controles de mixer o parámetros de BJT. [Caller público](../crates/rf-d-circuit/examples/decay_control.rs).

| h máximo µs | Accepted | Endpoints finos | Resets | Restores | Accepted reproducidos |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 14535 | 29070 | 7 | 9 | 144 |
| 1 | 18349 | 36698 | 7 | 9 | 144 |

[Campaña](../evidence/voice_decay_native02.json):704.379 s, rlib y dos
callers compilados con Rust GNU; sin Cargo/cache/SPICE nuevos. Replay acotado
≤3 probes, máximo observado1;18 restores,
288 accepted por bits. Ocho corrupciones y dos
rollbacks de destino. Caller offline tiene I/O/heap; no medición nueva de
heap, deadline o stack máximo. Stack experimental32 MiB.

## Descarga que emerge del circuito

`10 µF·dC2/dt = (V208−V205)/10k + (V211−V205)/1k − (V205−V200)/10k`.

La resistencia cambia la corriente de la rama Q18–C2, mientras Q18, sustain,
seguidor y VCA se resuelven conjuntamente. El evento mantiene el voltaje de
C2 y su carga; las etapas siguientes producen la respuesta eléctrica.
En el perfil1 µs, C2 pasa3.942488720→**1.499697448 V** en16 ms;
pendiente final-63.121915084 V/s. Salida del seguidor
0.359363595 V y J7 final
0.000195223148 V. Son endpoints, no métricas
de ganancia, RMS o prueba de silencio.

65770 registros pasan el balance corriente/derivada≤2e−6 V/s, equivalente
a20 pA en C2. KCL estático inicial y derivadas Radau en endpoints están
rotulados por origen. 38 endpoints seleccionados recalculan las tres
corrientes con Decimal100. Máximo C2 muestreado y eventos observados se
registran, sin convertirlos en cotas continuas. La descarga no se declara
completa ni ajustada a un tiempo del instrumento físico.

## Grafo independiente, estados y memorias

[Auditor](../evidence/voice_decay_reference02.json): **24732
ecuaciones/108 candidatas** en triples seleccionados
al inicio/final/resets/cruces. Reconstruye PANEL_R16=1 kΩ en la red original,
con FD y cargas Decimal100; no usa el stamp Rust para comprobar ecuaciones.
Todos los calendarios/LTE/intentos/propuestas y KCL de BUS exportados se
auditan. No se presenta la selección como todos los solves independientes.

229 estados en21 relojes comunes pasan2 µV/2 nA: error de tensión máximo
0.042077738 µV, ratio0.021038869. 14 resets pasan10 ns. Nueve balances
orientados de carga por recorrido y unidos con el padre36.004 ms pasan
1 pA·duración. ΔQ se recalcula entre extremos reales y las integrales nativas
se suman; no es cuadratura independiente de todas las etapas. Duración
identificada por ticks y producto binario, separada de su etiqueta decimal.

## Audio continuo y CLI

[Dos WAV locales](../evidence/voice_decay_listening01.json):36.004 ms realmente
simulados,1728 frames/36 ms a48 kHz; cola4 µs truncada. Dos seams comprobados
con458 HIGH/LOW iguales y un único endpoint común; evento de R explícito.
Sinc18 kHz/Blackman,0.01 V/FS; sin loop, DC removal, normalización o fades.
Error entre resoluciones0.200598955 µV/
1 LSB. Cuadratura8/16 y todos los bytes
PCM/roundtrip pasan; derivación repetida idéntica. Fragmento corto de
laboratorio, sin acreditar nota musical completa, periodicidad o fidelidad.

[CLI](../tools/decay_render_cli.py) conserva hashes de tres trazas y del
evento eléctrico en el sidecar. Tres checks de [integración](../evidence/voice_decay_cli01.json):
WAV completo idéntico, salida existente preservada y seam incompatible
rechazado antes de publicar WAV/sidecar. No añade un loop o microscopio.

## Reproducir sin PDFs privados

Ejecutar primero [sostenido](VOZ_SOSTENIDA_RESULTADOS.md#reproducir) y
[liberación](VOZ_LIBERACION_RESULTADOS.md#reproducir-sin-referencias-privadas)
en carpetas propias. Nueva carpeta y biblioteca para la familia controlada:

```powershell
New-Item -ItemType Directory -Path tmp/decay-usuario
& $recipeRustc --edition=2021 --crate-name rf_d_circuit --crate-type rlib -C opt-level=2 -C debuginfo=0 crates/rf-d-circuit/src/lib.rs -o tmp/decay-usuario/librf_d_circuit.rlib
& $recipeRustc --edition=2021 -C opt-level=2 -C strip=symbols -C 'link-arg=-Wl,--stack,33554432' crates/rf-d-circuit/examples/decay_control.rs --extern rf_d_circuit=tmp/decay-usuario/librf_d_circuit.rlib -o tmp/decay-usuario/decay.exe
& ./tmp/decay-usuario/decay.exe tmp/receta-usuario/liberacion/final.ckp tmp/decay-usuario/recorrido
python -B tools/decay_render_cli.py --held tmp/receta-usuario/sostenido/selected.txt --release tmp/receta-usuario/liberacion/selected.txt --controlled tmp/decay-usuario/recorrido/selected.txt --output tmp/decay-usuario/recorrido/j7.wav
```

El input determina su resolución propia; el caller tiene el evento1 kΩ y
su reloj declarados. La API permite otros valores dentro del dominio, cuya
trayectoria necesita validación propia. No hay presets vintage identificados.

## Fallo conservado y alcance

[Primera compilación](../evidence/voice_decay_native01.json) y replay rechazan
el caller: faltó el nuevo argumento R en su observador de corriente de
puertos. [Reparación](../evidence/voice_decay_repair01.json) añade ese argumento;
gates, circuito y controles no cambian. Archivos del rechazo se conservan.
El [primer auditor](../evidence/voice_decay_reference01.json) y su replay
rechazaron una propuesta8192 ticks frente a un4096 heredado de otra frontera.
La [corrección](../evidence/voice_decay_auditor_repair01.json) compara con el
checkpoint padre real y versiona el recibo, preservando todas las trazas,
estados y gates eléctricos. El evento conserva la propuesta8192 recibida.
[QA](../evidence/voice_decay_tests01.json) protege la línea anterior, nueva
familia, fuentes medidas, trazas y archivos privados; nominal y nuevo control
tienen admisiones separadas. No contorno desde silencio, voz completa,
fidelidad física o RT. Siguiente: duración útil y eficiencia del motor,
contrastando la señal del circuito antes de optimizar o completar controles.
