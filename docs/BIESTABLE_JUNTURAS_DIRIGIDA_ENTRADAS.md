# Corpus del certificado de tasa dirigida

Se amplía la reconstrucción a **65 informes y 379 entradas**:
**376 blobs idénticos** y tres excepciones históricas LF→CRLF.
Conserva ocho versiones fallidas anteriores de tests. Helpers, pruebas y
validador se congelaron en `9b1c1f4` antes de generar el corpus.
Se añaden informe dirigido y recibo, con todas sus fuentes transitivas.
No cambian atributos Git, bytes anteriores, parámetros o gates.

[Datos](../evidence/loudness_latch_bdf_static_precision_directed_inputs.json.gz):
**361920 bytes**, SHA comprimido
`bec81784c3dc1da71233e58781f9dc37f82a1a580f7daadaa714b00c6080ba64`,
SHA canónico `785e933771425fc7cf03bdb6d104a1db01001fdb0e98575b68a75ab8342823d2`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_directed_inputs_summary.json).
La referencia Git exacta identifica blobs, fuentes, membresía y versiones
históricas. La reconstrucción declara y reproduce las excepciones, y
rechaza cambios de contenido además de cambios no identificados de fuente.

La [suite](../tests/test_loudness_latch_bdf_static_precision_directed_inputs.py)
pasa **2/2 al primer intento**, 66.7948900 s. Comprueba cobertura exacta de identidades, recuperación de blobs, excepciones,
versiones de tests, esquemas y destinos propios. Mantiene separados tasa,
métricas y campos de admisión; verifica que la variante dirigida conserva
norma y P anteriores. El [recibo](../evidence/loudness_latch_bdf_static_precision_directed_inputs_validation.json)
registra comando, conteos, salida y SHA antes/después idénticos.

Este bloque suma **ocho regresiones nuevas**, todas pasan al primer intento:
seis dirigidas y dos de reconstrucción. No hay nuevos intentos fallidos
de validación ni archivos rechazados.
Se conservan candidatos de reset rechazados y cotas enormes de ataque N2
como datos, sin alterar versiones de tests o fuentes anteriores.
**1 mV global sigue abierto.** Bytes recuperables y cotas tangentes no
certifican anclaje, restos, recorrido, sonido o física del Model D.

```powershell
python tools/loudness_latch_bdf_static_precision_directed_inputs.py
python tools/validate_bdf_static_precision_directed_inputs.py
```
