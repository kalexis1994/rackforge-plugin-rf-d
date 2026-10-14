# Cutoff del panel en la voz cargada

## Escena y control

Desde cada final propio del retrigger a 156,446 ms: 4 µs de continuidad con α=1, 8 ms con α=0,5 y 8 ms de reapertura a α=1. Final 172,450 ms; 16,004 ms nuevos y 164,012 ms de historia propia desde 8,438 ms. KEY 0 V/S abierto, decay ON/R16 1 kΩ y CV de VCO fijos. Sin gatillo nuevo ni sustitución de la onda por una fuente grabada.

α es la fracción eléctrica desde −10 V del potenciómetro R11 de 5 kΩ: Vth=−10+20α V y Rth=5000α(1−α) Ω en serie con R55 de 200 kΩ. Se conservan todas las ramas del panel, Q26/Q28/C18 y su carga sobre la escalera. [Fuentes, dominio e incertidumbres](CUTOFF_NATIVO_Q26_Q28.md), [receta](RECETA_CONDICIONADA_PROTOCOLO.md). Estas posiciones no son frecuencias Hz o una curva angular calibrada. Pin16 del contorno de filtro sigue impuesto a 0 V; el generador de ese contorno permanece pendiente.

Se reutiliza `references-local/voice-assembly-public01/librf_d_circuit.rlib`, SHA256 `9dbada9779f30c4972b057befe092524d091d3444ea777206b618d701236385d`. El llamador reconstruye la misma receta nominal cambiando sólo α; no modifica la biblioteca ni el solver. La historia sigue condicionada. El contorno de volumen evoluciona durante el experimento: no se atribuye a cutoff toda diferencia entre ventanas temporales de J7 ni se declara un A/B desde el mismo estado.

## Checkpoints y eventos

RFCTF001 extiende RFDCY001 con f64 α: 3736 bytes, HIGH/LOW desde offset72. La conversión inicial cambia magic/phase e inserta α=1; conserva exactamente reloj, propuesta, fuentes, resistencia y 458 valores de estado. Dos eventos por resolución cambian únicamente α/fase; checkpoints antes/después verifican preservación de lo demás.

Ocho Accepted completos en la unión y 16 después de los eventos coinciden por bits con la familia block anterior usando la misma posición de cutoff. El codec contiene ahora el control realmente usado al restaurar, además de la memoria del circuito.

| Semipaso máximo (ticks) | Fase | α | Accepted | C2 final (V) | Loudness final (V) | J7 final (V) |
| --- | --- | --- | --- | --- | --- | --- |
| 1048576 | 0 | 1.0 | 16 | 1.49953878388 | 0.359205738441 | 0.000132173956332 |
| 1048576 | 1 | 0.5 | 6833 | 1.15101149684 | 0.0124539658652 | 4.42958675025e-05 |
| 1048576 | 2 | 1.0 | 6650 | 0.989365379339 | -0.148353502688 | 3.37718769158e-05 |
| 524288 | 0 | 1.0 | 16 | 1.49953878357 | 0.359205738135 | 0.000132173957355 |
| 524288 | 1 | 0.5 | 8723 | 1.1510114967 | 0.0124539657248 | 4.42958674745e-05 |
| 524288 | 2 | 1.0 | 8558 | 0.989365379274 | -0.148353502753 | 3.3771876917e-05 |

Observables del puerto de control al final de cada fase, derivados de los estados HIGH/LOW auditados: base Q26=índice195, colector Q28=198, TAIL=138. El mapa `chain_index(k)=133+k` y la rama R60 `(TAIL−Q28C)/680 Ω` proceden de `assembly_decay_voice.rs` y `circuit66.rs`; el signo positivo indica corriente desde TAIL hacia Q28C. Son puntos de la trayectoria, no una medición de frecuencia de corte o un equilibrio DC nuevo.

| Semipaso máximo (ticks) | Fase | Base Q26 (V) | Colector Q28 (V) | Corriente TAIL→Q28C (A) |
| --- | --- | --- | --- | --- |
| 1048576 | 0 | 0.090267732454 | 1.28177293106 | 0.000144421881342 |
| 1048576 | 1 | 0.000122528823873 | 1.4500929888 | 6.82489850903e-06 |
| 1048576 | 2 | 0.090267732454 | 1.27431499121 | 0.000144421881342 |
| 524288 | 0 | 0.090267732454 | 1.28177293107 | 0.000144421881342 |
| 524288 | 1 | 0.000122528823873 | 1.45009298879 | 6.82489850903e-06 |
| 524288 | 2 | 0.090267732454 | 1.27431499121 | 0.000144421881342 |

