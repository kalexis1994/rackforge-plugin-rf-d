# Selección explícita del motor nominal por incidencias

Condición previa: el [candidato](INCIDENCE_VOICE_PROTOCOLO.md) pasa precisión,
auditoría original y ratio de costo ≤0,90. Conservar fuentes históricas y
elegirlo mediante active_nominal_voice.rs, que reexporta su implementación.
Ese punto de entrada mantiene el mismo dominio de laboratorio; no es una
integración de plugin, renderer general o garantía RT.

Compilar el consumidor de la fachada y ejecutar 64/32 µs desde la misma
semilla. Exigir GRID/ROOT/SOLVER y estados finales idénticos al candidato
verificado, 1 pA/2 nV, heap cero, ocho replays y diez rechazos atómicos.
Volver a medir sin timers internos con un directo fresco de 32 µs y el
mismo compilador/rlib/flags. Ratio seleccionado/directo ≤0,90 sin ajuste.
Un fallo impide seleccionar el nuevo motor, conservando fuente/entrada/replay.

Registrar por ruta y SHA la implementación, solver, fachada y recibos.
El commit que incluye su propia QA no se puede escribir dentro de ella:
dejar su campo de commit pendiente explícitamente y resolver identidad
con los SHA y la comprobación del commit real tras crearlo. Conservar el
origen de la implementación anterior como historial, sin adjudicar ese
commit viejo al nuevo solver.

Un único tmp/lab-current, retiro de ejecutables después de recibos y
presupuesto conjunto 8 MiB sin QA; sin audio, Cargo o caché nuevos.
