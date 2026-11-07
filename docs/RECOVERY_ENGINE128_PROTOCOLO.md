# Núcleo RF-D en el motor de plugins a 128 frames

2026-11-07. Base RF-D e6e6a90. Cargar un paquete wasm-v1 de laboratorio
con PluginPackage y LoadedPlugin. Compilar el núcleo exponencial y
el FIR congelados con el SDK de RackForge. La salida del paquete
incluye los 48 frames de latencia del FIR y la conversión a f32
estéreo. La fuente de excitación es la misma tabla del banco nativo.
La interfaz de audio recibe silencio durante las mediciones.

Comparar 2048 frames con el adaptador nativo y cotejar PluginInstance
y RackEngine en un solo slot con ganancia unitaria. Exigir muestras
finitas, ambas ramas estéreo iguales, arranque de 48 frames y
diferencia máxima de 1e-10 V más 1e-7 por el pico de referencia.
Contabilizar asignaciones Rust por hilo durante la llamada al motor.
Guardar fallos de slot y telemetría del propio RackEngine.

Usar la salida ASIO4ALL v2 del banco previo con reloj de muestras y
alternancia de búfer. Período 128 a 48 kHz. El presupuesto de pared
es 2.667 ms, con margen objetivo de 1.333 ms. Medir el callback entero
y el tramo de render por separado. Incluir el primer callback y sumar
su preparación al gate. Exigir avance de 128 entre posiciones,
cero plazos perdidos, ausencia de avisos y de intervalos >1.5 períodos.

Orden de bancos: apertura corta de 32 y control silencioso de 1200
a través de RackEngine, referencia nativa de 1200, PluginInstance
de 1200, RackEngine de 1200 y confirmación de 4800. Repetir una vez
cada rechazo, conservar la primera medida y registrar la restauración
del perfil ASIO4ALL. Medir el runtime y RackEngine reales desde un
adaptador de laboratorio. La ventana, colas de UI y dispositivo de
la aplicación instalada requieren una prueba aparte.

Un único tmp/lab-current para el paquete y la caché portátil temporal.
Compilación directa del invitado y artefactos locales del host
identificados por hash. Preservar 8769 entradas y la escucha anterior.
Guardar recibos acotados antes de retirar los artefactos generados.

La primera comprobación agotó 95 s y su replay idéntico también.
El capturador retenía stdout al destruir el pool. Los workers usan
stdout para anunciar su inicio. Las muestras binarias se escriben
ahora en un archivo temporal propio para que el pool pueda cerrarse.
Los umbrales numéricos y de tiempo se mantienen.
