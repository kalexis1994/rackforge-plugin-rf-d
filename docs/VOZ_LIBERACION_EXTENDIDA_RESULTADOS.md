# Liberación extendida con la familia pública optimizada

## Resultado y dominio

32 ms adicionales propios desde 44,442 a 76,442 ms. Se une una trayectoria de 68,004 ms desde 8,438 ms; dos WAV nativos de 68 ms (3264 muestras a 48 kHz). Modelo documental vintage CA3046, receta eléctrica heredada KEY=0 V/S abierto/decay ON/R=1 kΩ, con OSC1, mezclador, escalera, VCA y J7 cargados. No hay nuevo evento de teclado ni de resistencia. Sigue siendo una historia sintética condicionada y una ventana finita.

La biblioteca pública es `references-local/voice-block-library02/librf_d_circuit.rlib`, SHA256 `cf290b02e69e703c479597a36a7853d2cb024f8357154ff98b2dda22d984ea3c`. No se recompila ni modifica el circuito. El llamador nuevo restaura los 3728 bytes propios completos; cuatro avances por perfil comparan todos los estados, incrementos, observables, ratios, iteraciones, trials, relojes y propuestas con el ensamblado original. Ocho avances coinciden por bits. La identidad previa de 4 ms del candidato permanece como evidencia histórica, separada de esta nueva duración.

| Semipaso máximo (ticks) | Accepted | Endpoints finos | Resets VCO | C2 final (V) | dC2/dt final (V/s) | Loudness final (V) | J7 final (V) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1048576 | 28051 | 56102 | 13 | 0.88001118198 | -2.81731426339 | -0.25713265444 | -0.00014860456757 |
| 524288 | 35664 | 71328 | 13 | 0.88001118198 | -2.81731426331 | -0.25713265444 | -0.000148604567431 |

## Contraste eléctrico y memoria

180 candidatos / 41220 ecuaciones seleccionadas nuevas se evalúan con la red original, diferencias finitas y carga Decimal100; las puertas eléctricas permanecen iguales. No se atribuye auditoría original independiente a todos los endpoints. Los 229 estados se comparan en 41 relojes comunes: error máximo de tensión 6.0309658016e-07 V, ratio máximo de puerta 0.30154829008; resets interpolados difieren como máximo 1.65423230669e-13 s frente a la puerta 10 ns. Se conservan los nueve balances ΔQ orientados y su unión desde el primer estado real de 8,438 ms; la cuadratura de todos los estadios sigue siendo nativa.

127432 registros de flujos C2; 62 endpoints de componentes se contrastan en Decimal100. Error máximo de balance de derivada 7.81597009336e-14 V/s, puerta 2 µV/s. La caída incluye corriente de ataque, rama eléctrica decay y seguidor cargado; no presupone una exponencial RC aislada. Eventos TURN/LATCH nuevos observados: 0. Esto no demuestra descarga completa ni silencio asintótico.

30 restauraciones reproducen 480 Accepted completos por bits; máximo simultáneo de motores sombra: 1, con workspace compartido. Ocho corrupciones se rechazan; dos destinos inválidos conservan el checkpoint por bytes. Fuentes, parámetros, reloj y propuesta de ambas uniones permanecen idénticos al final anterior.

## Escucha y reproducción

Dos derivaciones completas de audio coinciden; máximo error entre resoluciones 2.00598955058e-07 V / 1 LSB. Kernel heredado sinc 18 kHz/Blackman, escala 0,01 V/full scale, sin loop, normalización de pico, fade o eliminación de DC. La extensión constante se limita a los bordes del filtro; 4 µs del circuito quedan fuera del WAV por la rejilla de 48 kHz. El contenido nuevo procede de solves nativos.

WAV privados ignorados:

- `artifacts/extended-release01/rf-d-j7-release-68ms-1048576-nativo.wav`
- `artifacts/extended-release01/rf-d-j7-release-68ms-524288-nativo.wav`

CLI desde la raíz, con las trazas y checkpoints propios disponibles:

```powershell
python -B tools/extended_render_cli.py --held references-local/sustained-voice01/524288/selected.txt --release references-local/release-voice01/524288/selected.txt --controlled references-local/decay-voice02/524288/selected.txt --extended references-local/extended-release01/524288/selected.txt --output artifacts/escucha-68ms.wav
```

El destino debe existir y la salida debe ser nueva. El sidecar registra hashes de las siete entradas, renderer, kernel, CLI y WAV, eventos heredados, parámetros y duración. Cuatro checks de integración verifican WAV completo/sidecar, salida existente sin cambios, seam incompatible y traza incompleta rechazados antes de publicar. El esquema RFDCY001 coincide con el contrato del perfil, no identifica cualquier receta arbitraria.

## Evidencia y presupuesto

- [Protocolo fijado antes de ejecutar](VOZ_LIBERACION_EXTENDIDA_PROTOCOLO.md).
- [Entradas propias](../evidence/voice_extended_inputs01.json), [ejecución nativa](../evidence/voice_extended_native01.json).
- [Red original, refinamiento y cargas](../evidence/voice_extended_reference01.json), [audio derivado](../evidence/voice_extended_listening01.json), [CLI](../evidence/voice_extended_cli01.json).
- [QA integral](../evidence/voice_extended_tests01.json), [llamador portable](../crates/rf-d-circuit/examples/extended_release.rs).

Campaña nativa 1124.106284 s; auditor original 32.932783 s. Productos privados nuevos 88897146 bytes, dentro de 128 MiB, reserva 1 GiB. Sin Cargo/cache nueva, nueva biblioteca, SPICE o modificación de productos heredados. Stack de laboratorio 32 MiB, IO y replay fuera del hilo de audio. 255 tests Rust y dos definiciones Python heredados, sin reejecución: se ejecutan las regresiones del recorrido y cuatro integraciones CLI de este bloque.

No se admite fidelidad contra hardware, voz completa desde silencio, periodicidad estable, heap nuevo medido o tiempo real. La mejora de costo anterior facilita esta extensión; no mide un deadline de audio. Siguiente: usar la observación cargada para avanzar duración útil y controlar el costo, conservando estados, eventos y cargas.
