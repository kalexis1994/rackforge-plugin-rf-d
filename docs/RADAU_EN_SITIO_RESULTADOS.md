# Radau en ubicación final: resultados

2026-10-13. [Protocolo previo](RADAU_EN_SITIO_PROTOCOLO.md). Cambio de la
vida del Stamp y de su aceptación en Newton; Parts, ecuaciones eléctricas,
solver Schur, controlador y constantes originales conservados.

## Ensamblaje y estado

Mantiene la [voz condicionada admitida](SCHUR_CADENA_RESULTADOS.md):
CA3046 VCO1→BUS→ladder/VCAs/J7 y contorno cargado R59/Q18, con sus fuentes,
designadores, conflictos e incertidumbres. No añade parámetros audibles ni
identificación vintage.229 estados HIGH/LOW,458 correcciones y140 exteriores.

Stamp::initialize escribe residual458, Jacobiano458×458 y candidatas
directamente en un destino inicializado. Misma secuencia parts0?→parts1?,
misma suma Radau, G/M, multiplicaciones y cero del término no diagonal.
Cada preparación exitosa repone todos los coeficientes, sin usar el J anterior.
La fachada linearize conserva su firma y resultados.

Dos buffers locales seguros contienen el Stamp actual y el trial. La
aceptación guarda sólo incrementos/corrección y permuta referencias a
buffers, sin llevar el Stamp grande dentro del Option. Un trial rechazado
conserva el Stamp actual; después de un fallo, el destino puede reutilizarse.
No cambia Newton, line search, refinamiento, tolerancias o publicación externa.
Sin unsafe, heap nuevo o cache entre J/trials. blank devuelve un inicializador
constante: la API no demuestra por sí sola cuántas copias elimina el binario.
[Receta reproducible](../tools/prepare_radau_inplace.py).

## Costo pareado con identidad

84 parejas congeladas ON/OFF,2/1 µs y coarse/mid/end. El motor de cadena
admitido es el control; LU completo verifica el packet y gates previos.
Warmup separado y cinco rondas alternadas. Por pareja, identidad1834 campos
por bits, iteraciones y trials, también dentro de las rondas medidas.

Ratios: 1.3846827×, 1.3529998×, 1.4413459×, 1.4003650×, 1.4156996×.
Mediana **1.4003650×**, equivalente a
**28.59% menos tiempo** en ese banco/plataforma.
Supera1.10: no corresponde ejecutar la confirmación reservada para utilidad
marginal. No se repite timing para elegir el mejor resultado.
[Banco](../evidence/voice_schur_refined_radauinplacebench01.json).

## Matrices, recuperación y herencia explícita

396 trazas completas J/b/correcciones, LU crudo/refinado y estadísticas
de refinamiento coinciden con el banco anterior por bytes. Permite heredar
**181.368 filas lineales Decimal100**; no se reejecutan sus ecuaciones.
84 raíces completas por bytes permiten heredar38.472 ecuaciones de banco.
1.680 observaciones de memoria y2.016 corrientes LM741 vuelven a medirse
y pasan los gates previos. [Banco/replay](../evidence/voice_schur_refined_radauinplacebank01.json).

11 regresiones de ensamblaje pasan con replay idéntico. En84 stamps se
comparan todos los bits de **17.620.176 coeficientes J**,38.472 residuales
y76.944 coordenadas HIGH/LOW de candidatas. La fachada coincide también.
Reinicialización A→B→A, destino envenenado con NaN, dt inválido, teclado
fuera de dominio, error de primera/segunda etapa, recuperación posterior,
trial rechazado y permuta de referencias conservan resultados/clases de error.
Se verifica la dirección de las referencias y ambos stamps después de aceptar.
[Regresiones](../evidence/voice_schur_refined_radauinplacestructure01.json).

## Cuatro recorridos nuevos, mismos datos completos

Ventana8.438→11.442 ms desde las cuatro historias/propuestas propias,
mismo controlador, parámetros, reloj y receta.

| Final decay | h máximo µs | Accepted | Wall del perfil s |
| --- | ---: | ---: | ---: |
| ON | 2 | 3020 | 74.8299 |
| ON | 1 | 3704 | 85.4812 |
| OFF | 2 | 2987 | 73.5948 |
| OFF | 1 | 3674 | 83.0381 |

Campaña318.104582 s, incluidos I/O y replays. Estos walls históricos
no son una medición pareada de aceleración. [Nativo](../evidence/voice_radau_inplace_native01.json).

**Los40 archivos de datos exportados son idénticos por bytes** a la campaña
admitida: selected con etapas/observaciones/balances, checkpoints, restores,
prefijos repetidos y rollback. Inventario completo, sin incluir el ejecutable
o timers como datos idénticos. Total20628988 bytes de datos.
13385 accepted/26770 finos,24 restores,368 avances repetidos,16 corrupciones
y8 rollbacks se reejecutan y conservan sus conteos. Los archivos originales
se mantienen protegidos; cada pareja lleva ambas rutas y su hash.

Esa identidad permite heredar las **38.472 ecuaciones temporales** del
grafo/FD/Q Decimal100 y los gates de LTE, masas, corrientes, balances,
resets, comparaciones229 al mismo reloj y unión con el tramo previo.
No se vuelve a ejecutar el grafo ni se hereda por cercanía de voltajes.
La cobertura sigue siendo la de esos exports/selecciones, sin declarar
todos los estados internos no exportados como una medición independiente.
[Identidad temporal y alcance](../evidence/voice_radau_inplace_trajectory01.json).

## Admisión y siguiente bloque

**Ensamblaje en sitio admitido para esta ventana condicionada de laboratorio**.
[QA](../evidence/voice_radau_inplace_tests01.json) conserva fuentes y privados
anteriores;248 tests Rust heredados por identidad, no reejecutados.
Sin biblioteca/SPICE, duración/audio nuevos, contorno desde silencio,
periodicidad asintótica, identificación física o DSP/RT admitidos.

La API de buffers sigue siendo de laboratorio con stack32 MiB; no acredita
el presupuesto de memoria del producto. Siguiente: fijar una integración
portable del conjunto229 con ownership del workspace y contrato de memoria,
separando esa promoción de las mediciones de heap/deadline. Eliminar pasos
de traslado debe preservar datos, rechazos y confirmación atómica del conjunto.
