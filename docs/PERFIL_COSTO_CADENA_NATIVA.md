# Perfil del costo nativo por etapas

Se ejecutaron secuencialmente los [siete ejemplos de benchmark](../crates/rf-d-circuit/examples/) el **30 de septiembre de 2026** sobre Windows/AMD Ryzen 5 5600X con `rustc 1.97.0`, compilación `--release`, una pasada de calentamiento y una medida de `48 000` muestras en bloques de `64` a `48 kHz`. El plazo teórico por bloque es `1333,3 µs`. Los números exactos de esa corrida y las órdenes están en [evidencia JSON](../evidence/native_stage_benchmark_2026-09-30.json). Los escenarios de estímulo y temperatura **cambian entre ejemplos**; sus tiempos indican dónde investigar, no se suman ni atribuyen costo exclusivo a un componente.

| Ruta incluida | Media por bloque | p99 | Evaluaciones posteriores/muestra |
| --- | ---: | ---: | ---: |
| Placa 3, `32 Ω+32 Ω` | `311,1 µs` | `369,4 µs` | — |
| Panel + placa 3 | `597,2 µs` | `632,9 µs` | — |
| C2 + panel + placa 3 | `607,1 µs` | `765,8 µs` | — |
| Q1/Q12/Q17 + C2→J7 | `1279,6 µs` | `1372,8 µs` | `2,00` |
| Q1_BASE/C4 + conversión→J7 | `1341,5 µs` | `1516,2 µs` | `2,00` |
| VCA2 + conversión→J7 | `3093,4 µs` | `3374,8 µs` | `2,00` |
| VCA1/R2/C6/C15 + VCA2→J7 | `5400,4 µs` | `6104,1 µs` | `2,00` |

La cadena VCA1 excedió el plazo por `4,58×` en p99 en esta corrida, con **cero fallos** y KCL máximo `2,398×10⁻¹¹ A`. La medición anterior del mismo ejemplo dio p99 `6847,9 µs`; esa variación de Windows confirma que una corrida no estima el peor caso. Las tres capas superiores invocan repetidamente el solve posterior para evaluar sus KCL y tangentes: el conteo observado de `2,00` por muestra en cada una hace de la **anidación de Newton** la primera hipótesis de costo. Esa es una inferencia del flujo de código y del conteo, no una partición temporal de CPU por función. La placa 3 aislada está por debajo del plazo, pero el caso completo no.

El siguiente experimento de optimización debe medir una variante con menos reevaluaciones profundas o una formulación conjunta, usando el **mismo estímulo**, parámetros, cargas y máquina para A/B. Una variante sólo se admitiría si mantiene los [12 pasos completos](VCA1_SALIDA_NATIVA.md), la [traza de 192 muestras](TRAZA_AUDIO_NUMERICA_VCA1.md), las corrientes y derivadas de puertos, el estado transaccional y la prueba sin heap; después se vuelve a medir p99, máximo y fallos. No se debe interpretar la equivalencia numérica con el oráculo como fidelidad sonora al Model D.

Una [primera optimización A/B](OPTIMIZACION_TANGENTES_MULTI_RHS.md) comparte la factorización al calcular las columnas de tangente en C4 y VCA2. Conservó las regresiones y redujo la media de VCA1→J7 alrededor de `4,8 %` en dos pares de corridas alternadas; la anidación de solves y el incumplimiento del plazo permanecen.
