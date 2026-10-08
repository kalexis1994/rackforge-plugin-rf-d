# Almacenamiento serial de la campaña de incrementos

Fecha: 2026-10-08. Complementa el protocolo eléctrico congelado; no modifica sus gates.

El intento 01 quedó sin procesos por falta de espacio para seis archivos crudos simultáneos. El intento 02 ejecuta una escena cada vez. Antes de cada escena exige su estimación de archivo crudo más 2 GiB libres. Las estimaciones no son cotas: durante la ejecución se comprueba la reserva y, si se cruza, se detiene el proceso y se conserva el prefijo como rechazo de recursos.

Después de medir una escena completa se comprime con gzip, se descomprime por streaming y se verifica el SHA-256 de todos los bytes originales. Sólo entonces se elimina ese archivo crudo exitoso, comprobando su ruta dentro del directorio de este intento. Se conservan el archivo comprimido, el hash original, el tamaño original y la medición. Los prefijos de procesos fallidos se conservan y el comando se repite sin cambios antes de cualquier reparación. La repetición tiene la misma reserva y monitor de recursos.

También se comprueban todos los intervalos desde la primera fila, la normalización hi/lo y el transporte del incremento. Las métricas de frecuencia, dispersión, carga y refinamiento mantienen el protocolo original.
