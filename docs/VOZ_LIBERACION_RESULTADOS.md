# Liberación restaurada: conmutación y descarga de C2

## Recorrido y seam

El [caller público](../crates/rf-d-circuit/examples/release_continuation.rs)
continúa cada checkpoint propio ON de la campaña sostenida:20.442→28.442 ms,
**8 ms adicionales**,12 ms después de KEY0/contactoabierto. Mantiene decayON,
CV, fuentes impuestas, grafo229, puertos y cargas. No aplica otro gatillo.
[Protocolo previo](VOZ_LIBERACION_PROTOCOLO.md).

La conversión RFHLD001→RFREL001 sólo cambia magic y fase del contenedor.
Conserva458 valores HIGH/LOW por bits, reloj y propuesta4096 ticks.
La copia original y el checkpoint de entrada se comparan antes del solve;
el primer estado del export es exactamente el último del padre. No se
recondiciona la raíz ni se sustituye la historia de otra resolución.

| h máximo µs | Accepted | Endpoints finos | Resets | Restores | Accepted reproducidos |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 7175 | 14350 | 3 | 7 | 112 |
| 1 | 9041 | 18082 | 3 | 7 | 112 |

[Campaña](../evidence/voice_release_native01.json):353.318 s incluyendo caller
y observación. Biblioteca anterior intacta; sin compilación de rlib, Cargo
cache o SPICE nuevos. Hasta3 probes, máximo observado1,16 accepted por
checkpoint.224 accepted reproducidos,14 restores,8 corrupciones rechazadas
y2 rollbacks atómicos. Los probes de transición tampoco acumulan Accepted.

## Conmutación observada

Se exportan C2, derivada del polinomio Radau, tres corrientes resistivas,
diferencia de colectores Q25/Q15 y colectorQ20. El primer registro usa KCL
estático en su estado propio; los demás son endpoints finos. Ninguno de
estos observadores cambia las cargas o dispara un evento del motor.

En el recorrido1 µs:

| Observación | Tiempo absoluto ms | Después de KEY0 ms | Bracket ns |
| --- | ---: | ---: | ---: |
| V(Q25c)−V(Q15c) cruza cero hacia positivo | 20.532572897 | 4.090572897 | 3.90625 |
| dV(C2)/dt cruza cero hacia negativo | 20.532718225 | 4.090718225 | 1.953125 |

Tiempos interpolados linealmente en brackets observados; el primer cruce es
una definición eléctrica del observador, sin umbral digital de envolvente.
La diferencia entre resoluciones es1.588 ps para colectores y43.503 ps para
la derivada, dentro del gate100 ns. Esa coincidencia numérica no representa
precisión de componentes o tiempo medido en un Model D físico.

## Balance que explica el signo

Para C2=10 µF, decayON:

`C2·dV205/dt = (V208−V205)/10k + (V211−V205)/100k − (V205−V200)/10k`.

Las dos primeras corrientes entran desde ataque/decay; la última sale hacia
la base del seguidor Q3. Se conserva la carga posterior Q2/R59/VCA. El
balance no usa una envolvente ADSR ideal o un reset impuesto.

| Endpoint del perfil1 µs | Ataque hacia C2 µA | Decay hacia C2 µA | Seguidor desde C2 µA |
| --- | ---: | ---: | ---: |
| Inicio20.442 ms | 527.862911 | aproximadamente0 | 0.053310 |
| Primer endpoint después del cruce de pendiente | 27.933965 | −30.503813 | 0.053331 |
| Final28.442 ms | 0.000002936 | −30.869021 | 0.053227 |

La corriente de ataque deja de dominar y el balance se vuelve negativo.
C2 tiene máximo **muestreado**3.966944130211 V, luego llega a3.942488719820 V;
pendiente final−3.092224515 V/s. El máximo de endpoints y el valor interpolado
no son una cota del máximo continuo. La ventana no cubre descarga completa
o silencio; demuestra inicio y continuación de la descarga en esta receta.

32.434 registros de flujo (dos iniciales más32.432 endpoints) pasan el balance
de derivada≤2e−6 V/s, equivalente a20 pA en10 µF. Máximo observado7.106e−14 V/s.
Además,30 endpoints seleccionados recalculan corrientes con Decimal100 a
partir de los estados exportados; no presentan todas las filas nativas como
un solve independiente.

## Grafo original y cargas

[Auditor independiente](../evidence/voice_release_reference01.json):
**19.236 ecuaciones no lineales /84 candidatas** coarse/mid/end seleccionadas
en inicio, final, resets y cruces. Grafo original/FD y cargas Decimal100,
sin consultar Rust para comprobar sus ecuaciones. Audita todos los
calendarios/LTE/intentos/propuestas y KCL de BUS del recorrido exportado.

