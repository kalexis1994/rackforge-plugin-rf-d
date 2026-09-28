# Lazo de EMPHASIS en pequeña señal

## Camino eléctrico y reducción

El [grafo del retorno](../evidence/filter_regeneration_path.json) procede de SVC-9 **Fig. 9-11, PDF p. 13**, **Fig. 9-17, p. 19** y tabla 7-8, **pp. 30–31** (SVC-204D pp. 69, 75). La señal en el tap `R7/R3` de la [recuperación Q5–Q8](RECUPERACION_ACTIVA_FILTRO.md) cruza C10 `10 µF`, pin 7, la resistencia eléctrica entre cursor y extremo superior de R14 de panel (`0–50 kΩ`), pin 6 y el segmento derecho del trimmer R73 (`0–1 kΩ`) hasta la **base de Q30**. R14 está marcado `50K REV AUD`, pero la curva entre posición de perilla y resistencia no está medida. El otro segmento de R73 llega a `BOTTOM` por R76 `330 Ω`.

La [referencia de 16 nodos](LADDER_EBERS_MOLL_DC.md) ya incorpora `R76 + R73_L` entre `BOTTOM` y la base de Q30, con corriente de base finita y `BOTTOM` dinámico. En DC C10 abre el lado derecho, por lo que se puede conservar su punto de trabajo. En AC pin 7 y pin 6 no tienen ramas adicionales en el dibujo trazado; se eliminan exactamente como dos nodos internos de serie. Si `R_top=R14_e+R73_R`, `R73_R=1000 Ω−R73_L`, `s=j2πf`, la admitancia entre tap y base es:

```text
Y_return(s) = s C10 / (1 + s C10 R_top)   [S]
I_return(s) = Y_return(s) · (V_tap − V_Q30base)   [A]
```

No se duplica `R76+R73_L`: permanece en la matriz del ladder. La [referencia ejecutable](../tools/filter_emphasis_loop_small_signal_reference.py) exige que el segmento izquierdo usado al calcular DC coincida con el segmento del barrido AC. La rama nueva se estampa en las dos KCL, conservando exactamente la corriente en ambos terminales. La base de Q30 conserva su conductancia diferencial Ebers–Moll; `BOTTOM` puede moverse. Esta extensión cierra la red AC del [ladder de 16 nodos](LADDER_PEQUENA_SENAL.md) con la [recuperación de ocho nodos](RECUPERACION_ACTIVA_FILTRO.md) y C1/C5/C9/C10. La entrada continúa siendo una perturbación ideal de 1 V en el bus de mezcla, por C27.

## Contraste condicionado

Con `I_S=10⁻¹⁴ A` para cada BJT, β directo `100`, β inverso `5`, `298,15 K`, `R73_L=500 Ω`, ajustes de cutoff descritos en los scripts y `100 Hz`:

| R61 | Estado | `R14_e` | `|V_tap/V_bus|` | `|ΔV_top/V_bus|` |
| ---: | --- | ---: | ---: | ---: |
| `200 Ω` | C10 abierto | — | 3,883 | 0,383 |
| `200 Ω` | C10 conectado | `0 Ω` | 1,677 | 0,188 |
| `200 Ω` | C10 conectado | `25 kΩ` | 4,106 | 0,408 |
| `200 Ω` | C10 conectado | `50 kΩ` | 4,002 | 0,396 |
| `200 kΩ` | C10 abierto | — | 1,068 | 0,105 |
| `200 kΩ` | C10 conectado | `0 Ω` | 0,864 | 0,098 |
| `200 kΩ` | C10 conectado | `25 kΩ` | 1,070 | 0,106 |
| `200 kΩ` | C10 conectado | `50 kΩ` | 1,070 | 0,106 |

El valor R61 del esquema (`200 Ω`) contradice la lista de piezas (`200 kΩ`), de ahí los dos escenarios. Las cifras son **ganancias incrementales locales** en V/V, no nivel de salida, posición de perilla, estimación de autooscilación ni validación sonora. La respuesta a 100 Hz no es monótona entre los tres valores de R14 en el escenario de `200 Ω`: la red contiene polos, carga y fase, por lo que no cabe convertir una posición del control en un coeficiente único a partir de esta tabla. En `0 Hz`, C10 y C27 abren sus caminos y la respuesta excitada vale cero. Las pruebas verifican la KCL en ambos extremos de C10/R14/R73, con residuo `<10⁻¹¹ A/V`.

## Límites para el siguiente bloque

El cálculo usa un punto DC por escenario y un Jacobiano local. No representa excursiones grandes, capacitancias de juntura, fuga/ESR de C10, cargas del VCA, saturación de etapas, estabilidad temporal de la autooscilación ni variantes reales de placa. En particular, una magnitud mayor que uno para una fuente de *1 V normalizado* no puede interpretarse como una excursión físicamente válida de varios voltios. La [referencia temporal no lineal acoplada](TRANSITORIO_FILTRO_ACOPLADO.md) ya conserva las cargas y ambas junturas BJT; la [malla de sensibilidad](SENSIBILIDAD_EMPHASIS.md) varía C10 dentro de su tolerancia `+50/−10 %` y controles eléctricos discretos. Antes de elegir constantes DSP faltan barridos más amplios de polarización, un solver de tiempo acotado y comparación audible de procedencia trazable.

```powershell
python tools/filter_emphasis_loop_small_signal_reference.py
python -m unittest discover -s tests -q
```
