# Corpus de continuidad y transporte certificado de memoria

El [productor](../tools/loudness_latch_bdf_static_precision_certified_prefix_inputs.py)
amplía la auditoría con el intento de prefijo contiguo y su recibo primario.
Recibo aceptado, helper, dos pruebas y validator se fijan en `68752ac`;
corpus y resumen, en `4ef9ed5`, antes de validar.

Se reconstruyen **484 entradas de 84 informes**, con **116 hashes propios**
(84 informes y 32 helpers). Se conservan exactamente las tres excepciones
históricas LF→CRLF y las **trece versiones fallidas anteriores de tests**.
La evidencia incluye además el lanzamiento del productor fallido antes
de medir, su fuente completa ligada al blob `9b59056` y la corrección
posterior. No se añade una versión fallida de test: las ocho regresiones
primarias y dos del corpus pasan al primer intento.

Las dos pruebas del corpus pasan en **77,4796224 s**, con entradas idénticas
antes/después. Verifican recuperación de blobs, excepciones, versiones y
los nuevos campos tipados: un único intervalo adicional intentado, cero
admitidos, primer hueco en índice 1, reloj sin traslación y sin reset DC.
La duración realmente certificada permanece igual al primer soporte;
ninguna memoria rechazada alimenta otra etapa. La suite primaria pasa
en **92,8890656 s**, también con fuentes intactas.

[Datos](../evidence/loudness_latch_bdf_static_precision_certified_prefix_inputs.json.gz):
**383688 bytes**, SHA comprimido
`4450846870eff72412664366199e534bb92ae595724c7861d91f1dc498f8350f`,
canónico `1687205f6c6760f1b8274c0606eb17fef827912741ef09e3353184f4b01e43b5`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_certified_prefix_inputs_summary.json)
y [recibo](../evidence/loudness_latch_bdf_static_precision_certified_prefix_inputs_validation.json).

Los bytes del primer certificado, integrador original y atributos Git
permanecen intactos. La reconstrucción de entradas no prueba portabilidad
numérica o sonido vintage. El [resultado](BIESTABLE_PREFIJO_CERTIFICADO_RESULTADOS.md)
conserva 195,3125 ns de error real certificado, sin cierre de 1 mV global,
recorrido completo, física, voz o deadline.
