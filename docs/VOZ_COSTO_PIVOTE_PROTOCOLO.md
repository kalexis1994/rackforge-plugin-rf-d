# Costo de la voz y pivotes exactamente nulos

Base0a02e77, antes de medir; conservar3528 fuentes/8169 privados. Rlib
decay-voice02 y física vigentes. Laboratorio aislado: derivar kernel de
decay_voice y su solver por transformación explícita, sin cambiar producción
hasta gates de utilidad y trayectoria. Sin rlib/Cargo/cache/SPICE nuevos
en el laboratorio. Stack32 MiB; reserva1 GiB, privados≤96 MiB.

## Banco y perfil

78 pares:54 coarse/mid/end seleccionados a1 kΩ de la campaña16 ms y24 pares
de los ocho accepted nominales a100 kΩ. Historial propio de cada1/2 µs;
conservar old HIGH/LOW, h, parámetros y1834 f64 esperados por par. Nominales
incluyen iteraciones/trials capturados; en los seleccionados a1 kΩ esos dos
contadores se comparan entre ejecuciones actuales, sin atribuirlos al export
histórico que no los incluía. Scalar h en segundos, clocks enteros originales.

Perfil instrumental separado: step, initialize, parts, joint_parts, preparar
Schur, factores LU64/58/132/140, RHS por tamaño, soporte, corrección y residual.
Tiempos son anidados, no sumarlos como fases disjuntas. Relojes y atomics sólo
en copias offline del perfil; comprobar todos los bits antes de interpretar
tiempos. No es benchmark de deadline o cobertura de todo el dominio.

## Candidato y gates

LU escalado: omitir división abs(a[row][col])/scale[row] sólo cuando a es
exactamente0, antes de comparar score>best. Con scale positiva, score0 no
puede mejorar best inicial0; orden y desempate quedan iguales. No epsilon,
descartar cargas/puertos, reducir masa, reutilizar factorizaciones entre
iteraciones o modificar BACKWARD_GATE/MAX_REFINEMENTS. Conserva validación
de matriz finita, soporte permitido, singularidad y refinamiento original.

Kernel sin instrumentación de identidad y kernel candidato comparados con
rlib original en todos los pares/1834 campos y contadores. Medir5 rondas
con orden alternado, mismo executable/proceso/banco. Gates de utilidad:
mediana de tiempo step candidato≤.90·baseline, y ninguna ronda más lenta
que1.05·baseline. El perfil informa mecanismo, no acredita utilidad por sí
solo. Si falla, guardar resultado sin promover optimización.

Comprobar también errores: matrices nula/no finita, RHS no finito, soporte
fuera de puertos, pérdida de pivote y overflow del solve; mismo tipo de
rechazo, sin resultado publicable. No convertir un rechazo en fallback.

Si pasa utilidad: campaña pareada desde cada entrada a1 kΩ en28.442 ms,
4 ms propios y cortes.8 ms. Avanzar baseline y candidato con mismo target;
comparar cada Accepted completo, estado, observables, reloj y propuesta por
bits; errores son atómicos. Exportar baseline/candidato separados y comparar
STEP/OBS/GRID del prefijo4 ms de campaña anterior. Estados en los cinco
cortes, checkpoints y9 integrales orientadas deben coincidir; no sólo J7.
La igualdad del export permite heredar ecuaciones correspondientes ya
admitidas, sin adjudicar nueva auditoría independiente de todos los solves.

## Promoción y escucha

Promover familia explícita del motor sólo si pasan banco/costo y recorrido
pareado; nominales anteriores quedan intactos. Validar generación fuente,
ABI lógico/checkpoint, rlib nueva y repetición del recorrido promovido antes
de seguir duración nueva. Separar corpus medido, prefix/audio heredados y
nueva duración realmente simulada. Se hereda WAV36 ms por bytes si su
trayectoria y renderer siguen idénticos; no inventar audio más largo.

Compilar cada caller≤120 s; perfil/banco≤300 s; campaña pareada≤900 s por
resolución y≤1900 s total. Comparación portable promovida≤600 s, oráculo/
QA≤600 s. Historial de255 tests Rust y2 definiciones Python anterior por
identidad; no reejecutarlo sin riesgo/gate concreto. Contar checks nuevos
aparte. Preservar fallo y replay antes de corregir. Sin heap/deadline/uso
máximo de stack nuevos medidos, fidelidad física, voz completa o RT.
