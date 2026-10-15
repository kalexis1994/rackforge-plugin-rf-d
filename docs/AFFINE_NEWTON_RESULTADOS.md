# Corrección física completa desde una preparación reducida

## Cambio y alcance

El [contrato previo](AFFINE_NEWTON_PROTOCOLO.md) conserva CA3046/SVC-204D,
118 nodos físicos por etapa, 111 coordenadas retenidas, cuatro memorias
internas del ladder, cinco puertos, cargas cruzadas e historial HIGH/LOW.
No añade constantes audibles ni cambia leyes eléctricas, arranque o CV.

El candidato forma el Schur desde los J/M físicos del punto actual. Conserva
el residual de las siete variables eliminadas: `p=A⁻¹bz`, lado derecho
retenido `by−D·p` y reconstrucción `dz=p−A⁻¹C·dy`. Permite varios RHS con
los mismos factores, incluyendo refinamientos físicos. Un préstamo exclusivo
liga etapas, factores y CSR; no reutiliza factores entre puntos distintos.

La salida verifica la dirección contra el operador físico 236 mediante
residual compensado y backward ≤1e-11, con tres refinamientos como máximo.
La corrección física de convergencia sale de esa misma preparación. Se
retira el segundo solve completo de la ruta candidata; sigue disponible
únicamente como referencia de laboratorio. También se elimina la proyección
111×111 intermedia del Stage. Newton conserva 1 pA/2 nV y el estimador
examina todos los nodos físicos reconstruidos.

## Verificación numérica

[Recibo nativo](../evidence/affine_newton_native01.json):

| Comprobación | Resultado |
| --- | --- |
| Etapas/pares originales | 48 / 24 |
| Direcciones contra solve completo | 576; fracción máxima del gate 0,309237 |
| Coeficientes físicos contra fórmula original | 1.336.704, iguales |
| Rechazos de RHS/matriz y reintentos exactos | 44 / 93 reintentos, contando replays válidos |
| Overflow de normalización con productos finitos cancelados | rechazado |
| Preparación común a los 24 RHS de cada par | comprobada |
| Backward físico máximo local después de refinar | 9,921047e-12 |
| Trayectorias 40–100 ms, KEY OFF 75 ms | 64/32 µs; 481 observaciones cada una |
| Replays / rechazos atómicos / heap del candidato | 8 / 10 / 0 |

Las direcciones incluyen 14 incidencias algebraicas, ocho puertos, el
residual real y una mezcla en las 236 filas. Hay 56 refinamientos físicos
locales; el gate se verifica también sobre cada dirección reconstruida.
Se prueban singularidad, masa en z, enlace fuera del contrato, capacidad,
no finitos y overflow. Cada rechazo de preparación se sigue con un retry
válido exacto sobre el mismo workspace. Se conserva un enlace nuevo legal.

Los gates frente al directo, voz reservada y refinamiento temporal pasan.
Error J7 RMS frente al directo: 1,928637e-6 y 1,240670e-7 relativos. Newton
llega a 1,996898 nV frente a 2 nV, todavía con margen pequeño. El candidato
acepta pasos mínimos observados de 0,25 µs, frente a 1 µs en los controles;
5340/5345 pasos frente a 5280. La trayectoria ya no es idéntica byte a byte.
No se amplía el dominio autorizado por las leyes o por MIN_DT_S.

Las estadísticas incluyen replays: 50.816/50.856 preparaciones para cada
trayectoria, 50.817/50.859 RHS reducidos y 1/3 refinamientos físicos. No son
cantidades de pasos aceptados. Máximo backward físico final 9,989057e-12.

[Auditoría independiente](../evidence/affine_newton_audit01.json): 24 pares,
5712 filas del grafo original, incluyendo Amount y estrella resistiva del
VCO. Máximos 0,719007 pA y 1,677321 nV; pasan 20 pA/2 nV. Reevalúa estas
etapas; no produce una nueva trayectoria original de 250 nodos.

## Costo: candidato rechazado

Mismo compilador/rlib/flags, controles frescos 32 µs y medición sin timers
internos. Los segundos acumulan procesamiento de una rama de 60 ms,
excluyendo los replays exactos de la medición principal.

| Motor | Segundos |
| --- | ---: |
| Directo activo | 17,042172 |
| Unión experimental anterior | 27,829742 |
| Nueva corrección afín | 27,403263 |

Ratio frente al directo **1,607968**, superior al gate **0,90**. Frente a
la unión anterior: 0,984675, diferencia pequeña de una medición única;
no demuestra una mejora estable ni aísla causalmente cada cambio.
**El directo permanece activo.** Menos factorizaciones no bastó para
compensar el trabajo añadido. No hay admisión RT ni evidencia de parecido
audible con una unidad física.

El [perfil separado del predecesor](../evidence/affine_newton_profile01.json)
mide llamadas completas: dirección reducida 7,005680 s / 49.873 llamadas,
dirección original 2,706435 s / 15.920 llamadas. Incluye preparación,
refinamiento/reconstrucción y replays. Sus GRID/ROOT/SOLVER son idénticos
al control anterior. No mide sólo la factorización ni puede restarse
directamente del benchmark principal, que excluye replays. No es un banco
de admisión. Retirar el solve original por sí solo no explica todo el costo.

## Evidencia, almacenamiento y continuación

El fallo de costo conserva las fuentes, entrada y replay sin cambios antes
de retirar ejecutables. Las fuentes inmutables se identifican por commit,
ruta y SHA; las nuevas/editadas tienen imágenes incorporadas. El recuperador
comprueba SHA del blob y materialización exacta o LF→CRLF explícita. No
anida imágenes de recibos históricos. Presupuesto original de recibos 8 MiB,
excluyendo QA. `tmp/lab-current` queda vacío; sin WAV, Cargo, rlib o inputs
privados de sonido nuevos. [Cierre global](../evidence/affine_newton_tests01.json).
Los 255 tests Rust previos se heredan por identidad; no se reejecutaron.

Siguiente: localizar el costo del candidato actual separando evaluación
residual/J, preparación Schur/CSR y solve/refinamiento. Comparar esa
distribución con el directo antes de otra transformación. Priorizar el
camino activo como base de ejecución si la reconstrucción local sigue
costando más; conservar este candidato como referencia de equivalencia.
Mantener puertos, cargas, 1 pA/2 nV y costo ≤0,90; evitar otra cadena de
certificados locales sin regresar a una medición de voz completa.
