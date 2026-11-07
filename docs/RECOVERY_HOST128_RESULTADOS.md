# RF-D a 128 frames efectivos

2026-11-07. El banco ASIO4ALL v2 procesó el núcleo exponencial y el
FIR original a 48 kHz en los canales HD Audio output 1 y 2. El reloj
del controlador avanzó 128 muestras en cada transición entre callbacks
y el índice del doble búfer alternó. La medida corresponde al adaptador
nativo de laboratorio, con la biblioteca ASIO y la política de hilo de
RackForge. El motor de plugins de la aplicación queda por medir.

Dos consultas WASAPI dieron mínimo y fundamental compartido de 480
frames para las cuatro salidas estándar, y para las tres que aceptaron
RAW. El mínimo exclusivo informado fue 3 ms en las cuatro, equivalente
a 144 frames a 48 kHz. FL Studio ASIO anunció mínimo de 256 frames.
Los dos controladores Focusrite rechazaron ASIOInit. ASIO4ALL anunció
rango de 64 a 2048 con paso 8 y aceptó la consulta de 48 kHz.
[WASAPI compartido](https://learn.microsoft.com/en-us/windows/win32/api/audioclient/nf-audioclient-iaudioclient3-getsharedmodeengineperiod)
y [mínimo exclusivo](https://learn.microsoft.com/en-us/windows/win32/api/audioclient/nf-audioclient-iaudioclient-getdeviceperiod).

## Campañas de procesamiento

El plazo fue de 2.667 ms por callback y el margen objetivo de 1.333 ms.
El reloj incluyó el trabajo del núcleo, FIR, borrado de búferes, consulta
del reloj de muestras e instrumentación. La preparación del primer
callback se registró aparte y se incluyó en su gate. La salida enviada
fue silencio. El DSP reprodujo 1536 valores J7 y 464 frames FIR por bits
en las comprobaciones de referencia y partición.

| Banco | Llamadas | Mediana | P99 | Máximo | Plazos perdidos |
| --- | ---: | ---: | ---: | ---: | ---: |
| Control inicial largo | 1200 | 0.002 ms | 0.004 ms | 0.005 ms | 0 |
| DSP inicial corto | 1200 | 0.696 ms | 0.981 ms | 1.073 ms | 0 |
| DSP inicial largo | 4800 | 0.688 ms | 0.964 ms | 1.166 ms | 0 |
| Control de confirmación | 1200 | 0.001 ms | 0.003 ms | 0.004 ms | 0 |
| DSP de confirmación corto | 1200 | 0.678 ms | 0.979 ms | 1.130 ms | 0 |
| DSP de confirmación largo | 4800 | 0.685 ms | 0.842 ms | 1.205 ms | 0 |

La primera apertura corta de 32 llamadas registró un aviso de reset
del driver. El replay y los bancos principales no lo repitieron.
El resultado estricto de la primera campaña conserva ese rechazo.
La confirmación con restauración automática pasó su apertura corta y
los tres bancos principales sin avisos, intervalos largos ni pérdida
de plazo. El mayor intervalo entre inicios fue 1.011 períodos en su
banco de 4800.

## Preferencia del controlador

ASIO4ALL guardó 128 como tamaño preferido del perfil del ejecutable
de laboratorio. Se conservó el intento fallido de restauración por
creación y liberación de búferes. Se quitó el override de ese perfil y
se verificaron 512 frames preferidos y 44.1 kHz mediante otra carga
del controlador. El banco de confirmación guardó y restauró el valor
del perfil al salir y verificó la misma configuración.
[Documentación de perfiles ASIO4ALL](https://asio4all.org/about/developer-resources/user-registry-settings/).

[Protocolo](RECOVERY_HOST128_PROTOCOLO.md),
[consulta WASAPI](../evidence/recovery_host128_native04.json),
[consulta ASIO](../evidence/recovery_host128_native05.json),
[primera campaña](../evidence/recovery_host128_native08.json),
[restauración](../evidence/recovery_host128_native10.json),
[confirmación](../evidence/recovery_host128_native11.json) y
[auditoría](../evidence/recovery_host128_tests01.json).
