# Liberación cargada extendida: 44,442 a 76,442 ms

Campaña finita de 32 ms adicionales desde ambos `decay-voice02/final.ckp` propios, protegidos por `voice_block_tests01.json`. El ensamblado público optimizado `block_decay_voice` y su motor conservan las ecuaciones, puertos, cargas y estados de la familia anterior. La biblioteca es la ya admitida en `voice_block_library02.json`; se compila únicamente el llamador de laboratorio.

## Receta y dominio

Modelo documental vintage CA3046 de `OBJETIVO.md`. Parámetros y fuentes heredados de `DECAY_CONTROL_PROTOCOLO.md`: OSC1 y sus cargas de mezclador, escalera, VCA y J7; KEY=0 V, S abierto, decay ON, resistencia eléctrica PANEL_R16=1000 Ω. Sin nuevo disparo ni evento de resistencia; sin nueva calibración de perilla ni constantes audibles. Los estados de filtro/contorno iniciales impuestos pertenecen a la historia sintética previa, no al encendido físico desde silencio.

Inicio entero 23300407296 ticks; extensión 16777216000 ticks; tick=125 ns/65536; destino 40077623296 ticks. Observaciones cada 419430400 ticks (0,8 ms), incluyendo el destino. Resoluciones máximas de semipaso 1048576/524288 ticks (2/1 µs), controlador LTE 2 µV/2 nA y límite 20 intentos heredados. HIGH/LOW, reloj, propuesta, KEY, S y R de los 3728 bytes RFDCY001 se preservan completos en la unión. Cuatro avances completos por perfil se comparan por bits con el ensamblado original en esa unión.

## Admisión

- Cada Accepted registra coarse, dos endpoints, calendario, LTE, observaciones y reseteos del VCO. Se exportan los tres pares completos del primer/último Accepted y de cada reset o transición TURN/LATCH. Las restauraciones se reproducen por bits durante hasta 16 avances, con máximo tres motores sombra activos y workspace compartido.
- Auditor original de red, diferencias finitas y carga Decimal100, independiente del nuevo ensamblado: KCL 20 pA, restricciones 200 pA; correcciones 1 µV/1 nA, mismas puertas anteriores. Comparación de 229 estados en 41 relojes compartidos, 2 µV/2 nA; resets interpolados ≤10 ns, transiciones ≤100 ns. No se relajan puertas por aumentar duración.
- Flujos C2 completos: derivada contra corrientes de ataque, decay y seguidor ≤2 µV/s; componentes seleccionados Decimal100 ≤10 fA. Ledger de nueve filas frente a ΔQ independiente ≤1 pA × duración; cuadratura de todos los estadios aún nativa. Ledger unido desde 8,438 ms.
- Audio real concatenado 68,004 ms; WAV 48 kHz de 3264 muestras (68 ms), kernel heredado sinc 18 kHz/Blackman, 0,01 V/full scale. Sin loop, repetición, fade, normalización de pico ni eliminación de DC. Extensión constante solo para bordes del filtro. Uniones completas por 458 valores binarios y una única muestra compartida. Refinamiento de audio ≤2 µV/7 LSB; dos derivaciones completas idénticas.
- CLI reproducible con sidecar de procedencia; rechazo de unión incompatible y de salida existente antes de publicar.

## Presupuesto y alcance

Sin Cargo ni nueva caché; stack de laboratorio 32 MiB. Reserva de disco 1 GiB, entradas heredadas inmutables, nuevos productos privados ≤128 MiB. Cada perfil ≤1800 s de ejecución nativa, proceso ≤1900 s, campaña ≤4000 s, auditor original ≤600 s. Un rechazo conserva fuentes, recibo y repetición sin cambios antes de corregir. No se admite fidelidad física, funcionamiento en tiempo real, periodicidad estable ni voz completa desde silencio. Una ventana mayor sigue siendo una observación finita.
