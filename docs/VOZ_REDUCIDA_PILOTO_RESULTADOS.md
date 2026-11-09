# Primer piloto del motor reducido de RF-D

La primera ruta audible usa la sierra H128, el puerto
R6/R45, el núcleo reducido del ladder con recuperación y
ambos VCA, y el FIR de J7. Conserva 18 voltajes de capacitor
y 12 leyes de juntura en ese núcleo. Renderiza 48.128
muestras a 48 kHz con eventos monofónicos a offset de
muestra y latencia FIR de 48 muestras.
[Protocolo](VOZ_REDUCIDA_PILOTO_PROTOCOLO.md)

## Contraste del tramo de audio

El tramo a 192 kHz se comparó con el mismo modelo a
384 kHz, desde DC y con la misma escena MIDI. Pasaron
las tres comprobaciones de mapas exponenciales contra
la formulación independiente. Las cuatro observaciones
por muestra de salida fueron idénticas al dividir el
render nativo en bloques de 64 y 128. El banco verificó
tres rechazos atómicos y recuperaciones. Las seis
ventanas de pitch comprobaron prioridad grave, vuelta a
la nota retenida e ignorar la nota aguda mientras suena
una más grave. El peor error de frecuencia fue menor
que 0,01 Hz.

| Contraste 192/384 kHz | Máximo observado |
| --- | ---: |
| Error RMS relativo J7 | 2,77e−6 |
| Error pico relativo J7 | 3,08e−6 |
| Diferencia BUS | 17,86 nV |
| Diferencia de voltaje de C27 | 18,39 nV |
| Diferencia de corriente de panel | 0,457 pA |

## Coste y escucha

376 bloques de 128 muestras en CPU lógica 9. La cuenta
de asignaciones durante el render nativo fue cero.
Los límites corresponden al banco ejecutado.

| Ruta | Máximo observado | Bloques sobre 1,333 ms |
| --- | ---: | ---: |
| Nativo, 192 kHz | 0,445 ms | 0/376 |
| Nativo, 384 kHz | 0,808 ms | 0/376 |
| ABI wasm-v1 en Node, 192 kHz | 0,852 ms | 0/376 |

La salida estéreo wasm-v1 fue idéntica por bits a la
conversión a f32 del render nativo. Se midió después
de calentar la instancia y preparar una voz nueva. El
primer intento portátil omitió SIMD, el SDK rechazó
la compilación y el replay reprodujo el diagnóstico.
El tercer recibo corresponde al render corregido.

El WAV de escucha usa la salida de 192 kHz después del
FIR, con una conversión fija de 125 µV por escala
completa. Tiene 48.128 muestras, sin normalización
por pico. Se retiraron los ejecutables, mapas y
el WAV de prueba de nivel anterior.
[Primer banco nativo](../evidence/rf_d_reduced_voice_pilot01.json),
[rechazo portable](../evidence/rf_d_reduced_voice_pilot02.json),
[medición y escucha final](../evidence/rf_d_reduced_voice_pilot03.json)

## Frontera de la siguiente integración

Este piloto usa cutoff y polarización de VCA fijos,
entrada atenuada y una rampa de laboratorio en el
mixer. El siguiente tramo de la voz debe cerrar C2/C5,
R59/R60 y la conmutación con los puertos dinámicos,
contrastar la salida con el solver offline y medir
el mismo presupuesto. La medición wasm-v1 se hizo
fuera del motor de RackForge y del driver físico.

## Paquete jugable en RackForge

El paquete portable RF-D Pilot 0.1.0 expone
una entrada MIDI y una salida estéreo. Usa la
misma sierra H128, la cadena de audio y la
rampa de laboratorio del piloto archivado.
La prioridad de nota grave conserva el rango
MIDI 36–72. Cutoff y polarización de VCA quedan
fijos en esta base.

El archivo `artifacts/rf-d-pilot-0.1.0.rfplugin`
se instaló en un almacén temporal. Ocho eventos
entraron por el enrutador MIDI real. Los dos
pases de 376 bloques a 48 kHz y 128 frames
reprodujeron por bits las 48.128 muestras
estéreo archivadas. Hubo cero eventos
descartados, fallos del slot o bloques por
encima de 1,333 ms.

| Pase offline | Máximo | Percentil 99 |
| --- | ---: | ---: |
| 1 | 1,212 ms | 0,852 ms |
| 2 | 1,282 ms | 0,952 ms |

La verificación cubre el host offline y el
alcance de este piloto. El presupuesto físico
y la integración de C2/C5, R59/R60 y el
biestable siguen abiertos. El ensayo de
empaquetado usa el componente SIMD construido
por Rust y el esquema 1 del manifiesto.
[Protocolo](VOZ_PILOTO_JUGABLE_PROTOCOLO.md),
[registro inicial de fuentes](../evidence/rf_d_playable_pilot01.json),
[rechazo del esquema 2](../evidence/rf_d_playable_pilot02.json),
[campaña MIDI admitida](../evidence/rf_d_playable_pilot03.json).