## Red original y memoria

30796 Accepted/61592 endpoints finos; 144 candidatos y 32976 ecuaciones seleccionadas nuevas. El auditor reconstruye la red original de panel a α de cada fase, FD y cargas Decimal100; conserva KCL 20 pA, restricciones 200 pA y correcciones 1 µV/1 nA. Se seleccionan coarse/mid/end de bordes, resets y TURN/LATCH; no se atribuye solve original al resto de endpoints.

22 relojes de 229 estados: error máximo 5.83578460404e-08 V, ratio de puerta 0.0291789230202. 12 resets refinados ≤10 ns. Nueve balances ΔQ orientados pasan por fase/total y unión desde 8,438 ms, puerta 1 pA×duración; incluyen C18, C27/BUS, contorno y junturas. La cuadratura de todos los estadios es nativa. 61594 flujos C2 completos; componentes seleccionados Decimal100 y balance de derivada ≤2 µV/s. 24 restores/352 Accepted reproducidos por bits, máximo 1 motores sombra; corrupciones y destinos inválidos rechazados atómicamente.

## Audio y CLI

Dos WAV mono PCM16 de 164 ms, 7872 muestras a 48 kHz; historia eléctrica 164,012 ms, truncamiento 12 µs. Siete tramos con familias originales identificadas. Uniones de estado completo/receta/endpoint único, sin loop, fades o normalización; DC y escala 0,01 V/FS conservados. Sinc 18 kHz/Blackman, extensión constante sólo en bordes del filtro. Dos derivaciones completas idénticas; diferencia entre resoluciones 2.00598955058e-07 V/1 LSB, puertas 2 µV/7 LSB.

- `artifacts/voice-cutoff01/rf-d-j7-cutoff-164ms-1048576-nativo.wav`
- `artifacts/voice-cutoff01/rf-d-j7-cutoff-164ms-524288-nativo.wav`

CLI con entradas propias y salida nueva desde la raíz:

```powershell
python -B tools/cutoff_render_cli.py --held references-local/sustained-voice01/524288/selected.txt --release references-local/release-voice01/524288/selected.txt --controlled references-local/decay-voice02/524288/selected.txt --extended references-local/extended-release01/524288/selected.txt --tail references-local/long-tail01/524288/selected.txt --retrigger references-local/voice-retrigger01/524288/selected.txt --cutoff references-local/voice-cutoff01/524288/selected.txt --output artifacts/escucha-cutoff.wav
```

Sidecar con 24 entradas reales, código importado, clocks, familias y eventos de cutoff. Cuatro integraciones pasan: WAV/sidecar completos, protección de salida existente y rechazos específicos antes de publicación de unión incompatible/traza incompleta. Los fixtures incluyen todos los checkpoints requeridos.

## Evidencia y alcance

[Protocolo](VOZ_CUTOFF_PROTOCOLO.md), [entradas](../evidence/voice_cutoff_inputs01.json), [nativo](../evidence/voice_cutoff_native01.json), [red original/refinamiento/carga](../evidence/voice_cutoff_reference01.json), [audio](../evidence/voice_cutoff_listening01.json), [CLI](../evidence/voice_cutoff_cli01.json), [QA](../evidence/voice_cutoff_tests01.json).

Campaña 513.593836 s, auditor 25.387867 s; privados nuevos 47487058 bytes dentro de 96 MiB, reserva 1 GiB. Sin Cargo/cache/SPICE o biblioteca nuevos. Stack offline 32 MiB. 255 tests Rust y dos definiciones Python heredados sin reejecución; campañas/integraciones nuevas separadas. Sin fidelidad física, voz desde silencio, periodicidad, heap/deadline, RT o calibración musical admitidos.

Siguiente: controles útiles de la voz y sus fronteras pendientes, manteniendo cargas y receta completa; contrastar una respuesta A/B desde el mismo estado cuando se quiera atribuir diferencias sonoras sólo al cutoff.
