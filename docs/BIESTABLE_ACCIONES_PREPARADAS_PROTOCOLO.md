# Acciones preparadas: protocolo congelado

## Banco e identidad

Una pasada por las 64 macroceldas completas de los soportes 16–23 de la
[continuación compartida](BIESTABLE_CONTINUACION_COMPARTIDA_RESULTADOS.md),
variante width=8, trial=1. Leer los 17 artefactos tipados mediante el loader
congelado y verificar sus SHA comprimidos y canónicos. El helper original
`loudness_latch_residual_action.py` es el control A; el helper inmutable
`loudness_latch_prepared_action.py` es B. No cambiar fuentes históricas.

Preparar una vez X, D, E, q, sumas por fila y factores racionales derivados.
Copiar a tuplas de Fraction, sin alias mutables. Identificar todos los datos
de entrada, incluido el recinto completo, radio, dominios y flags de prueba.
Verificar identidad de entrada e integridad del estado antes de cada budget.
No preparar ni reutilizar RHS: cada macrocelda tiene sus polinomios con signo,
restos independientes, duración y ocho subceldas.

## Medición fijada antes de ejecutar

Recorrer soportes 16–23 y celdas 0–7 en orden. Alternar A→B si el índice plano
es par, B→A si es impar: 32 pares AB y 32 BA. Una sola pasada, sin calentamiento
ni selección posterior. 64 budgets por helper, 512 certificados de subcelda
por helper. Medir wall con perf_counter_ns y CPU con process_time_ns; conservar
cada muestra y entorno. Medir preparación separadamente y sumarla al total B.

Incluir verificación por llamada, compilación, Bernstein, restos, corrección,
cola, intersección y normas de salida. Excluir de ambos temporizadores lectura
de archivos, compresión, comparación y serialización canónica; los helpers
sí incluyen las conversiones internas a texto que forman sus certificados.
Registrar mediana, totales, separación AB/BA y razón A/(B+preparación).
Una pasada en este equipo describe este banco; no estima distribución de
rendimiento, deadline o ganancia en una implementación nativa.

## Gate de equivalencia

Comparar directamente todos los bytes canónicos A == B == acción archivada
por macrocelda. Registrar SHA y longitudes, sin sustituir igualdad de bytes
por comparación de picos. Conservar todo el certificado original por su ruta,
SHA tipado, trial y celda; si difiere, archivar completos los tres resultados
antes de detener el banco. Conservar traceback y fuentes exactas si falla.
Archivar el intento y commitear antes de corregir; congelar corrección antes
de repetir. Destinos frescos y distintos de todas las entradas.

Mantener orden racional, redondeos dirigidos, escala física, primera corrección,
restos independientes, particiones, norma fija y gates. Validar reproducción
de las 64 acciones, contextos alterados, formas inválidas, estado sin alias y
RHS/duración alterados. Congelar datos, tests y validator antes de validar.
Ampliar corpus con recibos y fuentes recuperables desde Git.

## Alcance

Laboratorio offline nominal. Los 24 soportes hasta ≈225 µs y su cota acumulada
se conservan: este bloque no extiende tiempo. Gate global de 1 mV, fidelidad
física, audio, implementación nativa y deadline continúan abiertos.
