# Entradas del defecto de carga y su aproximación muestreada

El 2 de octubre de 2026 se amplía el
[corpus de forzamiento](BIESTABLE_FORZAMIENTO_ENTRADAS.md) con los
[testigos conocidos](BIESTABLE_DEFECTO_CARGA_RESULTADOS.md), el
[diagnóstico de trazas](BIESTABLE_DEFECTO_MUESTREADO_RESULTADOS.md) y
sus recibos. Se reconstruyen las entradas de **28 informes** desde
**`a06d53d`**, sin repetir experimentos numéricos anteriores.

## Bytes y versiones

**215 entradas vigentes**: 212 blobs idénticos y las mismas tres
excepciones históricas LF→CRLF. Se mantienen fuentes completas, SHA
de blob/materialización y pertenencia por informe; cualquier otro
cambio se rechaza. No se modifica el fallo inicial de comparación
directa, los atributos Git o datos anteriores.

Se conservan las **cuatro versiones de pruebas fallidas** identificadas
por recibo: presupuesto BDF2, ruta SVD, polarización auxiliar y formato
Decimal del cero virtual. Las suites nuevas pasan al primer intento y
no añaden otra versión fallida. Los **12 + 2 fallos de cuadratura** de
los perfiles de carga son resultados numéricos distintos, conservados
en sus niveles originales, sin cambiar los dos niveles finales declarados.

Las entradas nuevas identifican las leyes de kernel/carga, productor de
testigos, productor de aproximación, protocolos, datos y adaptadores de
validación. La tasa reconstruida usa las cargas almacenadas de las
referencias propias congeladas; sus coeficientes/timestamps se mantienen.

## Evidencia y pruebas

[Datos](../evidence/loudness_latch_bdf_static_precision_charge_inputs.json.gz):
333.787 bytes; SHA comprimido
`1d926eca89c3b95c4a743f3bec0f082bbe27cdb597cdde2a7252911ceff5a935`;
SHA canónico
`e6f2eb560b58f18a0eaf0b5d8415ea7d10e6808966e5d093467819a5570f0840`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_charge_inputs_summary.json)
contiene identidades y versiones. La
[suite](../tests/test_loudness_latch_bdf_static_precision_charge_inputs.py)
reconstruye los 215 archivos y todas las versiones identificadas,
con controles negativos de contenido. El
[recibo](../evidence/loudness_latch_bdf_static_precision_charge_inputs_validation.json)
registra **2/2 pruebas**, primer intento, **44,8549351 s**, SHA antes/después
idénticos.

El bloque suma **12 pruebas nuevas** (6 + 4 + 2), todas en primer intento.
Se verifican 72 identidades BDF2, 18 BE, 512 actualizaciones RC racionales,
32 perfiles no lineales manufacturados y 496 aproximaciones sobre trazas.
Los 24 replays racionales del diagnóstico se cuentan aparte. No se repite
toda la suite histórica ni se añaden solves no lineales o trayectorias
físicas nuevas. El archivo de entradas no añade solves.

```powershell
python tools/loudness_latch_bdf_static_precision_charge_inputs.py
python tools/validate_bdf_static_precision_charge_inputs.py
```

Identidad de bytes no verifica portabilidad BLAS, regularidad de Q en
conmutación o exactitud de la tasa interpolada. No hay defecto temporal
exacto del DAE, estimador independiente ni cota global desde DC; el gate
de **1 mV**, identificación física, audio y deadline permanecen abiertos.
