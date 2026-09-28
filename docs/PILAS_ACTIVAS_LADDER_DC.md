# Pilas activas del ladder: cierre DC condicionado

## Topología documentada

La **Fig. 9-11, SVC-9 PDF p. 13** (SVC-204D PDF p. 69) muestra dos pilas de transistores de placa 4. De abajo arriba: `Q29→Q23→Q19→Q10→Q2` a la izquierda, y `Q30→Q24→Q20→Q11→Q3` a la derecha. El colector del transistor inferior se une al emisor del siguiente. Los colectores de Q2 y Q3 llegan a `+10 V`. Cada par superior comparte una tensión de base tomada de un tap de la [columna resistiva](COLUMNA_RESISTIVA_LADDER_DC.md): Q2/Q3, Q10/Q11, Q19/Q20 y Q23/Q24. C3/C7/C11/C16 unen lados opuestos como capacitores y quedan abiertos en DC. Q29/Q30 comparten emisor `TAIL`, pero sus bases tienen las rutas diferentes descritas en [bases inferiores](BASES_FILTRO_ACOPLADAS_DC.md). El [grafo transcrito](../evidence/filter_ladder_dc_active_stacks.json) fija el orden y los taps.

## Cálculo y dominio

La [referencia ejecutable](../tools/filter_ladder_active_dc_reference.py) impone `I_S` en A y β adimensional para los **ocho transistores superiores**, además de los parámetros impuestos de Q26/Q28/Q29/Q30, las fuentes de panel y un candidato de R61. Usa la ley exponencial de [TI SLOA059B, PDF p. 6, ec. (3)](https://www.ti.com/lit/an/sloa059b/sloa059b.pdf), como aproximación de transistor ideal; para cada transistor superior se supone región activa directa, sin efecto Early ni saturación:

```text
I_B = I_E/(β+1)                  A
I_C = I_E−I_B                    A
V_BE = (kT/q)·ln(I_C/I_S)        V, sólo candidato activo
```

La corriente de colector de Q29 alimenta el emisor de Q23; se repite en cada unión de las dos pilas. La suma de las dos corrientes de base en cada nivel da `J1…J4`, ya **derivadas** dentro de esta ley condicionada. La columna y BOTTOM se resuelven conjuntamente. Las bases se toman de sus taps y se resta `V_BE` para obtener cada emisor. El colector de cada transistor es el emisor del siguiente; Q2/Q3 terminan en +10 V. La prueba de margen `V_CB=V_C−V_B≥0`, junto con `V_BE>0` y la condición necesaria de Q28, determina si la solución supuesta **puede** mantenerse en región activa. Si falla, sus voltajes y corrientes son únicamente el intento algebraico de un modelo fuera de dominio; hace falta una ley de saturación y resolver nuevamente el circuito.

El ejemplo de regresión usa R39 `=0,1`, R11 centrado, R49 `=250 Ω`, `V16=0 V`, `T=298,15 K`, todos los β `=100`, todos los `I_S=10⁻¹⁴ A` y R73 `=500 Ω` desde BOTTOM. Son **parámetros de prueba**, no una medición de TIS97 ni de una placa vintage. Para R61 `=200 Ω`, `V_BOTTOM≈1,96075 V`; el margen mínimo `V_CB` entre los diez transistores es ≈`0,966 V` y el candidato activo es consistente. Para R61 `=200 kΩ`, `V_BOTTOM≈9,95899 V` y ocho márgenes `V_CB` son aproximadamente `−0,497 V`; **la suposición activa falla**. Esta comparación da una restricción útil del escenario, pero no demuestra qué R61 se instaló: faltan confirmación de población, parámetros, tolerancias, variaciones de alimentación y solución en saturación.

## Estado RACE y siguiente paso

Continuación: el [cierre Ebers–Moll de 16 nodos](LADDER_EBERS_MOLL_DC.md) resuelve también escenarios con junturas base colector hacia adelante. Esta página conserva el límite activo y su prueba de margen como referencia independiente.

El [barrido de supuestos](BARRIDO_SESGO_LADDER_DC.md) muestra cómo cambian estos márgenes con RANGE, β e `I_S` en 72 escenarios calculados.

Hay cierre DC de la topología nominal del ladder **sólo en el dominio activo impuesto**. Las regresiones comprueban KCL en cada tap, continuidad de corriente y tensión de cada pila, el límite β infinito y detección de márgenes negativos. El modelo no contiene la dinámica de C3/C7/C11/C16, efecto Early, saturación, dispersión, recuperación Q5–Q8 ni lazo de emphasis. Tampoco predice frecuencia, resonancia o similitud sonora. El siguiente paso es incorporar la región de saturación y barrer condiciones de panel y parámetros antes de derivar el sistema temporal.

```powershell
python tools/filter_ladder_active_dc_reference.py
python -m unittest discover -s tests -q
```
