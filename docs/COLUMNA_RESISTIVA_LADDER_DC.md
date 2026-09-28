# Columna resistiva del ladder en DC

## Evidencia y frontera

La Fig. 9-11 de **SVC-9, PDF p. 13** (SVC-204D PDF p. 69), cotejada con la tabla 7-8, PDF pp. 30–31, muestra la columna de placa 4: `+10 V → R4 220 Ω → R16 150 Ω → R32 150 Ω → R41 150 Ω → R52 150 Ω → BOTTOM`. Sus cuatro taps sucesivos están asociados a los pares Q2/Q3, Q10/Q11, Q19/Q20 y Q23/Q24. El [registro legible por máquina](../evidence/filter_ladder_dc_spine.json) distingue **R52 de placa 4** de R52 de FILTER MOD en panel. En DC los capacitores C3, C7, C11, C16, C27 y C24 están abiertos.

Las corrientes hacia los elementos activos de cada tap aún no se deducen de sus tensiones. Se imponen como `J1…J4` en amperios, **positivas al salir de la columna**, de arriba abajo. Admitir signos opuestos permite probar KCL, pero no declara físicamente admisible cualquier conjunto de fronteras. `I_L` es la corriente de R52 que entra a BOTTOM. Los rieles se tratan ideales y cada resistor nominal; tolerancias y temperatura de la placa permanecen desconocidas.

## Reducción exacta de la red pasiva

```text
R_Σ = 220 + 4·150 = 820 Ω
I_L = [10 V − V_BOTTOM − (220 Ω·J1 + 370 Ω·J2
                      + 520 Ω·J3 + 670 Ω·J4)] / 820 Ω
```

Cada peso es la suma de resistencias desde `+10 V` hasta el tap correspondiente. Por KCL, las corrientes de R52, R41, R32, R16 y R4, en orden ascendente, son `I_L`, `I_L+J4`, `I_L+J4+J3`, `I_L+J4+J3+J2`, `I_L+J4+J3+J2+J1`. Las caídas correspondientes reconstruyen las cuatro tensiones de tap y `V_BOTTOM`. La [referencia ejecutable](../tools/filter_ladder_spine_dc_reference.py) devuelve residuos de KCL y del voltaje reconstruido.

El [solver inferior](BASES_FILTRO_ACOPLADAS_DC.md) usa `V_BOTTOM=R61·(I_L−I_B29−I_B30)`. En ese modelo, desplazar ambas bases por igual no altera el reparto `I_B29/I_B30`. Para cada candidato documental de R61, se obtiene una solución algebraica conjunta:

```text
I_L = [10 V − (220 Ω·J1 + 370 Ω·J2 + 520 Ω·J3 + 670 Ω·J4)
       + R61·(I_B29+I_B30)] / (820 Ω + R61)
```

El cálculo de ejemplo con los parámetros hipotéticos de [bases inferiores](BASES_FILTRO_ACOPLADAS_DC.md), `J1…J4=0` y β29/β30 `=100`, da `I_L≈9,8039 mA`, `V_BOTTOM≈1,9608 V` para R61 `=200 Ω`; con R61 `=200 kΩ` da `I_L≈49,863 µA`, `V_BOTTOM≈9,9591 V`. Con β infinito, ambas opciones reducen exactamente al divisor `I_L=10 V/(820 Ω+R61)`. **J=0 sólo ilustra el sistema; los pares activos no se declararon apagados.** Ningún resultado elige el valor real de R61.

## Estado RACE

La [continuación con las dos pilas activas](PILAS_ACTIVAS_LADDER_DC.md) deriva las cuatro corrientes de tap si se imponen β e `I_S` para los ocho dispositivos superiores y se cumple la región activa.

La topología y la ecuación de esta **columna pasiva** están documentadas y sometidas a regresión. El acoplamiento es condicional: faltan funciones de corriente de los cuatro pares, sesgos de colector, región de operación, parámetros de transistores instalados y la resolución física de R61. No es todavía un modelo de cuatro polos, frecuencia de corte, resonancia ni sonido. El siguiente paso es cerrar las dos ramas de transistores y comprobar márgenes de tensión antes de trasladar este sesgo a un modelo temporal.

```powershell
python tools/filter_ladder_spine_dc_reference.py
python -m unittest discover -s tests -q
```

Las pruebas conservan KCL en los cuatro taps y BOTTOM, reconstruyen el voltaje de la columna, recorren ambos R61 y comprueban el límite de β infinito.
