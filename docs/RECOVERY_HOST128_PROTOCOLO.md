# Período efectivo de 128 frames a 48 kHz

2026-11-07. Base RF-D 3ef1c67. Consultar el formato de mezcla y los
períodos de WASAPI compartido por salida y modo. Para 128 frames,
el período debe pertenecer al rango y ser múltiplo del fundamental.
Solicitarlo por IAudioClient3 y comprobar el período devuelto y el
espacio efectivo de escritura en cada evento. Conservar los rechazos.

Orden de salidas físicas para la campaña: monitor LS27AG55x, Realtek
Digital Output, PRO X 2 LIGHTSPEED. Usar la primera que confirme una
apertura de 128 a 48 kHz, con preferencia por el modo estándar.
Steam puede documentar una ruta virtual por separado.

El SDK distingue la tarea MMCSS Pro Audio de las categorías WASAPI.
El primer enlace del probe rechazó el nombre de categoría incorrecto.
La exploración usa AudioCategory_Other en los modos estándar y RAW.

En una ruta admisible, preroll silencioso y arranque del DSP en el
primer evento medido. Incluir en el tiempo de pared la consulta de
padding, la adquisición del buffer, el DSP y la entrega. La preparación
del hilo y el preroll se registran fuera de esa sección. Guardar por
fila los frames ofrecidos y el padding. Una fila de cero frames cuenta
como evento sin trabajo y una de más de 128 revela coalescencia. Ninguna
de ellas satisface el gate de tamaño exacto.

Mantener el núcleo exponencial y el FIR original con las reservas
previas, 48 frames de arranque y cero asignaciones Rust en el DSP.
Secuencia de 1200 eventos de control en silencio, 1200 con DSP y 4800
con DSP. Conservar desde el primer evento. Comparar contra 2.667 ms
con objetivo de 50 %, sin incumplimientos ni intervalos >1.5 plazos.
Repetir una vez el banco que falle. La primera medida conserva su
resultado. Los ciclos del hilo se guardan en sus unidades originales.

El banco mide el adaptador nativo de laboratorio y reutiliza la
política de hilo de RackForge. La aplicación y su motor de plugins
requieren su propia medición. Conservar el inventario de 8769 inputs,
usar sólo tmp/lab-current y retirar binarios al guardar los recibos.

[Consulta de períodos](https://learn.microsoft.com/en-us/windows/win32/api/audioclient/nf-audioclient-iaudioclient3-getsharedmodeengineperiod)
y [apertura por período](https://learn.microsoft.com/en-us/windows/win32/api/audioclient/nf-audioclient-iaudioclient3-initializesharedaudiostream).

## Consulta de modo exclusivo

Los cuatro endpoints compartidos devolvieron período mínimo y fundamental
de 480 frames en los dos intentos. Consultar el período mínimo exclusivo
y las sesiones activas de cada dispositivo. La consulta no abre un stream.
Una campaña exclusiva sólo puede usar una salida alternativa física
libre con mínimo compatible y con un búfer negociado de 128 frames.
[Período mínimo del dispositivo](https://learn.microsoft.com/en-us/windows/win32/api/audioclient/nf-audioclient-iaudioclient-getdeviceperiod).
