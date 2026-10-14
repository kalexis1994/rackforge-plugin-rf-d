# Retrigger con memoria desde la cola propia

2026-10-14, base `beef9dae6db96015e6bf7081fb3c5bbc38ac5076`, QA `voice_tail_tests01.json`. Modelo documental vintage CA3046, sin unidad física. Se reutiliza la biblioteca assembly congelada; no cambian dispositivos, solver, cargas ni constantes audibles.

## Pregunta y escena fijadas antes de medir

¿Cómo responde el contorno cargado a un segundo gatillo, sin borrar la memoria de la primera liberación? Se parte de cada final propio a 140,442 ms, KEY 0 V/S abierto/decay ON/R16 1 kΩ. Se continúa 4 µs y luego KEY 10 V/S cerrado durante 8 ms; después KEY 0 V/S abierto durante 8 ms. El CV del VCO permanece fijo: no son cambios de nota MIDI ni un preset calibrado. Los niveles y contactos proceden de la escena nominal en [receta condicionada](RECETA_CONDICIONADA_PROTOCOLO.md); las duraciones son estímulos de laboratorio, no constantes físicas identificadas.

Tick 125 ns/65536. Inicio 73632055296; eventos en 73634152448 y 77828456448; final 82022760448. Duración nueva 16,004 ms; historia completa desde 8,438 ms: 148,008 ms. Cortes cada 0,8 ms en las fases largas: 22 relojes comunes y 25 checkpoints por perfil. Mantener los 458 HIGH/LOW, resistencia, reloj y propuesta exactamente al aplicar los eventos. Registrar antes/después. Cuatro avances completos por resolución en la unión, y cuatro tras cada evento, deben coincidir por bits con la familia block anterior.

## Puertas

- Dos resoluciones máximas de semipaso: 2 y 1 µs. LTE 2 µV/2 nA, veinte intentos; no cambiar puertas para completar la escena.
- Red original en coarse/mid/end del primer/último Accepted, resets y TURN/LATCH: KCL 20 pA, restricciones 200 pA, correcciones 1 µV/1 nA; diferencias finitas y cargas Decimal100.
- 229 estados al mismo reloj: 2 µV/2 nA. Resets interpolados ≤10 ns; TURN/LATCH ≤100 ns. Contrastar todos los flujos C2: balance ≤2 µV/s y componentes seleccionados ≤10 fA. Nueve balances ΔQ orientados ≤1 pA×duración por fase, total y unión con la historia previa.
- Restores/replay completo por bits, hasta 16 Accepted por checkpoint, máximo tres motores sombra. Corrupciones y destinos inválidos deben rechazarse atómicamente.
- Dos derivaciones completas del audio iguales; comparación entre resoluciones ≤2 µV/7 LSB. WAV mono PCM16 48 kHz, 7104 muestras/148 ms, sinc 18 kHz/Blackman y 0,01 V/FS heredados. Sin loop, fades, normalización o retiro de DC; truncamiento de 8 µs por la rejilla. Uniones completas y endpoint único. CLI con hashes de entradas/código, eventos y clocks; rechazos previos de salida existente, unión incompatible y traza incompleta.

## Recursos y alcance

Outputs privados nuevos ≤96 MiB y reserva de 1 GiB; stack de laboratorio 32 MiB. Perfil nativo ≤1800 s, proceso ≤1900 s, campaña ≤4000 s, auditor ≤600 s. Sin biblioteca, Cargo/cache o SPICE nuevos. Conservar cada fallo, fuente y replay sin cambios antes de reparar. La historia sigue condicionada; no admitir voz desde silencio, fidelidad física, periodicidad, heap/deadline o RT. Registrar el motor de cada tramo del audio.
