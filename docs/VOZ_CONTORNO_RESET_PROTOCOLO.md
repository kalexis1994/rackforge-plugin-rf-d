# Contorno229 en milisegundos y reset del VCO

Antes de medición, 2026-10-12. [Motor anterior](VOZ_CONTORNO_ADAPTATIVO_RESULTADOS.md),
Model D CA3046, sin hardware. Misma red229, dispositivos condicionados,
panel, Newton64/24 y cargas; sin nuevas constantes audibles ni reglas ADSR.

## Calendario y evolución

Inicio2848980992 ticks de125 ns/65536 (5.434 ms). Se toma el final fino
de125 ns propio ON/OFF;458 componentes conservadas por bits y misma
semilla por cada pareja de límites. No se reinicia C2/C4/C7 o el VCO.
Reposo4 µs, KEY10/S cerrado1.5 ms, KEY0/S abierto1.5 ms:3.004 ms nuevos.
Observaciones al fin del reposo y cada300 µs de los tramos largos,
además de todas las salidas finas aceptadas. No se fuerzan voltajes.

Se amplía sólo el máximo permitido del controlador, de131072 a1048576
ticks: límites deh2/1 µs (1048576/524288). No se cambia la ley LTE:
coarse2h frente a dos finosh,2 µV/2 nA, acepta≤1, duplica≤.25;
20 intentos/min full8 ticks. La red admite estos pasos en su dominio
≤1 ms, pero su precisión se decide con la misma LTE y comparación
temporal. La ampliación de dominio no hereda una admisión de trayectoria.

## Reset y evidencia necesaria

Reset creciente de rampa43: Vprev<−2 V y Vnext≥−2 V, convención de
observación heredada del banco de ciclos; no un umbral Schmitt físico.
Guardar los dos endpoints y su reloj, interpolación descriptiva y
accepted completo que cruza. Exigir≥1 reset por perfil y mismo número
entre límites, distancia de tiempos interpolados≤10 ns (gate numérico
de esta ventana). Auditar sus coarse/finos y KCL con el contorno cargado.

Primer/último accepted de cada tramo y todos los que contienen reset:
grafo/FD y Q Decimal100, mismas gates20 pA/0.2 nV,1 µV/1 nA.
Todas las229 coordenadas comparadas en12 relojes por ON/OFF a2 µV/2 nA.
Balances C2/C18/C27/C7/C4 y terminales Q25/Q15 por tramo/total a1 pA×duración,
usando sólo etapas finas publicadas. Cuadratura nativa, no oráculo de
todos los pasos. Fuentes y bibliotecas protegidas por SHA.

Restore en comienzo de tramo, primer corte interior y en cada accepted
que cruza reset. Repetir hasta16 accepted siguientes dentro del mismo
tramo: candidatos, incrementos, LTE, intentos, observaciones y checkpoint
por bits. Son restores de prefijo de16, no replays completos de1.5 ms;
el banco anterior ya conserva replays completos de sus tramos cortos.
Destino inválido, presupuesto1 insuficiente y cuatro corrupciones por
perfil permanecen comprobados. Fronteras no modifican458 componentes.

Conservar checkpoint entrante y destino exacto de cualquier rechazo de
integración, con rollback por bytes. Guardar también el último estado
ante presupuesto administrativo, sin confundirlo con un fallo numérico.
Presupuesto900 s/perfil,4000 s/campaña,120 s/compilación,300 s/auditor;
64 MiB de salida privada, reserva1 GiB, stack32 MiB. Rechazos numéricos
y replay idéntico preservados antes de reparar; ninguna gate relajada.

Sin nuevo audio, SPICE, cargas de los otros BJT/diodos de placa2,
nota completa, identificación física o RT.248 tests heredados por identidad.
La continuidad de un reset con C2 precargado no acredita un contorno
completo desde silencio; C7 y el release pueden seguir evolucionando.
