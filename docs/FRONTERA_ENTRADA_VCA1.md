# Frontera pasiva de la entrada del primer VCA

## Circuito que se puede afirmar

El manual de servicio **SVC-204D §2.9, PDF p. 12** dice que la señal del filtro se acopla en AC a la base de Q16. La **Fig. 9-11, SVC-9 PDF p. 13** (SVC-204D p. 69) dibuja **C6** hacia esa base, **R34** entre las bases de Q16 y Q15, y **C15/R36** desde la base de Q15 a masa. La tabla 7-8, **SVC-9 pp. 30–31**, da C6 `0,33 µF ±10 %`, R34 `820 Ω ±5 %`, C15 `220 µF +50/−10 %` y R36 `510 Ω ±5 %`. El [grafo](../evidence/vca1_input_boundary.json) registra esas cuatro ramas y el resto de la etapa por trazar.

El mismo texto §2.9 identifica a Q16/Q15 como par de entrada controlado por la corriente de Q18, conectada al contorno de volumen. Su salida alimenta el segundo multiplicador Q14/Q13, bajo control del jack **EXTERNAL LOUDNESS**, y Q12/Q17 forman la conversión a salida simple. Por tanto, C6 **no** es una salida final ni puede reemplazarse todo el bloque por una ganancia fija. Las conexiones activas y la red de balance del primer VCA todavía no tienen un punto DC calculado.

## Referencia aislada

La [solución de dos nodos](../tools/vca1_input_boundary_reference.py) impone `V_RECOVER=1 V` sólo como normalización de pequeña señal, abre la red de balance y fija a cero las corrientes de base Q16/Q15. Usa rieles AC ideales. Para `s=j2πf`, la KCL en Q16_BASE y Q15_BASE es:

```text
s·C6·(V_RECOVER−V_Q16) = (V_Q16−V_Q15)/R34
(V_Q16−V_Q15)/R34 = V_Q15/R36 + s·C15·V_Q15
```

Los voltajes son V/V, resistencias en Ω, capacitancias en F y corrientes resultantes en A/V. C6 bloquea DC. Con C15 casi cortocircuitado a 100 Hz, la frontera se aproxima a un paso alto con escala `1/(2π·R34·C6)≈588 Hz`: el cálculo completo de dos nodos da `|V_Q16/V_RECOVER|≈0,051` a 30 Hz, `0,167` a 100 Hz, `0,454` a 300 Hz y `0,862` a 1 kHz. La KCL de las pruebas cierra a `<10⁻¹² A/V`.

Estas cifras son **de la red pasiva aislada**. La impedancia y sesgo del recuperador Q5–Q8, las corrientes y capacitancias de Q16/Q15, el movimiento de su emisor común y la red de balance R14/R19/R23/R22/R13 pueden cambiar la carga y la transferencia. La atenuación calculada a baja frecuencia es una señal concreta para verificar al cerrar la etapa; no es una medición del Model D, ni una respuesta de salida del RF-D. No se ajustará un compensador DSP para ocultarla sin resolver primero el circuito y las variantes documentales.

## Siguiente cierre

Transcribir el punto DC de Q16/Q15/Q18 y la red de balance, luego cargar el nodo de recuperación con C6 y las corrientes de base activas. Continuar por Q14/Q13, Q12/Q17 y el divisor de salida; barrer niveles y control de contorno antes de comparar audio público.

```powershell
python tools/vca1_input_boundary_reference.py
python -m unittest discover -s tests -q
```
