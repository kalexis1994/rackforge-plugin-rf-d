# Radio balanceado: misma métrica, incertidumbre mejor acotada

## Experimento congelado

El [protocolo](BIESTABLE_JUNTURAS_BALANCEADA_PROTOCOLO.md), helper y productor
se congelaron en `963fb3d` antes de medir. Datos, suite y validador se fijaron
en `4da3da4` antes de validar. Se mantienen los seis candidatos P aceptados,
los dos rechazos de reset, la base racional D, norma, W, escala temporal,
normalización del anclaje, conversiones, acoplamientos y forzamiento.
No se resuelve otra inversa del circuito ni se busca otra métrica.

Cada intervalo fija Gamma_i=ceil_40(sqrt_upper_256(1/Di)), con raíces
racionales exteriores. Gamma es positivo y constante en sus ocho celdas.
Son pesos de la prueba de perturbación; no son parámetros del sonido ni
coordenadas nuevas de la norma. Un factor positivo común se cancela.

El centro C y radio Q archivados del certificado dirigido se reutilizan
exactamente. Para |Delta_ij|<=Qij, la desigualdad de Young ponderada da
Delta<=diag(rGamma), rGamma_i=sum_j Qij*Gamma_j/Gamma_i. Así,
U=C+diag(rGamma) domina toda la familia transformada. LDLᵀ racional prueba
alpha*D-U positiva definida mediante seed estricto y 32 bisecciones.
El inferior del bracket es auxiliar; no es una cota inferior de la tasa real.
Tampoco se afirma que Gamma sea óptimo.

Se intersecta siempre el superior bruto con el previo dirigido en la misma
métrica, según la regla fijada antes de medir. Se conservan ambos y el final.
**14/48 tasas finales son estrictamente menores**: ocho de ataque N2 y seis
de ataque N4. Las otras 34 conservan el superior previo. Sólo M_JJ cambia;
se reconstruyen las seis propagaciones con todos sus componentes restantes.
Hay **48 certificados y 1.584 consultas exactas de tasa**.

## Comparación de todas las ventanas

Las seis cotas nodales no empeoran; los dos candidatos de reset siguen
rechazados. Los términos forzados de la tabla suponen anclaje cero
**hipotético**. El error entrante común ponderado sigue desconocido.
Son cotas del tangente ideal variable, no errores observados del DAE.

| Ventana | N | Mayor tasa superior balanceada (1/s) | Forzado dirigido previo (V) | Forzado balanceado (V) | Coeficiente del anclaje |
| --- | --- | --- | --- | --- | --- |
| prefix | 2 | -1,98006911325e7 | 6,41857983995e-6 | 6,41857983995e-6 | 1758,21341958 |
| prefix | 4 | -1,98138588773e7 | 5,78532726688e-6 | 5,78532726688e-6 | 589,543782934 |
| attack | 2 | 5,11162399268e7 | 9,16353967054e9 | 6,72300997972e-6 | 5360,45764024 |
| attack | 4 | 1,28450393522e7 | 5,21848261270e-6 | 5,21848245391e-6 | 1399,79699724 |
| reset | 2 | candidato previo rechazado | sin nueva propagación | sin nueva propagación | sin coeficiente nuevo |
| reset | 4 | candidato previo rechazado | sin nueva propagación | sin nueva propagación | sin coeficiente nuevo |
| tail | 2 | -5,26286918326e6 | 5,33902712938e-6 | 5,33902712938e-6 | 589,543782955 |
| tail | 4 | -5,27203318180e6 | 9,92152208336e-6 | 9,92152208336e-6 | 341,381585581 |

Ataque N2 pasa de una cota enorme a **~6,72 µV** de término forzado.
Su coeficiente de anclaje también baja, de ~6,09e18 a ~5360,46.
Ataque N4 cambia muy poco en forzamiento, pero su coeficiente baja de
~2130,29 a ~1399,80. Las fracciones exactas preservan diferencias que la
tabla redondeada oculta. Prefijo y cola conservan exactamente los resultados
previos. No se elige una norma diferente por ventana después de medir.

La contracción interna variable sigue certificada en las **32 celdas de
prefijo y cola**. Los superiores positivos de ataque no prueban crecimiento
real ni inestabilidad modal. El balance reduce incertidumbre de la prueba,
sin cambiar la dinámica modelada. N2 y N4 son dominios seleccionados:
su comparación no demuestra convergencia temporal global.

Todas las seis cotas forzadas aceptadas están ahora por debajo de 10 µV.
Esto **no cierra 1 mV global**: el anclaje debe multiplicarse por los
coeficientes publicados, falta el resto no lineal, y las ventanas no son
contiguas. Reset carece de esta métrica y no recibe admisión por herencia.
No hay una P común a todos los intervalos ni prueba del circuito acoplado.
Física vintage, voz audible y deadline mantienen sus gates propios.

## Evidencia y pruebas

[Datos](../evidence/loudness_latch_bdf_static_precision_junction_balanced.json.gz):
**2166054 bytes**, SHA comprimido
`03060e628a3b5a0789823af739546d89886c7137facc89871f729f17de1e8f38`,
SHA canónico `ab20c522839a2751252060ebc23f5e3ac4feb561e6a439be6ea9c38ce84db9b3`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_junction_balanced_summary.json).
Gamma guarda brackets, redondeo y SHA de la base; cada certificado referencia
centro/radio por SHA y conserva diagonal ponderada, seeds, consultas,
factores y superiores bruto, previo y final. La propagación conserva picos
interiores y términos de anclaje por separado del forzamiento.

La [suite](../tests/test_loudness_latch_junction_balanced.py) pasa **6/6 al
primer intento**, 11.5151985 s. Verifica raíces exteriores, redondeo de
40 bits, pesos positivos, invariancia por factor común y guards de dominio.
Comprueba todos los menores principales de las **1.024 matrices vértice**
de una caja simétrica 4×4 con Gamma dispar, usando eliminación exacta
independiente. Una familia con D=diag(1,100,1,1) certifica contracción
con balance cuando el majorante previo no la certifica; se comprueban
todos los vértices de su generador, sin fabricar certificados anteriores.

Se reproducen las 1.584 consultas, las seis propagaciones, rechazos y
conversiones intactas, fuentes, almacenamiento canónico y destinos propios.
El [recibo](../evidence/loudness_latch_bdf_static_precision_junction_balanced_validation.json)
conserva SHA antes/después idénticos. El [corpus](BIESTABLE_JUNTURAS_BALANCEADA_ENTRADAS.md)
identifica las dependencias y versiones históricas.

Próximo bloque: cuantificar el presupuesto admisible de anclaje y separar
qué regiones necesitan cubrirse desde DC. Una mejora adicional de una tasa
local ya no sustituye el trabajo de anclaje, resto y cobertura completa.
Mantener el gate de 1 mV y los rechazos de reset explícitos.

```powershell
python tools/loudness_latch_bdf_static_precision_junction_balanced.py
python tools/validate_bdf_static_precision_junction_balanced.py
```
