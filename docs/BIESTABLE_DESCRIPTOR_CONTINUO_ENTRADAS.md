# Entradas del descriptor continuo

El corpus ampliado incluye **49 informes**, **295 entradas** y **siete versiones
fallidas de tests** desde sus recibos. Se reconstruyen **292 blobs idénticos**
y las tres excepciones históricas LF→CRLF declaradas. No cambian atributos,
bytes de datos previos ni gates. La referencia de reconstrucción es `e68f195`.

Se añaden los informes de ocho inversas flotantes fallidas y ocho solves
racionales con gate binary64 fallido, las ocho inversas levantadas certificadas,
el presupuesto uniforme incorrecto preservado, el presupuesto de norma
integrada corregido y los dos recibos. El rechazo matemático de una cota y
el fallo numérico del solver se mantienen como hechos distintos.
La última versión fallida de test se conserva en UTF-8 con su SHA: comparó
Decimal100 con un producto bajo el contexto por defecto de 28 cifras.
La comparación corregida usa Fraction; productor, leyes y datos permanecen iguales.

Los archivos del helper, test y validador de corpus se commitearon antes de
reconstruir. Se verifica cada identidad de informe, entrada y versión de test,
incluyendo la etiqueta Gauss heredada previamente declarada. JSON canónico
conserva esquemas propios para los tres recibos nuevos de este bloque.

[Datos](../evidence/loudness_latch_bdf_static_precision_descriptor_inputs.json.gz):
**350.301 bytes**, SHA comprimido
`f5f47505682e17999a059ece68bb3344a214097bc2cbfc86541d29db0c7df8c0`,
SHA canónico `31dc571ac36892e37c040fbb7117ac976e460fc3324b2bb6bbb9d92376f34709`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_descriptor_inputs_summary.json).
La [suite](../tests/test_loudness_latch_bdf_static_precision_descriptor_inputs.py)
pasa **2/2** al primer intento, 57,0645402 s.
El [recibo](../evidence/loudness_latch_bdf_static_precision_descriptor_inputs_validation.json)
conserva comando, salidas, entorno, fuentes antes/después idénticas y conteo.

El bloque suma **11 regresiones nuevas**: seis de descriptor pasan en el segundo
intento, tres de norma integrada y dos de corpus pasan al primero.
El intento matemático fallido no fue detectado por la primera suite aprobada;
la regresión adicional de soportes disjuntos documenta el contraejemplo.
Todos los intentos anteriores permanecen identificados.

```powershell
python tools/loudness_latch_bdf_static_precision_descriptor_inputs.py
python tools/validate_bdf_static_precision_descriptor_inputs.py
```

La reconstrucción preserva evidencia; no repite experimentos de circuito,
no encierra coeficientes ideales, estabilidad no lineal, anclaje, trayectoria
completa, error global de voltaje, física, sonido ni deadline.
