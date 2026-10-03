# Comparación dirigida de seis bloques

## Partición y certificado

El [protocolo](BIESTABLE_COMPARACION_BLOQUES_PROTOCOLO.md), helper y productor
se fijaron en `a8664e0` antes de medir. La partición sigue las memorias del
circuito documental CA3046: audio (17), C10, C2, C4, C7 y junturas (4).
Se conserva la norma ponderada anterior, los ocho intervalos y sus ocho
celdas, las inversas ideales encerradas y los L1 del residual por celda.
No se ajustan los grupos ni pesos a las medidas; no hay nuevos solves.

Las normas de bloque del error tangente ideal satisfacen una desigualdad
con matriz Metzler 6×6. La diagonal conserva la medida logarítmica interna
firmada; los otros términos conservan los acoplamientos dirigidos. Se usa
la norma integrada del forzamiento por máximos de columna sobre filas de
cada grupo, manteniendo la conversión a voltaje de cada uno de los 94 nodos.

Se encierran **64 núcleos de extremo y 64 de pico**. El extremo usa una
serie positiva de la matriz desplazada, damping racional y cuadrados.
El pico inicial elimina sólo diagonales negativas durante el subintervalo
escalado y se duplica con P2=max_entrada(P,P*E). Es una cota para todas las
duraciones entre cero y h, no sólo una rejilla. Cada serie tiene 32 términos,
cola geométrica y redondeo exterior de 256 bits; el soporte transitivo
conserva ceros exactos. El dominio fijado de norma escalada <=4096 pasa
en las 64 celdas. Los recintos anteriores de inversa se reconstruyen sin cambios.

## Comparación completa

Todos los casos dan cotas menores que la propagación escalar por celdas,
sin intersección retrospectiva. La tabla presenta el término forzado con
**anclaje cero hipotético** y el coeficiente del anclaje ponderado desconocido.
Son cotas de la ODE tangente ideal variable, no errores observados del DAE.

| Ventana | Subpasos | Cota escalar anterior (V) | Cota dirigida de bloques (V) | Coeficiente de anclaje, pico nodal |
| --- | --- | --- | --- | --- |
| prefix | 2 | 113.903325 | 0.0595069218 | 534473.222 |
| prefix | 4 | 0.0105575284 | 0.0000337170217 | 1616.82485 |
| attack | 2 | 4.90999919E+254 | 6.26714339E+251 | 4.24883157E+259 |
| attack | 4 | 1.42077786E+123 | 1.03982664E+121 | 1.02455881E+130 |
| reset | 2 | 0.00000457299253 | 0.00000367506766 | 198.104053 |
| reset | 4 | 5.29266303E-7 | 4.86537697E-7 | 197.892775 |
| tail | 2 | 1.19355917E+18 | 3.00335182E+16 | 3.37514089E+24 |
| tail | 4 | 189921.923 | 4828.01837 | 4.18247928E+12 |

Prefijo N4 pasa de ~10,56 mV a **~33,72 µV** y reset N4 de ~0,529 a
**~0,487 µV** de término forzado. Ataque y cola siguen enormes: la partición
física conserva dirección, pero dentro de cada grupo se pierden signos y
dependencias. Estas cotas no prueban crecimiento real, inestabilidad ni
parecido al instrumento. La mejora incluye agrupación y conversión nodal;
no se atribuye exclusivamente a una de ellas sin un contraste separado.

El mayor valor de max_celda sum_b M_ab pertenece al grupo de junturas
en los ocho casos. Es una cota de fila de la matriz de comparación, no
una amplificación observada. Los acoplamientos internos y sus signos
constituyen el siguiente diagnóstico; la partición permanece documentada.

El forzamiento nuevo se propaga con P, incluso cuando E contrae. Los
vectores de anclaje y término forzado permanecen separados en cada celda.
La conversión nodal archiva ambos coeficientes; no supone error inicial cero
para aceptar gates. Las ocho cubiertas son no contiguas y no se encadenan.

## Evidencia y regresiones

[Datos](../evidence/loudness_latch_bdf_static_precision_block_comparison.json.gz):
**8722816 bytes**, SHA comprimido
`fbb8b2bb67f137aec07626c5bbeaad9ea838b678980f7afe59feed15d5373504`,
SHA canónico `981bca9bf2e36f3d290bf7c6568c39163891ebe8adc10e740ca25ebf6e1247e3`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_block_comparison_summary.json).
Se conserva partición, cada matriz de comparación, forzamiento, 94 mapas
nodales, E/P, cola, desplazamiento, escala, hashes y propagaciones.

La [suite](../tests/test_loudness_latch_block_comparison.py) pasa **6/6 al primer intento**
en 123.5605623 s. La cascada triangular se contrasta con su solución
exponencial a Decimal180 en tres duraciones y 33 consultas interiores por
caso, incluyendo el máximo interior exacto 1/2 en t=log(2). Estos testigos
no sustituyen el certificado. Se contrastan productos diádicos, ceros,
dominios, matrices de bloque racionales, máximos de columna con forzamientos
disjuntos, contracción, pulso tardío y continuidad. Se reconstruyen todas las
**64 inversas, métricas, núcleos y propagaciones**, fuentes, bytes y alcance.
El [recibo](../evidence/loudness_latch_bdf_static_precision_block_comparison_validation.json)
conserva SHA antes/después idénticos.

El [corpus ampliado](BIESTABLE_COMPARACION_BLOQUES_ENTRADAS.md) verifica las
entradas desde Git y preserva las versiones e intentos anteriores.
Los gates binary64 rechazados, atributos Git, datos y sonido no cambian.
**1 mV global, física, audio y deadline siguen abiertos.** Faltan restos
N_I/N_Q, anclaje/DC y trayectoria completa. Próximo corte: aislar la
contribución del grupo de junturas y sus cancelaciones internas, sin
repartir memorias o cambiar pesos según resultados favorables.

```powershell
python tools/loudness_latch_bdf_static_precision_block_comparison.py
python tools/validate_bdf_static_precision_block_comparison.py
```
