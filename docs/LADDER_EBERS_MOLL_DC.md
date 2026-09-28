# Punto DC del ladder con ambas junturas BJT

## Evidencia y alcance

La topología de los diez transistores, cuatro taps de base, ocho conexiones internas de colector/emisor, BOTTOM y TAIL proviene de **SVC-9 Fig. 9-11, PDF p. 13** (SVC-204D p. 69), trazada en [pilas activas](PILAS_ACTIVAS_LADDER_DC.md). La columna pasiva R4/R16/R32/R41/R52 y las rutas R54/R76/R73/R61 proceden del mismo esquema y de la lista de piezas 7-8, PDF pp. 30–31. Los capacitores C3/C7/C11/C16/C24/C27 permanecen abiertos en DC.

La [referencia ejecutable](../tools/filter_ladder_ebers_moll_dc_reference.py) usa el modelo **Ebers–Moll simple**: [Nagel y Pederson, *SPICE*, 1973, PDF pp. 4–5](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1973/ERL-m-382.pdf) dan las ecuaciones terminales del BJT y distinguen β directo e inverso; el [manual de ngspice, §7.3.3](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf) aclara que el modelo Gummel–Poon se reduce al Ebers–Moll simple al omitir parámetros de segundo orden. Se imponen `I_S` en amperios, β directo y **β inverso para cada uno de los diez BJT**, y temperatura de unión en kelvin. No se dispone de estos parámetros medidos en una placa Model D. El cierre Q26/Q28 que fija la corriente de TAIL aún usa su ley activa condicional; se comprueba por separado su margen de colector.

## Ecuaciones de cada transistor

Con corrientes positivas entrando por base y colector, y saliendo por emisor:

```text
F = I_S · [exp(V_BE/V_T) − 1]             A
R = I_S · [exp(V_BC/V_T) − 1]             A
I_C = F − R − R/β_R                      A
I_B = F/β_F + R/β_R                      A
I_E = I_C + I_B                           A
V_T = kT/q                                V
```

En región activa, `V_BC<0` y la rama inversa aporta casi nada. Con `V_BC>0` el modelo incluye conducción base colector y puede resolver un BJT saturado. No contiene efecto Early, caída de β a alta inyección, resistencias internas, ruptura ni almacenamiento de carga. La igualdad `I_E=I_C+I_B` se comprueba en la regresión. Un `V_BC>0` clasifica la juntura polarizada hacia adelante; no da una especificación medida de `V_CE(sat)`.

El solver resuelve **16 incógnitas de voltaje**: cuatro taps, BOTTOM, TAIL, bases Q29/Q30 y ocho uniones internas de las dos pilas. Aplica KCL en los cuatro taps, BOTTOM, TAIL, ambas bases y las ocho uniones. Usa Newton amortiguado con Jacobiano numérico y pivoteo, iniciado en la solución activa anterior. Acepta sólo un residuo máximo de KCL inferior a `10⁻¹¹ A`; si no converge o sale del dominio exponencial, falla explícitamente. Los rieles ±10 V y los resistores nominales se tratan ideales.

## Escenario de regresión

Se usan los parámetros hipotéticos previos: RANGE eléctrico `0,1`, R11 centrado, R49 `250 Ω`, `V16=0 V`, R73 `500 Ω` desde BOTTOM, `T=298,15 K`, `I_S=10⁻¹⁴ A` y β directo `100` en todos los dispositivos. Se **impone β inverso `5`**; también se prueban `2` y `20` como sensibilidad, no como tolerancias documentadas.

| R61 documental | BOTTOM | TAIL | Junturas base colector hacia adelante | KCL máximo |
| --- | ---: | ---: | --- | ---: |
| 200 Ω | ≈1,96075 V | ≈1,45617 V | ninguna | <`10⁻¹¹ A` |
| 200 kΩ | ≈9,95640 V | ≈9,43195 V | Q29/Q23/Q19/Q10 y Q30/Q24/Q20/Q11 | <`10⁻¹¹ A` |

La solución de 200 Ω reproduce el límite activo dentro de la precisión del modelo. Para 200 kΩ, la solución activa previa **salía de su dominio**; Ebers–Moll devuelve una solución distinta con ocho junturas inversas conduciendo. Su voltaje TAIL cambia al variar β inverso entre 2 y 20, mostrando que el parámetro desconocido importa. **Ambos candidatos siguen siendo escenarios**, no una selección del R61 físico. Para discriminar la discrepancia esquema/BOM hará falta evidencia de población de placa u otra fuente independiente y parámetros de dispositivo defendibles.

## Siguiente gate

El punto DC incluye ahora una ley válida en saturación simple, pero aún no es un filtro sonoro. Faltan dinámica de C3/C7/C11/C16, C24/C27, recuperación Q5–Q8, realimentación por R14/C10, variación de β e `I_S` entre dispositivos, efectos de alta inyección y carga del VCA. El siguiente bloque grande debe derivar la red temporal de cuatro celdas alrededor de este punto DC y validar balances de carga y límites de pequeña señal antes de integrarla en audio.

```powershell
python tools/filter_ladder_ebers_moll_dc_reference.py
python -m unittest discover -s tests -q
```
