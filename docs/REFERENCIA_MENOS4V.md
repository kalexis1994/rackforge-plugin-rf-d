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

## Rizado de 100 Hz en el riel de −10 V

El manual SVC-204D describe el puente CR1–CR4 y los
condensadores de filtrado de la placa 5. En la placa 3, el
regulador de −10 V sigue al de +10 V y ambos realimentan
desde la placa de osciladores. Una red de 50 Hz puede
producir 100 Hz tras el puente. El ajuste de servicio mide
la continua en los pines de la placa de osciladores. Las
secciones consultadas no cuantifican el rizado residual.
[SVC-204D, §2.7, §5.6 y Fig. 9-13](FUENTES.md).

Se aplicaron 2 y 8 mV pico a 100 Hz al riel de −10 V del
banco cargado. El control conserva la misma polarización
y el mismo paso máximo, con amplitud cero. Se mantienen
C14, la carga continua de OSC2/3, el mixer y la entrada
activa de la placa 4. Los otros rieles y las tensiones
de control siguen ideales. Una prueba aplica los 8 mV
sólo a R166 para medir la vía del divisor.

Por ciclo se toma el tiempo del punto medio de 9B
respecto al mismo ciclo en el control. Se extrae la
componente a 100 Hz con un ajuste que admite offset
y deriva lineal. También se mide el retardo local
entre la rampa al bajar de −3,8 V y el punto medio
de 9B. Hay 11 flancos en La2 y 22 en La3.

| Respuesta a 100 Hz | La2 | La3 |
| --- | ---: | ---: |
| Riel completo, desplazamiento del flanco | 3,484 µs/mV | 4,781 µs/mV |
| Riel completo, variación del retardo local | 2,015 µs/mV | 1,007 µs/mV |
| Sólo R166, desplazamiento del flanco | 0,178 µs/mV | 0,159 µs/mV |
| Tensión en −4 V por mV aplicado al riel completo | 0,381 mV | 0,381 mV |
| Tensión en −4 V por mV aplicado sólo a R166 | 0,379 mV | 0,379 mV |
| Componente equivalente de 100 Hz en el tiempo del flanco vintage | 0,86–2,35 µs pico | 5,27–6,60 µs pico |

Las dos amplitudes del riel completo dan ganancias que
difieren menos de 0,1 %. Al reducir el paso máximo de
500 a 250 ns y la tolerancia relativa de 10⁻⁵ a 5·10⁻⁶,
las ganancias a 8 mV cambian menos de 0,01 %. Sin
estímulo, el mayor piso a 100 Hz es de 2 ns pico. Gear
con la tolerancia original rechazó el transitorio.
También se archivó el rechazo de la medición de Q10
con Trap, donde el umbral de corriente tuvo múltiples
cruces. La medida de 9B exige un solo cruce en su
propia ventana y conserva el mismo circuito.

Para alcanzar la escala de La3, el riel completo
requeriría **1,10–1,38 mV pico**. Por R166 solo, la
extrapolación a partir de 8 mV da 33–42 mV pico.
La amplitud en −4 V es casi la misma en ambos ensayos,
pero la respuesta temporal completa es unas 30 veces
mayor en La3. Hay otras conexiones al riel que pueden
dominar el efecto.

Un mismo rizado de 1,10–1,38 mV predice 3,84–4,81 µs
pico en La2. Esa nota no sostuvo el ajuste de 100 Hz
entre bandas y mitades de la toma. La discrepancia
limita la hipótesis de un único rizado estable de −10 V
para ambas notas. El rizado real del instrumento, su
correlación con +10 V y la ruta de captura permanecen
sin medir. El cálculo compara tiempos en 9B con
estimaciones de la salida grabada.

