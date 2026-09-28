# Alimentación local del balance del primer VCA

La **Fig. 9-11 de SVC-9, PDF p. 13** (SVC-204D p. 69) conecta el cursor del ajuste R14 `1ST VCA BAL` al cursor de R12 `2 ND VCA BAL` por **R13 `120 Ω`**, confirmado con la tabla 7-8, **SVC-9 PDF pp. 30–31**. R22 `120 Ω` baja desde el primer cursor hasta Q15_BASE, que llega a masa por R36 `510 Ω`. Los colectores Q16/Q15 también extraen corriente del cursor por las dos mitades de R14 y R19/R23. La [transcripción](../evidence/vca1_active_core.json) incluye R13 y distingue ambos R14 del panel de EMPHASIS.

El [solver de nueve nodos](../tools/vca1_balance_supply_dc_reference.py) deja de imponer el voltaje del **primer** cursor: lo obtiene con la KCL

```text
(V_segundo−V_primero)/R13
  = (V_primero−V_Q15b)/R22 + I_C16 + I_C15
```

Las corrientes de colector de la derecha son las que pasan por `R19+R14_izq` y `R23+(25−R14_izq)`, respectivamente. Las otras ocho KCL y la ley de ambas junturas BJT son las del [núcleo activo](NUCLEO_ACTIVO_VCA1_DC.md). `V_segundo` sigue siendo una **frontera impuesta**: R12, R11/R10, el segundo VCA y la salida aún no están cerrados. El cálculo no asume una resistencia de fuente cero para el primer cursor; tampoco puede predecir la tensión real de `V_segundo`.

Como prueba condicionada, `V_segundo=9 V`, contorno impuesto `2 V`, R14 izquierdo `12,5 Ω`, `I_S=10⁻¹⁴ A`, `β_F=100`, `β_R=5`, `298,15 K` y riel −10 V dan `V_primero≈7,538 V`, `V_Q15b≈6,102 V` e `I_C18≈221,38 µA`. La caída de R13 alimenta principalmente R22/R36; el residuo de nueve KCL queda `<10⁻¹² A`. Los `9 V` son un estímulo elegido para la frontera, **no** un valor medido del Model D. El resultado cambia si el segundo balance o el suministro se cargan de otra manera.

Las [regresiones](../tests/test_vca1_balance_supply_dc_reference.py) prueban conservación de corriente en R13, equivalencia con el solver de ocho nodos cuando se le da el cursor resuelto, variación de la frontera y extremos del balance. El [segundo VCA](NUCLEO_ACTIVO_VCA2_DC.md) ya está trazado y calculado **por separado**. El siguiente paso es integrar sus corrientes de base y la cadena R11/R10 para que ambos cursores salgan del mismo sistema. La referencia AC/transitoria de 33 nodos todavía usa el [cursor ideal anterior](CARGA_ACTIVA_VCA1_FILTRO.md); este modelo de nueve nodos no se ha promocionado a esas matrices.

```powershell
python tools/vca1_balance_supply_dc_reference.py
python -m unittest discover -s tests -q
```
