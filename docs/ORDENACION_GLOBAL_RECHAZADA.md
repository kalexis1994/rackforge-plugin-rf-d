# Ensayo rechazado de ordenación global

## Hipótesis y método

Después del [solver global de 66 nodos](SOLVER_GLOBAL_66_NODOS.md), se probó una ordenación que elige, en cada eliminación, el nodo con menos vecinos aún presentes. Al eliminarlo se conectan entre sí esos vecinos para representar el fill-in potencial. Los empates se resuelven por índice de nodo. El grafo simétrico parte de los coeficientes no nulos del Jacobiano inicial y añade siempre el enlace C10 entre nodos 7/22, incluso si el lazo arranca abierto.

La ordenación se calcula en inicialización con arrays fijos. Antes de cada solve se permutan filas y columnas del Jacobiano y el residual; después se devuelve la dirección al orden eléctrico original. **Se conservan todas las ecuaciones y todos los coeficientes futuros**, aunque aparezcan conexiones que no estaban en el Jacobiano inicial. La inferencia del grafo afecta al costo, no elimina circuitería.

No se cambian fuentes, valores, parámetros, Euler implícito, dominio exponencial ni tolerancias del [circuito documentado](CUTOFF_LADDER_J7_NATIVO.md). Este es un ensayo numérico sobre el perfil SVC-9, no una nueva hipótesis audible.

## Señal y costo

La traza de 8192 muestras contra la ruta por puertos pasó los criterios vigentes: J7 máximo **21,48 nV**, nodos **1,322 µV**, C10 **0,06108 nV**, cola **0,0001822 pA**, relación señal/error numérica **141,512 dB**. La preservación de señal no bastó para admitirlo.

Se alternaron cinco corridas de `--global --emphasis` y cinco de `--ordered --emphasis` en el mismo ejecutable release, Windows/Ryzen 5 5600X. Cada corrida reinicializó el circuito, calentó 8192 muestras y midió otras 8192, en bloques de 64 a 48 kHz. Registro íntegro en `evidence/circuit66_ordering_experiment.json`.

| Media de medias | Resultado |
| --- | --- |
| Global en orden original | 2,75332 ms/bloque |
| Candidato ordenado | 2,84738 ms/bloque |
| Cambio de costo | **+3,416 %** |

Hubo cero fallos. Los plazos siguieron excedidos. Estas medidas corresponden a esta comparación alternada; no deben sustituirse por las de otra sesión para calcular la diferencia. La copia/permutación de matrices y el comportamiento del pivote pueden contrarrestar una reducción de fill-in; esta comparación mide el costo total y no atribuye porcentajes a esos componentes.

## Decisión y reproducción

**No admitido.** Se restituyeron `circuit66.rs` y el benchmark exactamente a `1fd4492`. No queda constructor ordenado, campo extra de estado ni flag `--ordered` en el código activo. El circuito y el solver global previos se conservan.

El parche del candidato se guarda como `evidence/circuit66_min_degree_candidate.patch`, con contexto cero, para reconstruir el experimento sobre `1fd4492` en un checkout de investigación. No se aplica a la rama activa ni forma parte del plugin.

```powershell
# En un checkout de investigación que parte exactamente de 1fd4492:
git apply --unidiff-zero evidence/circuit66_min_degree_candidate.patch
cargo build --release -p rf-d-circuit --example bench_ladder_recovery_output
./target/release/examples/bench_ladder_recovery_output.exe --global --emphasis
./target/release/examples/bench_ladder_recovery_output.exe --ordered --emphasis
./target/release/examples/bench_ladder_recovery_output.exe --ordered --compare --emphasis
```

En esa revisión base, los archivos de este registro deben copiarse desde el commit que los incorpora antes de aplicar el parche. Alternar ambas mediciones cinco veces; no tomar una única corrida como decisión. La lección para RACE es medir el costo total de una transformación de solver, incluyendo la conversión de datos: un orden que parece favorable en el grafo puede ser más lento en un circuito pequeño.
