# Cutoff A/B desde el mismo estado cargado

2026-10-14, base `14bbce669f4569d434cdafac436e4a866a5ab6ca`, QA `voice_cutoff_tests01.json`. Perfil documental vintage CA3046, sin unidad física. Reutilizar la biblioteca assembly y la rama cerrada ya admitida; conservar sus evidencias y duración publicadas.

## Pregunta y bifurcación fijadas antes de medir

Separar el efecto de cutoff de comparar dos momentos diferentes de una liberación. Origen propio: `voice-cutoff01/<resolución>/event1-before.ckp`, 82024857600 ticks (156,450 ms), RFCTF001/phase0/α1. La rama cerrada existente aplica α0,5 desde ese estado durante 8 ms. La rama nueva mantiene α1 durante los mismos 4194304000 ticks, hasta86219161600 (164,450 ms). Ambas parten de 458 HIGH/LOW, clock, propuesta, KEY0/S abierto, decay ON/R16 1 kΩ, CV, fuentes y cargas idénticos; difieren sólo en α. Cada resolución conserva su checkpoint propio. No imponer iguales los estados futuros: la realimentación entre bloques pertenece al efecto del control.

α es fracción eléctrica del potenciómetro, no Hz o curva angular calibrada. Mantener [fuentes, derivación y dominio](CUTOFF_NATIVO_Q26_Q28.md) y [receta nominal](RECETA_CONDICIONADA_PROTOCOLO.md). Pin16 del contorno de filtro sigue impuesto a 0 V. La historia inicial continúa condicionada. No concatenar las ramas ni atribuir 8 ms adicionales a la historia continua anterior.

## Puertas y observaciones

Rama abierta nueva: dos máximos de semipaso 2/1 µs, LTE2 µV/2 nA y veinte intentos. Once clocks comunes cada0,8 ms, doce checkpoints por perfil. Cuatro Accepted completos por resolución en la unión coinciden por bits con block. Auditor original/FD/Decimal100 en coarse/mid/end de primer/último Accepted, resets y TURN/LATCH: KCL20 pA, restricciones200 pA, correcciones1 µV/1 nA; refinamiento229 estados2 µV/2 nA, resets≤10 ns, transiciones≤100 ns. Flujos C2 completos y componentes seleccionados; balance≤2 µV/s, componentes≤10 fA. Nueve balances ΔQ≤1 pA×duración y replay hasta16 Accepted, máximo tres motores sombra, corrupciones/destinos inválidos atómicos. Cobertura cerrada heredada por identidad, sin contarse como ecuaciones nuevas.

En A/B medir diferencias, sin exigir cercanía entre ramas. Registrar los once clocks compartidos y la diferencia de estados/puertos de control, además de J7 completo. Cada rama debe cumplir refinamiento entre resoluciones≤2 µV/7 LSB. Medir RMS, media/DC, máximo y diferencia RMS de voltios filtrados al mismo reloj; no normalizar por pico ni imponer igualdad de volumen. Las métricas pertenecen a esta ventana finita, sin estimar cutoff en Hz o transferencia estacionaria.

Cuatro WAV reales de8 ms,384 muestras48 kHz, escala0,01 V/FS, sinc18 kHz/Blackman y DC heredados. Dos derivaciones completas idénticas, sin loop/fades/repetición ni nuevos tramos concatenados. Verificar estados/recetas/ventana completa, origen común y timestamps enteros. CLI con hashes de todas las entradas/código, clocks/α y cuatro comprobaciones: salida íntegra, protección de salida existente y rechazos específicos de estado inicial incompatible y traza incompleta con fixtures completos.

## Recursos y alcance

Privados nuevos≤64 MiB, reserva1 GiB, stack offline32 MiB. Perfil≤1800 s/proceso≤1900 s, campaña≤4000 s, auditor≤600 s. Conservar fallo/fuente/replay sin cambios antes de reparar; no Cargo/cache/SPICE o biblioteca nuevos. Sin fidelidad física, voz desde silencio, periodicidad, calibración, heap/deadline o RT. Sin prolongar el WAV continuo anterior de164 ms.
