# Realimentación LO en la voz de desarrollo

**LO Feedback** conecta una salida de nivel bajo virtual al jack
de entrada externa. **External On** conecta esa rama al bus.
**External Level** ajusta cuánto retorna y **Output Level** cambia
la señal enviada a la salida y al lazo. **Loop Drive** deja la
conexión activa. Al abrir el cable virtual, el jack vuelve a
recibir la captura de RackForge.

## Ruta de señal

La conexión reproduce un cable de J5 LO a J6 EXT. En la
[red clásica HI/LO](SALIDAS_PANEL_HI_LO.md), SVC-9 Fig. 9-17 p. 19,
el cursor de R20 alimenta HI, R57 conecta HI con LO y R58
lleva LO a masa. La reducción usa 33 kΩ y 1 kΩ para un cociente
LO/HI de 1/34 con carga alta. El manual MOOG-2022 p. 27 documenta
la conexión interna de la reedición como referencia de uso.
[Registro de fuentes](FUENTES.md).

La señal del VCA se toma antes del antialias de salida, con
1 V nominal por unidad de escala y un límite de ±1 V en HI.
Se multiplica por el mismo Output Level suavizado que escucha el
usuario. LO entra al [preamplificador externo](ENTRADA_EXTERNA_TOCABLE.md)
en el siguiente subpaso de 96 kHz, con una demora de 10,42 µs.
Con el cable conectado, la toma sustituye la captura del host.
Al cambiar la conexión, ambas fuentes se interpolan en hasta
64 frames a 48 kHz. El nivel del preamp, sus dos acoplamientos
RC, el indicador de sobrecarga y la carga de R46 comparten la
ruta de la entrada externa. El lazo está después del VCA y
responde al cierre del contorno al soltar la nota.

La escala en voltios, el límite en HI y el cable interno son
decisiones nominales. La etapa de salida, la carga real de
J5/J6 y su calibración quedan para contraste con el circuito.

## Verificación sin empaquetar

`python -B tools/check_rf_d_playable_voice.py --feedback` comprueba una
nota con el cable abierto, con External Level al 25 % y al
100 %. En esa escena, el RMS pasó de 0,0672 a 0,1068 y a
0,8011, con pico de 0,9095 en el caso de mayor realimentación.
El preamp marcó sobrecarga y la salida regresó a cero en el
release. El ensayo permuta la atenuación entre Output Level
y External Level para comprobar el producto de ganancia,
contrasta External On apagado y verifica la sustitución de
captura al conectar el cable. Los cambios de cable y nivel
reproducen por bits en particiones de 127, 128, 480 y 4096.

El banco de RackForge compara **External Filter** y **Loop Drive**
con WASM directo a 128, 480 y 4096 frames. Loop Drive usa el
mismo resultado con el canal de captura presente o ausente.
El máximo observado para Loop Drive a 128 frames fue 0,237 ms,
con cero pérdidas de plazo en los dos escenarios de captura.
La escucha y la prueba con dispositivo físico quedan pendientes.
[Resultados](../evidence/rf_d_voice_development03.json).

La [etapa de salida de desarrollo](SALIDA_TOCABLE.md) toma el
retorno LO desde el puerto C2/R20 e incorpora Main Output.
