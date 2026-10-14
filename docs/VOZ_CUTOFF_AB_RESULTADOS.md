# Cutoff A/B desde un origen común

## Diseño y alcance

Se bifurca el checkpoint propio antes del cierre de panel a 156,450 ms: 458 HIGH/LOW, clock y propuesta, KEY0/S abierto, decay ON/R16 1 kΩ, CV y cargas idénticos. La rama cerrada ya admitida cambia α1→0,5; la nueva mantiene α1 durante los mismos 8 ms, hasta 164,450 ms. Se reutiliza la biblioteca assembly. El estado posterior evoluciona libremente en ambas redes: no se impone igualdad del contorno de volumen o de la onda del VCO tras el evento.

α es fracción eléctrica, no Hz o curva de panel calibrada. La generación del contorno de filtro permanece impuesta a pin16=0 V. [Derivación y fuentes](CUTOFF_NATIVO_Q26_Q28.md), [receta](RECETA_CONDICIONADA_PROTOCOLO.md). Historia condicionada, sin unidad física.

Se calcula una rama alternativa de 8 ms en una ventana ya existente. No se concatenan ambas ni se amplían retrospectivamente la historia continua/WAV anterior de 164 ms. RFCTF001 y todos los campos de receta inicial coinciden por bytes; el cierre difiere sólo en fase/α. Ocho Accepted de la rama nueva coinciden completos por bits con block.

## Validación numérica y memoria

Rama abierta: 15524 Accepted/31048 endpoints; 13740 ecuaciones seleccionadas nuevas, original/FD/Decimal100, puertas KCL20 pA, restricciones200 pA, correcciones1 µV/1 nA. Once relojes de 229 estados por resolución; peor ratio de puerta 0.00803701168017. Resets≤10 ns, transiciones≤100 ns, flujos C2/componentes seleccionados y nueve balances ΔQ≤1 pA×duración pasan. 10 restores/160 Accepted por bits, máximo 1 motores sombra; corrupciones y destinos inválidos rechazados atómicamente.

Rama cerrada: 13740 ecuaciones seleccionadas heredadas por identidad de [la campaña anterior](../evidence/voice_cutoff_reference01.json), sin reejecución ni contabilizarlas como nuevas. Comparación A/B en once clocks comunes conserva la igualdad inicial y registra diferencias posteriores de C2, loudness, J7, base Q26 y corriente TAIL→Q28C. No hay puerta de cercanía entre α diferentes: la diferencia es el objeto de estudio.

## Voltios y escucha

Métricas de las 384 muestras filtradas sobre la misma ventana, con DC incluido y escala idéntica:

| Semipaso máximo (ticks) | Media abierto (V) | Media cerrado (V) | RMS abierto (V) | RMS cerrado (V) | RMS diferencia (V) | Máxima diferencia (V) |
| --- | --- | --- | --- | --- | --- | --- |
| 1048576 | 5.51803805832e-05 | 5.66259148922e-05 | 5.68675841119e-05 | 5.83851447593e-05 | 9.95593304377e-06 | 2.48200341682e-05 |
| 524288 | 5.51803759901e-05 | 5.66259118879e-05 | 5.68675806146e-05 | 5.8385140129e-05 | 9.95595331579e-06 | 2.48200453094e-05 |

En resolución 1 µs, RMS cerrado/abierto=1.02668584628, 0.228751499 dB. Este cociente describe J7 con transitorio y DC de esta ventana; no es frecuencia de corte, respuesta estacionaria o un nivel perceptual calibrado. Las diferencias incluyen toda la respuesta de la voz cargada a α, incluida la realimentación sobre vecinos.

Como estadística adicional, RMS respecto de la media de cada ventana: abierto=1.37494665552e-05 V, cerrado=1.42242993059e-05 V; cociente=1.03453463076, 0.294900663 dB. Se calcula sobre los mismos voltios filtrados, conservando DC en los WAV. No se ajusta el audio ni se interpreta este estadístico como transferencia estacionaria.

Cuatro WAV mono PCM16 de 8 ms, 384 muestras a 48 kHz. Dos derivaciones completas idénticas; refinamiento entre resoluciones de cada rama ≤2 µV/7 LSB. Sinc18 kHz/Blackman, 0,01 V/FS y DC conservados, sin normalización, fades, loop o repetición. Extensión constante sólo en bordes del filtro; todos los clocks de circuito de la ventana están presentes.

- `artifacts/cutoff-ab01/rf-d-cutoff-ab-open-8ms-524288.wav`
- `artifacts/cutoff-ab01/rf-d-cutoff-ab-closed-8ms-524288.wav`
- Las dos versiones de 2 µs están en la misma carpeta con sufijo `1048576`.

CLI desde la raíz, con entradas propias y salida nueva:

```powershell
python -B tools/cutoff_ab_cli.py --open references-local/cutoff-ab01/524288/selected.txt --closed references-local/voice-cutoff01/524288/selected.txt --output artifacts/cutoff-ab-pair.json
```

Publica `cutoff-ab-pair-open.wav`, `cutoff-ab-pair-closed.wav` y el sidecar con siete entradas, código importado, clocks/α y métricas. Cuatro checks: identidad de ambos WAV/sidecar, protección de los tres archivos existentes y rechazos específicos previos de estado inicial incompatible y ventana incompleta. Fixtures completos.

## Evidencia, recursos y límites

[Protocolo](VOZ_CUTOFF_AB_PROTOCOLO.md), [entradas](../evidence/cutoff_ab_inputs01.json), [nativo](../evidence/cutoff_ab_native01.json), [red original y origen A/B](../evidence/cutoff_ab_reference01.json), [audio/métricas](../evidence/cutoff_ab_listening01.json), [CLI](../evidence/cutoff_ab_cli01.json), [QA](../evidence/cutoff_ab_tests01.json).

Preparación: una sustitución amplia reescribía un `for` y producía SyntaxError. [Fallo y repetición sin cambios](../evidence/cutoff_ab_preflight_failure01.json); [reparación acotada](../evidence/cutoff_ab_preflight_repair01.json) antes de medir, conservando snapshot previo y caller. No se cambiaron gates ni circuito.

Campaña nativa 249.976064 s, auditor 10.993979 s; privados nuevos 23950264 bytes dentro de 64 MiB, reserva1 GiB. Sin Cargo/cache/SPICE o biblioteca nuevos, stack offline32 MiB. 255 tests Rust y dos definiciones Python heredados sin reejecución. Sin fidelidad física, voz desde silencio, periodicidad, calibración, heap/deadline o RT nuevos.

Siguiente: controles pendientes de la voz y su contorno de filtro, con comparaciones desde el mismo estado cuando se quiera aislar el efecto de un parámetro.
