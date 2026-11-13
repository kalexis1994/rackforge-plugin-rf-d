# Referencia compartida de −4 V, placa CA3046

## Evidencia y conexiones

La Fig. 9-3 de **SVC-9, PDF p. 5** (misma placa en SVC-204D, PDF p. 61) muestra R166 = 6,2 kΩ desde −10 V, R174 = 3,9 kΩ hacia masa y C14 = 0,12 µF hacia masa. La [transcripción estructurada](../evidence/neg4_reference_loads.json) registra las entradas inversoras de IC3/IC5/IC10 (pin 2 de cada 741) y R49/R86/R161 = 1 kΩ hacia las bases de Q4/Q22/Q30, respectivamente. Cada par pertenece a uno de los tres osciladores de la misma placa. El cotejo visual corrigió dos designadores de una lectura anterior. Q15 y Q27 son las etapas de salida de la sierra de OSC2 y OSC3.

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

## Corrientes de OSC2 y OSC3 con C14

Se midió la corriente combinada del 741 y la base del transistor
de cada oscilador silenciado. Se conservó la dinámica de sus
núcleos, los formadores de onda y la carga del selector en sierra
con cursor a cero. OSC2 incluye su divisor de afinación y OSC3
su inversor Q37. Para OSC3 se fijó la tensión de salida de IC6,
antes del convertidor exponencial, en −4,940 o −4,955 V. La
posición de los registros y los trims de la unidad grabada
siguen sin identificarse. Se usaron las tarjetas nominales
del oráculo y un nivel de referencia de −3,895 V en las
mediciones aisladas.

El intento con los tres núcleos y el nodo común rechazó el
transitorio en ngspice. Los ensayos aislados que completaron
con Trap2 a 750 y 500 ns coincidieron en frecuencia y excursión
de carga. Se conservaron recibos y ventanas finales de los
intentos rechazados. [Rechazos](../evidence/vco_shared_neg4_coupled_rejection01.json).

Cada rama consume unos 4,615 µA de media. Aunque aparecen
pulsos breves, la integral de corriente alterna durante un
ciclo tiene sólo unos 7,3 pC de excursión por rama. Con
`G = 1/R166 + 1/R174`, el divisor atenúa cada armónico
según `Z(jω) = 1/(G + jω·C14)`. La integral permite acotar
también la excursión de la tensión de esas dos ramas
para cualquier fase relativa. Si `q` es la integral de
corriente de media cero, `v` es, salvo el signo, la
diferencia entre `q/C14` y su versión filtrada por el
polo del divisor. El pico a pico de `v` está acotado por
`2·pico_a_pico(q)/C14`.

Se repitió el transitorio del OSC1 cargado en 9B con la
componente DC de ambas corrientes y luego con sus primeros
24 armónicos, calculados sobre los tiempos adaptativos
del solver. C14, IC3/R49, R6/R45, C27 y la carga activa
del filtro permanecen en el circuito. La corriente medida
en OSC2/3 se aplica en una sola dirección. Su dependencia
dinámica del propio −4 V queda pendiente del cierre
simultáneo. Los valores resultantes son condicionales al
perfil, a los estados de panel y a esas frecuencias.

| Magnitud | La2 | La3 |
| --- | ---: | ---: |
| Frecuencias de las dos cargas | 239,4 / 302,7 Hz | 482,2 / 513,3 Hz |
| Tensión RMS alterna de la referencia, con ambas cargas | 15,0 µV | 19,9 µV |
| Tensión pico a pico de la referencia, con ambas cargas | 100,5 µV | 117,7 µV |
| Cota pico a pico de las dos corrientes aisladas por C14 | 242 µV | 242 µV |
| Excursión del retardo local de 9B | 1,32 ns | 2,04 ns |
| Desviación estándar de los períodos de C1 | 1,50 ns | 1,61 ns |
| Desplazamiento equivalente estimado en la toma vintage | 7,26 µs RMS | 4,29 µs RMS |

La carga continua de OSC2/3 baja el nodo cerca de 22 mV
y sube la frecuencia nominal de OSC1 unos 10 cents.
La variación de ciclo a ciclo queda muy por debajo de la
escala temporal asociada al residuo vintage en ambas notas.
La conclusión alcanza esta ruta de carga nominal. Los
rieles ideales, la tensión fija de IC6 y las tarjetas
nominales dejan abiertas otras vías de acople.

`python -B tools/check_vco_shared_neg4.py --write-report`
reproduce las doce corridas completas.
[Recibo de medidas](../evidence/vco_shared_neg401.json) ·
[Banco anterior de 9B](VCO1_FLANCO_9B_CARGADO.md).
