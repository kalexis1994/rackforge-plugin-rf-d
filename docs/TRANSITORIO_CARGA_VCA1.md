# Transitorio con carga pasiva del primer VCA

La [referencia posterior de 33 nodos](TRANSITORIO_VCA1_ACTIVO.md) incorpora Q16/Q15/Q18 de forma no lineal bajo fronteras de balance y contorno impuestas. Este modelo de 27 nodos conserva valor como control pasivo aislado.

## Frontera documentada

La [referencia offline de 27 nodos](../tools/filter_vca1_passive_transient_reference.py) continúa el [transitorio de 24 nodos](TRANSITORIO_FILTRO_ACOPLADO.md) con R2 `82 kΩ`, C6 `0,33 µF`, R34 `820 Ω`, C15 `220 µF` y R36 `510 Ω` de la [entrada del primer VCA](FRONTERA_ENTRADA_VCA1.md). Fuentes: **SVC-204D §2.9, PDF p. 12; SVC-9 Fig. 9-11, PDF p. 13; tabla 7-8, pp. 30–31**. El colector del recuperador Q5–Q8 alimenta R2; C6 llega a la base de Q16, y R34/C15/R36 fijan la frontera de la base Q15. Las leyes Ebers–Moll de los catorce BJT **del filtro y recuperador** permanecen activas. Q16/Q15 y los siguientes transistores del VCA siguen sin corrientes ni ganancia modeladas.

## Estado y ecuaciones

El punto inicial combina los DC independientes del ladder y del recuperador. Como C6 está abierto en DC, el nodo a su izquierda adopta la tensión del colector por R2; las dos bases pasivas empiezan en 0 V por R34/R36. C10 conserva su tensión de estado. Durante un paso Euler implícito, `F(v)` incluye resistencias y las 14 leyes BJT, y la matriz `C` agrega C6 entre los nodos 24/25 y C15 desde el nodo 26 a masa:

```text
F(v_n) + I10·(e_Q30base−e_tap)
       − [C·(v_n−v_(n−1)) − C27·ΔBUS·e_BASE]/Δt = 0     A
I_R2 = (V_RECOVER_COLLECTOR−V_C6LEFT)/R2                 A
I_C6 = C6·Δ(V_C6LEFT−V_Q16base)/Δt                     A
```

La matriz Newton deriva analíticamente los BJT del [Jacobiano de 24 nodos](JACOBIAN_ANALITICO_FILTRO.md) y estampa R2/R34/R36, C6/C15 y el compañero de C10. La ruta de diferencias finitas sigue disponible como regresión. Todo el solver es **offline**: aloca memoria y usa iteraciones variables. No se ha incorporado al hilo de audio.

## Comprobaciones y límites

Con los dos candidatos R61, `I_S=10⁻¹⁴ A`, β directo `100`, β inverso `5`, `298,15 K`, R73_L `500 Ω`, R14 eléctrico `0 Ω` y `48 kHz`:

- El punto DC sin señal es fijo, sin iteraciones Newton.
- Escalones BUS de `±0,1 V` cierran la carga/KCL bajo `10⁻¹⁰ A`; la corriente de R2 coincide con la de C6. Al sumar cargas nodales, las ramas internas C6, C1/C5 y los cuatro capacitores del ladder se cancelan; quedan los términos a masa C24/C9/C15 y la excitación C27.
- Un primer paso de `10 µV` coincide con Euler implícito de la [red AC de 27 nodos](CARGA_VCA1_FILTRO.md) dentro de `1 %` por nodo o `0,1 nV` cerca de cero.
- Trazas de 32 muestras con Jacobianos analítico y numérico concuerdan dentro de `1 µV` por nodo, para ambos R61.

La base de Q16 en este cálculo **no** es audio de salida. Faltan el sesgo y las corrientes activas Q16/Q15/Q18, la red de balance, Q14/Q13, Q12/Q17, control de volumen y cargas externas. El BUS sigue siendo fuente ideal y la corriente Q28 se mantiene fija dentro del paso. No se afirma respuesta de graves, clipping, estabilidad global ni parecido audible de un Model D. El siguiente bloque debe cerrar el punto DC activo del primer VCA antes de interpretar su ganancia.

```powershell
python -m unittest discover -s tests -q
```
