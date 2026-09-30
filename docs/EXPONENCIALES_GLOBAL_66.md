# Evaluación de junturas con una exponencial

## Ecuación y precisión

El [circuito global](SOLVER_GLOBAL_66_NODOS.md) conserva las dos junturas Ebers–Moll por BJT y los diodos Shockley documentados en SVC-9. Para un argumento adimensional `x=Vj/(n Vt)`, requiere `exp(x)−1` para corriente y `exp(x)` para conductancia. La implementación anterior calculaba `expm1(x)` y `exp(x)` separadamente en cada juntura.

Se calcula siempre `E=exp(x)`. Si `|x|<0,5`, se conserva `expm1(x)` para la corriente; fuera de esa zona se usa `E−1`. La resta tiene amplificación de error relativa acotada por `E/|E−1|≤2,542` en la región exterior positiva; en inversa es menor. El umbral 0,5 es un criterio de evaluación numérica, no una tensión de encendido ni un parámetro de sonido. Cerca de cero se evita cancelación, incluidos valores subnormales.

La derivada se obtiene **siempre de E**, no de `expm1(x)+1`: en inversa, esa suma puede redondear a cero y borrar una conductancia existente. No se descartan junturas ni conductancias débiles. El límite exponencial superior sigue siendo 45; se conservan el dominio eléctrico, las unidades A/S, los parámetros de cada placa, KCL <10 pA, Euler implícito y los presupuestos 16/16.

La incertidumbre nueva es exclusivamente redondeo de la corriente. El test compara 32769 puntos entre −750 y 45, ambos lados del umbral, ceros con signo y potencias ±2⁻ᵖ hasta p=1074. Exige error de corriente ≤4ε veces el módulo de `expm1` y derivada idéntica bit a bit a `exp`. Incluye inversa a x=−100, cuya derivada debe permanecer positiva.

La feature `solver-dual-exp` mantiene la evaluación anterior como referencia. Esta optimización afecta sólo al ensamblador global; la partición nativa y Python siguen siendo referencias independientes.

## Gates y costo

Pasó toda la suite Rust, incluidas las 128 muestras del oráculo de 66 nodos, todas las columnas del Jacobiano por diferencias finitas, heap cero, rechazo atómico y predictor alternativo. También pasó la ruta de referencia `solver-dual-exp` y el contraste de 8192 muestras contra la partición, sin relajar sus criterios.

Cinco pares alternados en release, con orden invertido cada segundo par: **2,46252→2,23336 ms/bloque**, reducción **9,306 %**. Cero fallos de convergencia, 640/640 bloques candidatos fuera de plazo, peor bloque 3,0132 ms. Datos y hashes en `evidence/circuit66_junction_exp_comparison.json`.

Se admite experimentalmente por conservar los gates y reducir la media local. Todavía supera 1,333 ms por 64 muestras a 48 kHz. C7 permanece abierto y el resultado no aporta comparación sonora vintage para C6.

```powershell
cargo test --workspace
cargo test -p rf-d-circuit --features solver-dual-exp --test cutoff_ladder_output
```

Lección RACE: compartir una función trascendente exige comprobar tanto corriente como derivada. Una corriente inversa aparentemente idéntica puede ocultar la desaparición de su conductancia si se reconstruye la derivada con una suma cancelada.
