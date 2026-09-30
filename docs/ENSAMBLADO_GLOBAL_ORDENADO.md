# Ensamblado global en orden de eliminación

## Procedencia y dominio

El circuito, ecuaciones y cotas son los del [solver global de 66 nodos](SOLVER_GLOBAL_66_NODOS.md): SVC-9 Fig. 9-11, 9-8 y 9-17. Esta modificación cambia la numeración interna de filas y columnas del Jacobiano. No cambia componentes, leyes, historial, tolerancias ni presupuesto Newton 16/16. Los estados públicos siguen en orden documental.

Para una permutación P, se resuelve `(P J Pᵀ) z = −P r` y se devuelve `dx=Pᵀz`. El ensamblador escribe directamente cada derivada en `POSITION[i],POSITION[k]`. Sólo se permutan dos vectores de 66 elementos por dirección; no se copia/transpone una matriz de 4356 elementos en cada Newton. El diagnóstico `linearize` devuelve el Jacobiano en orden documental para conservar el contraste por diferencias finitas.

La ordenación fija procede del grafo simétrico del Jacobiano nominal de la muestra 1023 del benchmark: grado mínimo, llenado de vecinos, desempate por índice, incluyendo la rama 7↔22 de C10. `--profile` reproduce el algoritmo offline. Ese grafo orienta la numeración; **no restringe** los coeficientes futuros. Cambios de controles, R61, cargas, diodos y C10 abierto/cerrado conservan todas sus entradas, aunque no estuvieran presentes en el punto nominal.

La feature `solver-natural-order` conserva la numeración original como referencia ejecutable. `solver-profiling` habilita relojes y bucles de medición únicamente en una función de diagnóstico offline; el paso de audio no contiene relojes, asignaciones ni logging.

## Ensayos previos descartados

Además de la [permutación con copia de matriz rechazada](ORDENACION_GLOBAL_RECHAZADA.md), se midieron dos variantes sobre la eliminación original:

| Variante | Media anterior | Media candidata | Cambio de costo | Decisión |
| --- | --- | --- | --- | --- |
| Lista de columnas exactamente no nulas por pivote | 2,59540 ms | 2,69636 ms | +3,890 % | Restituida |
| Recortar ceros finales de la fila pivote | 2,63456 ms | 2,69498 ms | +2,293 % | Restituida |

Ambas conservaron el contraste de 8192 muestras y tuvieron cero fallos. Sus parches y corridas quedan en `evidence/circuit66_active_columns_*` y `evidence/circuit66_pivot_span_*`. No están en el solver admitido. Las listas indirectas o los recorridos adicionales pueden costar más que las multiplicaciones evitadas; no se infiere una mejora por contar operaciones.

## Medidas y gates

El perfil en un único punto midió ensamblado **7,336 µs**, factorización natural **10,325 µs** y factorización ordenada **8,925 µs**, con 8192 repeticiones. La última excluye la permutación, realizada fuera del bucle. Es una herramienta de diagnóstico, no una cota de audio.

Cinco pares alternados, invirtiendo el orden cada segundo par, del benchmark completo dan **2,59546→2,46534 ms por bloque**, reducción **5,013 %**. Registro y hashes de ejecutables: `evidence/circuit66_direct_order_comparison.json`. No hubo fallos de convergencia; los 640 bloques candidatos excedieron 1,333 ms y el peor fue 3,6053 ms. La reducción media se admite experimentalmente; **C7 sigue abierto** y no se afirma una mejora del peor caso.

Pasaron las 128 muestras del oráculo Python independiente, las 66 columnas de Jacobiano por diferencias finitas, publicación atómica, predictor rechazado y toda la suite Rust, incluido heap cero. También pasó el contraste de 8192 muestras contra la partición original, con los mismos criterios de nodos, J7, C10, cola y relación señal/error numérica. C6 sigue sin evidencia de una unidad vintage.

```powershell
cargo test --workspace
cargo test -p rf-d-circuit --features solver-natural-order --test cutoff_ladder_output
cargo run --release -p rf-d-circuit --features solver-profiling --example bench_ladder_recovery_output -- --profile --emphasis
```

`tools/compare_circuit66_variants.ps1` exige ejecutables ya construidos y conservados, no superpone compilación con las medidas y detiene la comparación si falla la señal. Los resultados son locales a CPU, compilador y escena. Los dos rechazos y la admisión no son una caracterización de toda la voz.
