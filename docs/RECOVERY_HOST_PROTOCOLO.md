# Medición de colas en la salida de Windows

Base 12189ab, 2026-11-06. La observación previa de 4.800 ms sólo tiene tiempo
de pared. Este banco usa el núcleo exponencial y el FIR original a 384/48
kHz. La entrada de banco repite una tabla de un segundo de la excitación
de 137 y 1103 Hz, construida fuera de la devolución de audio.

El banco abre la salida WASAPI compartida con la biblioteca CPAL del
host RackForge y reutiliza su política de hilo, exención de throttling
y tratamiento de subnormales. Solicita 128 frames a 48 kHz. Registra los
frames efectivos y calcula el plazo por devolución como frames/48000.
También registra el mayor tiempo de un tramo DSP de 128 frames por
devolución. Este banco ejecuta el candidato nativo en la devolución de
CPAL. La aplicación RackForge y su motor de plugins quedan fuera de la
medida. La salida al dispositivo contiene silencio.

Secuencia fijada: calibración del contador con espera y trabajo
sintéticos de 4 ms, banco nativo sin reloj de audio de 4800 bloques de
128, control WASAPI de 1200 devoluciones silenciosas, WASAPI con DSP de
1200 devoluciones y confirmación de 4800 con DSP. Conservar cada banco,
desde el primer bloque. Repetir una vez cada banco que pierda un plazo
de procesamiento o falle el objetivo del 50 %. La primera medida
determina el resultado. Un salto entre devoluciones mayor que 1.5 veces
el plazo de la devolución actual se informa por separado, como hace
RackForge. Excluir la primera fila únicamente de esta diferencia.

Medir pared con Instant y ciclos del mismo hilo con QueryThreadCycleTime.
Comparar picos con la distribución de ciclos para el mismo número de
frames. Informar el tamaño de la muestra de comparación. Los ciclos
quedan en sus unidades nativas. Un pico de pared con ciclos habituales
apoya una explicación de espera o interferencia, sin identificar la
causa. Registrar cambios de hilo y procesador, errores de stream y
discontinuidades de tiempo, sin identificar silencios del dispositivo
sólo por ausencia de errores. La activación de la política de hilo se
mide aparte. Conservar instrumentación dentro del presupuesto de pared.

Validación numérica: comparar bits de J7 con el banco previo en las
primeras 1536 muestras internas. Repetir 512 frames de salida bajo
particiones diferentes y comparar toda la secuencia del FIR por bits.
Verificar 48 frames de arranque, consumo y cero asignaciones de Rust en
el tramo DSP. Guardar tablas binarias empaquetadas y resúmenes
recalculables, con hashes de fuentes, librerías, compiladores y binarios.
Un área temporal existente y hasta 4 MiB de recibos nuevos sin QA.
Conservar los bancos rechazados y los 8769 inputs del inventario anterior.

[Contador de ciclos de Windows](https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-querythreadcycletime)
y [WASAPI](https://learn.microsoft.com/en-us/windows/win32/coreaudio/wasapi).

## Selección de salida tras el primer intento

2026-11-07. La salida por defecto rechazó la apertura WASAPI con
AUDCLNT_E_DEVICE_IN_USE en el intento y el replay. Antes de medir otra
campaña, enumerar salidas, primero la predeterminada y después las
enumeradas por CPAL. Fijar la primera que complete 16 devoluciones con
la configuración solicitada. La prueba de apertura verifica el stream.
El coste de esas 16 filas no interviene en la selección. Conservar las
pruebas fallidas y usar el mismo dispositivo en los bancos WASAPI.