`python -B tools/check_vco_neg10_ripple.py --write-report`
reproduce las doce corridas.
[Medidas](../evidence/vco_neg10_ripple01.json) ·
[Rechazos y replays](../evidence/vco_neg10_ripple_rejections01.json) ·
[Contraste vintage](PATCHES_REFERENCIA_MODEL_D.md#componente-periódica-en-el-tiempo-del-flanco).

### Contraste directo a 1,25 mV pico y vía de R37

La Fig. 9-3 une −10 V a R37 (11,8 kΩ), en serie
con la sección activa del ajuste de frecuencia R11
hacia el sumador de IC1. Se repitió a 1,25 mV pico
con el riel completo y con la senoide aplicada
sólo en el extremo de alimentación de R37.

| Desplazamiento de 9B a 100 Hz | La2 | La3 |
| --- | ---: | ---: |
| Riel completo | 4,36 µs pico | 5,98 µs pico |
| Sólo R37 | 5,70 µs pico | 5,70 µs pico |

El ensayo directo concuerda con la extrapolación del
riel completo dentro de 0,09 %. En La3, R37 reproduce
el 95 % de la amplitud con una diferencia de fase de
2,5°. En La2, su amplitud supera la del riel completo.
La suma de las demás conexiones modifica la respuesta
y se opone en parte a la de R37 en La2. El ensayo
refuerza la vía de afinación como mecanismo eléctrico
para La3 y conserva la discrepancia con La2. El
estímulo pertenece al banco de medición.

`python -B tools/check_vco_neg10_r37.py --write-report`
repite las seis corridas.
[Medidas a 1,25 mV](../evidence/vco_neg10_r37_01.json).

## Rizado conjunto de +10 V y −10 V

Se aplicaron 1,25 mV pico a 100 Hz a +10 V solo y
a ambos rieles con 0°, 90° y 180° de diferencia de
fase. C14, la carga continua de OSC2/3, el mixer y
la placa 4 siguen conectados. Las fuentes del banco
fijan las tensiones de CV y −5 V. El regulador y
la retención de teclado quedan fuera de este banco.

| Desplazamiento de 9B, pico | La2 | La3 |
| --- | ---: | ---: |
| +10 V solo | 4,40 ns | 0,81 ns |
| −10 V solo | 4,36 µs | 5,98 µs |
| Ambos, en fase | 4,36 µs | 5,98 µs |
| Ambos, en cuadratura | 4,36 µs | 5,98 µs |
| Ambos, en oposición | 4,36 µs | 5,98 µs |

La suma vectorial de los ensayos por riel predice
los desplazamientos combinados con un error máximo
de 44 ns. En oposición, repetir a 250 ns en vez de
500 ns y reducir la tolerancia relativa a la mitad
cambia el fasor menos de 0,24 ns. El primer intento
completó los solves y se detuvo al serializar un
booleano de NumPy. Se repitieron las catorce corridas
con el mismo circuito y las mismas comprobaciones.

Si la amplitud de ambos rieles es igual, las ganancias
medidas acotan la relación La2/La3 a **0,728–0,729**
para cualquier fase. Los dos estimadores por flanco
de la toma dieron 0,164 y 0,356. En el modelo lineal
local, bajar hasta 0,356 requeriría un +10 V con al
menos 514 veces la amplitud de −10 V y fase ajustada.
Esa relación extrapola las ganancias de pequeña señal
y queda fuera de los ensayos de cancelación. El
contraste reduce la plausibilidad del rizado común
por los pines de alimentación del VCO bajo CV fijo.
Las entradas de CV y la cadena de salida siguen
siendo vías posibles.

`python -B tools/check_vco_dual_rail_ripple.py --write-report`
repite las catorce corridas.
[Medidas de los dos rieles](../evidence/vco_dual_rail_ripple01.json) ·
[Bandas laterales de la toma](PATCHES_REFERENCIA_MODEL_D.md#bandas-laterales-de-100-y-120-hz).

El [ensayo del CV de teclado](CV_TECLADO_RIZADO.md)
mide el acople por C6/Q13/Q10 y lo combina con la
sensibilidad de los pines de alimentación.
