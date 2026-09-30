# Saltos VCA con continuación numérica e historial fijo

## Ecuación de una muestra

El [arranque DC por continuación](DC_VCA_CONTINUACION.md) abre capacitores y reconstruye sus cargas. No puede usarse para resolver Note Off. Aquí se conserva la ecuación temporal global de SVC-9 Fig. 9-11 (PDF p. 13), Fig. 9-17 (p. 19) y Fig. 9-8 (p. 10), con las hipótesis nominales y ambos R61.

Para cada capacitor se resuelve `I=C/dt·(V_n-V_anterior)`. Las **18 memorias entrantes**, `dt`, BUS y las otras fronteras permanecen fijas durante toda la llamada. Una continuación sólo cambia la semilla del sistema no lineal: sus etapas no representan instantes de audio, no dividen `dt` y no actualizan cargas.

`circuit66::step_vca_continuation` recibe la fuente inicial numérica de los dos controles y un número de etapas `1..=32`. Las fuentes iniciales/solicitadas deben estar en `0..=2 V`, dominio de laboratorio, sin identificar la escala del instrumento. Se calcula el punto con las fuentes iniciales y luego se interpolan hacia el blanco. La etapa final usa exactamente la frontera solicitada.

Cada solve conserva el presupuesto 16/16, KCL <10 pA, igualdad R21 <10 pV cuando corresponde y corrección Newton <10 nV. El presupuesto total de una muestra aumenta hasta 33 solves. Una etapa fallida no publica nodos, predictor ni carga; sólo el último punto convergente publica **una** actualización del estado. `previous_node_v` conserva los nodos reales de la muestra anterior.

`TransientContinuation` informa solves, actualizaciones Newton y máximo KCL entre etapas; el resultado contiene evaluaciones de residual de la continuación y salidas físicas de la frontera final. Si el caller intentó antes `step`, esas evaluaciones fallidas no están en ese contador. El banco mide el tiempo conjunto del intento normal y la continuación.

No se selecciona automáticamente en `step`. El banco la llama sólo tras un rechazo atómico del camino normal, con las fuentes de la muestra anterior como ancla. No añade smoothing, un mute digital, un contorno, resistencias artificiales ni publicación de las etapas.

## Contraste y reactivación

Se ensayan seis escenas: primer VCA, segundo o ambos × R61=200 Ω/200 kΩ. Cada escena tiene 64 muestras: ocho al centro, 16 a cero, 16 de restauración, otros 16 a cero y ocho de restauración. BUS=20 mV/100 Hz, 48 kHz, R14=25 kΩ, cargas nominales J7 de 32 Ω y R21 interior. Hay cuatro saltos por escena, sin rampas temporales.

El camino normal falla en **16 muestras** de los cuatro casos que modifican Q21, incluyendo apagado y restauración. La continuación de 32 etapas las resuelve, para **384 muestras completas**. La reactivación puede empezar con una semilla que viola el límite exponencial del BJT a la nueva fuente; no se suprime esa comprobación ni se recorta el transistor.

[`circuit66_vca_jump_vectors.py`](../tools/circuit66_vca_jump_vectors.py) integra sus propios DC e historiales, con 66 columnas por diferencias finitas y presupuesto por solve fuera de audio 40/32. Los datos nativos aportan estímulos y comparaciones, nunca semillas/cargas. Los apagados directos Python pasan; sus ocho reactivaciones requieren un camino numérico de **64 etapas**, independiente de las 32 nativas, manteniendo el historial fijo.

| Máximo Python frente al prototipo nativo | Resultado |
| --- | ---: |
| Error de los 66 nodos | 7,150162 nV |
| Error de las 18 memorias en V | 0,291437 nV |
| Error de jack | 0,0152569 nV |
| Error de cola | 2,61225 aA |
| KCL del oráculo | 1,41484 pA |
| Corrección Newton del oráculo | 7,14972 nV |

