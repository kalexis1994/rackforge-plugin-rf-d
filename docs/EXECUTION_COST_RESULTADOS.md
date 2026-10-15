# Perfil actual y ensayo de soporte pivote

## Qué se midió

[Contrato del perfil](EXECUTION_COST_PROTOCOLO.md) y
[contrato del cambio](SUPPORT_PIVOT_PROTOCOLO.md), fijados antes de ejecutar.
Mismas ecuaciones/documentación CA3046/SVC-204D, puertos, cargas, estados
HIGH/LOW y rama nominal 40–100 ms. No se cambió ninguna constante audible.

Las copias instrumentadas salen de sustituciones exactas sobre los motores
existentes. El [perfil](../evidence/execution_cost_profile01.json) conserva
GRID/ROOT/SOLVER/AFFINE y estados finales idénticos a sus controles. Registra
también salidas por error y los cuatro replays por rama. Los timers son
inclusivos: no sumar padres con hijos ni restarles benchmarks de otra corrida.
La instrumentación puede cambiar inlining/costo; no es un banco de admisión.

| Tramo inclusivo | Directo, s | Afín, s |
| --- | ---: | ---: |
| Evaluación con J, 99.934 / 101.712 llamadas | 5,470919 | 8,080233 |
| Evaluación residual, 68.200 / 74.136 llamadas | 2,254492 | 4,303924 |
| Preparación, 49.967 / 50.856 llamadas | 6,232122 | 12,179957 |
| Solve directo, incluida preparación | 7,256833 | — |
| Solve afín, después de preparar | — | 1,202750 |
| Advance completo, incluidos replays/rechazos | 16,306724 | 27,672568 |

En el directo, factorizar ocupa 3,634893 s dentro de preparación; la
corrección triangular 0,866709 s y el backward 0,142931 s están dentro del
solve. La resta preparación−factores incluye ensamblaje y todo otro trabajo
de initialize: no identifica por sí sola el costo de cada scan.

Dentro de la preparación afín: CSR físico 3,996129 s, álgebra local
1,055455 s, proyección retenida 1,395021 s y preparación reducida 5,693847 s.
Dentro de sus evaluaciones full/residual: kernel 1,283313 s, padre
8,653087 s, validación 0,084947 s y transferencia 0,702510 s, cada uno con
175.848 llamadas. Son tramos medidos hasta completar su asignación; no
cubren el retorno exterior de Stage. El padre es el tramo combinado de
dispositivos, cargas y ensamblaje, no una identificación de copias de memoria.

La variante condensada sigue teniendo más trabajo de preparación y
evaluación que el directo en estas corridas. No se atribuye esa diferencia
a una única causa. El siguiente ensayo usa el directo como base.

## Cambio probado: soporte actual del pivote

El [solver candidato](../crates/rf-d-circuit/src/support_pivot_solver.rs)
lee cada fila pivote después de swaps y fill, guarda sus columnas no nulas
en orden ascendente y actualiza sólo esas columnas tanto en el interior
como en las reacciones de los cuatro puertos. Arrays fijos, sin cache de
soporte entre puntos. Ensamblaje, selección de pivotes, escalas y guards
permanecen iguales. Se conservan capacidades, backward ≤1e-11 y refinamiento.

[Prueba nativa](../evidence/support_pivot_native01.json):

- 24 pares/48 etapas; 1.336.704 coeficientes físicos idénticos.
- 192 direcciones idénticas a la referencia estructurada y dentro del gate
  del solve completo refinado; fracción máxima 0,972279.
- 33 rechazos con recuperación exacta, 24 enlaces legales nuevos comprobados
  también con solve, una cancelación y un caso sintético de swap con fill.
- Dos trayectorias 64/32 µs: GRID/ROOT/SOLVER y estados finales idénticos al
  directo. Pasan voz reservada y refinamiento, ocho replays, diez rechazos
  atómicos y heap cero. Backward local final máximo 9,972265e-12.
- [Auditoría independiente](../evidence/support_pivot_audit01.json): 5712
  filas originales, máximos 0,719007 pA y 0,325050 nV frente a 20 pA/2 nV.

Costo sin timers internos, 32 µs, directo fresco y toolchain/rlib/flags
iguales: **17,541832 s frente a 16,639246 s**, ratio **1,054244**. Falla el
gate **0,90** y cuesta 5,42 % más en esta medición. El intento queda
**rechazado** y el directo anterior permanece activo. Conservar menos
multiplicaciones no demuestra menor costo: este cambio añade inspección,
listado y accesos indirectos. El banco no aísla cuál de ellos explica la
regresión ni compara generación de instrucciones.

## Cierre y siguiente bloque

[QA global](../evidence/execution_cost_tests01.json) protege las fuentes
previas y los 8769 inputs privados; 255 tests Rust heredados por identidad,
sin reejecutarlos. Se ejecutaron dos ramas instrumentadas, un control
directo fresco y dos ramas del candidato. Fallo de costo con imágenes de
fuentes/entrada y replay sin cambios antes de retirar binarios. Un único
tmp/lab-current vacío, sin WAV, Cargo, rlib, cache o muestras nuevas.
Recibos por commit/ruta/SHA e imágenes de cambios, presupuesto 8 MiB sin QA.
Sin admisión RT, parecido audible demostrado o ampliación de dominio.

Prioridad siguiente: ensamblar el sistema directo desde incidencias del
stamp actual, preservando acumulación DC/masa y coeficientes, para reducir
materialización y recorridos repetidos de matrices densas. Usar soporte
derivado del grafo documental y coeficientes actuales, con detección de
enlaces nuevos y cancelaciones. Volver a voz completa, auditoría y costo;
no continuar con otra condensación local ni con listados de pivote variantes
sin una razón medida. El perfil aún no demuestra cuánto se ahorraría.
