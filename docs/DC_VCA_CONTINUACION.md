# Inicialización DC de los VCAs mediante continuación

## Problema y alcance

La [semilla DC completa](DC_GLOBAL_SEMILLA_COMPLETA.md) permitía resolver cutoff máximo, pero el solve global directo desde el centro agotaba Newton al imponer cero en uno o ambos controles VCA. El [barrido histórico](EXTREMOS_CONTROLES_GLOBAL_66.md) conserva esos fallos. El salto durante audio conserva además 18 historiales de capacitores y constituye un problema diferente.

Se añade `circuit66::initial_state_vca_continuation`: una ruta explícita para **preparar un nuevo estado DC**, fuera del plazo de procesamiento de audio. Usa las mismas ecuaciones de SVC-9 Fig. 9-11 (PDF p. 13), Fig. 9-17 (p. 19) y Fig. 9-8 (p. 10), las hipótesis nominales de dispositivos y ambas alternativas R61. No cambia componentes ni leyes de transistor.

## Camino numérico y dominio

La API recibe los 66 voltajes de una semilla finita y la frontera DC solicitada. Su dominio ensayado de fuentes impuestas es `0..=2 V` para `loudness_v` y `q21_base_v`. Este intervalo delimita el inicializador de laboratorio; **no identifica la escala de volumen del Model D ni sustituye el circuito de contorno**. Las otras API conservan su dominio anterior.

1. Resolver las mismas 66 incógnitas con ambas fuentes a 2 V, manteniendo todas las demás fronteras y dispositivos solicitados.
2. Hacer 32 solves DC, llevando cada fuente desde 2 V a su valor solicitado en fracciones `k/32`.
3. En la etapa final usar los valores `f64` originales exactamente. No reconstruirlos mediante `2+(objetivo-2)`, que puede redondear una fuente pequeña a cero.
4. Reconstruir las 17 tensiones de capacitores y C10 desde los terminales del **DC final**, y copiar sus nodos actuales al predictor anterior.

Los **18 capacitores permanecen abiertos** durante todo el camino. No hay Euler, carga transferida ni estado temporal en las etapas. BUS no participa mediante C27 abierto, pero su valor solicitado se usa al reconstruir esa memoria. C10 se inicializa por diferencia de terminales incluso con R14 desconectado, como en la API DC directa.

Cada solve conserva presupuesto 16/16, residual físico <10 pA, eventual igualdad R21 <10 pV y corrección Newton <10 nV. El presupuesto **total de preparación aumenta**: hasta 33 solves, cada uno con su límite. No se presentan las etapas como una sola llamada Newton de 16 iteraciones. Si ambas fuentes ya son 2 V, sólo se hace el solve inicial.

`DcContinuation` informa estado final, cantidad de solves, actualizaciones Newton acumuladas, evaluaciones de residual y máximo KCL físico de las etapas. Sólo se publica el resultado completo al terminar; los errores no publican estados parciales. Todas las matrices, direcciones y nodos siguen siendo arrays fijos.

El ancla de 2 V y las 32 etapas son elecciones **numéricas**, no parámetros sonoros, tiempos de envolvente ni smoothing. No se garantiza cualquier semilla o variante de dispositivos. El inicializador anidado `initial_state` y la API directa `initial_state_from_nodes` permanecen disponibles; la continuación no se invoca automáticamente en ellos ni en `step`.

## Referencia independiente

[`circuit66_vca_dc_vectors.py`](../tools/circuit66_vca_dc_vectors.py) calcula seis blancos: primer VCA a cero, segundo a cero, ambos a cero × R61=200 Ω/200 kΩ. Python parte de su propia solución DC central, usa 66 columnas por diferencias finitas y presupuesto fuera de audio 40/32. Calcula tanto el camino directo como las 32 etapas.

