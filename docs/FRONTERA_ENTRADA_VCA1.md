# Frontera pasiva de la entrada del primer VCA

## Circuito que se puede afirmar

El manual de servicio **SVC-204D §2.9, PDF p. 12** dice que la señal del filtro se acopla en AC a la base de Q16. La **Fig. 9-11, SVC-9 PDF p. 13** (SVC-204D p. 69) lleva la salida del recuperador **por R2 y luego C6** a esa base, coloca **R34** entre las bases de Q16 y Q15, y **C15/R36** desde la base de Q15 a masa. La tabla 7-8, **SVC-9 pp. 30–31**, da R2 `82 kΩ ±5 %`, C6 `0,33 µF ±10 %`, R34 `820 Ω ±5 %`, C15 `220 µF +50/−10 %` y R36 `510 Ω ±5 %`. El [grafo](../evidence/vca1_input_boundary.json) registra esas cinco ramas y el resto de la etapa por trazar. La rama R2 se confirmó siguiendo el cable desde el colector de recuperación hasta C6; omitirla altera de forma sustancial tanto la escala como el corte calculado.

El mismo texto §2.9 identifica a Q16/Q15 como par de entrada controlado por la corriente de Q18, conectada al contorno de volumen. Su salida alimenta el segundo multiplicador Q14/Q13, bajo control del jack **EXTERNAL LOUDNESS**, y Q12/Q17 forman la conversión a salida simple. Por tanto, C6 **no** es una salida final ni puede reemplazarse todo el bloque por una ganancia fija. Las conexiones activas y la red de balance del primer VCA todavía no tienen un punto DC calculado.

## Referencia aislada

La [solución de tres nodos](../tools/vca1_input_boundary_reference.py) impone `V_RECOVER_COLLECTOR=1 V` sólo como normalización de pequeña señal, abre la red de balance y fija a cero las corrientes de base Q16/Q15. Usa rieles AC ideales. Para `s=j2πf`, la KCL en C6_LEFT, Q16_BASE y Q15_BASE es:

```text
(V_RECOVER−V_C6LEFT)/R2 = s·C6·(V_C6LEFT−V_Q16)
s·C6·(V_C6LEFT−V_Q16) = (V_Q16−V_Q15)/R34
(V_Q16−V_Q15)/R34 = V_Q15/R36 + s·C15·V_Q15
```

Los voltajes son V/V, resistencias en Ω, capacitancias en F y corrientes resultantes en A/V. C6 bloquea DC. Con C15 casi cortocircuitado en audio, la escala del paso alto aislado es `1/[2π·(R2+R34)·C6]≈5,82 Hz`, y el límite de alta frecuencia es `R34/(R2+R34)≈0,00990`. La solución de tres nodos da `|V_Q16/V_RECOVER_COLLECTOR|≈0,00974` a 30 Hz, `0,00989` a 100 Hz y `0,00990` a 1 kHz. La KCL de las pruebas cierra a `<10⁻¹² A/V`.

Estas cifras son **de la red pasiva aislada**. La impedancia y sesgo del recuperador Q5–Q8, las corrientes y capacitancias de Q16/Q15, el movimiento de su emisor común y la red de balance R14/R19/R23/R22/R13 pueden cambiar la carga y la transferencia. R2 produce una atenuación de aproximadamente 100:1 hacia las bases bajo estas condiciones; no es una medición del Model D ni una respuesta de salida del RF-D. El cálculo anterior sin R2 sugería erróneamente un corte de cientos de hertz desde la salida de recuperación: esa conclusión queda descartada por la ruta documentada de 82 kΩ.

## Siguiente cierre

La [red AC conjunta de 27 nodos](CARGA_VCA1_FILTRO.md) ya carga el colector de recuperación con R2/C6 y el camino pasivo de bases. El siguiente paso debe transcribir el punto DC de Q16/Q15/Q18 y la red de balance, incorporar sus corrientes de base, continuar por Q14/Q13 y Q12/Q17, y barrer niveles y contorno antes de comparar audio público.

```powershell
python tools/vca1_input_boundary_reference.py
python -m unittest discover -s tests -q
```
