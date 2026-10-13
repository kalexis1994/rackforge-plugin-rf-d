# Condensar el contorno cargado de placa 2

2026-10-13, antes de medir. Base919cde5 y QA3283 fuentes/7778 privados.
Una intervención: añadir al Schur en sitio el bloque de29 incógnitas
200..228 en ambas etapas Radau.58 correcciones internas, puertos165/394,
exterior272. Conservar los128 interiores LM741 y todas las458 correcciones.

## Frontera y derivación eléctrica

La implementación revisada de [placa 2](../tools/contour_closed_driver.rs)
conecta su incógnita29 a loudness por R59=68 kΩ, entre incógnitas3/29.
El [ensamblaje admitido](../tools/joint_schur_inplace_kernel.rs) transforma
29→165,0..28→200..228 y retira la anterior carga impuesta de68 kΩ.
Sus fuentes ideales quedan en el stamp, con sus retornos auditados.
Esto reduce una frontera numérica del modelo operativo; no declara
identificados los transistores reales ni completa la placa 2 vintage.
La procedencia y las incertidumbres eléctricas son las de ese ensamblaje.

C2=10 µF, C7=0.1 µF, C4=10 nF y las cargas Q25/Q15 permanecen en J y Q.
El bloque dinámico incluye ambas etapas y sus acoplamientos de masa.
La única frontera con el resto del Jacobiano debe ser165/394, en ambas
direcciones; rechazar cualquier acoplamiento no declarado. No congelar
loudness ni reemplazarlo por una fuente. Historia HIGH/LOW fija en Newton.

Para cada J: factorizar A58, calcular W=A58⁻¹B58×2, restar C2×58W al
Schur exterior y C2×58A58⁻¹bI al RHS. Resolver exterior y reconstruir
dI=A58⁻¹bI−WdP. Restituir las58 correcciones antes de evaluar la raíz.
No cachear factores entre J, trials o pasos. Sin unsafe/heap en el solver.
Se conservan escalas, pivote1e-12, capacidad4096, tres refinamientos y
gate mixto1e-11, con τ=2 nV/2 pA por tipo de incógnita.

## Experimento finito

84 parejas congeladas, ON/OFF,2/1 µs, coarse/mid/end. Control de costo:
Schur en sitio actualmente admitido; LU completo conserva el contraste
independiente y la identidad del packet. Cinco rondas alternadas tras
warmup separado. Mediana>1; si1<mediana≤1.10, una única confirmación del
mismo ejecutable/packet y ambas medianas>1. Si falla, conservar el
resultado y seguir con el control admitido, sin otra variante en este bloque.

Si supera utilidad: banco lineal de cada resolución, residuo independiente
Decimal100≤1e-11, contraste contra LU≤2 nV/2 pA, memoria y puertos LM741
con gates previos. Reejecutar grafo no lineal; cercanía no hereda ecuaciones.
Regresiones adicionales: dos etapas del contorno cargado, pivote local,
singularidad local, acoplamiento ajeno en cada dirección, entre bloques,
respuesta después de reinicializar, y masa cruzada entre etapas.

Un banco aprobado aún no admite trayectoria. El recorrido posterior reutiliza
8.438→11.442 ms desde sus cuatro historias/propuestas propias y exige el
oráculo temporal vigente: LTE, checkpoints, cargas, corrientes, balances,
resets, replay y rollback; contraste229 al mismo reloj con el Schur admitido
y LU. No cambiar duración, física, audio, tolerancias o reglas de publicación.

Compilar120 s, banco/auditor600 s, perfil990 s, campaña4000 s; stack32 MiB,
64 MiB privados nuevos, reserva1 GiB.248 tests Rust heredados por identidad.
Conservar cualquier fallo y replay antes de reparar. Laboratorio condicionado,
sin promoción DSP/RT ni afirmación de fidelidad física.
