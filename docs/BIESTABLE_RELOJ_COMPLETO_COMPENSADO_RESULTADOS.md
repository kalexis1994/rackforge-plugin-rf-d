# J66 compensado: trayectoria completa con reloj publicado

El [protocolo](BIESTABLE_RELOJ_COMPLETO_COMPENSADO_PROTOCOLO.md) y productor
se fijaron en `de484bb`. Tras las cuatro ventanas, la variante conserva
el residual original y usa estados propios en **0..3 ms**, sobre el reloj
publicado E4G8. Es un contraste de implementación con el mismo circuito
documental, fuentes y parámetros sintéticos; no existe referencia física.

## Resultado

| Comprobación | Resultado | Gate |
| --- | --- | --- |
| DC recién calculado / DC archivado | Estado completo idéntico | Igualdad canónica/tipada |
| Linaje y reloj originales | 6.486 intervalos verificados | Tiempo, fuente y estado anterior exactos |
| Continuación con memoria propia | 6.486/6.486 válidos, hasta 3 ms | Sin sustitución, rechazo o reset |
| Máximo nodal compensado | **6,20949×10⁻¹² V** | <10⁻⁸ V |
| Máximo de memoria en coordenada V | **8,76941×10⁻¹² V** | <10⁻⁸ V |
| Máximo KCL publicado | **9,95576×10⁻¹² A** | <10⁻¹¹ A |
| Máximo error de ecuación de rama | **5,12666×10⁻²⁴ V** | <10⁻¹⁴ V |
| Iteraciones candidato / referencia | **13.064 / 13.064** | Conteo, sin benchmark |

Pasan los 6.486 contrastes de nodos y los 6.486 de memoria. El máximo nodal
está en el nodo 28, Q18_COLLECTOR, en el último intervalo a 3 ms. Se incluyen
los componentes low de nodos y capacitores; las cuatro cargas usan escala
10⁻¹² C/V exclusivamente numérica. Todos los solves conservan KCL y
corrección Newton originales, publicación directa y restauración exacta.

Se reproducen los dos intervalos de arranque (BE y BDF2) y 6.484 BDF2
posteriores. Los **49 rechazos históricos no se ejecutan**: sus decisiones,
predictores y sombras pertenecen al controlador original. Aquí el reloj
está impuesto. No se afirma equivalencia del controlador adaptativo.

## Evidencia y validación

[Datos completos](../evidence/loudness_latch_bdf_static_precision_fixed_clock.json.gz):
**27.793.726 bytes**, SHA256 comprimido
`c9cfa170690b0cde1d935220797bc56c2748a260ffecb32afaebd75f1864a7d6`;
SHA256 JSON canónico
`5dae4c2ae22999e42e2884b29c8089febfde0f4b600d57bb37d3bf510048b110`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_fixed_clock_summary.json)
identifica **133 entradas**, HEAD contextual `de484bb`, extremos y máximos.
Los SHA permanecen iguales antes/después.

El [recibo](../evidence/loudness_latch_bdf_static_precision_fixed_clock_validation.json)
registra **4/4 pruebas**, un intento exitoso, 59,6922 s: linaje de los 6.486
intervalos, DC fresco, todas las publicaciones/diferencias, seis replays
nuevos seleccionados previamente por región y conservación ante presupuesto
inválido, almacenamiento y alcance. No se repite la suite histórica.

`python tools/validate_bdf_static_precision_fixed_clock.py`

## Gate siguiente

La equivalencia de implementación pasa en este reloj completo. Falta ejecutar
el controlador adaptativo con el Jacobiano candidato y conservar sus propios
rechazos, sombras y decisiones. La comparación temporal anterior desde DC
mantiene **8,234 mV frente a 1 mV**; este resultado no la modifica ni aporta
una cota continua. Contorno y carga permanecen compartidos. Física vintage,
audio de voz completa y deadline siguen abiertos.
