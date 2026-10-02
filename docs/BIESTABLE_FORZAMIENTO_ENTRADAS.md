# Entradas de forzamiento y calendarios refinados

El 2 de octubre de 2026 se amplía el
[corpus de curvatura](BIESTABLE_CURVATURA_ENTRADAS.md) con el
[intento bloqueado](BIESTABLE_FORZAMIENTO_INTENTO_INICIAL.md), la
[variante completada](BIESTABLE_FORZAMIENTO_RESULTADOS.md) y sus recibos.
Se reconstruyen las entradas de **24 informes** desde **`a96aa23`**.

## Resultado de bytes

**201 entradas vigentes**: 198 blobs idénticos y las mismas tres
excepciones históricas LF→CRLF, con sus fuentes completas archivadas.
Se conservan SHA de blob/materialización y pertenencia por informe.
Se rechaza cualquier alteración que no sea la transformación histórica
declarada. No se cambia el fallo original de comparación directa.

También se reconstruyen **cuatro versiones de pruebas fallidas** desde
sus recibos: presupuesto BDF2, ruta SVD, polarización auxiliar y formato
Decimal del cero virtual. Cada versión conserva fuente UTF-8 exacta,
SHA, ruta, comando e índice de intento. Las versiones vigentes proceden
de blobs, incluida la prueba del primer experimento importada como
testigo racional por la suite posterior.

Los fallos del primer experimento son evidencia diferente del fallo de
su prueba: dos detenciones de reloj por razón >2 y ocho adaptadores de
RHS bloqueados antes de resolver permanecen intactos. La variante
completada identifica además su planificador, protocolo y esos informes
anteriores como entradas congeladas. No normaliza atributos ni datos.

## Archivo y validación

[Datos](../evidence/loudness_latch_bdf_static_precision_forced_inputs.json.gz):
332.116 bytes; SHA comprimido
`645c981faef871ed0c2e52a8cfce4fd074c536a2b271a96d6b262afbaf0c36c3`;
SHA canónico
`fe0429ec785389c12a2c1d1fbb0bb692ad86058d8665c54612f3dd9c042d29c4`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_forced_inputs_summary.json)
incluye todas las identidades y versiones. La
[suite](../tests/test_loudness_latch_bdf_static_precision_forced_inputs.py)
reconstruye el corpus completo y rechaza contenido/fuentes alterados.
El [recibo](../evidence/loudness_latch_bdf_static_precision_forced_inputs_validation.json)
registra **2/2 pruebas**, primer intento, **43,6012156 s** y SHA
antes/después idénticos.

El bloque suma **11 pruebas nuevas** (4 + 5 + 2). Sólo la primera suite
necesitó un segundo intento; ambos se conservan. No se repite toda la
suite histórica. Los experimentos añaden **2.812 intervalos no lineales
publicados** (1.276 + 1.536), con dos intentos de reloj rechazados,
**1.024 solves espaciales** de variaciones y 24 lotes racionales de dos
RHS. Los 16 + 24 replays no lineales de regresión se cuentan aparte.
El archivo de entradas no añade solves. Tiempos offline no son deadlines.

```powershell
python tools/loudness_latch_bdf_static_precision_forced_inputs.py
python tools/validate_bdf_static_precision_forced_inputs.py
```

Identidad de bytes no prueba portabilidad de BLAS, identificación física,
defecto temporal exacto ni cota global. El forzamiento se extrae de
referencias condicionadas; no es un estimador independiente. El gate
temporal de **1 mV desde DC**, audio y deadline permanecen abiertos.
