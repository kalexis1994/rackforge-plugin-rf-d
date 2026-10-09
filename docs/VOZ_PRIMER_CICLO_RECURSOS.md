# Continuación ante fluctuación externa de disco

2026-10-08. La continuación01 se detuvo cooperativamente por disco, no
por límite temporal ni rechazo eléctrico: mínimo observado1040076800
bytes, por debajo de la reserva1073741824 bytes. Se conserva su recibo
fallido y todos sus archivos. Su reloj final1760362240 ticks =3,3576225 ms
incluye un reset y el replay de2,25 ms; el prefijo anterior conserva el
replay de0,25 ms. La integral C1 del segmento pasa, balance1,216e-15.

El espacio libre volvió sobre la reserva. Retomar desde `final.ckp`
de ese segmento en un directorio nuevo, con el mismo caller y biblioteca
verificados por SHA256; no volver a compilar ni integrar prefijos.
Presupuesto restante19758 intervalos del total48000, estimación12 MiB
de escrituras, reserva1 GiB y límite1800 s iguales a la enmienda anterior.
La vigilancia permanece activa; otra caída conserva otra pausa y estado.
Las estimaciones no acotan cambios de espacio causados por otros procesos.

Agregar segmentos solo con reloj continuo y estado/propuesta/ajustes
idénticos por bits en cada unión. Los cruces, replays, etapas seleccionadas
e integral se cuentan sobre la trayectoria continua sin duplicar prefijos.
Cada nuevo comienzo restaurado añade un full/mid/end contrastado.
El segmento fallido conserva su mínimo bajo reserva: no reinterpretarlo
como una ejecución que respetó siempre el margen. La admisión eléctrica
del banco agregado y el cierre administrativo de cada proceso se informan
por separado. Newton, LTE y refinamiento permanecen intactos.
