# R21: conexiones exactas en ambos topes

## Circuito y dominio

SVC-9 Fig. 9-17, PDF p. 19, y Fig. 9-8, PDF p. 10: R77 de 1 kΩ une C2_RIGHT (nodo 47) con PIN22 (48); R21 de 5 kΩ tiene tramo superior `5000-L` entre PIN22 y cursor (49), tramo inferior `L` entre cursor y masa; C19 de 2,5 µF conecta el cursor con la base del amplificador (50).

La ruta **global `circuit66`** admite `L ∈ [0,5000] Ω`. La ruta por particiones mantiene su dominio interior para R21. No se cambia la ley angular del potenciómetro, que sigue sin identificar, ni se incorporan resistencias de contacto desconocidas. Las hipótesis de semiconductores y revisión documental siguen siendo las mismas del modelo nominal.

En el interior permanecen las dos resistencias. En los topes se omite únicamente el tramo de cero ohmios y se identifica su conexión, sin epsilon, conductancia infinita ni resistencia sustitutiva:

- `L=0`: cursor a masa, `V49=0`; el tramo de 5 kΩ PIN22→cursor permanece.
- `L=5000`: PIN22 y cursor unidos, `V49=V48`; el tramo de 5 kΩ cursor→masa permanece.

Se conservan las 66 coordenadas documentales. En el máximo se suman las KCL de PIN22 y cursor en la fila 48. En ambos topes la fila 49 se reemplaza por la igualdad de voltaje. La identificación se hace **después** de estampar todos los dispositivos y capacitores, incluido C19, para conservar su corriente y su historial.

## Unidades, convergencia y estado

Las filas físicas tienen residual A y derivada A/V. En los topes, fila 49 tiene residual V y derivada V/V. Las columnas siguen siendo voltajes. El coeficiente 1 de la igualdad no representa un resistor de 1 S.

La norma de Newton usa escala de 1 A para las filas KCL y 1 V para la igualdad. El gate `1e-11` exige simultáneamente KCL <10 pA e igualdad <10 pV; se conserva la corrección completa <10 nV y el presupuesto 16/16. El residual publicado en `StepResult` excluye la fila de voltaje, y `Result66.voltage_constraint_error_v` la informa por separado.

`Result66.r21_short_current_a` recupera la corriente del tramo eliminado mediante KCL:

- Mínimo, signo cursor→masa: `Ishort=(V48-V49)/5000-I19`.
- Máximo, signo PIN22→cursor: `Ishort=(V47-V48)/1000`, también `V49/5000+I19`.
- `I19=(2,5 µF/dt)·(V49-V50-V19_anterior)`, A.

No hay una incógnita, estado ni carga adicional. Las 18 memorias de capacitores siguen publicándose atómicamente tras converger. Poner el cursor a masa no impone J7=0 instantáneamente: la carga previa de C19/C21 sigue formando parte del transitorio.

El arranque global usa R21=2500 Ω **sólo para obtener la semilla numérica** del inicializador por particiones; luego resuelve el DC con el tope realmente solicitado y todos los capacitores abiertos. Ningún paso temporal usa ese valor sustitutivo. Esta adaptación no resuelve los otros fallos de arranque con cutoff máximo o fuentes VCA en cero.

## Contraste independiente

[`circuit66_r21_vectors.py`](../tools/circuit66_r21_vectors.py) calcula sus propios DC, cargas e historiales para **128 pasos completos**, cuatro escenas: ambos topes × las alternativas documentales R61=200 Ω/200 kΩ. Cada escena aplica 16 pasos al tope y 16 de restauración al centro, con BUS sinusoidal de 20 mV, 100 Hz, 48 kHz, R14=25 kΩ, SW18 ON y ambas cargas J7=32 Ω. Python calcula las 66 columnas por diferencias finitas; presupuesto fuera de audio 40/32.

