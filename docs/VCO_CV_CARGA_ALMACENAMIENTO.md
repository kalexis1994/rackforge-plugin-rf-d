# Ventanas exactas sin overhead de JSON

Antes de admitir las ventanas, la primera escena baja conserva 111316
filas ×17 float64 =15138976 bytes. Gzip genérico intercalado más base64
supera el presupuesto conjunto de 32 MiB de la campaña. No reducir
muestras, precisión, ventanas, métricas ni gates para resolverlo.

El primer ensayo usa XOR temporal y barajado como vco1_radau_trace.
Comparar después diferencias enteras de primer/segundo orden: la selección
de segundo orden reduce el primer caso a 3623368 bytes, con restauración
idéntica. Son diferencias de las palabras uint64 módulo 2^64 por columna,
no diferencias aritméticas float64 ni cuantización de señal. Invertir con
dos sumas acumuladas modulares. Barajar bytes y comprimir XZ sin pérdida.
Guardar todas las ventanas como streams XZ concatenados en un único
evidence/vco_cv_load_windows01.xz, con offsets/longitudes/digests. Así se
evita el overhead base64 del payload binario. No se crean carpetas de
muestras. Son observaciones sintetizadas del modelo, no un documento
original, grabación externa o export del macromodelo del fabricante.

Antes de reemplazar la representación del recibo aún no admitido, probar
cada float64 por bytes y reconstruir el JSON original completo por bytes,
incluido su empaquetado gzip previo. Conservar ambos hashes/tamaños y
fuentes del codec. No retirar ninguna muestra de las ventanas ni entrada
admitida; sólo cambia representación. No volver a integrar para verificar
esta serialización. El prefijo transitorio retirado conserva el alcance
limitado del protocolo original. Todo el pack entra al presupuesto de
recibos, con regla -text y validación de blobs Git después del commit.

Registrar Python, NumPy y zlib del banco: reconstruir exactamente el gzip
previo exige su representación, además del contenido. La restauración del
JSON original por bytes es una comprobación en ese entorno; la identidad
de cada ventana float64 se valida separadamente por longitud y SHA256.
No atribuir portabilidad del compresor anterior a la identidad física de
las muestras decodificadas.
