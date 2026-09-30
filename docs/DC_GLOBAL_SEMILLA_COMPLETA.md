# DC global con semilla completa y criterio de voltaje

## Problema observado

El [barrido de controles](EXTREMOS_CONTROLES_GLOBAL_66.md) encontró arranque en frío fallido con cutoff máximo. `initial_state` requería primero resolver la cadena anidada; ese solve podía agotar su presupuesto antes de intentar las 66 ecuaciones simultáneas.

Un primer contraste DC con semilla completa también encontró **31,5344 µV** de diferencia en TAIL, RANGE=0/R61=200 Ω, entre dos solves que ya cumplían KCL <10 pA. Es una observación exploratoria del criterio anterior, no una admisión ni un error físico medido. Una corriente residual pequeña no garantiza un voltaje pequeño cuando el nodo tiene muy poca conductancia.

## API y criterio numérico

`circuit66::initial_state_from_nodes` acepta 66 voltajes finitos como semilla numérica y resuelve DC directamente. Conserva todos los componentes de SVC-9 Fig. 9-11 (p. 13), Fig. 9-8 (p. 10), Fig. 9-17 (p. 19), los parámetros y las hipótesis de R61. No añade parámetros sonoros. `initial_state` conserva su inicialización anidada y después delega al mismo cierre global. La nueva API permite usar una solución de otro punto como semilla; no garantiza convergencia desde cualquier vector.

En DC se abren **los 18 capacitores**. Se exige simultáneamente:

- `max|r| < 10 pA` en las 66 KCL;
- `max|ΔV_Newton| < 10 nV`, con `J ΔV = −r` sin amortiguar.

El segundo umbral es numérico, 100 veces menor que el gate de equivalencia entre nodos de 1 µV. Cerca de una raíz simple la corrección estima el error de voltaje a primer orden; no es una prueba global de unicidad ni una cota rigurosa contra el circuito físico. No se elimina ninguna conductancia débil ni se cambia el umbral de pivote escalado.

Antes de cumplir KCL, la búsqueda reduce su máximo residual. Después, cada candidato debe conservar KCL <10 pA y reducir el máximo de corrección de voltaje; así los nodos débiles pueden avanzar aunque una fila fuerte esté en su piso de redondeo. Se rechaza dentro de la búsqueda un candidato cuyo Jacobiano no se pueda resolver. Se conservan **16 iteraciones/16 intentos de línea**, sin subpasos. DC puede requerir hasta 272 factorizaciones por llamada; el inicializador anidado conserva además su propio costo acotado. Esta política adicional se aplica sólo con capacitores abiertos. El paso temporal mantiene su criterio de KCL y su búsqueda anterior.

Sólo tras converger se devuelve un estado: predictor igual a los nuevos nodos, 17 voltajes de capacitor calculados desde sus terminales y C10 inicializado con Q7/Q22. No se reutiliza un historial temporal al cambiar de DC. Una semilla de un estado vivo no convierte esta API en un cambio de preset que conserve carga. `linearize_dc` expone KCL/J en el orden documental para diagnósticos, sin publicar candidatos.

## Oráculo y resultados

[Python](../tools/circuit66_dc_vectors.py) ensambla DC completo desde las ecuaciones independientes del ladder, Q26/Q28, recuperación, VCAs, conversión, panel y amplificador; diferencia las 66 columnas. Tiene presupuesto offline 40/32 y el mismo criterio doble. No usa coeficientes ni Jacobiano de Rust.

Los [14 puntos](../evidence/circuit66_dc_vectors.json) cubren centro, cutoff mínimo/máximo, RANGE mínimo/máximo y SCALE mínimo/máximo, en ambos R61. Se parte del DC central Python declarado. Rust pasa con **2,25484 nV** de error interno máximo, conserva KCL, reconstruye exactamente los 18 historiales y reproduce la corriente de cola. El test usa BUS=0,125 V y R14 desconectado para comprobar que el bloqueo DC no oculta el voltaje inicial de C27/C10. Todas las columnas analíticas DC se contrastan por diferencias simétricas en cutoff máximo de ambos R61.

El [barrido de semillas](../evidence/circuit66_dc_seed_survey.json) intenta los mismos puntos con desplazamientos uniformes 0/+1/−1 mV: **40 soluciones y dos rechazos `NoDecrease`**, ambos +1 mV con RANGE=0. Máximo interno de las soluciones 6,61841 nV. El campo `passed` sólo evalúa las 14 semillas de referencia; las perturbaciones son exploratorias y sus fallos quedan explícitos. Esto no admite cualquier semilla finita.

El [barrido general con ambas rutas DC](../evidence/circuit66_control_survey_full_dc.json) conserva 16384 pasos aceptados y seis casos fallidos en la política fría original. La semilla central completa resuelve cutoff máximo; falla DC en primero/segundo/ambos controles de volumen a cero. La ruta fría todavía resuelve el primer control a cero. Por eso no se reemplaza automáticamente una por otra. Q21 a cero y R21 exacto siguen pendientes.

## Recursos y límites

Pasa `cargo test --workspace`, incluido heap cero extendido a la nueva API. Python regenera exactamente los 14 puntos y los 128 vectores de R20. El [worker Win64 de 512 KiB](../evidence/circuit66_stack_full_dc_512.json) pasa 32768 muestras, reintentos forzados y rechazos atómicos; se observan **324 KiB comprometidos** (300 KiB normales +24 KiB guardas), frente a los 288 KiB de la compilación anterior. El aumento aparece también con DC fuera del worker: las ramas del solve compartido pueden afectar el frame generado para pasos temporales. Quedan 188 KiB reservados sin commit; no es un pico exacto ni un margen admitido para RackForge.

La [corrida nominal de costo](../evidence/circuit66_full_dc_deadline.json) da 2,3576 ms por bloque de 64 y 128/128 fuera de 1,3333 ms, sin fallos. Es una sola corrida; no demuestra un cambio causal de velocidad. No se admite C7. C6 permanece abierto.

```powershell
cargo test --workspace
python -m unittest discover -s tests -p test_circuit66_dc_vectors.py -v
cargo build --release -p rf-d-circuit --example circuit66_admission
./tools/run_circuit66_admission.ps1 -Mode dc-seeds -Output evidence/circuit66_dc_seed_survey.json
```

Lección RACE: conservar la convergencia de corriente, el error de voltaje y la dependencia de semillas como evidencias distintas, especialmente cerca de apagado. Una mejora sólo de inicialización también requiere volver a observar los recursos del binario.
