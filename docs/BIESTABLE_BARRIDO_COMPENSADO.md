# Barrido compensado: cobertura completa y refinamiento pendiente

## Método y gates fijados antes de medir

`tools/loudness_latch_increment_survey.py` ejecuta las políticas A2/B2
de [incrementos compensados](BIESTABLE_INCREMENTOS_COMPENSADOS.md).
Cada una parte de su propio DC, con R61=200 Ω, BUS=0 V, KEY 0→10 V en t=0
y el mismo modelo sintético Q25/Q15. Conserva 21 pares de memoria lineal
y cuatro cargas de juntura, sin reponer estado ni escoger otra raíz.

Cada intento compara un paso completo con dos medios pasos. Sólo publica
ambos medios pasos después de comprobar sus errores de nodos/junturas,
incrementos de juntura, modos congelados y KCL de memoria publicada.
Los gates de solve siguen en 10 pA/10 nV. Decimal de 80 dígitos verifica
las corrientes derivadas de los pares guardados y la ecuación de C10/R.
La reconstrucción desde el formato serializado debe mantener KCL <10 pA.

Para el contraste entre políticas se fija **1 mV máximo en los 94 nodos**
antes del barrido. Se comparan los tiempos aceptados de ambas trazas mediante
interpolación lineal en su unión; se excluyen los puentes del salto algebraico
inicial hasta 25 µs. Es un contraste entre dos ejecuciones del mismo modelo,
sin oráculo independiente ni cota del error entre muestras.

## Resultado

Informe: `evidence/loudness_latch_increment_survey.json`, esquema v2;
el informe adaptativo v1 fallido permanece intacto.

| Dato | A2 | B2 |
| --- | ---: | ---: |
| Tiempo alcanzado | 3 ms | 3 ms |
| Macro pasos aceptados | 689 | 1387 |
| Medios intervalos publicados | 1378 | 2774 |
| Intentos rechazados | 25 | 30 |
| Macro paso mínimo | 3,051758 ns | 1,525879 ns |
| KCL máxima de memoria publicada/reconstruida | 9,88096 pA | 9,90548 pA |
| Diferencia máxima de corriente por publicación | 1,12e−19 A | 6,96e−20 A |
| Error máximo de ecuación de rama | 2,52e−25 V | 5,15e−25 V |

Los **4152 medios intervalos** conservan memoria continua y pasan sus gates.
Los 55 rechazos corresponden a error de voltaje o incremento de juntura;
no hay rechazo de solve, publicación o presupuesto mínimo en este barrido.
Los historiales previos de todos los rechazos se conservan por hash.

## El gate temporal falla

La unión tiene 4141 tiempos de comparación. La diferencia máxima es
**5,146985 V** en nodo 67, `ATTACK_OUT`, a **2,424609375 ms**. Al final de
los 3 ms, la diferencia máxima entre nodos aún es **6,4488 mV**.
Ambas superan 1 mV: `temporal_refinement_admitted=false`.

La cobertura completa corrige el bloqueo numérico observado en C2.
No demuestra que el control local de error limite suficientemente el error
acumulado de la transición. La separación principal aparece en ATTACK_OUT
antes de la caída rápida del colector Q25; el siguiente diagnóstico debe
medir ambos momentos por separado. No se retiman las trazas para aprobar
el contraste al mismo tiempo.

## Regresión y continuación

Cinco pruebas reconstruyen cada medio intervalo, publican de nuevo sus
21 memorias, verifican las cuatro cargas Q(V), reproducen decisiones de
duplicación de paso/modos en puntos iniciales, centrales, mínimos y finales,
y contrastan los hashes de fuentes y rechazos. La cobertura y el gate de
refinamiento se comprueban como resultados separados.

`python tools/loudness_latch_increment_survey.py`

`python -m unittest discover -s tests -p test_loudness_latch_increment_survey.py -v`

Siguiente bloque: tiempos de subida de ATTACK_OUT y caída de Q25,
sensibilidad acumulada antes de esos eventos, refinamiento adicional y
contraste con otra integración. Parámetros vintage, cargas omitidas,
admisión de audio y recursos del motor permanecen abiertos.
