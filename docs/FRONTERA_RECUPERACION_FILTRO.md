# Frontera pasiva entre ladder y recuperación

## Circuito documentado

La **Fig. 9-11, SVC-9 PDF p. 13** (SVC-204D p. 69) lleva el emisor de Q2, lado izquierdo del ladder, por **C5** a la base de Q8; **R31** une esa base a masa. El emisor de Q3, lado derecho, llega por **C1** a la base de Q6; **R38** une esa base a masa. La **tabla 7-8, PDF pp. 30–31** especifica C1/C5 `0,22 µF ±10 %` y R31/R38 `47 kΩ ±5 %`. El [grafo verificable](../evidence/filter_recovery_input_boundary.json) distingue ambas ramas. En DC C1/C5 están abiertos; si se impone corriente de base nula, las bases Q8/Q6 quedan a 0 V por R31/R38.

La [referencia de pequeña señal cargada](../tools/filter_recovery_input_boundary_reference.py) agrega dos nodos a la [red de 16 nodos](LADDER_PEQUENA_SENAL.md): `Q8_BASE` y `Q6_BASE`. Estampa ambos capacitores en la matriz `C` en faradios y la conductancia de cada shunt en la matriz `G` en siemens. El bus de mixer sigue siendo una fuente ideal normalizada por voltio; C27, C24 y las cuatro celdas permanecen. Se resuelve una matriz compleja de **18 nodos** alrededor del mismo punto DC. Las **corrientes de base de Q8/Q6 se imponen en cero**, de modo que este bloque representa la carga pasiva, no la etapa de recuperación activa.

Con esa frontera, cada base de recuperación obedece por separado:

```text
V_base/V_emisor = s·C·R / (1+s·C·R),  s=j2πf
C=0,22 µF, R=47 kΩ
```

Esta ecuación comprueba la orientación de C1/C5 y la KCL de cada nodo nuevo; **no** basta multiplicar la transferencia del núcleo abierto por ella, porque C1/C5 y R31/R38 también cargan los emisores superiores y modifican el ladder.

## Contraste condicionado

Para el escenario de [sesgo Ebers–Moll](LADDER_EBERS_MOLL_DC.md) y `100 Hz`, con R61 `200 Ω`, la magnitud diferencial en emisores superiores pasa de ≈`0,457 V/V` con salida abierta a ≈`0,406 V/V` cargada; en las bases Q8/Q6 es ≈`0,401 V/V`. Con R61 `200 kΩ`, las cifras correspondientes son ≈`0,127`, `0,112` y `0,111 V/V`. En DC, C27 bloquea la transferencia; el residuo KCL complejo de las pruebas es `<10⁻¹¹ A/V`. Estos números dependen de β directo/inverso e `I_S` impuestos y no son niveles de jack o promesa de sonido.

Q8/Q6 **no** son cargas de base nula en el instrumento. La [recuperación activa Q5–Q8](RECUPERACION_ACTIVA_FILTRO.md) ya calcula su sesgo DC y su carga AC condicionada, incluido R7/R3. Aún faltan la realimentación C10/R14, ESR de C1/C5, VCA y salida. La [referencia no lineal temporal](LADDER_TRANSITORIO_NO_LINEAL.md) conserva por ahora los emisores superiores sin esta carga; no deben confundirse las dos fronteras.

```powershell
python tools/filter_recovery_input_boundary_reference.py
python -m unittest discover -s tests -q
```
