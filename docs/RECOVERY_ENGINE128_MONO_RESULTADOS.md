# Voz nominal con VCO y contornos en RackForge

2026-11-07. El paquete de laboratorio wasm-v1 usa la voz
monofónica de referencia con un VCO nominal transpuesto,
C27, los dos contornos cargados y el gatillo compartido.
Los eventos MIDI llegan con su offset de muestra. El mismo
KEY gobierna los contornos de filtro y volumen y conserva
la prioridad grave y el legato. El audio se toma de J7
tras el FIR de 48 muestras, en voltios y duplicado a estéreo.
[Protocolo](RECOVERY_ENGINE128_MONO_PROTOCOLO.md),
[referencia monofónica](MONO_VOICE_RESULTADOS.md)

## Reservas eléctricas

El paquete repitió la escena nativa de 480 muestras con seis
eventos y arranque DC propio. El máximo error nodal en los
dos estados de comparación fue 3,11e−16 V frente al límite
de 1 µV. El error RMS relativo de J7 fue 2,43e−8. El residual
máximo del solver fue 0,927 pA, la corrección máxima fue
0,718 nV y el estimador máximo fue 0,031. Se observaron
las mismas memorias y el retraso de 48 muestras. El tiempo
de un bloque completo en la ejecución directa del paquete
estuvo en el orden de 15 s. Esta escena de 10 ms cubre
eventos y estados de arranque. La cola larga conserva su
evidencia anterior.
[Escena nativa](../evidence/mono_voice_native01.json),
[primer contraste portable y replay](../evidence/recovery_engine128_mono01.json)

El BUS de la voz nominal quedó entre −0,942 y −0,910 V
en las cinco observaciones. H128 está contrastado para
BUS entre −0,125 y +0,125 V. El núcleo rápido de recuperación
conserva sus reservas O3 de tres cutoff, sus 18 cargas y
el FIR exacto en 9288 frames. Sus mapas están condicionados
a los controles de aquel banco. La voz integrada usa el
solver nominal que resuelve las cargas del contorno en cada
etapa, con el control rápido conservado por identidad.
[Dominio H128](FAMILIA_FILTRO_RESULTADOS.md),
[reservas de recuperación](../evidence/recovery_engine128_reserve07.json),
[FIR](../evidence/recovery_engine128_broadcast_fir07.json)

## Banco físico

Con la misma CPU 9 y la salida NVIDIA, se hicieron dos
aperturas independientes. Cada una registró dos callbacks
silenciosos para establecer el reloj y un intento de render
de la voz a 128 frames con NoteOn a offset cero. El reloj
avanzó 128 muestras en ambos saltos de cada apertura y el
búfer alternó 0/1/0. El driver recibió silencio a 48 kHz.
[Filas físicas y cuarentenas](../evidence/recovery_engine128_mono02.json)

| Intento | Callback con la voz | Plazos perdidos | Muestras de voz entregadas |
| --- | ---: | ---: | ---: |
| 1 | 293,1473 ms | 1 | 0 |
| 2 | 300,4881 ms | 1 | 0 |

Fuera de ASIO, Wasmtime interrumpió la misma llamada a
los 298,418 ms. En cada apertura, RackForge puso el slot en
cuarentena y silenció su salida. Se registraron diez
asignaciones del host durante cada callback fallido.
Los tiempos físicos incluyen el render interrumpido y
su gestión de error. **El margen de 1,333 ms queda rechazado
para la voz nominal.** Cada apertura terminó tras el primer
intento de voz, con los bancos de 4800 aún pendientes.

El primer lector falló al calcular el hash de Node. Se
conservaron el render y el replay, con datos idénticos por
bytes. El lector físico inicial esperaba que el contador del
planificador registrara la cuarentena. RackForge ya la había
gestionado dentro del slot y el contador quedó en cero. La
auditoría verifica las dos cuarentenas en los registros y
reanaliza las filas originales con el mismo límite de pared.
[Primer fallo y replay](../evidence/recovery_engine128_mono01.json),
[auditoría](../evidence/recovery_engine128_mono_tests01.json)

La salida volvió a 44,1 kHz y al valor original de búfer.
Las consultas finales conservaron el par NVIDIA. Se retiraron
el target temporal, los paquetes y las cachés. La voz nominal
queda disponible como referencia portable reproducible.
[Salida final](../evidence/recovery_engine128_endpoint08.json)
