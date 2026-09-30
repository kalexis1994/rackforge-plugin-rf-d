# Cantidad de etapas y reproducibilidad de los saltos VCA

## Barrido numérico

La [continuación con cargas fijas](SALTOS_VCA_HISTORIAL_FIJO.md) permite variar una cantidad **numérica** de etapas. No se modifican componentes, ecuaciones, tasa, memorias entrantes, fuentes solicitadas, gates ni presupuesto 16/16 por solve. Se sigue publicando una sola muestra al final.

[`profile_circuit66_vca_stages.ps1`](../tools/profile_circuit66_vca_stages.ps1) ensaya 1, 2, 4, 8, 16 y 32 etapas con el mismo ejecutable release. Cada candidato completo vuelve a comparar los 384 pasos, 66 nodos, 18 memorias, tres jacks y cola contra los vectores Python independientes congelados. Se verifican también identidad de escenas/estímulos y KCL. Gates: 1 µV nodo/capacitor/jack, 1 nA cola, 10 pA KCL; el kernel conserva corrección Newton <10 nV.

| Etapas | Resultado en las seis escenas |
| ---: | --- |
| 1 | `IterationBudget`, segundo VCA/R61=200 Ω, primer apagado |
| 2 | Mismo primer caso fallido |
| 4 | Mismo primer caso fallido |
| 8 | 384 pasos y todos los gates aprobados |
| 16 | 384 pasos y todos los gates aprobados |
| 32 | 384 pasos y todos los gates aprobados |

Los candidatos fallidos se detienen en ese primer rechazo; no se afirma haber completado sus seis escenas. Se conservan los diagnósticos. El `passed=true` del [perfil](../evidence/circuit66_vca_stage_profile.json) corresponde a los candidatos 8/32 contrastados y medidos, no a todos los tamaños del barrido.

## Costo de ocho frente a 32

Se ejecutan barridos de calentamiento excluidos y cinco pares alternados, invirtiendo el orden por pareja. Cada ejecución contiene seis escenas de 64 muestras, con cuatro saltos de fuente, ambos R61 y primer/segundo/ambos VCAs. Se comparan todos los datos numéricos en **cada ejecución medida**.

El reloj por muestra incluye el intento normal rechazado y su eventual continuación. Se suma el costo del kernel para cada escena; quedan fuera construcción de la captura JSON y serialización. Es una medida de kernel en el banco, no de un callback completo del host.

| Medida | 32 etapas | 8 etapas |
| --- | ---: | ---: |
| Media de las medias de seis escenas, cinco ejecuciones | 15776,47 µs | 9708,1433 µs |
| Mayor muestra observada en los pares | 5100,9 µs | 2329,5 µs |
| Bloques que exceden 1333,3 µs | 30/30 | 30/30 |

**−38,4644 %** de costo medio en estas escenas. Los saltos que requieren rescate pasan de 33 solves a nueve, manteniendo todos los historiales y criterios. El camino normal y su política de selección no cambian. Ocho etapas quedan contrastadas para estas escenas nominales; no constituyen una garantía para toda frontera, carga, tasa o hipótesis de dispositivo.

La regresión Rust ahora repite la integración independiente con **8/16/32 etapas: 1152 pasos, 48 rescates**, máximo de nodo 7,149470 nV. Conserva los Jacobianos de los 24 saltos de la política de 32 y las pruebas de publicación atómica. Heap cero incluye apagado/reactivación con ocho y 32 etapas. No se añade un selector automático ni se reduce el presupuesto de Newton para declarar velocidad.

Incluso la mayor muestra de ocho etapas excede el plazo de un bloque completo. C7 sigue fallido y el contorno real continúa pendiente. Esta mejora tampoco reduce el costo de la escena normal sin rescates, medido aparte en el bloque anterior.

## Identidad temporal y variación de arranque

El banco anterior mantenía un gate de **1 pV** entre resultados tras partir de dos arranques DC hechos en contextos distintos. Las semillas diferían 1,332268 fV y, tras los saltos, una comparación llegaba a 1,301182 pV. Ese informe fallido se conserva. No prueba por sí solo que entradas idénticas produzcan salidas distintas.

El nuevo modo `-CommonTemporalState` mide dos cosas separadas:

1. Ejecuta el DC y la continuación DC dentro/fuera del worker, conserva sus nodos reales en `dc_probe_initial_node_v` y observa sus páginas de stack.
2. Para la escena temporal entrega a ambos workers una copia **idéntica del mismo `State` previamente admitido**, incluidos predictor y 18 memorias. Conserva ese punto en `initial_node_v`. No redondea ni modifica el resultado del DC medido; lo descarta explícitamente para este experimento de entrada fija.

El [informe de estado temporal común](../evidence/circuit66_stack_vca_jump_common_state_512.json) completa **32768 pasos** en cuatro workers de 512 KiB, ambos R61, topes R21, dos intervalos de fuentes VCA en cero, restauraciones, continuación DC, reintento forzado y rechazos atómicos. Las dos comparaciones finales dan **0 V de diferencia**, dentro del gate de 1 pV. Se observan **328 KiB comprometidos**, incluidas 24 KiB de guardas, y cuatro rescates temporales por worker; se usa la política de 32 etapas en esta prueba de stack.

La sonda DC conserva su diferencia inicial de 1,332268 fV. No se atribuye una causa, no se sustituye el informe anterior por uno aprobado y no se reclama identidad universal de los inicializadores. La nueva comprobación confirma reproducibilidad temporal para **entradas completas iguales** en este banco y contexto. Quedan abiertos la sensibilidad del arranque, el pico exacto de stack y la admisión de recursos en RackForge.

## Criterios reutilizables para RACE

- La continuación de una ecuación temporal debe mantener la memoria entrante inmutable; actualizar capacitores entre etapas cambia el sistema físico.
- Reducir etapas exige contrastar las raíces finales, cargas, corrientes y costo. Un tamaño válido de API puede ser insuficiente para converger.
- Comparar reproducibilidad con un estado completo idéntico; ensayar la sensibilidad a semillas como otra propiedad y conservar sus diferencias.
- Separar tiempo de kernel, captura de laboratorio y plazo real del host. Una reducción de costo no convierte un gate fallido en aprobado.

## Reproducción

```powershell
cargo build --release -p rf-d-circuit --example circuit66_admission
./tools/profile_circuit66_vca_stages.ps1 -Output evidence/circuit66_vca_stage_profile.json -Runs 5
cargo test --release -p rf-d-circuit --test cutoff_ladder_output --test no_alloc
./tools/run_circuit66_admission.ps1 -Mode stack -StackKib 512 -R21Endpoints -VcaDcContinuation -VcaJump -CommonTemporalState -Output evidence/circuit66_stack_vca_jump_common_state_512.json
```

El perfil incluye hashes de kernel, banco, oráculo, script y ejecutable. Los relojes no se regeneran exactamente; los vectores numéricos sí tienen sus propias regresiones congeladas.
