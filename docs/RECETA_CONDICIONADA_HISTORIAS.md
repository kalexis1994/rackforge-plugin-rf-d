# Corrección del binding de historia por resolución

El [protocolo inicial](RECETA_CONDICIONADA_PROTOCOLO.md) propuso usar A/D,
las historias nominales2 µs, con las dos resoluciones. El primer recorrido
2 µs coincidió por bits. El segundo,1 µs, completó el mismo calendario pero
falló el gate J7: su condición inicial publicada es propia de1 µs.
La diferencia máxima de los cinco observables fue3.9657e−11 en sus unidades
de tensión; esa cercanía no permite heredar identidad.

Conservar native01, biblioteca01, estados, fuentes y replay de adaptador.
Antes de reparar, repetir el mismo ejecutable/receta1 µs y comparar los
cuatro exports completos por bytes; el rechazo vuelve a ocurrir.
[Replay nativo sin cambios](../evidence/voice_conditioned_recipe_rejection_replay01.json).

## Receta corregida, antes de la segunda campaña

Cada combinación decay/resolución selecciona su historia propia: ON2(A),
OFF2(D), ON1(A_FINE), OFF1(D_FINE). Los458 bits de cada historia estaban
publicados en el primer grid de
[la trayectoria Schur](../evidence/voice_schur_chain_trajectory01.json).
Contrastar cada array fino con el checkpoint admitido propio1 µs y comprobar
reloj4423942144, settings524288/20, propuesta1024. No son capturas externas.

Añadir los dos arrays al prefijo intacto de la nueva receta; no modificar
`tests/support/conditioned_seed.rs` histórico. Registrar las fuentes anteriores
por base64/SHA y el diff del selector. La regresión comprueba ahora las cuatro
historias correctas. Biblioteca02 y cuatro recorridos frescos; mismos gates
por bits, ecuaciones, eventos, cargas, recursos y duración. Repetir ON1.

No recondicionar el estado2 µs a mano, sustituir cargas, relajar tolerancias
o modificar la referencia para aparentar identidad. La condición inicial
es parte del experimento junto con reloj y propuesta.
