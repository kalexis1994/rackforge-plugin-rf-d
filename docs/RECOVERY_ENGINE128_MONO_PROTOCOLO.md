# Voz monofónica nominal en el host de laboratorio

2026-11-07. Integrar el VCO nominal transpuesto y la cadena
de 118 incógnitas con los contornos cargados de filtro y
volumen, gatillo compartido, C27, VCA y J7. Usar la misma
voz que resolvió las reservas monofónicas previas.
MIDI conserva prioridad grave, disparo único y fase continua.
La latencia FIR sigue siendo 48 muestras a 48 kHz.
[Referencia monofónica](MONO_VOICE_RESULTADOS.md)

El perfil anterior del VCO nominal admite la carga de
esta voz. El dominio BUS de H128 es ±0,125 V; registrar
el BUS propio antes de considerar cualquier sustitución.
El núcleo rápido mantiene sus reservas de nivel y
controles fijos. Conservarlo por identidad como control
y registrar por separado la constitución de la voz nominal.

Comprobar el paquete wasm-v1 con la secuencia de 480
muestras y seis eventos que ya tiene referencia nativa.
Repetir el DC, retener los estados de los extremos de
bloque, los errores de Newton y la salida en voltios.
Exigir estado nodal de 1 µV contra la misma trayectoria
nativa, residual de 1 pA, corrección de 2 nV y estimador
≤1. Mantener RMS relativo 0,001, pico relativo 0,003 y
media 1 µV. La latencia y ambas salidas deben coincidir.

Si el solver nominal completo excede el plazo fuera de
ASIO, medir primero la protección temporal del runtime
RackForge. Si interrumpe la voz dentro de 1 s, ejecutar
dos aperturas físicas de rechazo con ese mismo runtime.
Registrar dos callbacks silenciosos para establecer el
reloj, luego un solo intento de render completo a 128
frames con NoteOn a offset cero. Mantener la salida
NVIDIA, CPU 9 y la condición previa anterior. Retirar
el banco después de ese intento. Un trap, falta de
producción o plazo perdido rechaza la admisión. Para
aprobar siguen siendo necesarios un control y dos pases
de 4800 bloques de voz, con todos los callbacks por
debajo de 1,333333… ms incluida la preparación inicial.
[Referencia física](RECOVERY_ENGINE128_NVIDIA_RESULTADOS.md)
