# Transitorio no lineal con el primer VCA activo

La [referencia offline de 33 nodos](../tools/filter_vca1_active_transient_reference.py) añade Q16/Q15/Q18 a los catorce BJT del [filtro y recuperador](TRANSITORIO_FILTRO_ACOPLADO.md). Mantiene simultáneamente los capacitores del ladder, entrada de filtro, recuperación, EMPHASIS y C6/C15 de la [entrada VCA](TRANSITORIO_CARGA_VCA1.md). Los valores y conexiones son de **SVC-9 Fig. 9-11, PDF p. 13, y tabla 7-8, pp. 30–31**, con función descrita en **SVC-204D §2.9, PDF p. 12**. El modelo Ebers–Moll de dos junturas y sus parámetros impuestos se documentan en el [núcleo DC](NUCLEO_ACTIVO_VCA1_DC.md). No se introducen nuevos valores de transistor inferidos de audio.

El estado inicial concatena los puntos DC del ladder, recuperador y primer VCA. C6_LEFT queda al DC del colector de recuperación por R2; Q16_BASE y Q15_BASE conservan su sesgo independiente porque C6 está abierto en continua. C15 guarda ese sesgo. Un paso de Euler implícito resuelve `F(v_n)−C·(v_n−v_{n−1})/Δt+b_BUS=0` en amperios, más el estado explícito de tensión de C10 con su resistencia de retorno. Se recalculan las 17 leyes BJT por paso y se amortigua Newton; el Jacobiano se aproxima por diferencias finitas, válido sólo como oráculo offline. El cursor de balance y la fuente de contorno permanecen voltajes constantes ideales; Q14/Q13 no cargan los colectores. La salida reportada `V_Q16c−V_Q15c` es **intermedia**, antes del segundo multiplicador y Q12/Q17.

Las [pruebas](../tests/test_filter_vca1_active_transient_reference.py) verifican que el estado DC es un punto fijo con BUS=0, que la corriente de R2 iguala la de C6, que la suma de cambios de carga coincide con los capacitores a masa y con la excitación por C27, y que un paso diminuto coincide con la matriz AC de 33 nodos discretizada por Euler. Una traza corta no nula confirma que el punto no queda congelado. El residuo de KCL/carga se exige `<10⁻¹⁰ A` en los casos probados. Es una comprobación de consistencia del modelo, no de fidelidad ni de estabilidad en todos los ajustes.

No se mide presupuesto de tiempo real: Python aloca matrices 33×33, usa derivadas numéricas y Newton de iteraciones variables. Antes de promocionar al motor se deben cerrar la red de alimentación del balance, segundo VCA y salida, cuantificar dispersión de TIS97 y transferir una solución acotada con pruebas de audio y tiempo. La frecuencia de `48 kHz` y los niveles de BUS de la regresión son estímulos de prueba, no especificaciones medidas del sintetizador.

```powershell
python -m unittest discover -s tests -q
```
