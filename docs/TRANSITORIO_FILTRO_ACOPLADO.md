# Transitorio no lineal acoplado del filtro y EMPHASIS

## Alcance y procedencia

La [referencia offline de 24 nodos](../tools/filter_full_nonlinear_transient_reference.py) une el [ladder Ebers–Moll de 16 nodos](LADDER_EBERS_MOLL_DC.md), la [recuperación Q5–Q8 de ocho nodos](RECUPERACION_ACTIVA_FILTRO.md) y el [retorno C10/R14/R73/R76](LAZO_EMPHASIS_PEQUENA_SENAL.md). Sus conexiones y valores nominales vienen de **SVC-9 Fig. 9-11, PDF p. 13**, Fig. 9-17, p. 19, y tabla 7-8, pp. 30–31 (SVC-204D pp. 69 y 75). La ley BJT simple se documenta en [Nagel y Pederson, *SPICE*, 1973, PDF pp. 4–5](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1973/ERL-m-382.pdf). Las catorce leyes BJT recalculan ambas junturas en cada paso: diez transistores del ladder y Q5/Q6/Q7/Q8. Las ramas C16/C11/C7/C3, C24/C27, C1/C5 y C9 se resuelven a la vez; C10 conserva su propia tensión de estado.

La fuente de BUS es ideal. La corriente de cola aportada por Q28 se fija al valor del punto DC condicionado; no se calcula la dinámica del circuito de cutoff. Tampoco están presentes el VCA, las cargas de salida, capacitancias de juntura, ESR/fugas ni los parámetros de una unidad física. R61 se ensaya en los dos candidatos documentales `200 Ω` y `200 kΩ`.

## Ecuación y estado

Para las 24 tensiones absolutas `v` en voltios, `F(v)` reúne KCL DC en amperios, con signo **entrante menos saliente**. `C` es la matriz nodal de carga en faradios para todos los capacitores salvo C10; `Δb` es el cambio de BUS. El estado adicional `u10` es la tensión del propio C10 desde el tap `R7/R3` hasta su otro terminal. Si `R_top=R14_e+R73_R`, Euler implícito elimina sus nodos de serie exactamente:

```text
g10 = C10/Δt                                       S
I10 = [g10/(1+g10·R_top)]·[(V_tap−V_Q30base)−u10_prev]     A
u10_new = V_tap−V_Q30base−R_top·I10                V
Δq = C·(v_new−v_prev) − C27·Δb·e_BASE              C
F(v_new) + I10·(e_Q30base−e_tap) − Δq/Δt = 0     A
```

Esto admite incluso `R_top=0 Ω` sin una división por resistencia nula. `R76+R73_L` ya vive entre `BOTTOM` y la base de Q30 en `F`; la rutina comprueba que el segmento del trimmer usado en el punto DC sea el mismo durante el paso. Newton amortiguado resuelve las 24 tensiones; rechaza parámetros no finitos, condiciones fuera de dominio exponencial y pasos que no disminuyen el residuo. El paso usa ahora un [Jacobiano analítico](JACOBIAN_ANALITICO_FILTRO.md), con la versión de diferencias finitas disponible para regresión. Como es referencia **offline**, las alocaciones y el número variable de iteraciones están permitidos aquí; no son diseño DSP para el hilo de audio.

## Contrastes reproducibles

Con ±10 V nominal, `I_S=10⁻¹⁴ A`, β directo `100`, β inverso `5`, `T=298,15 K`, `R73_L=500 Ω` y `Δt=1/48000 s`:

- El punto DC permanece exactamente fijo durante un paso sin cambio de BUS, para ambos R61.
- Escalones de `±0,1 V` conservan carga/KCL con residuo `<10⁻¹⁰ A`. La corriente de la rama en serie coincide con `C10·Δu10/Δt`; las cargas de C1/C5 y las cuatro celdas se cancelan por pares en la suma global.
- Un primer paso de `10 µV` coincide con Euler implícito de la [matriz de pequeña señal cerrada](LAZO_EMPHASIS_PEQUENA_SENAL.md) dentro del `1 %` por nodo o `0,1 nV` para valores próximos a cero, en el escenario ensayado.
- En 32 muestras tras un escalón, con R61 `200 Ω` y `R14_e=0 Ω`, el cambio del tap es `≈38,6 µV` para un BUS de `1 mV` y `≈1,95 mV` para un BUS de `0,1 V`. El segundo no es 100 veces el primero: muestra no linealidad **del modelo condicionado**. No se interpreta como ganancia o saturación de un Model D medido.

Estas pruebas comprueban conservación y consistencia de la discretización; no prueban autooscilación, estabilidad en todos los parámetros, respuesta audible ni fidelidad. La [malla de sensibilidad AC](SENSIBILIDAD_EMPHASIS.md) ya barre C10, R14, R73 y R61; falta hacerlo con excitación temporal y variar los parámetros BJT. Después habrá que identificar las variantes de placa y trasladar un modelo reducido a un solver de tiempo acotado, contrastado con este oráculo y con referencias sonoras de procedencia conocida.

```powershell
python -m unittest discover -s tests -q
```
