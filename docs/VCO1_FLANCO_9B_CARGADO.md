# Reinicio de C1 con el mixer conectado

La simulación usa el perfil CA3046 de la Fig. 9-3 de SVC-9.
Q5/Q6 disparan Q10, C1 vuelve hacia masa y Q3 lleva el
flanco a 9B. SW6 selecciona la sierra (contactos 3/10),
el cursor de R6 está a la mitad de su resistencia y R45
conecta la rama de OSC1 al bus. El solver resuelve el bus
junto con C27, Q29/Q30, el ladder y los dos VCA de placa
4. Las otras fuentes se representan desconectadas del
bus. El cutoff va al tope, con modulación y seguimiento
de filtro apagados y tensiones de contorno fijas. Los
rieles son ideales y se conserva R61 = 200 Ω. La carga de
la salida principal de placa 4 es de laboratorio.
[Red del panel](VCO1_CABLEADO_PANEL.md#cursor-de-r6-sw9-encendido-y-bus-del-mixer) ·
[Oráculo](VCO1_ORACULO_CIRCUITO.md) ·
[Tarjetas de dispositivos](../evidence/vco1_laboratory_devices.json).

Se conservaron los trims R8/R11 de la calibración
archivada. Se eligió el CV de placa de cada caso para
reproducir la fundamental medida del MP3. Esos CV son
fronteras eléctricas, fuera del alcance del ajuste original
en La2. Se midieron varios resets tras 15 ms, con Gear2
a paso máximo de 250 ns y Trap2 a 125 ns. El tiempo de
subida se mide entre los primeros cruces de 10 % y 90 %
del salto, con niveles tomados a ±1 µs del cruce de C1
por −2 V. En el primer intento se rechazó la hipótesis
de un único cruce del 90 %. El sobreimpulso y la caída
siguiente explican el segundo cruce.
[Cruces conservados](../evidence/vco1_loaded_reset_edge_crossing01.json).

| Magnitud | La2 | La3 |
| --- | ---: | ---: |
| Fundamental del circuito | 109,0734 Hz | 219,4957 Hz |
| Salto en 9B | 3,6950 V | 3,6947 V |
| Tiempo de subida 10–90 % | 196,159 ns | 196,132 ns |
| Q10 a punto medio de 9B | 182,29 ns | 182,28 ns |
| Salto en el bus | 20,59 mV | 20,59 mV |
| Dispersión pico a pico del retardo de 9B desde C1 = −3,8 V | 0,66 ns | 0,40 ns |
| Dispersión temporal estimada en el MP3, desviación estándar | 7,26 µs | 4,29 µs |

Q10 se marca al primer cruce de corriente de colector
por −1 mA. Cambiar método y paso desplaza el retardo
desde C1 = −3,8 V en menos de 0,19 ns, y la subida
10–90 % en menos de 0,001 ns en este banco. La similitud
entre solvers comprueba la resolución temporal del
modelo con sus tarjetas actuales.

Se aplicaron dos offsets constantes, ±1 mV en serie con
la base de Q5, conservando la corriente de su rama.
El retardo desde C1 = −3,8 V cambia 2,70 µs/mV en La2 y
1,34 µs/mV en La3. La extrapolación lineal de esa derivada
pone la escala del desplazamiento vintage en 2,69 y
3,20 mV equivalentes en Q5. Una tensión constante
desplaza el disparo y cambia el período. La prueba de
sensibilidad no identifica una fluctuación real de Q5.

Para comparar el orden de magnitud con el MP3 se calculó
el espectro de la diferencia entre un ciclo resuelto y
el mismo ciclo desplazado un tiempo fijo. Para cada
armónico de frecuencia `f`, la potencia de la diferencia
es la potencia nominal multiplicada por
`4·sin²(π·f·Δt)`. Se usó como Δt la desviación estándar
estimada en la grabación. La potencia de 8–12 kHz se
expresa respecto de la potencia AC total de cada nodo.

| Diferencia o residuo de 8–12 kHz | La2 | La3 |
| --- | ---: | ---: |
| Ciclo desplazado en 9B | −32,61 dB | −34,19 dB |
| Ciclo desplazado a la salida principal de placa 4 | −33,22 dB | −34,86 dB |
| Residuo de la toma vintage | −31,42 dB | −34,82 dB |

La diferencia a la salida de la placa 4 queda a 1,8 dB
del residuo en La2 y a 0,04 dB en La3 bajo este contraste.
La magnitud del desplazamiento se tomó del MP3. El cálculo
compara escalas de potencia y no estima qué produciría
esa fluctuación, cuánto aparece en una unidad real ni su
espectro de ciclo a ciclo. Tampoco identifica el
recorrido de captura del MP3.

`python -B tools/check_vco1_loaded_reset_edge.py --write-report`
ejecuta las ocho corridas de ngspice, mide los nodos y
publica los resultados por ciclo con los hashes de origen.
[Mediciones](../evidence/vco1_loaded_reset_edge01.json).

## Carga de la referencia compartida de −4 V

Con las mismas condiciones se repitió Gear2 con ±1 µA
en el puerto de carga de la referencia que comparten los
osciladores. R166/R174, C14 y las ramas resueltas de OSC1
conservan su conexión. La tensión se lee 100 µs antes
del reset. [Red de referencia](REFERENCIA_MENOS4V.md).

| Magnitud | La2 | La3 |
| --- | ---: | ---: |
| Variación de la referencia por µA adicional | −2,389 mV | −2,389 mV |
| Variación del retardo de 9B por µA adicional | −0,209 µs | −0,104 µs |
| Corriente equivalente para la dispersión temporal vintage | 34,7 µA | 41,2 µA |
| Cambio de referencia equivalente | 82,9 mV | 98,4 mV |

Los dos últimos renglones extrapolan la derivada local
medida con ±1 µA. Establecen una escala para contrastar
las corrientes de las otras ramas, cuya variación real
todavía no se midió. C14 hace que la impedancia dependa
de frecuencia. La excitación continua de este banco
no predice la respuesta a una corriente variable.

`python -B tools/check_vco1_loaded_reset_neg4.py --write-report`
repite las cuatro corridas a partir del banco nominal.
[Mediciones de la referencia compartida](../evidence/vco1_loaded_reset_neg401.json).
