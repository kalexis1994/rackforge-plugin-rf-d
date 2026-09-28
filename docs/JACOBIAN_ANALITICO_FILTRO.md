# Jacobiano analítico del transitorio acoplado

## Derivación y fuente

El [oráculo no lineal de 24 nodos](TRANSITORIO_FILTRO_ACOPLADO.md) usa la topología de SVC-9 **Fig. 9-11, PDF p. 13**, Fig. 9-17, p. 19 y tabla 7-8, pp. 30–31. La ley simple de ambas junturas BJT se apoya en [Nagel y Pederson, *SPICE*, 1973, PDF pp. 4–5](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1973/ERL-m-382.pdf). La nueva [matriz derivada](../tools/filter_full_analytic_jacobian.py) conserva los mismos supuestos de `I_S`, β directo, β inverso y temperatura que la referencia Ebers–Moll; no añade parámetros de una unidad medida.

Para cada transistor, con `f=I_S·expm1(V_BE/V_T)`, `r=I_S·expm1(V_BC/V_T)`, β directo `β_F` e inverso `β_R`, la referencia utiliza:

```text
I_B = f/β_F + r/β_R
I_C = f − (1+1/β_R)·r
I_E = (1+1/β_F)·f − r
∂f/∂V_B = −∂f/∂V_E = I_S·exp(V_BE/V_T)/V_T     S
∂r/∂V_B = −∂r/∂V_C = I_S·exp(V_BC/V_T)/V_T     S
```

Se estampan estas derivadas en las KCL de base, colector y emisor con el signo **entrante menos saliente**. Cada resistor entre nodos agrega `−1/R` en ambas diagonales y `+1/R` entre nodos; los resistores a rieles fijos sólo aportan diagonal. Para Euler implícito se añade `−C/Δt` en siemens. C10, con el camino de serie `R_top=R14_e+R73_R`, añade una admitancia `y=(C10/Δt)/(1+(C10/Δt)R_top)` entre el tap R7/R3 y la base Q30. El resultado es el Jacobiano exacto **del modelo declarado**, no de efectos parasitarios excluidos.

## Regresión y coste

Las pruebas comparan las 576 entradas de la matriz DC con diferencias centrales de la KCL de los dos subcircuitos, para ambos candidatos R61. También fuerzan `V_BC,Q8>0` para ejercer el término de β inverso; no basta comprobar sólo transistores en activa directa. Cuatro trazas de 48 muestras (`R61=200/200 kΩ`, `R14_e=0/50 kΩ`) comparan el paso con Jacobiano analítico y con diferencias finitas: la desviación queda `<1 µV` por nodo y el residuo carga/KCL `<10⁻¹⁰ A`.

Una medición **local** en Python sobre 256 muestras, escalón sinusoidal de BUS `0,05 V` pico a `220 Hz`, `48 kHz`, R61 `200 Ω` y R14 eléctrico `0 Ω`, produjo `5,28 ms/muestra` con diferencias finitas y `2,43 ms/muestra` con el Jacobiano analítico; ambas rutas usaron 510 iteraciones Newton acumuladas. Es una medición de una ejecución en esta máquina, sin intervalo de confianza, y **no** un presupuesto de audio. La rama analítica evita 24 evaluaciones completas de KCL por iteración, pero Python todavía aloca listas, lee evidencia al preparar pasos y resuelve matrices densas con iteraciones variables.

## Gate siguiente

Para entrar al hilo de audio falta un solver portable de memoria preasignada y tiempo acotado, política explícita al no converger, barridos de tasa/nivel/controles y comparación contra este oráculo. El coste de `2,43 ms` excede ampliamente un periodo de muestra a `48 kHz` (`20,8 µs`); no se debe presentar esta optimización como motor DSP listo. Tampoco altera las incertidumbres físicas de R61, parámetros BJT, C10 y carga posterior del VCA.

```powershell
python -m unittest discover -s tests -q
```
