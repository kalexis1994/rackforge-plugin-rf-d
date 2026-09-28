# Sensibilidad documental del lazo de EMPHASIS

## Pregunta y malla

El [lazo de pequeña señal](LAZO_EMPHASIS_PEQUENA_SENAL.md) tiene una ambigüedad material en R61 y tres elementos cuyo ajuste o tolerancia alteran el retorno. La [malla trazable](../evidence/filter_emphasis_sensitivity_grid.json) usa **SVC-9 Fig. 9-11, PDF p. 13**, Fig. 9-17, p. 19 y tabla 7-8, pp. 30–31: dos candidatos R61 (`200 Ω` del esquema, `200 kΩ` de la lista), R73_L `0/500/1000 Ω`, R14 eléctrico `0/25/50 kΩ`, C10 `9/10/15 µF` (nominal `10 µF`, tolerancia `+50/−10 %`) y frecuencias `30/100/300 Hz`. Son **162 escenarios discretos**, no una distribución estadística de unidades vintage. La ley angular de R14, los parámetros TIS97 y la población R61 siguen sin identificar.

La [referencia ejecutable](../tools/filter_emphasis_sensitivity_reference.py) recalcula el punto DC del ladder por cada posición de R73 y el punto DC de recuperación bajo parámetros BJT impuestos (`I_S=10⁻¹⁴ A`, β directo `100`, β inverso `5`, `298,15 K`). El cálculo AC cambia C10 dentro de la tolerancia de fabricante, mantiene R14 como resistencia eléctrica y verifica cada matriz KCL. El [transitorio acoplado](TRANSITORIO_FILTRO_ACOPLADO.md) también acepta el mismo intervalo C10 para contrastes posteriores por nivel.

## Rango calculado

Extremos de `|V_tap/V_bus|` en V/V dentro de **esta malla**:

| R61 | 30 Hz | 100 Hz | 300 Hz |
| ---: | ---: | ---: | ---: |
| `200 Ω` | 0,584–4,438 | 1,034–4,238 | 0,357–0,392 |
| `200 kΩ` | 0,426–1,337 | 0,717–1,072 | 0,172–0,192 |

El residuo máximo de las 162 soluciones fue `<3·10⁻¹⁷ A/V`. A 100 Hz con R61 `200 Ω`, la magnitud varía más de cuatro veces entre extremos de la malla. Esto demuestra que un coeficiente fijo de realimentación derivado del circuito nominal sería frágil frente a los supuestos; **no** demuestra el rango de ningún instrumento real. La magnitud incremental no codifica fase ni garantiza estabilidad temporal. Los extremos muestreados tampoco prueban máximos globales entre puntos o fuera de la tolerancia.

## Decisiones que siguen abiertas

Antes de fijar parámetros DSP o una calibración musical hay que resolver R61 en la revisión objetivo, mapear posición de R14 a resistencia, explorar β/`I_S` y dispersiones de Q5–Q8/Q29–Q30, y barrer frecuencia con el transitorio no lineal a varios niveles. La salida del VCA y su carga aún no forman parte de esta transferencia. Sin audio de referencia comparable no se afirma similitud sonora.

```powershell
python tools/filter_emphasis_sensitivity_reference.py
python -m unittest discover -s tests -q
```
