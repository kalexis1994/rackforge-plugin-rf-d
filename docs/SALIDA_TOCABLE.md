# C2, HI y LO en la voz de desarrollo

**Output Level** ajusta el cursor de R20. **Main Output** conecta
o desconecta HI y LO. **Output Jack** elige cuál de los dos se
envía al host como señal mono duplicada a estéreo. El cable
virtual **LO Feedback** toma LO en ambos modos de monitoreo.

## Red de salida

La [referencia del puerto](PUERTO_NATIVO_C2_SALIDAS.md) toma C2 de
10 µF y R75 de 1 kΩ de SVC-9 Fig. 9-11 p. 13. R20 de 5 kΩ, R57
de 33 kΩ, R58 de 1 kΩ y SW18 vienen de Fig. 9-17 p. 19. La voz
usa los jacks con carga alta y conserva una rama pasiva de 6 kΩ
para R77 más R21. La impedancia de salida del VCA y la carga
activa del amplificador de auriculares quedan en el modelo de
circuito.

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
selecciona HI o LO después del FIR y el lazo de feedback
recibe LO antes del FIR, con un subpaso de demora.

El recorrido del volumen y la conmutación se suavizan en
hasta 64 frames a 48 kHz. Durante la transición de SW18 se
interpolan la conductancia de los estados ON/OFF y la
conexión al jack. El recorrido lineal de R20, la compresión
nominal y la transición del contacto quedan para calibración.

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

La batería conserva las verificaciones de salida sin C2 en el
perfil `--feedback`. En la voz con C2, el release conserva una
cola de descarga medible tras el cierre del VCA. La validación
en RackForge usa captura sintética y directorio temporal.
Quedan pendientes la escucha y la prueba con dispositivo
físico. [Resultados](../evidence/rf_d_voice_development04.json).
