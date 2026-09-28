# Transitorio lineal del núcleo de cuatro celdas

La [referencia temporal](../tools/filter_ladder_linear_transient_reference.py) continúa la [red de pequeña señal](LADDER_PEQUENA_SENAL.md) de la placa 4, con C16/C11/C7/C3 `68 nF` entre ramas, C24 `220 µF` a masa y C27 `10 µF` desde el bus. Topología y valores: **SVC-9 Fig. 9-11, PDF p. 13; tabla 7-8, PDF p. 30**. Los resistores y el Jacobiano de las diez leyes BJT proceden del [punto DC Ebers–Moll](LADDER_EBERS_MOLL_DC.md) para un candidato R61 y parámetros impuestos. La fuente de BUS se trata como tensión ideal; se observa la diferencia de emisores superiores Q2/Q3 sin carga. Recuperación, emphasis, VCA y salida siguen fuera.

Todos los voltajes son **perturbaciones en V respecto del punto DC**, no voltajes absolutos de una nota tocada. La matriz `C` está en faradios, `G` en siemens y el paso `Δt` en segundos. Cada capacitor entre ramas estampa cargas iguales y opuestas. Los 16 residuos KCL están orientados como **corriente entrante menos saliente**. La discretización por Euler implícito es:

```text
G·δv_n − C·(δv_n−δv_(n−1))/Δt
       + C27·(δBUS_n−δBUS_(n−1))/Δt · e_BASE = 0       A

(G−C/Δt)·δv_n = −C·δv_(n−1)/Δt
                   −C27·(δBUS_n−δBUS_(n−1))/Δt · e_BASE
```

La corriente de pin 4 hacia C27 se calcula como `C27·Δ(BUS−BASE)/Δt` en amperios. Se devuelve un residuo máximo de KCL por paso; la regresión exige `<10⁻¹¹ A`. La dirección de los ocho residuos de uniones internas se corrigió a entrante menos saliente antes de admitir esta referencia. Las raíces DC no cambiaron, pero esa convención sí determina el signo correcto de las corrientes de carga y la estabilidad del sistema temporal.

Con el escenario condicionado previo y un escalón **pequeño de 1 mV** en BUS a 48 kHz, el pico diferencial interno calculado es ≈`0,485 mV` con R61 `200 Ω` y ≈`0,149 mV` con R61 `200 kΩ` durante los primeros 10 ms. Son resultados de un circuito **linealizado** con fronteras abiertas, no niveles de salida del instrumento. Una prueba adicional excita un seno de 100 Hz durante diez ciclos a 4,8 kHz y compara la magnitud de la última vuelta con la [solución compleja](LADDER_PEQUENA_SENAL.md). La diferencia observada del 10–13 % es compatible con el amortiguamiento esperado de Euler implícito a 48 muestras por ciclo; se exige acuerdo dentro del 15 %.

Esta referencia es **offline**: resuelve una matriz densa por paso y no cumple aún el presupuesto de audio en tiempo real. No incluye la variación no lineal de las corrientes BJT al moverse lejos del sesgo, capacitancias de juntura, ESR/fuga, impedancia del mixer, recuperación ni lazo de regeneración. El siguiente bloque debe derivar un integrador no lineal de carga y acoplar las fronteras externas antes de optimizarlo para el plugin. No se infiere fidelidad sonora.

La [continuación no lineal](LADDER_TRANSITORIO_NO_LINEAL.md) ya resuelve las mismas seis cargas junto con las corrientes BJT actualizadas en cada paso. Esta referencia lineal se conserva como límite diferencial independiente.

```powershell
python tools/filter_ladder_linear_transient_reference.py
python -m unittest discover -s tests -q
```
