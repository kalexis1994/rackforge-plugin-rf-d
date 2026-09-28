# Segundo multiplicador Q14/Q13/Q21

**SVC-204D §2.9, PDF p. 12** describe la salida del par Q16/Q15 aplicada al segundo multiplicador Q14/Q13, controlado desde EXTERNAL LOUDNESS. La **Fig. 9-11 de SVC-9, PDF p. 13** (SVC-204D p. 69) conecta Q16_COLLECTOR a Q14_BASE y Q15_COLLECTOR a Q13_BASE. Los emisores de Q14/Q13 se reúnen y llegan por R33 `470 Ω` al colector de Q21. R42 `3,3 kΩ` lleva el emisor de Q21 a masa y R44 `150 kΩ` a −10 V. Su base tiene un shunt R51 `33 kΩ` a masa. La tabla 7-8, **SVC-9 PDF pp. 30–31**, da esos valores.

Los colectores Q14/Q13 llegan por R18/R21 de `330 Ω` a los extremos de R12 `100 Ω` (`2 ND VCA BAL`). El cursor de R12 conecta hacia el primer balance por R13 y hacia la alimentación por R11 `150 Ω` y R10 `120 Ω`. Las bases de Q12/Q17 y su carga posterior quedan fuera del [grafo de este corte](../evidence/vca2_active_core.json).

El [solver DC de cinco nodos](../tools/vca2_active_core_dc_reference.py) impone `V_Q14b`, `V_Q13b`, `V_Q21b` y `V_cursor2`; resuelve el emisor común, colector/emisor Q21 y ambos colectores de salida. Las tres leyes BJT de dos junturas son las documentadas para el [primer núcleo](NUCLEO_ACTIVO_VCA1_DC.md), con `I_S`, `β_F`, `β_R` y temperatura impuestos. Las KCL, en amperios, son:

```text
IE14 + IE13 = (Vemisor2−VQ21c)/R33 = IC21
IE21 = VQ21e/R42 + (VQ21e+10)/R44
IC14 = (Vcursor2−VQ14c)/(R18+R12_izq)
IC13 = (Vcursor2−VQ13c)/(R21+100−R12_izq)
```

El retorno expone `IB14` e `IB13` como **cargas pendientes** de Q16_COLLECTOR y Q15_COLLECTOR, respectivamente. También expone la corriente exigida a la fuente ideal de Q21_BASE: `IB21 + V_Q21b/R51`. El shunt R51 no desaparece por imponer esa tensión. Aún falta identificar el circuito completo de EXTERNAL LOUDNESS y convertir ese control en una tensión/corriente física; `V_Q21b` aquí no equivale a la posición de un jack o perilla.

Al dar como ejemplo las tensiones del [primer balance condicionado](ALIMENTACION_BALANCE_VCA1.md) con `V_cursor2=9 V`, y fijar `V_Q21b=2 V`, R12 izquierdo `50 Ω`, `I_S=10⁻¹⁴ A`, `β_F=100`, `β_R=5`, `298,15 K`, el solver obtiene `V_Q14c≈8,9079 V`, `V_Q13c≈8,9094 V`; las corrientes de base que deberían cargar el primer VCA son `≈2,42/2,38 µA`. El residuo máximo es `<10⁻¹² A`. Son valores **condicionados**: las tensiones Q14/Q13 se tomaron de una solución que aún no incluye esas corrientes, y el segundo cursor también es impuesto. No son niveles de salida del Model D.

Las [pruebas](../tests/test_vca2_active_core_dc_reference.py) cubren las cinco KCL, conservación de cola, corriente externa del shunt, control y extremos del balance. El próximo sistema debe resolver ambos VCA **juntos** para cargar de verdad Q16/Q15 con IB14/IB13 y cerrar R11/R10. Después sigue Q12/Q17, la red de salida y el jack externo. El audio externo sigue sin contrastar.

```powershell
python tools/vca2_active_core_dc_reference.py
python -m unittest discover -s tests -q
```
