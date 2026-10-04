# Corpus de acciones dirigidas del residual

El [productor](../tools/loudness_latch_bdf_static_precision_residual_action_inputs.py)
añade la acción del RHS y su recibo primario. Recibo aceptado, helper,
dos tests y validator se congelan en `8b7b67b`; corpus y resumen,
en `3a979f4`, antes de validar.

Se reconstruyen **518 entradas de 90 informes**, con **125 hashes propios**
(90 informes y 35 helpers). Se conservan las tres excepciones históricas
LF→CRLF y las **trece versiones anteriores de tests fallidos**. Este corte
no añade fallos o correcciones: ocho regresiones primarias y dos del corpus
pasan al primer intento.

Las ocho primarias pasan en **193,2137798 s**; las dos del corpus,
en **85,3391684 s**. Los dos recibos verifican entradas idénticas antes
y después. Los campos tipados nuevos ligan el cuarto soporte, selección
primaria [1,0], dos variantes aceptadas, cuatro intervalos certificados
hasta su endpoint y ausencia de hueco en ese soporte. Se verifican
16 inversas y tasas reutilizadas, 128 certificados de acción y cero
solves, precondicionadores, métricas o consultas LDL nuevos.

El corpus mantiene el lanzamiento fallido histórico del prefijo fino,
su fuente y fase de diagnóstico, y sus otros bancos rechazados. Una
mejora posterior de comparación no modifica ni elimina esas evidencias.
Tampoco elimina corrientes pequeñas, regulariza el circuito o cancela
restos independientes para cerrar el nuevo soporte.

[Datos](../evidence/loudness_latch_bdf_static_precision_residual_action_inputs.json.gz):
**387645 bytes**, SHA comprimido
`210ce8712541565d0c17815d61baa87b1311f1dbd622fa735cc28cf41dce2f6e`,
canónico `74f74ad777790cb436c5546be5b0a122a92565d74daf18ad3dadead43803dd95`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_residual_action_inputs_summary.json)
y [recibo](../evidence/loudness_latch_bdf_static_precision_residual_action_inputs_validation.json).

Una auditoría final recupera las 518 entradas y 125 hashes propios desde
Git y verifica las trece fuentes fallidas. Helpers y protocolo coinciden
con `01ecdcb`; datos y resumen numéricos, con `984392b`. Atributos Git,
integrador, helper y datos del prefijo anterior permanecen intactos.
Recuperar bytes no prueba portabilidad numérica o correspondencia sonora.
El [resultado](BIESTABLE_ACCION_RESIDUAL_RESULTADOS.md) admite sólo cuatro
intervalos nominales; trayectoria completa, 1 mV global, parámetros
físicos, audio, ejecución nativa y deadline conservan sus gates.