Se mantienen los gates fijados antes: 1 µV de nodo/capacitor/jack, 1 nA de cola, 10 pA KCL y 10 nV de corrección. Pasan los 384 puntos. La prueba Python regenera el archivo exactamente. La regresión Rust vuelve a integrar la escena y compara nodos, cargas, salidas y cola; contrasta las 66 columnas del Jacobiano en los 24 saltos y verifica que una continuación insuficiente de una etapa falla sin cambiar estado.

La [API frente al prototipo](../evidence/circuit66_vca_jump_trace_comparison.json) conserva **35730 f64 idénticos en bits** y 774 escalares de estados iniciales y filas completas, excluyendo tiempos/entorno. La [ruta normal](../evidence/circuit66_jump_api_default_trace_comparison.json) también conserva sus 23224 f64 y 308 escalares en 96 capturas de apagado. Sus cuatro fallos abruptos siguen presentes: no se oculta la falta de selección automática.

## Recursos y fallos retenidos

Pasan las nueve regresiones globales y heap cero; esta última incluye apagado y reactivación por la nueva API. Cinco pares alternados de [costo normal](../evidence/circuit66_vca_jump_normal_cost.json) dan 2939,72→2941,76 µs/bloque, +0,0694 %, sin mejora declarada. Candidato máximo 4871,2 µs, 640/640 bloques fuera de plazo y cero fallos. Esa escena no invoca la continuación.

En la captura de saltos se registra tiempo de kernel acumulado por escena y máximo por muestra, incluyendo el intento fallido y el rescate. Hay varios milisegundos por salto y los seis bloques exceden 1333,3 µs. La exactitud numérica no admite esta ruta como motor de audio. El siguiente corte debe estudiar cantidades de etapas con los mismos gates.

El [banco Win64 con saltos](../evidence/circuit66_stack_vca_jump_512.json) completa **32768 muestras** en cuatro workers de 512 KiB, con topes R21, continuación DC, fuentes VCA en cero durante dos tramos de 1024 muestras, restauraciones, reintento forzado y rechazo atómico. Se observan 324–328 KiB comprometidos y cuatro rescates temporales por worker.

**El informe de stack no pasa su gate separado de identidad de 1 pV**: una comparación de arranque dentro/fuera del worker alcanza 1,301182 pV tras la escena; las semillas DC ya difieren 1,332268 fV. No se relaja ese gate ni el del circuito. La diferencia está por debajo del gate de nodos de 1 µV frente al oráculo, pero no se atribuye una causa sin evidencia.

Se conservan el [primer fallo](../evidence/circuit66_stack_vca_jump_initial_failure.json), el [diagnóstico completo](../evidence/circuit66_stack_vca_jump_diagnostic.json) y el [intento de inicializador compartido](../evidence/circuit66_stack_vca_jump_shared_initializer.json). Un helper común `inline(never)` con argumentos `black_box` no eliminó la diferencia inicial; ese cambio de banco se descartó. El runner sigue devolviendo error para el gate de identidad. Capacidad de stack observada no equivale a admitir todos los gates.

No se repite el estrés completo de 752384 muestras ni se identifica el contorno físico. C6/audio vintage y C7/host siguen pendientes.

## Reproducción

```powershell
cargo build --release -p rf-d-circuit --examples
./tools/run_circuit66_admission.ps1 -Mode vca-jump -VcaStages 32 -Output evidence/circuit66_vca_jump_native.json
python tools/circuit66_vca_jump_vectors.py
python -m unittest discover -s tests -p test_circuit66_vca_jump_vectors.py
cargo test --release -p rf-d-circuit --test cutoff_ladder_output --test no_alloc
# Conserva el diagnóstico y devuelve error por el gate de identidad:
./tools/run_circuit66_admission.ps1 -Mode stack -StackKib 512 -R21Endpoints -VcaDcContinuation -VcaJump -Output evidence/circuit66_stack_vca_jump_512.json
```

La integración Python compara el prototipo congelado anterior, preservando su hash de entrada. El contraste exacto verifica la API posterior. Los informes de builds incluyen hashes de código/binario y el commit de partida.