La captura nativa se usa para comparar, nunca como semilla ni historial de la integración Python. Se mantienen gates previos de 1 µV para nodos, capacitores y jacks; 1 nA para cola/corriente del corto; 10 pA KCL, 10 pV igualdad y 10 nV corrección.

| Máximo Python frente a la captura nativa | Resultado |
| --- | ---: |
| Error de nodo | 0,219477 nV |
| Error de carga expresada en voltios | 0,291436 nV |
| Error de jack | 0,0127505 nV |
| Error de corriente del corto | 9,8753 fA |
| KCL del oráculo, incluidos nodos separados con corriente recuperada | 1,41483 pA |
| Igualdad de voltaje | 0 V |
| Corrección Newton del oráculo | 0,009835 nV |

La regresión Rust vuelve a integrar las cuatro escenas, contrasta los 66 nodos y 18 memorias y verifica las corrientes físicas de ambos nodos. Contrasta todo el Jacobiano por diferencias centrales al entrar al tope y al restaurar, ocho puntos × 66 columnas; también verifica rechazo de valores fuera de dominio sin publicar estado. El archivo congelado se regenera exactamente en la prueba Python.

El [barrido de controles actualizado](../evidence/circuit66_control_survey_r21.json) admite **17408 muestras**, incluidas 1024 nuevas de topes R21, sin reintentos en esas cuatro escenas. Ya no rechaza topes: conserva cuatro rechazos de valores fuera de dominio y los seis fallos previos del barrido. Su `passed=false` se conserva y el runner devuelve error; no constituye una admisión global de controles.

## Regresiones y recursos

La [comparación de escenas interiores](../evidence/circuit66_r21_interior_trace_comparison.json) conserva **23224 f64 idénticos en bits** y 308 escalares en las 96 capturas de apagado, con los cuatro fallos abruptos conocidos. Pasan las siete regresiones globales y heap cero, incluyendo DC y pasos por ambos topes.

La [prueba de stack con topes](../evidence/circuit66_stack_r21_512.json) añade 32768 pasos en cuatro workers de 512 KiB, ambos R61 y arranque dentro/fuera del worker. Incluye DC al mínimo, cambios entre centro/mínimo/máximo, reintento forzado y rechazos atómicos. Se observan 328 KiB comprometidos, incluidas 24 KiB de guardas, frente a 324 KiB en la compilación anterior. Es una observación por páginas, no el pico exacto del stack ni una admisión del host.

Cinco [pares de costo nominal](../evidence/circuit66_r21_cost_comparison.json) contra el ejecutable anterior dan **2973,22→2909,58 µs/bloque**, variación −2,14 %. No se reclama una optimización por ese resultado. Máximo candidato 4561,8 µs, **640/640 bloques fuera de 1333,3 µs**, cero fallos y contraste de 8192 muestras contra la ruta por particiones aprobado. Es costo de la escena interior nominal, no un máximo temporal de todos los topes/cargas.

No se repite aquí el estrés completo de 752384 muestras. Los gates de fidelidad contra audio vintage y tiempo real siguen pendientes.

## Reproducción

```powershell
cargo build --release -p rf-d-circuit --examples
./tools/run_circuit66_admission.ps1 -Mode r21 -Output evidence/circuit66_r21_native.json
python tools/circuit66_r21_vectors.py
python -m unittest discover -s tests -p test_circuit66*.py
cargo test --release -p rf-d-circuit --test cutoff_ladder_output --test no_alloc
./tools/run_circuit66_admission.ps1 -Mode stack -StackKib 512 -R21Endpoints -Output evidence/circuit66_stack_r21_512.json
# Conserva el diagnóstico y devuelve error por los seis fallos pendientes:
./tools/run_circuit66_admission.ps1 -Mode controls -Output evidence/circuit66_control_survey_r21.json
```

Los reportes incluyen hashes de fuentes/binario cuando corresponden. `source_head` identifica el commit de partida antes de los cambios, por lo que se deben consultar también los hashes del contenido medido.
