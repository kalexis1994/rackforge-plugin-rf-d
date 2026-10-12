# Rama muerta FAST_K y el auditor229

Antes de la reparación del oráculo01, 2026-10-12. Rechazo y replay:
`numpy.linalg.LinAlgError: Singular matrix`. Con final decay ON el grafo
Python elimina CR4 y la resistencia LHC_FAST_DECAY; al conservar FAST_K
en el codec229 su fila queda vacía. El nativo conserva la resistencia
1500 Ω de FAST_K a RESET_DRIVER y elimina sólo CR4, exactamente como
[C2 cargado](VOZ_C2_CARGA_PROTOCOLO.md). FAST_K=RESET_DRIVER resuelve cero
corriente, sin almacenamiento ni epsilon. El nodo sobrante es equivalente
a su eliminación algebraica; debe tener ecuación si permanece en el codec.

Se restaura esa rama sólo en el adaptador del auditor ON; OFF ya la incluye.
No se cambia el grafo histórico ni el nativo medido, la ley de carga,
las tolerancias, el calendario o los archivos privados. El Jacobiano FD
se calcula sobre la misma KCL corregida. Se exigen los mismos datos y
SHA antes/después, la fuente fallida conservada y sustitución exacta.
