# Carga AC del filtro hasta el segundo VCA

La [referencia de cuarenta nodos](../tools/filter_vca_cascaded_small_signal_reference.py) une el [filtro/recuperador/EMPHASIS y entrada R2/C6 de 27 nodos](CARGA_VCA1_FILTRO.md) con el Jacobiano local de quince nodos del [DC acoplado de ambos VCA](VCA_CASCADA_DC.md). Q16_BASE y Q15_BASE son compartidos, por lo que se agregan trece tensiones: seis del primer par, su cursor, cinco del segundo par y su cursor. R34/R36 ya estaban en la red pasiva y se eliminan de esa primera estampa antes de insertar el bloque completo. C6/C15 y el retorno C10 siguen presentes. Las fuentes documentales son **SVC-9 Fig. 9-11, PDF p. 13, tabla 7-8, pp. 30–31**, y **SVC-204D §2.9, PDF p. 12**.

Para una perturbación de BUS se resuelve `(G−j2πfC)v=b`. `G` es `∂KCL/∂V` en siemens alrededor del DC de seis BJT; `C` está en faradios. La fuente `BUS=1 V` es sólo normalización matemática de pequeña señal. La frontera antes de R11, el contorno de Q18 y la base de Q21 son **masa AC ideal**; las bases de Q12/Q17 no toman corriente. El sistema permite observar ambos cursores y las salidas diferenciales de Q16/Q15 y Q14/Q13. La segunda salida diferencial todavía es **interna**: faltan conversión a señal simple, etapa final y carga de salida.

Con el escenario DC condicionado `V_UPPER=9,5 V`, `I_S=10⁻¹⁴ A`, `β_F=100`, `β_R=5`, `298,15 K`, balances eléctricos `12,5/50 Ω`, `R61=200 Ω`, `R73_L=500 Ω`, EMPHASIS eléctrico `0 Ω` y ambos controles impuestos `2 V`, a `100 Hz` salen magnitudes `|V_Q16c−V_Q15c|/BUS≈0,05519` y `|V_Q14c−V_Q13c|/BUS≈0,19613`. Con ambos controles `0 V`, la segunda magnitud es casi cero. Las cuarenta KCL complejas cierran a `<10⁻¹¹ A/V`. La diferencia de magnitudes bajo estas fronteras **no es** una ley de volumen, una ganancia de salida ni una validación de audio vintage.

Las [regresiones](../tests/test_filter_vca_cascaded_small_signal_reference.py) comprueban que no se dupliquen R34/R36, que el control modifique la salida del segundo VCA, que C6 bloquee DC y que cierre la KCL en cuatro frecuencias. El próximo cierre debe llevar los seis BJT al transitorio no lineal, seguir Q12/Q17 y la salida, y reemplazar las fronteras de R10/control con sus circuitos. Hasta entonces la fidelidad sonora sigue abierta.

```powershell
python -m unittest discover -s tests -q
```
