# Corpus de entradas del estado post-KEY

El [productor](../tools/loudness_latch_bdf_static_precision_key_inputs.py)
amplía el corpus de DC con ambas mediciones del evento y su recibo de
validación. Helper, dos regresiones, validator y recibo primario aceptado
se fijan en `a14dea4` antes de generar; datos del corpus en `7e3de91` antes
de validar. No se repite ningún solve ni se cambia un informe previo.

Se reconstruyen **439 entradas de 76 informes**, con tres excepciones
históricas LF→CRLF y **diez versiones fallidas de tests**. La décima es la
fixture que exigía igualdad exacta con una cota exterior: su fuente está
archivada en el primer intento del recibo post-KEY y en el blob `f4e0933`.
El test vigente es el de `7ba069e`; ambas identidades son distintas y se
comprueban por versión. El fallo de import anterior se conserva separado,
con cero candidatos, fuente histórica Git y recibo ligado por SHA.

Los **104 hashes propios** ligan 76 informes y 28 helpers de reconstrucción.
Todos los bytes se cotejan con su blob Git y entrada original; las tres
excepciones se recuperan exactamente, sin normalizar JSON para ocultar
contenido. Se conserva la validación DC de dos intentos, junto con los
intentos previos de todo el corpus. Cada intento tiene entradas idénticas
antes/después. Los nuevos recibos usan la política `-text` ya vigente.

Las dos pruebas pasan al primer intento, **71,2107975 s**. Se comprueban
además schemas del evento/escala, las doce cajas nuevas, los rechazos de
la primera escala y binary64, reloj cero, certificado sólo de laboratorio
y los dos intentos primarios del evento. No se altera modelo o tolerancias.

[Datos](../evidence/loudness_latch_bdf_static_precision_key_inputs.json.gz): **375042 bytes**,
SHA comprimido `ba4edb9a4101e6273b5825c81fb204909695545c72f2ead5016d03f23be3816a`,
canónico `f3d84f019a5b7f5ba29f554a9c1647a99b7bfe12a879bafb6227686c3645526d`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_key_inputs_summary.json)
y [recibo](../evidence/loudness_latch_bdf_static_precision_key_inputs_validation.json).

Las ocho regresiones primarias pasan en el segundo intento y las dos del
corpus en el primero: **diez pruebas nuevas aceptadas**, con el fallo
conservado y sin regenerar mediciones. La procedencia no certifica hardware,
trayectoria temporal global, voz audible o deadline.
