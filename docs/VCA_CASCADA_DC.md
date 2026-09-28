# Dos VCA acoplados en DC

La [referencia de quince nodos](../tools/vca_cascaded_dc_reference.py) resuelve **Q16/Q15/Q18 y Q14/Q13/Q21 simultáneamente**. El punto de partida es el [primer núcleo](NUCLEO_ACTIVO_VCA1_DC.md), su [alimentación por R13](ALIMENTACION_BALANCE_VCA1.md) y el [segundo núcleo](NUCLEO_ACTIVO_VCA2_DC.md). La **Fig. 9-11, SVC-9 PDF p. 13** (SVC-204D p. 69) y tabla 7-8, **pp. 30–31**, dan R13 `120 Ω`, R11 `150 Ω`, los dos balances y las ramas de transistores. **SVC-204D §2.9, PDF p. 12** describe funcionalmente la cascada. Las tensiones Q16_COLLECTOR y Q15_COLLECTOR son ahora las bases Q14 y Q13; sus corrientes `IB14/IB13` se restan en las KCL de los colectores anteriores.

El cursor R14 de placa 4 sale de R13 y el cursor R12 sale de R11. Se impone sólo `V_UPPER`, **al otro lado de R11**. Eso retiene la carga compartida:

```text
(V_UPPER−Vw2)/R11 = (Vw2−Vw1)/R13 + IC14 + IC13
(Vw2−Vw1)/R13 = (Vw1−V_Q15b)/R22 + IC16 + IB14 + IC15 + IB13
```

Las corrientes de las ramas de balance incluyen las resistencias de R12/R14 y R18/R21/R19/R23. El sistema resuelve las quince tensiones y las seis leyes Ebers–Moll de dos junturas con `I_S`, `β_F`, `β_R`, temperatura y ambos controles **impuestos**. `V_UPPER` no se identifica todavía con +10 V: queda R10 `120 Ω`, la carga de Q1 y la conversión final. R51 `33 kΩ` carga la fuente ideal de Q21_BASE, aunque no modifica su tensión impuesta. Las bases Q12/Q17 siguen abiertas. El cálculo es DC, no tiene dinámica de C6/C15 ni de los contornos.

En un escenario numérico elegido (`V_UPPER=9,5 V`, ambos controles de base/fuente `2 V`, balances `12,5/50 Ω`, riel −10 V, `I_S=10⁻¹⁴ A`, `β_F=100`, `β_R=5`, `298,15 K`), salen `Vw1≈6,557 V`, `Vw2≈7,833 V`; Q14/Q13 consumen `≈2,423/2,383 µA` de las salidas del primer VCA. Las quince KCL cierran a `<10⁻¹² A`. La caída de suministro cambia los dos cursores al cambiar los controles. Estos números son **escenarios condicionados**, no voltajes medidos de una unidad Model D. Tampoco implican una respuesta audible: faltan Q12/Q17 y la red de salida.

Las [regresiones](../tests/test_vca_cascaded_dc_reference.py) comprueban los quince nodos, dos corrientes de cola, cargas base/colector entre etapas y KCL de R11/R13 bajo varios controles. El punto de operación ya alimenta la [matriz AC conjunta de cuarenta nodos](CARGA_AC_DOS_VCA.md). El próximo paso es llevarlo al transitorio no lineal y completar R10/Q1/Q12/Q17. El [transitorio de 33 nodos](TRANSITORIO_VCA1_ACTIVO.md) todavía usa el primer cursor ideal y el segundo VCA abierto.

```powershell
python tools/vca_cascaded_dc_reference.py
python -m unittest discover -s tests -q
```
