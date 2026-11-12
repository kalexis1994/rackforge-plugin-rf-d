# C2, HI, LO, auriculares y A‑440 en la voz de desarrollo

**Output Level** ajusta el cursor de R20. **Main Output** conecta
o desconecta HI y LO. **Headphones Level** ajusta R21. Con
**Main Output** apagado se puede seguir usando **Phones**.
**Output Jack** elige HI, LO o Phones para enviar al host
como señal mono duplicada a estéreo. El cable virtual
**LO Feedback** toma LO en las tres posiciones.

## Red de salida

La [referencia del puerto](PUERTO_NATIVO_C2_SALIDAS.md) toma C2 de
10 µF y R75 de 1 kΩ de SVC-9 Fig. 9-11 p. 13. R20 de 5 kΩ, R57
de 33 kΩ, R58 de 1 kΩ y SW18 vienen de Fig. 9-17 p. 19. La voz
usa los jacks con carga alta y conserva una rama pasiva de 6 kΩ
para R77 más R21. La impedancia de salida del VCA y la corriente
que C19 devuelve a C2 por R21 quedan en el modelo de circuito.

El VCA reducido impone la tensión a la izquierda de C2. El
estado de C2 es la diferencia de tensión entre sus terminales.
La carga de la salida principal en ON es R75 más el segmento
superior de R20 más el paralelo del segmento inferior con
R57 + R58. En OFF, el cursor va a masa y la rama queda en
R75 más el segmento superior. La tensión en ambos jacks es
cero en OFF. Los extremos eléctricos de R20 se calculan
con sus valores exactos. La carga total vista por C2 incluye
la rama pasiva de auriculares en paralelo.

C2 avanza con el paso exponencial del RC a 96 kHz. En el
extremo alto de R20, la escala del VCA se fija para que una
unidad de audio en banda media corresponda nominalmente
a 1 V en HI. La excursión de HI se comprime suavemente por
encima de 0,8 V. LO aplica el divisor 1/34 a la misma señal.
El FIR de salida conserva 48 frames de latencia. El host
selecciona la ruta de monitoreo después del FIR y el lazo de feedback
recibe LO antes del FIR, con un subpaso de demora.

El recorrido del volumen y la conmutación se suavizan en
hasta 64 frames a 48 kHz. Durante la transición de SW18 se
interpolan la conductancia de los estados ON/OFF y la
conexión al jack. El recorrido lineal de R20, la compresión
nominal y la transición del contacto quedan para calibración.

## Auriculares

SVC-9 Fig. 9-11 p. 13 y Fig. 9-17 p. 19 sitúan R77 de 1 kΩ
y R21 de 5 kΩ entre C2 y el pin 7 de placa 3. SVC-9 Fig. 9-8
p. 10 da C19 de 2,5 µF, C21 de 400 µF y R56 de 390 Ω a masa
en J7. Para una posición eléctrica `p` de R21 el cursor tiene
una relación en vacío `5000 p / 6000` y una resistencia de
Thévenin `(5000 p) ∥ (6000 − 5000 p)`.

El [oráculo AC de placa 3](AC_AMP_AURICULARES.md) fija el
modelo a 1 kHz en el punto de reposo nominal condicionado.
Si `B = V_base_Q16/V_pin7`, la resistencia reducida de entrada
es la parte real de `Z_C19 B/(1 − B)` con dos cargas de 32 Ω.
Resultan 4802,81 Ω, que incluyen R50, R53 y la entrada de Q16.
Para el equivalente de salida se usan dos soluciones del oráculo,
con R56 sola y con R56 en paralelo con las dos cargas. Cada
solución da `V_preC21/V_base_Q16 = G Z/(Z + R_out)` con
`Z = R_carga + Z_C21`. Las partes reales de la solución dan
`G = 0,98929334 V/V` y `R_out = 210,47218 Ω`.

C19 ve la suma de la resistencia del cursor y la entrada
reducida. C21 ve la suma de la resistencia de salida y la
carga de J7 de 15,369 Ω. El corte reducido de C21 es de
1,762 Hz con esa carga. El equivalente incluye la impedancia
activa que faltaba en el [cálculo pasivo de C21](ACOPLAMIENTO_SALIDA_AURICULARES.md).
Los dos estados RC avanzan por exponencial a 96 kHz. Phones
usa los mismos coeficientes FIR y los mismos 48 frames de
latencia que HI/LO. El selector funde los taps durante 64 frames.

La curva del cursor es lineal y arranca al 50 % en RF-D. El
equivalente corresponde a pequeña señal y a la carga indicada.
Quedan por identificar la curva de R21, la carga de auriculares
reales y la respuesta del amplificador en señal grande.

## A‑440

SVC-9 Fig. 9-11 p. 13 muestra el oscilador de referencia
Q22/Q9/Q4. R40 de 2,2 kΩ y C8 de 0,1 µF conectan su salida
al colector de Q14 y a la base de Q12, después del par del
segundo VCA y antes de C2. OP-EARLY PDF pp. 8 y 31 documenta
el tono de afinación y el ajuste a 440 Hz. MOOG-2022 PDF p. 33
corrobora el envío a Main y Phones como referencia de interfaz.
[Fuentes](FUENTES.md).

RF-D suma un seno de 440 Hz en la salida reducida del VCA,
antes de C2. Su pico de 0,1 en la escala del VCA es nominal y
da aproximadamente −20 dBFS en HI con R20 al máximo. Arranca
apagado, su transición usa hasta 64 frames y la fase vuelve a
cero al apagarlo. El tono sigue las cargas y volúmenes de las
salidas y se puede usar sin nota MIDI. La forma de onda, el
nivel y el arranque del oscilador de placa quedan para contraste.

## Verificación sin empaquetar

`python -B tools/check_rf_d_playable_voice.py` contrasta el nivel
a mitad de R20 con un solve nodal separado, el divisor HI/LO,
la descarga de C2 después del cierre del VCA, el mute y la
reconexión con feedback activo. Se comprueba la invariancia
al cambiar de partición de 127 a 4096 frames.

El cociente LO/HI medido fue 0,0294117647, equivalente a −30,63 dB.
A mitad de R20 se midió una relación de 0,49120390 frente a
0,49120405 del solve nodal. La cola de C2 cayó a 0,17095624 de
su nivel en 50 ms, según la constante de tiempo de 28,307 ms.
El slot de RackForge reprodujo por bits la salida directa de
Loop Drive a 128, 480 y 4096 frames. A 128 frames el máximo
offline del preset fue 0,181 ms, sin pérdidas de plazo.

La batería mide 440 Hz en las tres rutas con la voz cerrada,
comprueba independencia de los volúmenes y compara Phones/HI
con el oráculo AC a 40 y 440 Hz, en tres posiciones de R21.
El mayor error relativo de amplitud fue de 0,043 %.
Verifica la realimentación LO durante cambios de monitor y la
migración de estados antiguos. El slot de RackForge carga un
estado de Phones con Main Output apagado y A‑440 encendido.
Se compara por bits con el render directo a 128, 480 y 4096
frames. Los dos pases offline a 128 frames dieron máximos
de 0,207 y 0,215 ms frente al margen de 1,333 ms.
[Resultados](../evidence/rf_d_voice_development05.json).

`--main-output` reconstruye el perfil anterior de HI/LO.
`--feedback` reconstruye la salida anterior a C2. La prueba
en RackForge usa captura sintética y directorio temporal.
Quedan pendientes la escucha y la prueba con dispositivo físico.
[Resultados previos de HI/LO](../evidence/rf_d_voice_development04.json).
