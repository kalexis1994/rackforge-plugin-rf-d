# Retrigger cargado: segunda pulsación con memoria

## Escena y procedencia

Continuación de cada final propio a 140,442 ms, biblioteca assembly congelada SHA256 `9dbada9779f30c4972b057befe092524d091d3444ea777206b618d701236385d`. Se conserva decay ON/R16 1 kΩ, oscilador CA3046 y las cargas del BUS, escalera, VCA y J7. No se recompila la biblioteca. Se aplican 4 µs de continuidad, KEY 10 V/S cerrado durante 8 ms y KEY 0 V/S abierto durante 8 ms. Final 156,446 ms: 16,004 ms nuevos, historia unida 148,008 ms desde 8,438 ms.

Gatillo de contorno, con CV de oscilador fijo; niveles/contactos y parámetros heredados de [la receta](RECETA_CONDICIONADA_PROTOCOLO.md). Duraciones elegidas como estímulo de laboratorio. Es una segunda pulsación con memoria de una historia condicionada, sin arranque desde silencio ni control MIDI calibrado.

Los dos eventos por resolución conservan 458 HIGH/LOW, resistencia, reloj y propuesta por bits. Cuatro avances después de cada evento coinciden íntegramente con la familia block anterior: 16 Accepted pareados, además de ocho en la unión inicial. Los checkpoints antes/después permiten verificar la operación separadamente de su respuesta eléctrica posterior.

| Semipaso máximo (ticks) | Fase (0 reposo, 1 gate, 2 release) | Accepted | C2 final (V) | Loudness final (V) | J7 final (V) |
| --- | --- | --- | --- | --- | --- |
| 1048576 | 0 | 13 | 0.850987288338 | -0.286002859994 | 4.45475763538e-05 |
| 1048576 | 1 | 6810 | 1.49381257491 | 0.353508697635 | -3.85771235116e-05 |
| 1048576 | 2 | 8199 | 1.49978728282 | 0.359452971714 | 0.000132857934241 |
| 524288 | 0 | 13 | 0.850987288338 | -0.286002859994 | 4.45475763999e-05 |
| 524288 | 1 | 8720 | 1.49381257491 | 0.353508697635 | -3.85771235136e-05 |
| 524288 | 2 | 10080 | 1.49978728251 | 0.359452971408 | 0.000132857935203 |

C2 continúa creciendo después de soltar KEY antes de iniciar su descenso: máximo muestreado 1.79621376787 V; cambio de signo interpolado 3.99436646076 ms después del evento OFF. Se observan dos conmutaciones del biestable en cada resolución. Esta respuesta pertenece al modelo y a la historia cargada declarados; no se identifica como tiempo de panel o medición de un instrumento físico.

## Validación propia

33835 Accepted y 67670 endpoints finos; 192 candidatos y 43968 ecuaciones seleccionadas nuevas frente al grafo original, diferencias finitas y cargas Decimal100. Se mantienen KCL 20 pA, restricciones 200 pA, correcciones 1 µV/1 nA. Cobertura seleccionada en coarse/mid/end de los bordes, resets y transiciones; los demás endpoints no reciben solve independiente original por herencia.

22 relojes comunes de 229 estados, error máximo 1.89018553951e-07 V, ratio de puerta 0.0945092769757. 14 resets y 6 TURN/LATCH observados pasan las puertas interpoladas de 10/100 ns. 67672 flujos C2 completos; balance máximo de derivada 1.42108547152e-13 V/s. Cada corriente conectada, seguidor y retorno permanece en el balance.

Nueve filas ΔQ orientadas pasan por fase, total y unión desde 8,438 ms, puerta 1 pA×duración. La cuadratura de todos los estadios sigue siendo nativa; componentes seleccionados se contrastan en Decimal100. 32 restores reproducen 474 Accepted completos por bits, máximo 2 motores sombra. Ocho corrupciones y dos destinos inválidos rechazados atómicamente.

## Escucha y reproducción

Dos WAV mono PCM16, 7104 muestras a 48 kHz: 148 ms reales. Se unen seis trazas, con las primeras cuatro familias originales y los dos tramos assembly atribuidos explícitamente. Uniones por estado completo, receta y endpoint único; eventos con clocks enteros y checkpoints antes/después. Sinc 18 kHz/Blackman, escala 0,01 V/FS y DC conservados. Sin loop, fades o normalización; ocho µs finales fuera del WAV por su rejilla, extensión constante sólo en bordes del filtro.

Dos derivaciones completas idénticas. Diferencia entre resoluciones 2.00598955058e-07 V y 1 LSB, puertas 2 µV/7 LSB.

- `artifacts/voice-retrigger01/rf-d-j7-retrigger-148ms-1048576-nativo.wav`
- `artifacts/voice-retrigger01/rf-d-j7-retrigger-148ms-524288-nativo.wav`

CLI desde la raíz, con entradas propias presentes y salida nueva:

```powershell
python -B tools/retrigger_render_cli.py --held references-local/sustained-voice01/524288/selected.txt --release references-local/release-voice01/524288/selected.txt --controlled references-local/decay-voice02/524288/selected.txt --extended references-local/extended-release01/524288/selected.txt --tail references-local/long-tail01/524288/selected.txt --retrigger references-local/voice-retrigger01/524288/selected.txt --output artifacts/escucha-retrigger.wav
```

Sidecar con las 17 entradas realmente leídas, código importado, clocks, familias y dos eventos. Cuatro integraciones pasan: WAV/sidecar completos idénticos, protección de salida existente y rechazo previo de unión incompatible/traza incompleta.

La primera campaña CLI produjo el WAV correcto pero su fixture de unión incompatible omitió los cuatro checkpoints de eventos. La CLI rechazó primero la entrada faltante, por lo que no alcanzó el rechazo específico esperado. Se conservan [fuente y fallo](../evidence/voice_retrigger_cli01.json), [replay exacto sin cambios](../evidence/voice_retrigger_cli_replay01.json) y [reparación del fixture](../evidence/voice_retrigger_cli_repair01.json). El segundo intento completa esos checkpoints en un directorio nuevo y reejecuta las cuatro puertas idénticas; circuito, render y datos nativos permanecen sin cambios.

## Evidencia y siguiente bloque

[Protocolo](VOZ_RETRIGGER_PROTOCOLO.md), [entradas](../evidence/voice_retrigger_inputs01.json), [nativo](../evidence/voice_retrigger_native01.json), [grafo original y memoria](../evidence/voice_retrigger_reference01.json), [audio](../evidence/voice_retrigger_listening01.json), [CLI](../evidence/voice_retrigger_cli02.json), [QA](../evidence/voice_retrigger_tests01.json).

Campaña nativa 566.787229 s, auditor 52.004926 s; privados nuevos 52517358 bytes dentro de 96 MiB. Sin Cargo/cache, SPICE o biblioteca nuevos. Stack offline 32 MiB, IO y replay de laboratorio. 255 tests Rust y dos definiciones Python heredados sin reejecución; campañas e integraciones nuevas se contabilizan aparte. Sin fidelidad física, voz completa desde silencio, periodicidad, heap/deadline o RT admitidos.

Siguiente: ampliar la escena de control y su duración con una pregunta musical concreta, manteniendo historia propia y contraste del contorno cargado. No usar una onda impuesta ni reiniciar capacitores para facilitar el gatillo.
