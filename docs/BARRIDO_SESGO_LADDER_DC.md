# Barrido de supuestos del sesgo DC del ladder

La [referencia activa](PILAS_ACTIVAS_LADDER_DC.md) se evaluó con un barrido reproducible de parámetros **hipotéticos**, para comprobar si el resultado de margen del ejemplo nominal depende de un punto aislado. El [script](../tools/filter_ladder_active_dc_sweep.py) recorre el producto cartesiano de R39 RANGE a fracciones eléctricas `0,02`, `0,1`, `0,5`, `0,9`; β `50`, `100`, `200`; e `I_S` `10⁻¹⁵`, `10⁻¹⁴`, `10⁻¹³ A`. En cada caso todos los transistores reciben el mismo β e `I_S`; no es una distribución de fábrica ni una tolerancia documentada. Los demás controles y condiciones son los del ejemplo de [pilas activas](PILAS_ACTIVAS_LADDER_DC.md): R11 centrado, R49 `250 Ω`, `V16=0 V`, `T=298,15 K`, R73 `500 Ω` desde BOTTOM y rieles ideales ±10 V. Se corren **36 escenarios por candidato R61**, 72 en total.

| R61 documental | Candidatos activos | Fallos de margen o sesgo | Error de dominio numérico | Intervalo del mínimo `V_CB` de cada escenario |
| --- | ---: | ---: | ---: | ---: |
| 200 Ω | 36 | 0 | 0 | +0,830…+1,289 V |
| 200 kΩ | 0 | 36 | 0 | −0,632…−0,174 V |

La tabla es una **salida calculada dentro del modelo activo**. En los casos de 200 kΩ, el margen negativo invalida precisamente ese modelo; sus voltajes no son soluciones físicas de saturación. La coincidencia de 36 escenarios muestra estabilidad sólo dentro de este grid restringido, con parámetros igualados. No identifica la población real de R61 ni descarta una variante de placa: esa conclusión requiere evidencia independiente y un solver que incluya saturación. También faltan otros puntos de panel, dispersión entre dispositivos, cargas externas, fuente no ideal y transitorios.

```powershell
python tools/filter_ladder_active_dc_sweep.py
python -m unittest discover -s tests -q
```

Las regresiones comprueban los 72 casos únicos, la clasificación de salida y los signos de margen esperados. El siguiente trabajo es obtener un modelo DC de transistor válido cerca y dentro de saturación y repetir el barrido antes de usarlo como gate para el sistema temporal.
