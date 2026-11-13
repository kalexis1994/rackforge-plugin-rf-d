# Rizado de 100 Hz en el CV del teclado

## Circuito y medición

SVC-204D §2.19 (PDF p. 16) y el esquema de placa 2
(SVC-204D PDF p. 65, SVC-9 PDF p. 9, Fig. 9-7)
muestran esta ruta:

- Q9/Q11 y R1/R20/R22/R25 fijan la corriente de la
  escalera de 43 resistencias de 10 Ω. El contacto de
  pitch lleva la toma a Q23 y C9 (0,33 µF).
- Q23, Q14 y Q24 cierran el lazo sobre el CV de salida
  a través de R30. Con glide apagado, Q24 carga C6
  (1 µF) por R61 y Q13. El contacto de trigger abre
  antes que el de pitch. CR5, R34, R64 y R65 llevan
  Q13 a corte, dejando C6 retenido.
- Q10 conserva conexión a +10 V por R2 y a −10 V
  por R18. La compuerta toma el voltaje de C6 por R21.
  Su fuente entrega el CV por el pin 4 de placa 2.
  R27 (51,1 kΩ) lo lleva al sumador de IC1 en OSC1.

La prueba usa las tomas a 4, 16, 28 y 40 pasos de masa.
Son las posiciones de la nota La en la escalera que
empieza en Fa. Se comparan pares a una octava para
abarcar la incertidumbre de registro de la grabación.
Se usan 1,25 mV pico a 100 Hz en +10 V, −10 V o en
serie con el contacto de pitch. También se aplican
a ambos rieles con polaridad opuesta. La entrada de
trigger toma +10 V del contacto de teclado.

La salida de placa 2 ve tres ramas de 51,1 kΩ a
−5 V como cargas de sumador, con OSC3 siguiendo el
teclado y seguimiento del filtro apagado. Se calcula
el fasor después de restar el control sin estímulo.
Las ventanas son 80–180 ms con tecla pulsada y
270–370 ms después de soltarla. La apertura dura
0,2 ms en el modelo de contacto, con 2 ms entre
trigger y pitch. Se eligió esa transición para evitar
el rechazo numérico al abrir un contacto abrupto.
La comparación de pasos máximos de 40 y 20 µs
se realiza fuera de esas transiciones.
[Rechazos del contacto abrupto](../evidence/keyboard_cv_ripple_rejections01.json).

Los BJT y CR5 usan tarjetas de laboratorio. Para Q10
y Q13, Siliconix da 4–10 mA para `IDSS` y hasta 6 V
en magnitud para `VGS(off)`. Se probaron dos tarjetas
NJF condicionadas con `VTO` de −3,5 y −5,5 V y
`IDSS` nominal de 7 y 4 mA. La capacitancia de unión
se calcula a partir de Ciss/Crss de esa hoja con
`PB = 1 V` supuesto. Son perfiles de sensibilidad,
sin pretensión de cubrir toda la dispersión de
fuga, capacitancia o polarización de las unidades.
[Siliconix FET Data Book, p. impresa 3-26](https://www.bitsavers.org/components/siliconix/_dataBooks/1977_Siliconix_FET_Data_Book.pdf).

## Qué llega al VCO

| Estímulo de 1,25 mV pico | CV con tecla pulsada | CV después de soltarla |
| --- | ---: | ---: |
| En serie con el contacto de pitch | 1,247–1,253 mV | ≤0,0252 µV |
| Sólo +10 V | 44,5–423,2 µV | 9,1–84,5 µV |
| Sólo −10 V | 4,6–5,8 µV | 100,7–208,2 µV |
| +10 V y −10 V en oposición | 50,0–427,6 µV | 89,7–191,4 µV |

En retención, Q13 queda en corte en los casos
ensayados. Para ambos rieles en oposición, C6
recibe como máximo 1,24 µV pico a 100 Hz. Q10
y R18 mantienen un camino desde los rieles al CV
de salida aunque la tensión almacenada apenas se
mueva. El estímulo aplicado al propio contacto
queda atenuado al menos 93 dB al abrirlo.

Se reprodujeron fasores medidos en la placa 2
sobre el CV de continua del banco de OSC1 y se
midió la corriente de R27. Es un acople en una
dirección. El punto DC del teclado se usa para
resolver el track-and-hold y el punto DC de cada
nota del banco se conserva para medir 9B. C14,
la carga de mixer y la entrada de placa 4 siguen
en circuito. La calibración de 4 mV da una ganancia
de **1,10 µs/mV** a 100 Hz en ambas notas. Al
reproducir el par de tomas 16/28 en oposición,
el error respecto a esa ganancia queda por debajo
de 1 ns.

| Respuesta del VCO, tomas 16/28 | La2 | La3 |
| --- | ---: | ---: |
| CV de tecla pulsada, pico | 176,3 µV | 302,2 µV |
| Corriente de R27, pico | 3,45 nA | 5,91 nA |
| Desplazamiento de 9B, pico | 0,194 µs | 0,332 µs |
| CV en retención, pico | 98,6 µV | 93,8 µV |
| Desplazamiento de 9B en retención, pico | 0,109 µs | 0,103 µs |

## Contraste con La2 y La3

El ajuste continuo de la toma vintage sitúa la
componente de La3 entre **4,91 y 5,26 µs pico**.
Para alcanzar esa escala sólo por esta entrada,
el banco necesita **4,47–4,78 mV pico de CV**.
Con rizado de 1,25 mV en los rieles, el par
16/28 queda más de un orden de magnitud por
debajo. La relación de La2 a La3 para el CV solo
depende de qué teclas se usaron. El par más bajo
da cerca de 0,28 con la tecla pulsada, pero
produce menos de 0,20 µs pico en La3.

La suma de los fasores del CV y de los pines de
alimentación del VCO se aproxima linealmente.
Con rieles iguales y en oposición, predice que
La2 conserva **73–74 %** de la excursión de La3,
frente al **16–36 %** de las estimaciones por flanco.
La desigualdad triangular sobre los fasores de cada
riel acota el cociente a **62–85 %** para cualquier
fase si ambos rieles tienen igual amplitud. La suma
lineal de las dos rutas de placa 2 reproduce el caso
en oposición con menos de 0,03 ns de error proyectado
en 9B. El ensayo acota el rizado común que entra por
esta ruta nominal de teclado. Quedan fuera la
dinámica del regulador, el acople de las cargas
activas de OSC2/3 y las condiciones exactas de
la unidad grabada. El estímulo es determinista
y se aplica en el banco de circuito.

`python -B tools/check_keyboard_cv_ripple.py --write-report`
repite 60 corridas de placa 2. `python -B tools/check_keyboard_cv_vco_ripple.py --write-report`
repite ocho corridas del VCO.
[Medidas de placa 2](../evidence/keyboard_cv_ripple01.json) ·
[Medidas y comparación del VCO](../evidence/keyboard_cv_vco_ripple01.json) ·
[Análisis vintage](PATCHES_REFERENCIA_MODEL_D.md#bandas-laterales-de-100-y-120-hz).