Los229 estados en28 relojes comunes pasan2 µV/2 nA: error de tensión máximo
0.0830824 µV, ratio máximo0.0415412. Tres resets por perfil cumplen el gate
10 ns. Nueve balances orientados de carga por fase/total y la unión20.004 ms
pasan1 pA·duración. ΔQ se recalcula entre los endpoints reales; las integrales
de todas las etapas son nativas, sin adjudicar cuadratura independiente a
etapas no exportadas. Los brackets y el refinamiento de las transiciones
se comprueban además de los28 cortes periódicos.

[Revisión documental](VOZ_LIBERACION_REVISION.md): confirma los recorridos
C7/Q20, R28/C4, R36/CR8 y realimentación Q25/Q15. Registra un localizador
corregido (Figure9-7 frente a página impresa9-5), preservando el documento
anterior. No cambia valores ni topología. La descripción funcional orienta
el análisis; no identifica el retardo de4.09 ms ni las tarjetas vintage.

## Render continuo y CLI

[Dos WAV locales](../evidence/voice_release_listening01.json) unen el padre y
la continuación mediante458 valores HIGH/LOW iguales, fuentes iguales y
un único endpoint en el seam. **20.004 ms de trayectoria**,960 frames/20 ms
a48 kHz; cola4 µs truncada. Sinc18 kHz/Blackman, escala0.01 V/FS, extensión
constante sólo para filtrar. Sin repetición, DC removal, fades, normalización
o clipping. Cuadratura8/16, roundtrip PCM y replay de derivación completos
pasan. Error entre resoluciones0.200599 µV/1 LSB.

[CLI pública](../tools/release_render_cli.py): WAV y sidecar; tres checks de
[integración](../evidence/voice_release_cli01.json) pasan. Produce el mismo
WAV por bytes, rechaza salidas existentes sin mutarlas y rechaza un seam
con un estado distinto antes de publicar archivos. No añade un microscopio
o loop nuevo. Sigue siendo un fragmento corto del laboratorio condicionado.

## Reproducir sin referencias privadas

Primero ejecutar [la receta sostenida](VOZ_SOSTENIDA_RESULTADOS.md#reproducir)
en una carpeta propia, utilizando su resolución1 o2 y su rlib. Después:

```powershell
& $recipeRustc --edition=2021 -C opt-level=2 -C strip=symbols -C 'link-arg=-Wl,--stack,33554432' crates/rf-d-circuit/examples/release_continuation.rs --extern rf_d_circuit=tmp/receta-usuario/librf_d_circuit.rlib -o tmp/receta-usuario/release.exe
& ./tmp/receta-usuario/release.exe tmp/receta-usuario/sostenido/final.ckp tmp/receta-usuario/liberacion
python -B tools/release_render_cli.py --parent tmp/receta-usuario/sostenido/selected.txt --continuation tmp/receta-usuario/liberacion/selected.txt --output tmp/receta-usuario/liberacion/j7.wav
```

Una carpeta nueva por recorrido. Se restaura el perfil declarado en el
checkpoint; no hay selector para reemplazar su historia por otra.

## Alcance y siguiente bloque

[QA](../evidence/voice_release_tests01.json) protege la evidencia anterior,
fuentes medidas y privados nuevos.255 tests Rust y2 definiciones Python
heredados por identidad, sin reejecución; tres checks nuevos de integración.
Sin medición de heap, stack máximo o deadline en este bloque. Stack de
laboratorio32 MiB y tiempos de campaña no admiten el motor para RT.

El [primer cierre QA](../evidence/voice_release_qa_failure01.json) rechazó
comparar literalmente0.020004 con el producto binario del reloj. Se conserva
el error y su replay sin cambios. La [reparación de representación](../evidence/voice_release_qa_representation01.json)
cambia sólo esa comparación a ticks·TICK y su import; no toca trayectoria,
balance de cargas, tolerancias o recibos medidos. La duración rotulada sigue
siendo20.004 ms; el valor binario es0.020003999999999997 s.

Ahora se observan conmutación y descarga del contorno de volumen, con la
red completa cargada. Persisten fuentes/cutoff impuestos y parámetros de
semiconductores condicionados; no contorno desde silencio, voz completa,
periodicidad asintótica o fidelidad física admitidos. Siguiente: evolución
de la descarga y control eléctrico de decay para conseguir un fragmento
musical de duración útil, respetando cargas y memoria propias.
