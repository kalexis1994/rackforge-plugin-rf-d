# Perfil de Schur y tres hipótesis de costo no elegidas

2026-10-13. Base1e02f98, voz229 CA3046 condicionada, sin hardware.
[Contrato de costo](SCHUR_COSTO_PROTOCOLO.md). Los gates del banco numérico
anterior siguen vigentes; este bloque localiza costo y conserva resultados
negativos antes de intervenir otra vez.

## Perfil privado con identidad de resultados

84 pares contrastados con el kernel sin instrumentar: mismos1834 campos
por bits, iteraciones y trials. Timers/contadores sólo en la copia privada;
no están en ninguno de los candidatos del benchmark.
[Recibo](../evidence/voice_schur_refined_profile01.json).

| Medida | Tiempo acumulado ms | Calls |
|---|---:|---:|
| Preparación | 309.6124 | 396 |
| Factor64 | 8.3621 | 792 |
| Factor330 | 143.8945 | 396 |
| Soporte exacto | 51.2553 | 396 |
| RHS64 | 22.1868 | 8752 |
| RHS330 | 29.4546 | 416 |
| Corrección/reconstrucción | 32.8684 | 416 |
| Residuo | 2.6329 | 416 |
| Solve observado | 375.4313 | 396 |

Son tiempos anidados: no sumarlos como partición. Preparación82.47%,
corrección8.75% y residuo0.70% del solve observado. El resto incluye
trabajo y movimientos entre llamadas, sin atribución causal a copias.
RHS64 contiene las veinte respuestas de puertos de cada J más sus
correcciones; los416 RHS330 incluyen20 refinamientos. El perfil orienta
una hipótesis, pero no mide deadline o costo universal sin instrumentación.

## Tres intervenciones acotadas

1. [Constructores integrados](SCHUR_CONSTRUCCION_INLINE.md): cinco
   directivas inline(always), sin cambiar cuerpos. No pasa utilidad.
2. [Soporte de fronteras y RHS](SCHUR_SOPORTE_FRONTERAS.md): validar ambos
   sentidos de cada acoplamiento con el soporte de J; omitir productos por
   cero con comprobaciones finitas por producto. No pasa utilidad.
3. [Invariante de fila finita](SCHUR_RHS_FINITO.md): cerrar cada fila con
   una comprobación de finitud, omitir productos por cero cuando el
   acumulador es distinto de cero. Partir del kernel estable anterior,
   sin las otras dos intervenciones. No pasa utilidad.

La segunda propuesta primero rechaza compilación por inferencia de tipo
del acumulador. Dos compilaciones reproducen exactamente stderr; fuentes
y recibo preservados. Reparación limitada a escribir0_f64 en el array de
ceros ya inferido como f64 en la versión previa, sin cambiar gates.
[Rechazo](../evidence/voice_schur_refined_supportbench01.json) y
[reparación](../evidence/voice_schur_cost_type_repair01.json).

## Banco pareado, sin escoger por el mejor intento

Warmup separado, cinco rondas alternadas en cada banco. Comparador:
LU completa anterior sin refinar. No hubo confirmación: las tres
medianas fallan el gate>1 declarado; no repetir hasta obtener una ganancia.

| Ronda | Inline | Soporte/fronteras | Fila finita |
|---|---:|---:|---:|
| 1 | 0.872821× | 0.905599× | 0.937482× |
| 2 | 0.853485× | 0.927638× | 0.951333× |
| 3 | 0.852438× | 0.907771× | 0.937080× |
| 4 | 0.859205× | 0.926982× | 0.944135× |
| 5 | 0.850378× | 0.914858× | 0.939158× |
| Mediana | **0.853485×** | **0.914858×** | **0.939158×** |

[Inline](../evidence/voice_schur_refined_inlinebench01.json),
[soporte](../evidence/voice_schur_refined_supportbench02.json) y
[fila finita](../evidence/voice_schur_refined_rhsbench01.json).
Cada columna es pareada con su referencia en ese proceso; no es un
contraste simultáneo entre las tres variantes ni contra tiempos históricos.
El resultado no prueba que una intervención aislada sea siempre más lenta.

## Exactitud preservada y alcance heredado

Los tres archivos de84 raíces coinciden por bytes con el banco estable
anterior. Para soporte/fronteras y fila finita, también coinciden toda la
traza de396 J/b/correcciones, referencia cruda y referencia refinada.
[Soporte](../evidence/voice_schur_refined_supportbank01.json) y
[fila finita](../evidence/voice_schur_refined_rhsbank01.json).
Se vuelven a observar1680 memorias y2016 corrientes, con los mismos gates.
181368 filas Decimal100 y38472 ecuaciones del grafo se heredan por
identidad de los datos, sin reejecutar esos auditores ni aumentar cobertura.
El diagnóstico de396 trazas de inline no se ejecutó: ya falla utilidad;
sus helpers quedan disponibles, sin acreditarlos como ejecutados.

La última variante pasa doce regresiones de estructura y rechazo más
nueve controles de sustitución frente a Lu::solve anterior: ±0, coeficientes
con signo, subnormales, pivote, overflow, NaN/Inf de RHS y singularidad.
Comparar bits de todas las salidas finitas y la clase de error si rechaza.
Conservar las operaciones originales cuando el acumulador es cero evita
normalizar su signo. La variante de presupuesto cero sólo es de test.
[21 regresiones](../evidence/voice_schur_refined_rhsstructure01.json).

## Decisión y siguiente experimento

**No elegir ninguna de las tres para trayectoria o producción.** La LU
anterior conserva la voz aceptada; Schur estable conserva su admisión
numérica de banco y utilidad pendiente. No se altera el circuito ni se
añaden duración, audio, biblioteca, SPICE o RT.248 tests Rust heredados,
no reejecutados. [QA de alcance](../evidence/voice_schur_cost_tests01.json).

La siguiente hipótesis es construir/factorizar las matrices grandes en su
ubicación final mediante una API que las modifica allí. Eso puede evitar
retornos grandes sin depender de inline(always), pero requiere demostrar
el efecto y contrastar trazas, errores y costo antes de elegirla. No cambiar
gates físicos para resolver una pérdida de rendimiento. Este bloque se
cierra con el límite de experimentos declarado, preservando los negativos.
