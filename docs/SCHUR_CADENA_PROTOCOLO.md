# Condensar filtro/VCA conservando BUS y control

2026-10-13, antes de medir. Base7545506; QA3313 fuentes/7828 privados.
Una intervención: añadir la cadena cargada al Schur admitido del contorno.
La [frontera inspeccionada](../evidence/voice_schur_chain_frontier01.json)
contiene 132 correcciones: nodos133..199 salvo165, ambas etapas Radau.
Retener BUS12 y base Q18/165 en ambas etapas: puertos12/165/241/394.
Exterior272→140, interiores totales318 y reconstrucción de458 correcciones.
Estado físico229 HIGH/LOW conservado; no eliminar memoria del integrador.

## Procedencia eléctrica y derivación

SVC-9 Fig. 9-11 p. 13 (placa4), Fig. 9-8 p. 10, Fig. 9-17 p. 19
(cadena/panel), tablas7-8 pp. 30–31 y SVC-204D §2.9/2.10 pp. 12–14.
[Derivación cargada](CONTORNO_CADENA_94_Y_ESTABILIDAD.md) y
[ensamblaje conjunto](../crates/rf-d-circuit/src/joint_voice.rs).
Conservar sus hipótesis, designadores conflictivos y fronteras impuestas.
No añadir parámetros físicos ni extender su identificación vintage.

El bloque incluye ladder, recuperación, VCAs, salida y sus masas, cargas
de dispositivo y fuentes de historia. BUS conserva el acoplamiento al VCO.
Base Q18 queda exterior y conecta también al contorno por R59=68 kΩ:
no condensar ese terminal en ninguno de los dos bloques independientes.
No imponer una onda/voltaje de control o reemplazar cargas por shunts.
Verificar ambos sentidos de todo acoplamiento; rechazar los ajenos.

Para cada J, factorizar A132, W=A132⁻¹B132×4; sumar la contribución
−C4×132W al exterior y −C4×132A132⁻¹bI al RHS. Resolver exterior140 y
reconstruir dI=A132⁻¹bI−WdP. Conservar también interiores64/64/58,
sus respuestas a puertos y el orden previo de sus contribuciones.
Pivote escalado1e-12, capacidad4096, máximo3 refinamientos, gate mixto1e-11
y τ=2 nV/2 pA por tipo de incógnita. Sin cache entre J/trials, fallback,
unsafe o heap nuevo en el solver. Historia fija hasta publicar el conjunto.

## Experimento finito y decisión

84 parejas congeladas ON/OFF, máximos2/1 µs, coarse/mid/end. Control
pareado de costo: Schur con contorno admitido. LU completo comprueba
el packet y candidatos independientemente. Warmup separado, cinco rondas
alternadas. Utilidad mediana>1; si1<mediana≤1.10, una única confirmación
con el mismo ejecutable/packet y ambas medianas>1. Si falla, conservar
el negativo y usar el control admitido; no explorar otra variante aquí.

Si pasa utilidad: banco de todas las resoluciones lineales, residuo de
filas originales Decimal100≤1e-11 y contraste LU≤2 nV/2 pA. Memorias/
corrientes LM741 mantienen los gates previos. Reejecutar las38472
ecuaciones de las84 raíces; cercanía no hereda ecuaciones. Regresiones
de cadena cargada en dos etapas, masa cruzada, puertos compartidos con
contorno, pivote/singularidad local, acoplamientos extraños, capacidad,
finitud, presupuesto de refinamiento y recuperación del workspace.

Antes de admitir, cuatro recorridos propios8.438→11.442 ms, mismo reloj,
historia/propuesta, parámetros y controlador. Grafo/FD/Q Decimal100,
cargas, corrientes, balances, eventos, restores y rollback; comparar229
coordenadas con el Schur con contorno y LU, gates2 µV/2 nA, resets/periodo
10 ns. No cambiar tolerancias, duración o reglas de publicación.

Compilación120 s, banco/auditor600 s, perfil990 s, campaña4000 s;
64 MiB nuevos privados, reserva1 GiB, stack32 MiB.248 tests Rust heredados.
Preservar fallo y replay antes de reparar. Laboratorio condicionado;
sin audio/duración nuevos, contorno desde silencio, DSP/RT o fidelidad física.
