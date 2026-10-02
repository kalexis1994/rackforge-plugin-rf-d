# Reproducción del corpus de memoria acumulada

El 2 de octubre de 2026 se amplió el
[corpus de trayectorias](BIESTABLE_TRAYECTORIAS_ENTRADAS.md) con las
[ventanas de 64 pasos](BIESTABLE_MEMORIA_LARGA_RESULTADOS.md),
la [base de historia doble](BIESTABLE_BASE_DOBLE_RESULTADOS.md) y sus
recibos. Se reconstruyen entradas de doce informes numéricos/de validación
desde la revisión **`bfdaf84`**, sin repetir integración ni modificar
resultados anteriores.

## Identidades y versiones

Son **161 entradas vigentes**: 158 blobs con bytes idénticos y las mismas
tres excepciones históricas LF→CRLF ya documentadas. Se conserva el fallo
de comparación directa original, y se verifica la reconstrucción de cada
entrada por su SHA. No se normalizan datos ni `.gitattributes` congelados.

Hay **dos fuentes de pruebas anteriores** recuperadas de recibos fallidos
con ruta, comando, intento y SHA:

- El adaptador de presupuesto de la continuación de 16 pasos usaba un
  intervalo fuera del dominio de razón BDF2 antes de pedir presupuesto cero.
- El adaptador de base completa comparaba SVD sin vectores contra la ruta
  con vectores, con diferencias en singular values pequeños.

Las versiones vigentes proceden de blobs; las anteriores nunca commiteadas
proceden de sus recibos. Se rechaza una versión sin vínculo o con contenido
alterado. Se conservan datos, protocolos y gates numéricos mientras se
corrigen esos adaptadores.

## Evidencia

[Archivo](../evidence/loudness_latch_bdf_static_precision_memory_inputs.json.gz):
324.216 bytes; SHA comprimido
`17dfee5952a69275f096cf931d33fd13855c62525e6150b779d631487add107c`;
SHA canónico
`69760612cc579f4f072deefa3cc93fe25b858ad4334a2784e4610915ed71bf55`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_memory_inputs_summary.json)
incluye todos los SHA y pertenencia por informe.
El [recibo](../evidence/loudness_latch_bdf_static_precision_memory_inputs_validation.json)
conserva **2/2 pruebas**, un intento exitoso de 24,456 s: reconstrucción
completa, controles negativos y entradas idénticas antes/después.
Junto con las cinco pruebas de continuaciones y cuatro de base completa,
este corte suma **11 pruebas nuevas**, sin repetir toda la suite histórica.

```
python tools/loudness_latch_bdf_static_precision_memory_inputs.py
python tools/validate_bdf_static_precision_memory_inputs.py
```

La reconstrucción de bytes no certifica portabilidad de BLAS, precisión de
SVD, fidelidad vintage, error temporal ni deadline de audio. Los nuevos
informes mantienen cada uno su gate y alcance.
