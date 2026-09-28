# Núcleo del ladder en pequeña señal

## Alcance y evidencia

La **Fig. 9-11, SVC-9 PDF p. 13** y **tabla 7-8, PDF p. 30** muestran cuatro capacitores entre las ramas: C16 entre emisores de Q23/Q24, C11 entre Q19/Q20, C7 entre Q10/Q11 y C3 entre Q2/Q3. La lista de piezas da **0,068 µF ±10 %** para cada uno. C24 `220 µF` conecta BOTTOM a masa y C27 `10 µF` lleva el bus de mixer a la base de Q29; ambos tienen tolerancia documental `+50/−10 %`. El [grafo de capacitores](../evidence/filter_ladder_ac_core.json) fija nodos y exclusiones. Los valores nominales se convierten a faradios antes de calcular.

Esta [referencia de pequeña señal](../tools/filter_ladder_small_signal_reference.py) parte de uno de los [puntos DC Ebers–Moll](LADDER_EBERS_MOLL_DC.md), para R61 `200 Ω` o `200 kΩ` y todos los parámetros de transistor **impuestos**. El bus es una **frontera de tensión ideal**; una amplitud algebraica de `1 V` sólo normaliza la derivada de transferencia, no significa aplicar una señal física de 1 V a las junturas. Se observa la diferencia entre los emisores superiores Q2 y Q3 **sin carga**. C1/C5, recuperación Q5–Q8, VCA y salida del plugin quedan fuera. C10/R14 de emphasis está abierto; la base de Q30 mantiene únicamente la ruta DC R73/R76. La corriente de Q28 se mantiene constante ante la perturbación.

## Sistema lineal

El Jacobiano de los 16 residuos KCL DC respecto de los 16 voltajes da `G` en siemens. Cada capacitor entre nodos `a,b` estampa `+C` en las diagonales y `−C` en las dos posiciones cruzadas de la matriz `C` en faradios; C24 agrega `C` a BOTTOM y C27 a BASE_Q29. Como el residuo DC se escribió **corriente entrante menos saliente**, la ecuación compleja para frecuencia `f` en hertz es:

```text
s = j·2πf                          1/s
(G − sC) · v = −s·C27·e_BASE      A/V de BUS
H_core(f) = v_Q2_emisor − v_Q3_emisor    V/V de BUS
Y_in(f) = s·C27·(1 − v_BASE_Q29)        S
```

La [implementación](../tools/filter_ladder_small_signal_reference.py) resuelve la matriz compleja y devuelve todos los voltajes normalizados, la admitancia de entrada, las cuatro corrientes de capacitor y un residuo KCL en amperios por voltio de bus. La dirección de cada corriente de C16/C11/C7/C3 es izquierda → derecha; aparece con signo opuesto en el nodo derecho, por conservación de carga.

## Regresión y límites

Con el escenario de [sesgo DC](LADDER_EBERS_MOLL_DC.md) y β inverso `5`, C27 bloquea exactamente la perturbación en `f=0`. En R61 `200 Ω`, `|H_core(100 Hz)|≈0,457`, `|H_core(1 kHz)|≈5,04·10⁻⁴` y `|H_core(10 kHz)|≈5,28·10⁻⁸`. En R61 `200 kΩ`, los valores correspondientes son ≈`0,127`, `4,46·10⁻⁴` y `5,48·10⁻⁸`. Entre 10 y 100 kHz la magnitud desciende aproximadamente por un factor de `10⁴`, consistente con **cuatro celdas** en este circuito lineal y esta frontera abierta. Los residuos KCL calculados son menores que `10⁻¹¹ A/V` en la regresión. No se interpretan esas cifras como curva de corte o nivel audible del Model D.

Esta red carece de capacitancias de juntura y almacenamiento de carga BJT, ESR/fuga, impedancia del mixer, carga de recuperación, efecto Early y realimentación de emphasis. La tolerancia de los componentes tampoco se ha propagado. La linealización describe perturbaciones infinitesimales alrededor de un punto DC específico; no predice saturación dinámica, autooscilación ni sonido. El siguiente bloque debe incorporar las fronteras de recuperación y regeneración, y después formular un integrador temporal no lineal con balance de carga verificable.

```powershell
python tools/filter_ladder_small_signal_reference.py
python -m unittest discover -s tests -q
```
