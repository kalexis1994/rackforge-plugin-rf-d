# Q29/Q30: límite ideal de la entrada diferencial

## Procedencia eléctrica

La **Fig. 9-11, SVC-9 PDF p. 13** (SVC-204D PDF p. 69) muestra a Q29 y Q30 en el peldaño inferior del ladder: sus bases reciben, respectivamente, la [entrada tras C27](ENTRADA_FILTRO.md) y el [retorno tras R73](REGENERACION_FILTRO.md). Sus emisores comparten el nodo `TAIL`, que va por **R60 = 680 Ω** al colector de **Q28**; el emisor de Q28 va a masa. Los colectores de Q29/Q30 llegan a las ramas izquierda/derecha del ladder. La **tabla 7-8, SVC-9 PDF pp. 30–31** cataloga Q29/Q30 como **par TIS97 emparejado**, Q28 como **TIS92** (alternativa 2N3904) y R60 como 680 Ω. El [grafo mínimo](../evidence/filter_input_pair.json) conserva estas conexiones.

El [boletín de fábrica B-804C, hoja 2](https://synthfool.com/docs/Moog/minimoog/factory_service_bulleting_804C2.jpg) corrige la nota 3 de la Fig. 9-11: Q26/Q28 se emparejan en `V_BE` a **±3 mV con I_C=20 mA**. Ese es un **criterio de selección**, no una medición de la corriente de cola en funcionamiento. El boletín no asigna a Q29/Q30 una tolerancia numérica de emparejamiento. Su condición “matched pair” de la tabla 7-8 tampoco equivale a `I_S29=I_S30` exacto.

## Derivación condicionada

La ecuación bipolar [TI SLOA059B, PDF p. 6, ec. (3)](https://www.ti.com/lit/an/sloa059b/sloa059b.pdf) da `I_C=I_S exp(V_BE/V_T)` en el límite ideal. Para el par con emisor común, `ΔV = V_B29 − V_B30` y `V_T = kT/q`:

```text
I_29/I_30 = (I_S29/I_S30) · exp(ΔV/V_T)
```

Si se **impone** `I_S29=I_S30`, ganancia de corriente infinita, ambos transistores en región activa directa y una corriente de emisor total fija `I_T`, entonces `I_29+I_30=I_T` y:

```text
I_29 = I_T · [1 + tanh(ΔV/(2V_T))]/2
I_30 = I_T − I_29
I_29−I_30 = I_T · tanh(ΔV/(2V_T))
d(I_29−I_30)/dΔV = I_T/[2V_T] · sech²(ΔV/(2V_T))
```

Se usan las constantes SI exactas de [NIST/CODATA](https://physics.nist.gov/cuu/pdf/all.pdf), `k=1,380649×10⁻²³ J/K` y `q=1,602176634×10⁻¹⁹ C`, en la [función térmica compartida](../tools/semiconductor_ideal.py). `T` es **temperatura de unión** en K, no temperatura ambiente. `ΔV` y `V_T` están en V; `I_T`, `I_29` e `I_30` en A; el cociente de corrientes es adimensional y la derivada está en siemens. La [referencia ejecutable](../tools/filter_input_pair_reference.py) exige bases, `I_T` y `T` explícitos; no tiene valores por defecto de corriente o temperatura.

Como control matemático, con **1 mA impuesto** y **298,15 K hipotéticos** (`V_T≈25,69 mV`), bases iguales dividen 0,5/0,5 mA. A `ΔV=+25 mV`, el límite ideal da aproximadamente **0,726/0,274 mA**; al invertir el signo intercambia ambas ramas. **1 mA no es un valor documentado para el Model D.** La pendiente máxima en bases iguales sería `I_T/(2V_T)` bajo estos supuestos.

## Dominio y gate pendiente

El cálculo no determina `I_T`: Q26, Q28, R60, las fuentes de ±10 V y la carga de los colectores requieren un punto DC acoplado. Tampoco conoce `V_CE`, `β`, `I_S`, desajuste, efecto Early, capacitancias, temperatura real ni saturación; una base con gran excursión puede llevar un dispositivo fuera de región activa. La corriente de base ignorada cargaría tanto C27/R54 como R73/C10. Por ello **la sigmoide es una referencia teórica de partición**, no una curva de saturación ni una calibración del sonido RF-D. Las pruebas comprueban conservación de corriente, simetría, derivada y estabilidad numérica, no fidelidad audible.

```powershell
python tools/filter_input_pair_reference.py
python -m unittest discover -s tests -q
```

La [red Q26/Q28](COLA_FILTRO_Q26_Q28.md) ya admite una carga DC **condicionada** a parámetros de transistor y voltajes impuestos. La [base pasiva de Q26](BASE_Q26_CONTROL_FILTRO.md) calcula un voltaje candidato para las llaves J2/SW15/SW16/SW17, con fuentes aguas arriba y corriente de base impuestas. El próximo gate es resolver esas fronteras y el sesgo del peldaño inferior con las cargas reales del ladder. Sólo entonces se podrá evaluar cuándo esta aproximación ideal deja de ser válida y acoplarla a la entrada y la regeneración.
