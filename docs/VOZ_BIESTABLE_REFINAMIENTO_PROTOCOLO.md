# Refinar la ventana de conmutación229

Declarado después del oráculo04 rechazado y antes de la campaña04,
2026-10-12. El nativo03 converge y repite; el oráculo04 rechaza y reproduce
`ValueError: 229 refinement`. Al final del tramo S cerrado, C4_LEFT
difiere ≈14.30 µV ON/14.29 µV OFF entre31.25/15.625 ns: gate2 µV fallido.
Las KCL/cargas y balances de todos los perfiles se evalúan antes de ese
gate, pero no se promueve esta malla como trayectoria admitida.

Se repite la misma ventana con15.625/7.8125 ns. Ambos pasos ON/OFF
arrancan desde la misma semilla225 fina anterior, con los cuatro bias
nuevos idénticos. La semilla229 de15.625 ns permanece por bytes, y la
de7.8125 ns sólo cambia el campo de paso del checkpoint. Cinco tramos de
2 µs, misma ley de dispositivo, contactos y 64/24; no se relajan gates.
El modelo y sus predictores de Newton quedan idénticos. Sólo codec/receta
permiten8192/4096 ticks y el auditor compara esa pareja. Se exige que
la repetición15.625 ns coincida por bits con la campaña03 completa.

3840 pasos nuevos,5760 repetidos,40 restores,16 corrupciones.
80 candidatos/18320 ecuaciones independientes,40 vectores de corrientes.
El refinamiento cubre semilla y cinco finales, no cada instante de la
transición. El presupuesto anterior por perfil/campaña/disco se conserva.

También se conserva el rechazo del diagnóstico del adaptador: se esperaba
sólo FAST_K como fila vacía de DC, pero BUS también está vacío en la red
posterior con las otras fuentes OFF; su KCL la aporta el VCO al ensamblar.
El diagnóstico se corrigió a filas66/84, sin cambiar ecuaciones. La alias
EXTERNAL_S_TRIGGER→GROUND se restauró sólo en el auditor, con su fallo
KeyError y replay conservados. El contacto nativo ya estaba a0 V.