Los seis solves directos Python pasan y llegan a la misma rama que la continuación dentro de 1 µV. No se oculta que el presupuesto Python es mayor que el nativo. Los [vectores](../evidence/circuit66_vca_dc_vectors.json) contienen las 192 raíces intermedias y ambos resultados finales. Máximo KCL final Python 2,37002 pA; máxima corrección final 1,76352 nV, por debajo de los gates fijados.

El [banco nativo](../evidence/circuit66_vca_dc_survey.json) repite los seis blancos con semillas central, +1 mV y −1 mV: **18 intentos**. El solve directo nativo falla en **14/18** con `IterationBudget`; la continuación pasa **18/18**. Se comparan sus 576 puntos intermedios contra las raíces Python, y la API final coincide exactamente con el prototipo de solves DC sucesivos.

| Medida nativa | Resultado |
| --- | ---: |
| Máximo error de nodo, etapas y estados finales | 1,568833 nV |
| Máximo KCL de todas las etapas | 3,82644 pA |
| Máximo KCL del DC final | 0,000430212 pA |
| Actualizaciones Newton por inicialización | 101–168 |
| Evaluaciones de residual por inicialización | 141–247 |
| Solves por blanco a cero | 33 |

La regresión Rust verifica los 18 estados, **las 18 cargas exactas reconstruidas**, predictor sin historia del camino y residual DC. Añade valores fraccionarios solicitados, BUS=0,125 V, R14 desconectado, caso de una sola etapa y rechazos fuera de dominio. La prueba Python regenera exactamente las seis escenas y contrasta caminos directo/continuado.

## Reposo temporal, recursos y límites

Después de cada una de las 18 inicializaciones, el banco mantiene las fuentes solicitadas durante 64 pasos con BUS de 20 mV/100 Hz/48 kHz: **1152 muestras nativas aceptadas**, cero reintentos, máximo KCL 0,103885 pA. Esta prueba comprueba admisión y estado; no es otra integración temporal Python independiente ni una medida de silencio vintage.

Pasan las ocho regresiones globales y heap cero, que ahora incluye una inicialización de ambos VCAs a cero. El [banco de stack](../evidence/circuit66_stack_vca_dc_512.json) ejecuta la continuación en cuatro workers de 512 KiB con ambos R61, seguida de 32768 pasos de la escena nominal con topes R21, reintento forzado y rechazo atómico. Se observan **324–328 KiB comprometidos**, incluidas 24 KiB de guardas. Se descarta el estado de la sonda DC para volver a la escena nominal: el informe declara qué caminos mide. Sigue sin medir el pico exacto ni admitir el host.

Una ejecución local release del constructor, sin otro banco concurrente, observa **2225,4–4009,8 µs** por preparación entre los 18 intentos. Es un rango de observaciones de arranque, no un benchmark estadístico ni una mejora del plazo de audio. Las 33 etapas deben ejecutarse fuera de ese plazo.

La continuación **no corrige el salto de Q21 a cero durante una muestra de audio**. Reemplazar el estado en Note Off por este DC borraría las cargas y cambiaría el circuito. Falta resolver el salto preservando los historiales y modelar el contorno real. Los informes de apagado abrupto fallidos siguen vigentes; no hay cambio en C6 ni admisión C7.

## Reproducción

```powershell
python tools/circuit66_vca_dc_vectors.py
python -m unittest discover -s tests -p test_circuit66_vca_dc_vectors.py
cargo test --release -p rf-d-circuit --test cutoff_ladder_output --test no_alloc
cargo build --release -p rf-d-circuit --example circuit66_admission
./tools/run_circuit66_admission.ps1 -Mode vca-dc -Output evidence/circuit66_vca_dc_survey.json
./tools/run_circuit66_admission.ps1 -Mode stack -StackKib 512 -R21Endpoints -VcaDcContinuation -Output evidence/circuit66_stack_vca_dc_512.json
```

El hash de código/binario del informe identifica lo medido; `source_head` corresponde al commit de partida antes de incorporar el corte.
