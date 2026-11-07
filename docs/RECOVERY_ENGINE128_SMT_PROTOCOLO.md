# Afinidad guiada por la carga del hermano SMT

2026-11-07. Congelar el invitado O2 con LTO, el FIR contiguo,
el motor RackForge y las reservas del banco anterior. Medir el
mismo binario en ASIO. Verificar 2048 frames bit a bit, salida
silenciosa al driver, alternancia de búfer y reloj a 48 kHz.

Comparar núcleos físicos de dos hilos permitidos por Windows,
excluyendo el primero. Antes de abrir cada banco, medir 64 ms
de ciclos ociosos por CPU. Para la afinidad inicial elegir el
mejor mínimo entre los dos hermanos de cada núcleo. El
desempate usa la CPU lógica menor. Las lecturas se hacen en
el supervisor. Durante el banco adaptativo, consultar cada
4 ms con una ventana de cuatro lecturas. Cambiar si el hermano
actual baja del 75 % del mejor hermano disponible en dos
lecturas consecutivas. Exigir 24 callbacks entre solicitudes
y elegir el siguiente núcleo por la misma regla del mínimo.
El tiempo de aplicar la afinidad se incluye en el callback.
Los ciclos ociosos se usan para comparar CPUs de la misma
máquina y ventana.
[Contador de ciclos ociosos de Windows](https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-queryidleprocessorcycletime)

Primero medir el control silencioso y un banco de 1200 bloques
por postura bajo la misma carga sintética. Fijar CPU 8 al
inicio e iniciar carga en su hermano después del bloque 128.
Comparar la afinidad mantenida con la adaptativa. Registrar
el inicio de la carga, el destino y el coste de cada cambio,
así como la CPU observada. La carga termina con el proceso de
laboratorio.

Confirmar sin carga inducida con dos pases nuevos de 4800
bloques bajo la misma política. Medir primero la adaptativa y,
si falla, la afinidad guiada al inicio y mantenida durante
todo el pase. Conservar ambos pases de cada política. Exigir
incrementos de 128 muestras, el criterio de 1.333 ms para cada
bloque incluida la preparación del primero, y cero plazos
perdidos, avisos, asignaciones de render y fallos de slot.
La admisión exige los dos pases de una misma política. Su
alcance es el banco y la configuración medidos.

Si cambiar la afinidad dentro del callback agota el margen,
probar el cambio desde el supervisor. Fijar el supervisor en
el núcleo excluido. Intentar el cambio sólo con el callback
inactivo, hasta 500 µs después de terminar y con al menos 900 µs
hasta la siguiente llegada nominal. Registrar la duración de
la llamada fuera del callback y verificar la CPU real en el
render. Repetir el control de carga y los dos pases largos con
esa política. Mantener el primer ajuste dentro de la medición
del primer callback. Si falla, repetir la postura fija con el
supervisor en ese mismo núcleo excluido.

Si el control silencioso acusa interrupciones, medir la postura
fija con una condición previa de carga. Exigir cuatro ventanas de
250 ms con al menos 70 % de inactividad global y que ambos
hermanos del núcleo candidato alcancen al menos el 90 % del
máximo de ciclos ociosos de cada ventana. Elegir el mejor mínimo
entre las cuatro ventanas y desempatar por la CPU menor. Dar
hasta 40 s a la condición antes de cada banco. Registrar todas
las ventanas de admisión, incluyendo el control silencioso y
los dos pases largos nuevos. La selección usa sólo contadores
del sistema, sin consultar los tiempos de render. La confirmación
queda limitada a esa condición y mantiene el mismo criterio por
callback durante los pases.

Después de detectar `Not Connected`, exigir que el driver exponga
las dos salidas HD Audio con el mismo formato de cuatro bytes.
Comprobarlas antes del banco y en cada captura. Consultar el
driver hasta seis veces, cada cinco segundos, y conservar el
estado si las salidas no aparecen. Un avance de 128 en el reloj
de un driver sin esas salidas queda fuera de la confirmación física.

La afinidad se limita al proceso de laboratorio. Restaurar el
perfil ASIO y retirar paquetes, cachés y compilación temporal.
Conservar recibos acotados, incluidas las repeticiones fallidas.
[Banco anterior](RECOVERY_ENGINE128_SCHED_RESULTADOS.md)
