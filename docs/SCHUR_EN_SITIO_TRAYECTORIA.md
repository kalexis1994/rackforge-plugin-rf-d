# Recorrido de Schur en sitio, antes de medir

2026-10-13. El banco y su confirmación pasan utilidad (1.008589× y
1.013324×);396 trazas y26 regresiones pasan. El fallo previo del driver
de pruebas queda preservado, con reparación de scratch y stack32 MiB.
Esto no admite automáticamente la trayectoria.

Ejecutar los cuatro seeds propios de la referencia LU, conservando sus
229 estados HIGH/LOW y propuesta temporal entrante. Mismo calendario
8.438→11.442 ms, on/off de final decay y máximos2/1 µs. Contactos, fuentes,
GMIN, masa, predictor, Newton y gates no cambian. No reiniciar historias.
El mismo kernel público medido pasa al runner; sin instrumentación.

Auditar los nuevos coarse/mid/end seleccionados con el grafo/FD/Q
Decimal100 original. Reejecutar porque los estados pueden diferir de LU.
Contrastar229 coordenadas a los mismos relojes entre resoluciones y frente
a los cuatro perfiles LU previos:2 µV/2 nA. Eventos de reset y periodo:
10 ns; balances de carga1 pA×duración, mismos controles/brechas previos.
Verificar unión de historia, propuestas, selección/LTE, corrientes, ledgers,
checkpoints, restores, corrupciones y rollback. No exigir igualdad de
cantidad de pasos si el controlador acepta legítimamente otra propuesta.
Los replays del nuevo kernel sí conservan sus datos por bytes.

Rechazo nativo: conservar fuente/salida y repetir el perfil antes de reparar.
Compilación120 s, perfil990 s, total4000 s, auditor600 s, stack32 MiB,
reserva1 GiB. El conjunto nuevo de este bloque permanece bajo64 MiB.
No compilar biblioteca nueva, no SPICE, audio o duración simulada nuevos.
No acreditar fidelidad física, arranque desde silencio o RT.
