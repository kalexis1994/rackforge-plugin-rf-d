# Referencia compartida de −4 V, placa CA3046

## Evidencia y conexiones

La Fig. 9-3 de **SVC-9, PDF p. 5** (misma placa en SVC-204D, PDF p. 61) muestra R166 = 6,2 kΩ desde −10 V, R174 = 3,9 kΩ hacia masa y C14 = 0,12 µF hacia masa. La [transcripción estructurada](../evidence/neg4_reference_loads.json) inventaría las seis conexiones externas visibles a la línea: entradas inversoras de IC3/IC5/IC10 (pin 2 de cada 741) y R49/R86/R161 = 1 kΩ hacia las bases de Q4/Q15/Q27, respectivamente. Cada par pertenece a uno de los tres osciladores de la misma placa. Los cruces sin punto de unión en el dibujo no se han contado como cargas.

Los 741 tienen corrientes de entrada finitas y las tres bases consumen corriente según el estado de sus transistores y las sierras. El esquema no da esas corrientes ni el valor real de las alimentaciones. Por ello, la etiqueta **−4 V** no es una fuente ideal independiente ni una medida del nodo cargado.

## Reducción de continua condicionada

Con las alimentaciones impresas exactas, las resistencias nominales y C14 abierto en continua, el divisor sin carga tiene

`V_th = [(-10 V)/R166 + (0 V)/R174] / [1/R166 + 1/R174] = −3,861386 V`,

`R_th = R166 || R174 = 2394,059 Ω`.

Si `I_ext` es la **suma firmada de corrientes que salen** del nodo hacia IC3/IC5/IC10 y R49/R86/R161, entonces la ley de nodos da `V_ref = V_th − R_th·I_ext`. Un escenario impuesto de `I_ext = +1 µA` produce `−3,863780 V`: **−2,394 mV por µA** respecto del divisor sin carga. Una corriente de signo contrario lo desplaza en sentido opuesto. Esta sensibilidad no predice `I_ext`, ni implica que los tres osciladores compartan la carga por igual.

Si IC3 regula idealmente el colector de Qb a `V_ref` y R50 = 39 kΩ es su única carga, la corriente condicional de Qb varía en `R_th/R50 = 0,061386 µA` por cada `+1 µA` de `I_ext`. El valor absoluto y la dirección real de `I_ext` requieren resolver los tres formadores de sierra y los offsets/bias de los 741. C14 añade memoria en transitorios; no es una resistencia de carga DC.

La [herramienta de sensibilidad](../tools/neg4_reference.py) recibe una corriente **impuesta**, expresada en µA:

```powershell
python tools/neg4_reference.py --external-current-ua 1
```

**Estado RACE:** C1 identifica las conexiones visibles de la referencia compartida; C3 sólo establece la ecuación de carga de continua. Falta la corriente de cada rama, regulación de −10 V, tolerancias de R166/R174 y comportamiento transitorio de C14. Ningún resultado de este documento se usa aún para afirmar afinación o equivalencia sonora.
