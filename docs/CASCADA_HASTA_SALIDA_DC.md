# Cascada de dos VCA hasta el colector de salida

Actualización: además del escenario predeterminado de CR1/CR2 abiertos, el solver acepta la [familia paramétrica 1N458A](DIODOS_SALIDA_1N458A.md). Las 22 KCL incluyen sus corrientes cuando se suministra `diode_model`.

La [referencia DC conjunta de 22 nodos](../tools/vca_cascaded_output_dc_reference.py) extiende los [15 nodos anteriores](VCA_CASCADA_DC.md) con Q1_BASE y seis nodos de Q1/Q12/Q17. **SVC-9, Fig. 9-11, PDF p. 13**, muestra Q14_COLLECTOR→Q12_BASE y Q13_COLLECTOR→Q17_BASE; la [transcripción](../evidence/vca_output_conversion.json) registra la unión R10/R11/C4 en Q1_BASE. Los valores provienen de **tabla 7-8, PDF pp. 30–31**. **SVC-204D §2.9, PDF p. 12** describe la conversión diferencial a salida simple.

Las corrientes de base PNP de Q12/Q17 **entran** en los nodos de colector de Q14/Q13, y la corriente de base de Q1 entra en el nodo R10/R11. Por tanto, con las corrientes PNP positivas saliendo de la base:

```text
(10−V_Q1b)/R10 + IB_Q1 = (V_Q1b−Vw2)/R11
(V_Q1b−Vw2)/R11 = (Vw2−Vw1)/R13 + IC14 + IC13 − IB_Q12 − IB_Q17
IC14 = (Vw2−V_Q14c)/(R18+R12_L) + IB_Q12
IC13 = (Vw2−V_Q13c)/(R21+R12_R) + IB_Q17
```

En el escenario condicionado con controles `2 V`, balances eléctricos `12,5/50 Ω`, rieles `±10 V`, `I_S=10⁻¹⁴ A`, `β_F=100`, `β_R=5` y `298,15 K`, se obtiene `V_Q1b≈8,780 V`, `Vw2≈7,243 V`, `V_Q17c≈2,740 V`. La última tensión es **antes** de C2, no un nivel DC en el conector. Las 22 KCL cierran a `<10⁻¹² A`. La solución predeterminada mantiene CR1/CR2 abiertos y exige `0≤V_Q17c≤10 V`; fuera de ese dominio se utiliza el modelo paramétrico explícito de los diodos. C2/C4 están abiertos en DC.

La [regresión](../tests/test_vca_cascaded_output_dc_reference.py) comprueba R10/R11, ambos cursores, la contribución de las bases PNP y el cambio de sesgo con los controles. El modelo usa parámetros semiconductores **impuestos** y voltajes de control impuestos. Las tolerancias de componentes, modelos medidos de 2N4058/1N458A, ESR/fugas, saturación/clipping validado, contornos completos y unidad física siguen inciertos. Esta referencia proporciona el punto de trabajo y Jacobiano local para la [red AC hasta conectores](CARGA_AC_SALIDA.md), no una afirmación de fidelidad sonora.
