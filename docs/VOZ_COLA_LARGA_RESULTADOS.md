# Cola cargada y escucha real de 132 ms

## Dominio y resultado

64 ms eléctricos adicionales desde 76,442 a 140,442 ms. Historia unida 132,004 ms desde 8,438 ms; dos WAV reales de 132 ms, 6336 muestras a 48 kHz. Modelo vintage CA3046 documental y escena condicionada OSC1→BUS→escalera/VCA/J7. KEY 0 V/S abierto/decay ON/PANEL_R16=1000 Ω se heredan; no hay nuevo evento ni cambio de controles. El contorno aún parte de la historia sintética anterior, no de un encendido físico desde silencio.

La cola nueva usa `assembly_decay_voice/engine` y la biblioteca `references-local/voice-assembly-public01/librf_d_circuit.rlib`, SHA256 `9dbada9779f30c4972b057befe092524d091d3444ea777206b618d701236385d`. Se reutiliza sin recompilarla. Los cuatro tramos anteriores proceden de sus propias familias ya admitidas; el WAV unido identifica esos orígenes y la cola nueva. No se atribuye retrospectivamente toda la historia al ensamblado nuevo. La unión conserva 3728 bytes completos, 458 HIGH/LOW, reloj, propuesta y receta; cuatro avances por resolución coinciden por bits con `block_decay_voice/engine` en esta unión.

| Semipaso máximo (ticks) | Accepted | Endpoints finos | Resets VCO | C2 final (V) | dC2/dt final (V/s) | Loudness final (V) | J7 final (V) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1048576 | 56274 | 112548 | 26 | 0.850987312116 | -0.00594541270582 | -0.286002836343 | 4.4546792306e-05 |
| 524288 | 71481 | 142962 | 26 | 0.850987312116 | -0.00594541270567 | -0.286002836343 | 4.45467923521e-05 |

## Contraste original y memoria

336 candidatos/76944 ecuaciones seleccionadas nuevas pasan frente a la red original, diferencias finitas y cargas Decimal100. Las puertas de KCL, restricciones y correcciones son las anteriores. Se comparan 229 estados en 81 relojes comunes: error máximo de tensión 1.95325188898e-07 V y ratio de puerta 0.0976625944491; resets interpolados difieren como máximo 1.65617519698e-13 s, puerta de 10 ns. No se atribuye solve original independiente a los demás endpoints.

255512 registros completos de flujos C2 y 114 endpoints de componentes Decimal100. Error máximo de balance de derivada 1.46549439251e-14 V/s frente a 2 µV/s. Se incluyen ataque, decay, seguidor y cargas conectadas. TURN/LATCH nuevos observados: 0. El voltaje y pendiente finales describen esta ventana; no definen una descarga completa ni un silencio asintótico.

Nueve balances ΔQ orientados y su composición desde 8,438 ms pasan la puerta de 1 pA×duración. La cuadratura de todos los estadios sigue siendo nativa. 56 restores reproducen 896 Accepted completos por bits; concurrencia máxima de motores sombra: 1. Ocho corrupciones y dos destinos inválidos se rechazan sin publicar cambios.

## Audio y CLI

Dos derivaciones completas idénticas; error máximo entre resoluciones 2.00598955058e-07 V/1 LSB. Se conserva sinc de 18 kHz/Blackman, 0,01 V/full scale, nivel y DC. Sin loop, normalización de pico, fade o repetición; extensión constante solo en bordes del filtro. Cuatro µs finales del circuito quedan fuera del WAV por la rejilla de 48 kHz. Cada unión comprueba estado completo, receta y una muestra compartida única.

WAV privados ignorados:

- `artifacts/long-tail01/rf-d-j7-tail-132ms-1048576-nativo.wav`
- `artifacts/long-tail01/rf-d-j7-tail-132ms-524288-nativo.wav`

Reproducción desde la raíz con las entradas propias disponibles y salida nueva:

```powershell
python -B tools/tail_render_cli.py --held references-local/sustained-voice01/524288/selected.txt --release references-local/release-voice01/524288/selected.txt --controlled references-local/decay-voice02/524288/selected.txt --extended references-local/extended-release01/524288/selected.txt --tail references-local/long-tail01/524288/selected.txt --output artifacts/escucha-132ms.wav
```

Sidecar con hashes de las diez entradas y del código de render, kernel y dependencias, clocks enteros, evento de resistencia heredado y ausencia de eventos nuevos. Cuatro integraciones verifican identidad completa del WAV/sidecar, protección de salida existente, unión incompatible y traza incompleta rechazadas antes de publicación.

## Evidencia y recursos

- [Protocolo](VOZ_COLA_LARGA_PROTOCOLO.md), [entradas propias](../evidence/voice_tail_inputs01.json), [native](../evidence/voice_tail_native01.json).
- [Red original/refinamiento/ΔQ](../evidence/voice_tail_reference01.json), [escucha](../evidence/voice_tail_listening01.json), [CLI](../evidence/voice_tail_cli01.json), [QA](../evidence/voice_tail_tests01.json).

Campaña nativa 2055.079496 s, auditor 63.374926 s. Productos privados nuevos 175250053 bytes dentro de 192 MiB, reserva de 1 GiB. Sin Cargo/cache/SPICE o biblioteca nueva. Stack de laboratorio de 32 MiB; IO, replay y serialización fuera del hilo de audio. 255 tests Rust y dos definiciones Python heredados sin reejecución; las nuevas campañas y cuatro integraciones se contabilizan separadamente.

Sin fidelidad física, voz completa desde silencio, periodicidad, heap/deadline nuevos o RT admitidos. Siguiente: avanzar el comportamiento de la voz y una escucha musical útil con controles y cargas explícitos; esta cola finita no sustituye esa escena.
