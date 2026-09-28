# Transitorio no lineal del núcleo del ladder

## Frontera y evidencia

La [referencia offline](../tools/filter_ladder_nonlinear_transient_reference.py) resuelve las **16 tensiones nodales** de la [topología de placa 4](LADDER_EBERS_MOLL_DC.md) en cada paso. Las diez leyes BJT Ebers–Moll se evalúan con las tensiones **actuales**, incluidas ambas junturas de cada transistor. Los capacitores C16/C11/C7/C3 `68 nF`, C24 `220 µF` y C27 `10 µF` proceden de **SVC-9 Fig. 9-11, PDF p. 13, y tabla 7-8, PDF p. 30**; su [grafo](../evidence/filter_ladder_ac_core.json) es el mismo que usa la [referencia lineal](LADDER_TRANSITORIO_LINEAL.md). La formulación BJT simple se documenta en [Nagel y Pederson, *SPICE*, 1973, PDF pp. 4–5](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1973/ERL-m-382.pdf). Los valores de β directo/inverso, `I_S` y temperatura permanecen **impuestos**, sin medición de una unidad.

BUS es una frontera de voltaje ideal que excita C27. Q28 mantiene durante cada paso la corriente condicional del punto DC; se prueba su margen DC, pero no su dinámica. Los cuatro capacitores entre ramas y C24/C27 son ideales. Esta referencia **de núcleo abierto** no conecta C1/C5 ni la recuperación Q5–Q8, C10/R14 de emphasis, VCA o impedancia del mixer. La [referencia temporal acoplada](TRANSITORIO_FILTRO_ACOPLADO.md) ya une ladder, recuperación y retorno. Se observa la diferencia interna de los emisores Q2/Q3, no una salida de audio.

## Ecuación y unidades

`F(v)` reúne los 16 residuos DC en **amperios**, todos como corriente entrante menos saliente. `C` es la matriz de carga en faradios. Para un paso `Δt` en segundos, voltajes absolutos `v_n` en voltios y cambio de BUS `Δb`:

```text
Δq = C·(v_n−v_(n−1)) − C27·Δb·e_BASE       C
F(v_n) − Δq/Δt = 0                         A
```

Euler implícito permite que corrientes BJT y cargas se resuelvan **simultáneamente**. Newton amortiguado actualiza las 16 tensiones; cada iteración evalúa Ebers–Moll y un Jacobiano numérico, y sólo admite un paso si disminuye el residuo escalado. Los casos fuera de dominio exponencial o sin convergencia fallan explícitamente. La regresión exige un residuo máximo de balance carga/KCL `<10⁻¹⁰ A`. La corriente de pin 4 se obtiene como `C27·Δ(BUS−BASE_Q29)/Δt` en amperios. El estado que entra y sale del paso está en voltajes **absolutos**, a diferencia de la referencia lineal, que usa perturbaciones respecto del DC.

## Contrastes numéricos

Con RANGE eléctrico `0,1`, R11 centrado, R49 `250 Ω`, R73 `500 Ω` desde BOTTOM, `T=298,15 K`, todos los `I_S=10⁻¹⁴ A`, β directo `100`, β inverso `5`, rieles ideales ±10 V y `Δt=1/48000 s`:

- El punto DC inicial permanece fijo con BUS constante en ambos candidatos R61.
- Escalones BUS de `±0,1 V` convergen con balance de carga inferior a `10⁻¹⁰ A` y las cargas de C3/C7/C11/C16 se cancelan por pares en la suma global.
- Tras 200 muestras (`≈4,17 ms`), un escalón de `1 mV` coincide con el [modelo lineal](LADDER_TRANSITORIO_LINEAL.md) dentro del **2 %** en la diferencia Q2−Q3 para ambos R61. Un escalón de `0,1 V` se aparta claramente del escalado lineal, sin que esa divergencia se use como medida de fidelidad.

Se trata de un **oráculo de circuito offline**, no de un procesador de audio en tiempo real: aloca objetos, lee evidencia al preparar el paso y resuelve una matriz densa con iteraciones variables. La [extensión acoplada](TRANSITORIO_FILTRO_ACOPLADO.md) ya incluye recuperación y EMPHASIS; siguen pendientes carga de salida, componentes parásitos, variación de controles, identificación de parámetros, estabilidad y coste a distintas tasas de muestreo. Un solver DSP de tiempo acotado deberá contrastarse contra ambos oráculos.

```powershell
python tools/filter_ladder_nonlinear_transient_reference.py
python -m unittest discover -s tests -q
```
