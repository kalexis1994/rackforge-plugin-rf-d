# Espectro racional del bloque de junturas RMS

## Certificado y cambios fijados

El [protocolo](BIESTABLE_JUNTURAS_ESPECTRO_PROTOCOLO.md), helper y productor
se fijaron en `196fb46` antes de medir. Se mantiene la norma RMS, sus
conversiones, seis grupos, pesos, referencia de anclaje, residuales y 64 celdas.
Sólo se reemplaza la diagonal de junturas de la matriz de comparación.
Se reutilizan las partes simétricas intervalares validadas del bloque anterior,
sin resolver inversas del circuito ni generar estados o trayectorias.

Para cada recinto simétrico se forma centro C y radio R. El presupuesto
delta=max_i sum_j Rij encierra la perturbación de su mayor autovalor.
El centro se acota con **32 bisecciones racionales**, verificando positividad
de alpha*I-C mediante LDLᵀ exacto sin pivoteo. Se conserva la prueba superior
con sus factores y pivotes, y cada consulta por valor, resultado y SHA.
Un pivote cero o negativo rechaza positividad estricta; no se usa tolerancia.

Las **64 cotas** son estrictamente más estrechas que Gershgorin.
Se evalúan **2.112 consultas LDLᵀ** (33 por celda con el seed), sin nuevos
solves del circuito. El radio se suma al superior y se resta al inferior;
la prueba no se limita al centro. Se intersecta siempre con Gershgorin del
mismo recinto, norma y coordenadas, conservando superior bruto y final.
No se cambia la norma por ventana ni se mezcla con mu_infinito.

## Signos y comparación completa

Las **16 celdas de prefijo** certifican mu2<0 del bloque interno:
el superior más alto permanece por debajo de -1,88e7/s.
Las **48 restantes** certifican mu2>0: sus inferiores son positivos.
Esto identifica crecimiento instantáneo de alguna dirección en la norma
RMS interna; no prueba crecimiento observado ni estabilidad modal del
circuito o del Moog. Acoplamientos externos y forzamiento siguen activos.

Las ocho cotas nodales forzadas bajan. La tabla conserva el término con
**anclaje cero hipotético** y el coeficiente del anclaje ponderado común.
Son cotas del tangente ideal variable, no errores observados del DAE.

| Ventana | Subpasos | RMS/Gershgorin anterior (V) | RMS/espectro intervalar (V) | Coeficiente de anclaje, pico nodal |
| --- | --- | --- | --- | --- |
| prefix | 2 | 52742699.7 | 0.00000297828175 | 1758.21342 |
| prefix | 4 | 0.572593052 | 0.00000578532726 | 589.543783 |
| attack | 2 | 8.32609801E+120 | 1.02221976E+114 | 1.38377240E+122 |
| attack | 4 | 3.61955262E+55 | 1.26757414E+52 | 2.49289426E+61 |
| reset | 2 | 0.00000367506766 | 0.00000367506766 | 198.104053 |
| reset | 4 | 4.86537697E-7 | 4.86537697E-7 | 197.892775 |
| tail | 2 | 1644.02471 | 0.00000533904987 | 589.543783 |
| tail | 4 | 0.00131060101 | 0.00000992152196 | 341.381586 |

Cola N4 pasa de ~1,31 mV a **~9,92 µV**; prefijo N2/N4 da
**~2,98/~5,79 µV**. Estos términos no admiten 1 mV global: el anclaje,
restos no lineales y recorrido completo siguen pendientes. Ataque todavía
da cotas enormes, hasta ~1,022e114 V; reset apenas cambia. Se mantienen
las ocho filas y los coeficientes de anclaje. Comparar estas cotas de consultas
condicionadas no demuestra convergencia o monotonía del refinamiento.

La prueba muestra que Gershgorin perdía gran parte de la disipación de
prefijo. En las otras ventanas el signo positivo de mu2 permanece incluso
con el certificado inferior. Seguir refinando sólo ese mayor autovalor no
elimina la necesidad de estudiar el generador firmado y las direcciones
que excitan residual y acoplamientos.

## Evidencia y regresiones

[Datos](../evidence/loudness_latch_bdf_static_precision_junction_spectral.json.gz):
**1713598 bytes**, SHA comprimido
`b057e097988c05e7bc239bf391856c2f9a8e983af45288d5e8b252189c867b30`,
SHA canónico `46d829e154cbeb9bb07a517a0ca47ff4fabf05f152a8b4e763f3b03339c68b6f`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_junction_spectral_summary.json).
Cada celda identifica su índice anterior, centro, delta, seeds, consultas,
bracket, factores superiores, cota bruta/final y comparación nueva.
El forzamiento y los mapas nodales se reconstruyen desde las referencias
inmutables anteriores: se evita duplicarlos y no se recalculan las inversas.

La [suite](../tests/test_loudness_latch_spectral_junction.py) pasa **5/5 al primer intento**
en 8.5217616 s. Verifica reconstrucción LDL racional, pivotes cero
/negativo, guard de simetría, autovalores conocidos por similitud ortogonal,
intersección declarada en la misma norma y todas las **1.024 matrices vértice**
de un recinto simétrico 4×4. Un centro nulo con radio demuestra por qué no
se puede omitir incertidumbre. Reconstruye las **64 cotas, 2.112 consultas**
y propagaciones, certifica los factores superiores y exige que todos los
componentes RMS salvo M_JJ permanezcan iguales. Verifica fuentes, bytes,
destinos y alcance. El [recibo](../evidence/loudness_latch_bdf_static_precision_junction_spectral_validation.json)
conserva SHA antes/después idénticos.

El [corpus ampliado](BIESTABLE_JUNTURAS_ESPECTRO_ENTRADAS.md) verifica fuentes
y versiones históricas. Los intervalos seleccionados siguen no contiguos.
**1 mV global, física, audio y deadline siguen abiertos.** Próximo corte:
generador firmado de junturas, crecimiento de norma frente a comportamiento
modal, con variación temporal, anclaje y restos todavía explícitos.

```powershell
python tools/loudness_latch_bdf_static_precision_junction_spectral.py
python tools/validate_bdf_static_precision_junction_spectral.py
```
