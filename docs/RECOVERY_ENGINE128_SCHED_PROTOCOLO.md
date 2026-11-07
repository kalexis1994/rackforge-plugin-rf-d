# Trabajo del render y planificación a 128 frames

2026-11-07. Congelar el invitado Wasm y el FIR de
`recovery_engine128_native15`. Usar el mismo binario de host y el
mismo paquete para comparar el motor con reloj ASIO y un banco
fuera del driver. Conservar el paquete silencioso como control.
Repetir primero el contraste de 2048 frames y comprobar los hashes
del núcleo y las reservas ya capturadas.

Medir pared y ciclos del hilo alrededor del render y de todo el
callback. Calibrar la lectura de CPU con trabajo ocupado y espera
de duración conocida. Si el reloj de CPU por hilo es demasiado
grueso, guardar su evidencia y excluirlo de la atribución por
bloque. Los ciclos se comparan como ciclos, sin convertirlos a
tiempo. Si Windows rechaza la captura de cambios de contexto,
guardar el fallo y su replay.

Fuera del driver, usar un temporizador del período de 128 a 48 kHz.
Comparar dos pases en el mismo procesador lógico sin carga
introducida, con carga en su hermano SMT y con la misma carga
en otro núcleo físico. Alternar el orden de las dos cargas.
Seleccionar antes de las medidas el primer procesador lógico del
tercer núcleo físico elegible en la topología que entrega Windows.
La carga es de un hilo temporal del proceso de prueba.

En ASIO, comparar un control silencioso y cuatro pases de 4800
callbacks con el orden libre, afinidad, afinidad, libre. La
afinidad se limita al hilo del proceso de laboratorio. Verificar
avance de 128 muestras, alternancia, reloj a 48 kHz y procesador
observado cuando hay afinidad. Mantener cero avisos, plazos
perdidos, asignaciones y fallos, con máximo de 1.333 ms incluida
la preparación del primer callback. Evaluar por separado ambos
pases de cada postura. Una postura que cumple sólo en el banco
acredita ese banco y esa postura. El VCO y los contornos quedan
fuera hasta confirmar el margen en la ruta que se utilizará.

Si los dos pases fijos no cumplen, comparar 1200 callbacks en el
primer procesador lógico de cada núcleo físico elegible después
del primero. Seleccionar por reloj válido y criterio completo,
luego por cantidad de bloques sobre margen, máximo y CPU.
Reservar dos pases nuevos de 4800 callbacks para confirmar la CPU
seleccionada, sin volver a elegir según los resultados largos.
El criterio de aprobación de esta postura usa ambos pases largos
y el control silencioso.

Si la postura seleccionada no confirma el margen, mantener fija
esa CPU y probar la generación Wasm O2. Mantener LTO, el mismo
núcleo y el FIR. Repetir la igualdad bit a bit de las reservas y
el control del FIR en WASI antes del control silencioso y de dos
pases ASIO nuevos de 4800 callbacks.

Restaurar el perfil de ASIO y retirar la compilación y cachés del
área temporal única. Conservar todos los pases y un máximo de
5 MiB en recibos nuevos, sin duplicar las reservas eléctricas.
[Banco previo](RECOVERY_ENGINE128_HOT_PROTOCOLO.md)
