# RF-D Voice 0.4.0

Importá `artifacts/rf-d-voice-0.4.0.rfplugin` desde Plugins y elegí **RF-D Voice**
en PLAY. La entrada es MIDI 36–72 a 48 kHz, con salida estéreo duplicada y
callbacks de 1 a 4096 frames. El preset **Model D Saw** abre una sierra con
ambos contornos. El paquete usa su propia identidad de plugin y de estado.

## Voz y controles

- La sierra viene de H128, escenario de CV −1,6 V y BUS nominal. Usa la
  misma tabla interpolada de 4096 puntos, afinación MIDI A4 = 440 Hz y
  antialias del piloto de 96 kHz, con 48 frames de latencia a 48 kHz.
  Saw Level aplica 0–100 % antes del filtro sobre una entrada de ±80 mV.
- La nota más baja tiene prioridad. El primer Note On y la liberación de
  la última tecla conmutan el mismo gatillo para ambos contornos. Un
  cambio de nota con teclas sostenidas conserva ambas cargas. Si se suelta
  y vuelve a tocar desde el estado sin teclas, el ataque comienza desde
  la carga remanente. Se conserva el orden de eventos del mismo frame.
- Cada contorno tiene ataque, decay y sustain. La carga normalizada
  se acerca exponencialmente a 1,05 en ataque y cambia a decay al llegar
  a 1. El tiempo nominal de ataque desde 0 es 1–2000 ms. Decay reduce
  al 1 % la diferencia inicial con el sustain en 5–5000 ms. Con **Release
  Uses Decay** activado, cada contorno usa su tiempo de decay al soltar
  la última nota. Con el switch apagado usa una descarga rápida de 5 ms
  al 1 %. Por debajo de 0,001 % de carga termina la descarga.
- **Cutoff** define la posición base del filtro. **Contour Amount**
  aplica el contorno de filtro sobre el recorrido restante hacia
  apertura total. El contorno de volumen controla la ganancia después
  del ladder y antes del FIR. Output Level aplica 0–100 % a la salida,
  con una transición de hasta 64 frames para el recorrido completo.

## Modelo nominal

La revisión de referencia es la [CA3046 documental](OBJETIVO.md).
El [solver de ambos contornos](VOZ_DOS_CONTORNOS_RESULTADOS.md) sigue
siendo la referencia de las cargas, los retornos R59/R60 y el gatillo
compartido. Los tiempos, la asíntota de ataque y la ganancia de volumen
de la voz tocable son hipótesis funcionales. Las redes C2/C5 y la
conmutación eléctrica del biestable siguen en el solver.

El filtro usa cuatro pares diferenciales ideales con un capacitor de
68 nF por etapa y Vt = 25,693 mV a temperatura nominal. El
[manual de servicio SVC-9, Fig. 9-11 y tabla 7-8](LADDER_PEQUENA_SENAL.md)
documenta C16, C11, C7 y C3. Para tensión diferencial normalizada por
2·Vt, cada etapa integra la diferencia de dos corrientes tanh con un
paso Euler a 96 kHz. El coeficiente es Icola/(4·Vt·C·96000), entre
0,000362 y 0,2153. El control interpola logarítmicamente entre los
[tres puntos DC del oráculo de cutoff](VOZ_APERTURA_CUTOFF_RESULTADOS.md)
de 0,2431, 6,8249 y 144,4219 µA. La hipótesis cubre el recorrido 0–100 %
del control. El acople con el mixer y VCA reales, la resonancia, la
dispersión de componentes y el ajuste del recorrido quedan pendientes.
La [frontera pasiva C1/C5 y R31/R38](FRONTERA_RECUPERACION_FILTRO.md)
aporta un acoplamiento de 0,22 µF y 47 kΩ, con polo de 15,39 Hz antes
del VCA. El paso conserva el estado de carga equivalente y elimina DC.
La carga activa de Q6/Q8 queda en la referencia.

El primer ensayo conectó ambos contornos a la planta FOH de 0.3.2 dentro
del margen del pin 16 de ±1 mV. En MIDI 57 a 48 kHz, con Amount a cero,
la energía por encima de 2 kHz pasó de 9,7743·10⁻¹⁰ a 9,7705·10⁻¹⁰
del total al abrir el control de extremo a extremo. Falló la prueba de
apertura. Ese margen sirve para el banco de retornos. La voz 0.4.0 usa
el ladder nominal de recorrido amplio y ganancia de volumen normalizada.

## Verificación

`python -B tools/check_rf_d_playable_voice.py --single-saw` regenera e instala el
paquete en un store temporal de prueba. El [recibo](../evidence/rf_d_playable_voice01.json)
incluye audio determinista entre tamaños de bloque, apertura del filtro,
ataque y sustain, switch de release, legato, redisparo y automatización.
La prueba ABI comprueba el estado de los once parámetros y el preset.
RackForge procesa una nota sostenida en 100 bloques por tamaño. La
medición de RackForge es offline. Quedan pendientes la escucha y
la prueba de callbacks con dispositivo físico.

El [banco tocable de 0.5.0](BANCO_OSCILADORES_TOCABLE.md) agrega OSC2 y
OSC3 con rangos, formas de onda, afinación y mezclador.
