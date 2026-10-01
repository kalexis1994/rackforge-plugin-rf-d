# Barrido BDF2: dos trayectorias completas y discrepancia reducida

## Método fijado antes de ejecutar

Políticas A3/B3 de [BDF2 sobre carga](BIESTABLE_BDF2_CARGA.md), desde DC,
R61=200 Ω, BUS=0 V y KEY 0→10 V en t=0. Se mantienen los parámetros sintéticos
y cargas omitidas del laboratorio. Los solves conservan KCL <10 pA y
corrección <10 nV. Los dos estados entrantes permanecen intactos ante rechazo.

`tools/loudness_latch_bdf_time.py` compara un predictor BE desde el estado
actual con BDF2 desde los dos historiales aceptados, al mismo destino temporal.
La diferencia en nodos/BE/BC usa Vabs=100/25 µV y Vrel=1e−4/2,5e−5.
Se limita cada incremento de juntura a 50/25 mV y `hreal·λ+` a 0,1/0,05.
λ+ proviene del descriptor congelado en los extremos; no demuestra estabilidad
entre ellos. Ningún error se escala por el origen absoluto de Q.

El arranque compara BE completo con BE a medio paso y BDF2 a medio paso.
Publica esa ruta fina sólo si pasan ambos intervalos. Después publica un
intervalo BDF2 por intento aceptado. h máximo=100 µs, mínimo=1 ps,
crecimiento máximo ×2 del intervalo real previo y 3000 intentos por política.
La comparación BE/BDF2 es un estimador propio, no una cota de error global.

Decimal80 comprueba la corriente de cada carga publicada directamente desde
los **dos historiales reales**, las ecuaciones de C10/R y el estado restaurado.
La memoria virtual del solver nunca se presenta como una carga física.

## Resultado

Datos completos: `evidence/loudness_latch_bdf_survey.json.gz` (13,4 MB).
Resumen, hashes y observaciones: `evidence/loudness_latch_bdf_survey_summary.json`.
Se guarda JSON canónico comprimido sin pérdidas, con hashes de ambos formatos.

| Dato | A3 | B3 |
| --- | ---: | ---: |
| Tiempo alcanzado | 3 ms | 3 ms |
| Intentos aceptados | 1071 | 2163 |
| Intervalos publicados | 1072 | 2164 |
| Intentos rechazados | 37 | 39 |
| Intervalo real mínimo | 1,525879 ns | 0,762939 ns |
| KCL máxima de carga publicada | 9,96046 pA | 9,99439 pA |

Los **3236 intervalos** conservan memoria: dos son BE de arranque y 3234 son
BDF2. Todos los 76 rechazos son de error de voltaje/incremento de juntura;
no hay rechazos de solve, publicación o presupuesto en el informe final.
No hay reinicios, caída a Euler tras rechazo ni selección de otra raíz.

Una ejecución previa se interrumpió al detectar una comprobación de formato
que comparaba listas JSON con tuplas internas. Se corrigió la validación
de identidad canónica y se reinició desde DC con una sola revisión de fuentes.
`evidence/loudness_latch_bdf_survey_attempts.json` conserva la incidencia y el
último progreso impreso; no admite esa ejecución como trayectoria completa.

## Refinamiento y contraste entre métodos

La comparación A3/B3 usa 3228 tiempos de la unión de intervalos aceptados,
desde 25 µs hasta 3 ms, excluyendo los puentes del salto de fuente inicial.
El gate de **1 mV máximo en los 94 nodos** se declaró antes de medir.

| Comparación al mismo tiempo | Máximo | Diferencia final |
| --- | ---: | ---: |
| A2/B2, Euler previo | 5,146985 V | 6,4488 mV |
| A3/B3, BDF2 nuevo | 0,563357 V | 0,140795 mV |
| A3 frente a A2 | 7,034589 V | 13,0533 mV |
| B3 frente a B2 | 5,146769 V | 6,4637 mV |

La diferencia máxima A3/B3 aparece en nodo 66, `ATTACK_GATE_LOWER`,
a 2,442553711 ms. La diferencia final pasa 1 mV; el máximo de la trayectoria
**todavía falla**: `temporal_refinement_admitted=false`.

La menor discrepancia entre políticas de BDF2 es un resultado numérico útil.
No conocemos una solución exacta independiente del DAE que permita asignar
un error absoluto a cada integrador. La comparación entre métodos también
falla y ambos comparten el solver espacial y las hipótesis del dispositivo.
No se admiten conmutación física, audio ni tiempo real.

## Regresión y continuación

Cinco pruebas reconstruyen todos los intervalos, verifican los dos historiales,
el formato serializado, dQ/dt directo, C10/R, cargas Q(V), decisiones locales
y modos en puntos iniciales, centrales, mínimos y finales. También contrastan
los hashes de rechazos, fuentes y almacenamiento y separan cobertura del gate
de refinamiento.

`python tools/loudness_latch_bdf_survey.py`

`python -m unittest discover -s tests -p test_loudness_latch_bdf_survey.py -v`

Siguiente corte: localizar la diferencia antes de la subida ATTACK_OUT,
separar sensibilidad de malla de errores de interpolación y refinar los
tiempos de ambos eventos. Los informes de Euler conservan sus fallos originales.
