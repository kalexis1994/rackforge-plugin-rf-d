# Corpus de balances integrados y variante Gauss

El 2 de octubre de 2026 se amplía el
[corpus interior](BIESTABLE_CARGA_INTERIOR_ENTRADAS.md) con los
[balances Simpson](BIESTABLE_BALANCE_CARGA_RESULTADOS.md), la
[variante Gauss](BIESTABLE_BALANCE_GAUSS_RESULTADOS.md) y sus recibos.
Se reconstruyen entradas de **36 informes** desde `de43d60`, sin repetir
experimentos históricos ni cambiar sus archivos o atributos Git.

## Identidades, intentos y observaciones

**246 entradas vigentes**: 243 blobs exactos y las tres excepciones
históricas LF→CRLF, con fuentes originales y SHA de blob/materialización.
Se conservan cinco versiones de pruebas fallidas identificadas por recibo:
las cuatro anteriores y la primera suite Simpson de este bloque.
Esta última conserva tanto la comparación independiente fallida como
el testigo Decimal 0^0 inválido. Su corrección no modifica las integrales.

Las observaciones numéricas se mantienen por método: 371 fallos del
contraste Simpson32/64; 271 de Simpson64/Gauss16; 391 residuales medios
constitutivos sobre 10 pA. No se suman como si fueran casos independientes.
La comparación Gauss8/16 pasa 496 intervalos y el soporte mixto;
no equivale a una cota del resto ni al criterio de voltaje de 1 mV.

El corpus incluye leyes, protocolos, productores, datos, resúmenes,
pruebas y adaptadores. El generador identifica además sus ayudantes y
los 36 informes. La auditoría de cierre verifica estas identidades
contra Git y reconstruye la fuente de cada intento histórico fallido.

## Archivo y regresiones

[Datos](../evidence/loudness_latch_bdf_static_precision_balance_inputs.json.gz):
339.686 bytes; SHA comprimido
`626359074e39ed972e573a209fd12784e2f2b8093ad36271474d0f03f7a7f469`;
SHA canónico
`b08dd20f1989e28b86bc84dab1068065ccdd946a66010d33eb4f22fbb8b28272`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_balance_inputs_summary.json)
conserva las identidades y versiones. La
[suite](../tests/test_loudness_latch_bdf_static_precision_balance_inputs.py)
reconstruye todos los archivos y versiones con controles negativos.
El [recibo](../evidence/loudness_latch_bdf_static_precision_balance_inputs_validation.json)
registra **2/2 pruebas**, primer intento, **48,7877337 s**, SHA
antes/después idénticos.

El bloque suma **11 pruebas nuevas**: cinco de Simpson, que pasan en
segundo intento con el original conservado; cuatro de Gauss y dos del
corpus, que pasan al primero. Las integraciones cubren 496 intervalos y
un soporte mixto, con precisión explícita, 24 contrastes independientes
por método, continuidad de carga y puente manufacturado. Se verifican
112 momentos de cuadratura y 28 raíces escalares de Legendre; no son
solves nuevos del circuito. No se repite toda la suite histórica.

```powershell
python tools/loudness_latch_bdf_static_precision_balance_inputs.py
python tools/validate_bdf_static_precision_balance_inputs.py
```

La identidad de bytes no admite física, audio, deadline ni portabilidad
numérica a otro BLAS/SO. El criterio global de **1 mV** sigue abierto.
