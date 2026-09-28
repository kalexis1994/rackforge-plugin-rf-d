# Carga activa del primer VCA sobre el filtro

La [referencia de 33 nodos](../tools/filter_vca1_active_small_signal_reference.py) une la [red de filtro/recuperación/EMPHASIS y entrada pasiva de 27 nodos](CARGA_VCA1_FILTRO.md) con las ocho derivadas locales del [núcleo DC Q16/Q15/Q18](NUCLEO_ACTIVO_VCA1_DC.md). Se comparten las tensiones Q16_BASE y Q15_BASE, por lo que se añaden **seis** nodos: emisor común, colector y emisor de Q18, colectores Q16/Q15 y base Q18. R34 y R36 ya estaban en la matriz pasiva; se quitan sus primeras estampas antes de añadir el Jacobiano completo del VCA. C6 y C15 conservan sus ramas. El retorno C10/R14 de panel/R73 también permanece.

Las conexiones y los valores proceden de **SVC-9 Fig. 9-11, PDF p. 13 y tabla 7-8, pp. 30–31** (Fig. 9-11 en SVC-204D p. 69); **SVC-204D §2.9, p. 12** identifica la función de ambos multiplicadores. La linealización usa `G=∂F/∂v` del punto DC en siemens, `C` nodal en faradios y resuelve `(G−j2πfC)v=b` con `BUS=1 V` sólo como normalización. El cursor del balance y el origen de R59 se mantienen a **masa AC ideal**. No se resuelve el contorno dinámico ni la impedancia de R13/R11/R10. Las bases del segundo VCA Q14/Q13 se mantienen abiertas. La salida `V_Q16c−V_Q15c` es una señal diferencial **intermedia**, no la salida audible del instrumento.

Como control numérico, con los parámetros BJT impuestos `I_S=10⁻¹⁴ A`, `β_F=100`, `β_R=5`, `T=298,15 K`, `Vw=5 V`, balance a `12,5 Ω`, `R61=200 Ω` y R73_L `500 Ω`, a `100 Hz` la magnitud de `V_Q16b/BUS` pasa de `≈0,11834` para `Vcontorno=0 V` a `≈0,11632` para `2 V`. La magnitud de `(V_Q16c−V_Q15c)/BUS` pasa de `≈3,65×10⁻⁸` a `≈0,05577`. La KCL compleja cierra muy por debajo de `10⁻¹¹ A/V`. Es una **sensibilidad del circuito y fronteras elegidos**, no una curva de volumen ni de un Model D medido. A 0 Hz, C6 bloquea la perturbación desde BUS hacia el VCA.

Las [pruebas](../tests/test_filter_vca1_active_small_signal_reference.py) comprueban el conteo y estampado sin duplicaciones, carga de base dependiente del sesgo, apagado, bloqueo DC y residuo de la matriz. Faltan el suministro compartido de los dos VCA, las corrientes de base de Q14/Q13, la conversión Q12/Q17, capacitancias parásitas, la ley del contorno y variaciones de unidad. Sólo tras cerrar esas rutas puede interpretarse una transferencia a salida y contrastar grabaciones públicas.

```powershell
python -m unittest discover -s tests -q
```
