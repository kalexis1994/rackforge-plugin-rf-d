# Inversa estructurada y propagación por celdas

## Variante y resultados

El [protocolo](BIESTABLE_PROPAGACION_CELDAS_PROTOCOLO.md) se fijó en
`154a98f` antes de medir. Conserva el primer término firmado E*Y y
acota el resto Neumann por fila. Intersecta siempre con el recinto por
fila de la serie completa y el recinto global anterior. Los productos
son diádicos exactos, calculados mediante enteros con denominador común.
Se preservan E, X, D y hashes de matrices brutas/finales reproducibles.

Las **64/64 celdas** contraen. En cada celda las **14.161 entradas**
son estrictamente más estrechas que el recinto global anterior:
**906.304 entradas** en total. El certificado no admite las inversas
binary64 cuyo gate backward permanece rechazado. No hay solves nuevos.

Se reconstruye el forzamiento por celda desde los residuales correlacionados,
los demás nodos y las restricciones Bernstein. Los L1 recombinados no
exceden sus presupuestos anteriores en ningún caso. Se conserva la misma
partición y los mismos pesos; sólo cambia el certificado del diagnóstico.

La propagación usa exp(mu*h) para el extremo del error entrante y
exp(max(mu,0)*h) para picos y forzamiento nuevo conocido por L1.
El anclaje desconocido permanece separado del término forzado. La tabla
presenta cotas de voltaje de la **ODE tangente ideal variable**; no errores
observados del DAE, ganancias físicas ni mediciones de sonido.

| Ventana | Subpasos | Pico forzado con anclaje cero hipotético (V) | Coeficiente del anclaje ponderado, pico nodal |
| --- | --- | --- | --- |
| prefix | 2 | 113.903325 | 705080923 |
| prefix | 4 | 0.0105575284 | 372133.287 |
| attack | 2 | 4.90999919E+254 | 3.29170903E+262 |
| attack | 4 | 1.42077786E+123 | 1.38707107E+132 |
| reset | 2 | 0.00000457299253 | 2930.72707 |
| reset | 4 | 5.29266303E-7 | 761.139200 |
| tail | 2 | 1.19355917E+18 | 1.29222858E+26 |
| tail | 4 | 189921.923 | 1.58552515E+14 |

Las ocho cotas son menores que las [cotas temporales uniformes anteriores](BIESTABLE_DESCRIPTOR_PONDERADO_RESULTADOS.md).
Reset N4 pasa de ~0,563 a **~0,529 µV**; prefijo N4, de ~1,024 a
~0,01056 V. Ataque N2 baja de ~3,778e314 a ~4,910e254 V, todavía enorme.
La tabla completa conserva casos desfavorables. No se atribuye por separado
la mejora a la estructura y a la distribución temporal: ambas cambian en
esta variante. Ningún coeficiente de anclaje se fija a cero para admitir gates.

## Evidencia y regresiones

[Datos](../evidence/loudness_latch_bdf_static_precision_cell_propagation.json.gz):
**1254544 bytes**, SHA comprimido
`3d734045dd0546555405abe60c34e16628299093e0165888f7a9011ade82eab8`,
SHA canónico `47130c2052cfbd5c21a5404277852dc442b281bebc38b38f256d5d7b25e07a6d`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_cell_propagation_summary.json).

La [suite](../tests/test_loudness_latch_cell_propagation.py) pasa **7/7 al primer intento**
en 120.5049707 s. Contrasta productos enteros con Fraction independiente,
inversa racional 2×2 y tres recintos, métricas asimétricas por fila/columna,
contracción, pulso tardío, forzamientos disjuntos, continuidad y guards.
Reconstruye **todas las 64 inversas**, sus hashes brutos/finales, forzamientos,
métricas y propagaciones desde las entradas congeladas. Verifica fuentes,
almacenamiento canónico y alcance. El [recibo](../evidence/loudness_latch_bdf_static_precision_cell_propagation_validation.json)
conserva SHA antes/después idénticos.

El [corpus ampliado](BIESTABLE_PROPAGACION_CELDAS_ENTRADAS.md) añade la
reconstrucción de fuentes y recibos. Las ocho ventanas seleccionan intervalos
no contiguos: las ocho celdas sólo cubren cada intervalo por separado.
Quedan pendientes restos no lineales, anclaje inicial/DC y recorrido completo.
**1 mV global, fidelidad física, audio y deadline siguen abiertos.**
Siguiente corte: explotar estructura de bloques para reducir las cotas de
estabilidad de ataque/cola antes de extenderlas al error no lineal completo.

```powershell
python tools/loudness_latch_bdf_static_precision_cell_propagation.py
python tools/validate_bdf_static_precision_cell_propagation.py
```
