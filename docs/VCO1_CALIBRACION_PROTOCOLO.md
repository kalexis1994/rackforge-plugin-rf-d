# VCO1: protocolo de calibración nominal por dos trims

Fuente de procedimiento: **B-TUNE**, tabla 5-3, pasos 3–5, hoja de fábrica
que reemplaza 5-5/5-6 para osciladores antiguos. Fue revisada visualmente;
sus objetivos son 1760 Hz en A alta y 220 Hz en A baja, repitiendo ajuste
de frecuencia y escala. El circuito identifica R11 como frecuencia y R8
como escala (SVC-204D §2.16). No hay una unidad física disponible.

Este corte usa CV de placa **-3.1 y -0.1 V**, separados por tres voltios,
con las otras cinco entradas a -2.1 V, rieles/mixer/carga compartida como
en el banco. Es un banco de calibración de laboratorio: no se atribuye
esa tensión absoluta al teclado original, ni se declara reproducido el
panel Fig. 5-5, la posición 4', el ajuste de octavas o una ley MIDI.

Se ajustan exclusivamente R11 activo dentro de 0–1000 ohm y fracción de
R8 dentro de 0–1, sin variar resistencias nominales, parámetros BJT/JFET,
umbrales, corriente impuesta, formas de onda o rieles. Inicio R11=550 ohm,
R8=0.31: semilla de búsqueda, nunca trim físico identificado.

El solve conjunto mide frecuencia desde reset real. Jacobiano inicial
por perturbaciones declaradas de 5 ohm y 0.01 de fracción, seguido por
actualizaciones secantes sobre ambos residuos logarítmicos. Rechazar
salida de pistas, ausencia de mejora o más de cinco actualizaciones.
Cada intento tiene recibo/export/log/deck independiente conservado.

Antes de medir: **<=0.1 cent** en ambos extremos; comprobar después cuatro
puntos con paso máximo **125 ns**, duración 30 ms y observación tras 15 ms.
Los puntos intermedios -2.1/-1.1 V se reservan y no entran al ajuste: metas
440/880 Hz con discrepancia **<=5 cents**, límite del laboratorio que no
se presenta como especificación de Moog. No forzar la recta con ajustes
por nota si esos puntos fallan. El error de interpolación del modelo se
informa separado de convergencia temporal y de incertidumbre física.

```powershell
python -B tools/vco1_circuit_calibration.py --bank calibration-v1
```

Las cuatro corridas son notas aisladas, no un cambio de nota dentro de
una trayectoria. Modulación dinámica, controles completos y equivalencia
portable permanecen pendientes. C4=10 pF es el perfil de este ajuste;
el banco anterior conserva el contraste separado de 100 pF.
