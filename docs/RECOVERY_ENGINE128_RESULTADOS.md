# RF-D en RackForge a 128 frames efectivos

2026-11-07. El núcleo de recuperación con FIR se ejecutó como paquete
`wasm-v1` mediante Wasmtime, `PluginInstance` y un slot estéreo de
`RackEngine`. El banco abrió ASIO4ALL v2 a 48 kHz y verificó el avance
de 128 muestras y la alternancia de búfer en cada serie. El controlador
recibió silencio. La prueba cubrió el motor desde el adaptador ASIO de
laboratorio. La aplicación de escritorio queda como alcance de otra prueba.
[Protocolo](RECOVERY_ENGINE128_PROTOCOLO.md)

La captura de 2048 frames coincidió bit a bit en las tres rutas.
Ambos canales fueron iguales, con 48 frames iniciales de silencio y
un pico de 66.181 µV. La excitación fue la tabla congelada del banco
nativo. El VCO y los contornos quedan pendientes del gate de coste.
[Mediciones originales](../evidence/recovery_engine128_native02.json)

## Tiempo del callback

Cada bloque tiene 2.667 ms de plazo y un objetivo de 1.333 ms. Los
tiempos de la tabla están en ms. Los conteos de asignaciones corresponden
al asignador Rust del hilo que llamó al motor.

| Ruta | Bloques | Pase | Mediana | P99 | Máx. | Fuera de plazo | Sobre margen | Asignaciones |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Rack silencioso | 32 | Inicial | 0.0023 | 0.0181 | 0.0237 | 0 | 0 | 32 |
| Rack silencioso | 32 | Replay | 0.0023 | 0.0169 | 0.0223 | 0 | 0 | 32 |
| Rack silencioso | 1200 | Inicial | 0.0022 | 0.0047 | 0.0221 | 0 | 0 | 1200 |
| Rack silencioso | 1200 | Replay | 0.0025 | 0.0089 | 0.0441 | 0 | 0 | 1200 |
| Nativo | 1200 | Inicial | 0.6766 | 0.7429 | 0.9695 | 0 | 0 | 0 |
| PluginInstance | 1200 | Inicial | 1.5320 | 1.7729 | 2.5321 | 0 | 1200 | 1200 |
| PluginInstance | 1200 | Replay | 1.4962 | 2.5131 | 2.7076 | 3 | 1200 | 1200 |
| RackEngine | 1200 | Inicial | 1.5174 | 2.8379 | 2.9590 | 124 | 1200 | 1200 |
| RackEngine | 1200 | Replay | 1.5200 | 2.8960 | 4.8158 | 167 | 1200 | 1200 |
| RackEngine | 4800 | Inicial | 1.5200 | 2.6308 | 3.9099 | 32 | 4800 | 4800 |
| RackEngine | 4800 | Replay | 1.4950 | 2.3690 | 4.3322 | 8 | 4800 | 4800 |

**Rechazado para tiempo real a 128 frames.** La ruta directa portable
superó el margen en cada bloque, incluso antes de añadir el slot. Los
dos pases largos del Rack también superaron el margen desde el primer
callback con su preparación incluida. Hubo cero avisos del controlador
y cero fallos del slot. La telemetría interna del Rack contó 28 y 8
plazos perdidos en los pases largos. El reloj de pared del callback contó
32 y 8. El replay largo tuvo un intervalo entre callbacks de 1.641
períodos y el replay de 1200 tuvo tres por encima de 1.5 períodos.
[Mediciones originales](../evidence/recovery_engine128_native02.json)

La resta por bloque entre el callback completo y su tramo de render dio
una mediana de 1.5 µs en ambos pases largos y P99 de 4.2 y 3.3 µs.
En el peor bloque de cada pase, el render ocupó 3.9057 de 3.9099 ms
y 4.3282 de 4.3322 ms. El tramo incluye las comprobaciones del
adaptador y el trabajo del motor. Estos tiempos de pared localizan
los picos en ese tramo y admiten interrupciones del planificador.

## Asignación en el runtime portable

El control Wasm silencioso reprodujo una asignación por bloque, desde
el primero. Una traza offline separada, en `PluginInstance` después
de cuatro llamadas de calentamiento, capturó 24 bytes asignados al
construir un error de `StoreOpaque::get_fuel` de Wasmtime. El runtime
consulta combustible al terminar `process_interleaved_with_midi2`,
incluso con el medidor desactivado. El store devuelve el error y el
runtime lo convierte en cero. La traza quedó fuera de las mediciones
de latencia. Quitar esa consulta del camino sin medidor permitiría
medir de nuevo la asignación y el coste por separado.
[Traza de asignación](../evidence/recovery_engine128_alloc01.json)

## Reproducción y limpieza

El banco compiló el invitado con el SDK local y enlazó el adaptador
contra el artefacto Release local de `rackforge_core`. El recibo
identifica por separado el checkout del host `7a14c68a` y los hashes
del artefacto enlazado y sus dependencias. La carga usó la ruta normal
de optimización y caché de código portable. Los hashes de las fuentes
de cada ejecución identifican las versiones exactas del capturador.

La primera comprobación y su replay agotaron 95 segundos al cerrar
los workers por un bloqueo del capturador de stdout. El banco final
separó las muestras binarias de los mensajes y mantuvo los umbrales.
ASIO volvió a 44.1 kHz con preferencia de 512 frames y se restauró
el valor anterior de la opción propia del banco. Se retiraron el
paquete temporal, los binarios y la caché.
[Primer intento](../evidence/recovery_engine128_native01.json),
[replay](../evidence/recovery_engine128_timeout01.json),
[auditoría](../evidence/recovery_engine128_tests01.json)
