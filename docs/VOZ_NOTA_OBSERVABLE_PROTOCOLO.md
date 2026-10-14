# Nota corta continua con paso observable

Usa la primera política admitida de
[paso observable](VOZ_PASO_OBSERVABLE_PROTOCOLO.md), circuito completo nominal,
misma inicialización y panel. Escena nueva fijada antes de ejecutarla:
KEY 0→10 V a 1 ms; 10→0 a 75 ms; fin **100 ms**. Dos perfiles con
máximo completo 64/32 µs, clocks comunes cada 125 µs.

No hay referencia estricta de toda esta escena: comparar únicamente los
primeros 6 ms compartidos con el banco estricto y el refinamiento completo
de las dos nuevas trayectorias. Conservar gates externos del protocolo
anterior, Newton y BUS. Revisar las ecuaciones originales seleccionadas
en DC, primer avance y límites de evento/fin. No extender este resultado
a una nota de 500 ms, todos los controles o una liberación completa.

Cada trayectoria posee los 500 HIGH/LOW continuos, reloj y propuesta,
sin repetir ciclos ni unir notas independientes. Export completo comprimido
con gzip reversible y verificación del SHA256 del contenido antes de
retirar el archivo intermedio nuevo. Presupuesto total nuevo 48 MiB,
por proceso 600 segundos. Preservar falla/replay antes de reparar.

Escucha: J7 del perfil fino, 4800 frames a 48 kHz, PCM16 mono, ganancia
fija 4 muestras/V, sin quitar DC ni normalizar picos. Mismo adaptador
sinc/Hann de 64 taps, entrada a 8 kHz y banda nominal 2.8 kHz. Padding
constante en extremos y fade de 0.5 ms. No mide contenido sobre esa banda.
Contrastar también las dos exportaciones bajo los mismos gates de audio.
Una nota audible del modelo no demuestra parecido con hardware o RT.
