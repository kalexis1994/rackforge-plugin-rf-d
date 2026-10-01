# Tercera malla BDF2: política C3

## Contrato fijado antes de medir

Se repite desde DC la red cargada de 94 nodos, R61=200 Ω, BUS=0 V y
KEY 0→10 V en t=0, hasta 3 ms. No se cambian topología ni parámetros
sintéticos del perfil `finite_transit` del [BDF2 previo](BIESTABLE_BARRIDO_BDF2.md).
Se mantienen las dos memorias aceptadas y los gates de solve/publicación:
KCL <10 pA, corrección <10 nV y error de ecuación de rama <10 fV.

| Política | B3 anterior | C3 nueva |
| --- | ---: | ---: |
| Tolerancia absoluta de nodo y juntura | 25 µV | 6,25 µV |
| Tolerancia relativa de nodo y juntura | 2,5e−5 | 6,25e−6 |
| Incremento máximo BE/BC por intervalo | 25 mV | 12,5 mV |
| Producto máximo h real·λ+ congelado | 0,05 | 0,025 |
| Intervalo máximo | 100 µs | 100 µs |
| Intervalo mínimo | 1 ps | 1 ps |
| Presupuesto de intentos | 3000 | 6000 |

Las cuatro tolerancias de error se dividen por cuatro; los límites de
incremento y modo se dividen por dos. Se conserva crecimiento máximo ×2
respecto del intervalo real anterior. El predictor BE y el corrector BDF2
se comparan al mismo destino; el arranque publica BE medio seguido de BDF2
medio sólo cuando pasa el intento entero. No hay fallback a Euler,
reinicio de memoria ni selección de otra raíz tras un rechazo.

El gate global sigue siendo **1 mV máximo en los 94 nodos**. Se compara B3
con C3 en la unión temporal mediante interpolación lineal, excluyendo los
puentes del salto de fuente inicial. Cobertura completa, error final y
gate máximo son decisiones separadas. La interpolación requiere su propio
diagnóstico y no es una cota del comportamiento entre muestras.

## Resultado completo

C3 completa 3 ms con 4363 intentos aceptados y **4364 intervalos publicados**:
un BE de arranque y 4363 BDF2. Los 41 rechazos provienen del criterio de
voltaje/incremento de juntura. El mínimo real es 0,381470 ns y la KCL máxima
publicada es 9,88491 pA. No hay rechazo de publicación, solve o presupuesto,
reinicio de historial ni selección de raíz alternativa.

| Comparación | Máximo en 94 nodos | Diferencia final |
| --- | ---: | ---: |
| A3/B3 anterior | 0,563357 V | 140,795 µV |
| B3/C3 nueva | 0,126368 V | 39,8792 µV |

La comparación nueva incluye 6521 instantes entre 12,5 µs y 3 ms. Su máximo
permanece en nodo 66, `ATTACK_GATE_LOWER`, a 2,442491150 ms. La discrepancia
máxima se reduce por un factor 4,458 entre estos dos pares de mallas; ese
cociente no prueba un orden global ni mide el error contra una solución exacta.
El gate de **1 mV máximo sigue fallando**: `temporal_refinement_admitted=false`.
La diferencia final menor no modifica esa decisión.

Datos completos: `evidence/loudness_latch_bdf_refinement.json.gz` (17,79 MB).
Resumen: `evidence/loudness_latch_bdf_refinement_summary.json`.

## Evidencia y reproducción

`tools/loudness_latch_bdf_refinement.py` reutiliza el ejecutor verificado
sin modificarlo. Guarda una trayectoria C3 nueva, los rechazos y hashes
antes/después de ejecución; el archivo BDF2 A3/B3 conserva sus bytes.
El JSON canónico se comprime sin pérdidas y se verifica antes de publicar
su resumen con hashes de ambos formatos. `.gitattributes` conserva Python
con LF, para que un checkout con `core.autocrlf=true` no cambie los bytes
identificados por los hashes; la fuente histórica VCO con CRLF mantiene
una excepción explícita. Los JSON previos conservan su convención original.
Una exportación del índice con `core.autocrlf=true` verificó 26 archivos:
las 24 entradas identificadas por este informe, los atributos y la fuente
VCO con excepción. Todos conservaron sus hashes SHA256 de trabajo.

`python tools/loudness_latch_bdf_refinement.py`

`python -m unittest discover -s tests -p test_loudness_latch_bdf_refinement.py -v`

La regresión reconstruye todos los intervalos y comprueba dQ/dt directamente
desde ambos historiales reales con Decimal80, el estado serializado,
C10/R, los residuos del solve, decisiones locales seleccionadas y memoria
conservada en rechazos. No compara la memoria virtual del integrador como
si fuera una carga física.

## Alcance

Las tolerancias anteriores son una política numérica de laboratorio;
no son constantes eléctricas ni mediciones de un Model D. El modelo
conserva las fuentes, unidades, dominio y cargas omitidas del corte
[BDF2 sobre carga](BIESTABLE_BDF2_CARGA.md). El estimador local no demuestra
un error global; el solver espacial compartido no aporta una solución
exacta independiente. No se admiten identificación de carga vintage,
conmutación física, audio ni tiempo real por estrechar la malla.

La [auditoría entre muestras](BIESTABLE_OBSERVACION_ENTRE_MUESTRAS.md)
usa una rejilla fija, puntos medios y los máximos originales. Son diagnósticos
provisionales; no promueven la trayectoria fallida.
