# Corpus de la métrica cuadrática de junturas

Se amplía la reconstrucción a **63 informes y 368 entradas**:
**365 blobs idénticos** y las tres excepciones históricas LF→CRLF.
Se conservan ocho versiones fallidas anteriores de tests. Helpers, pruebas
y validador se congelaron en `03419fd` antes de generar. Se añaden la
variante de métrica y su recibo, con todas las fuentes transitivas.
No cambian atributos Git, fuentes congeladas, normas anteriores o gates.

[Datos](../evidence/loudness_latch_bdf_static_precision_metric_inputs.json.gz):
**360630 bytes**, SHA comprimido
`656aa8a3ce6321c314194209de6b539c7b43bd15af22a67db8002cabe4e07dfe`,
SHA canónico `4293b801a8e8342c3f0d48fa5f08bfc3ce50e9b6a881e23d43da7f26aac78169`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_metric_inputs_summary.json).
La referencia Git exacta, membresía y versiones archivadas identifican
todas las entradas y rechazan cambios de contenido en las excepciones.

La [suite](../tests/test_loudness_latch_bdf_static_precision_metric_inputs.py)
pasa **2/2 al primer intento**, 63.0127764 s. Comprueba cobertura exacta de identidades, recuperación de blobs, esquemas,
destinos propios, versiones y bytes canónicos. Distingue sistemas de métrica
numérica de resoluciones de circuito y conserva candidatos rechazados como
datos, sin confundirlos con pruebas fallidas. El [recibo](../evidence/loudness_latch_bdf_static_precision_metric_inputs_validation.json)
registra comandos, conteos, salidas e igualdad de SHA antes/después.

Este bloque añade **nueve regresiones nuevas**, todas pasan al primer intento:
siete de métrica y dos de corpus. No hay nuevas versiones de tests fallidas
ni intentos de archivo rechazados.
No se promueven cotas desfavorables ni se modifican datos anteriores.
**1 mV global sigue abierto**, con anclaje y restos desconocidos e intervalos
no contiguos. La reconstrucción de bytes no prueba fidelidad o audio.

```powershell
python tools/loudness_latch_bdf_static_precision_metric_inputs.py
python tools/validate_bdf_static_precision_metric_inputs.py
```
