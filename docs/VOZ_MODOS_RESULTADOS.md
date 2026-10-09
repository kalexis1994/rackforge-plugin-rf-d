# Modos: excitación desde BUS y observación en J7

2026-10-09. [Contrato previo](VOZ_MODOS_PROTOCOLO.md),
[diagnóstico reproducible](../evidence/voice_joint_modes_reference01.json) y
[auditoría de promoción](../evidence/voice_joint_modes_tests01.json).
Misma raíz DC condicionada CA3046, mismas matrices y misma física.

## Resultado

Los 18 modos se reconstruyen en las 68 coordenadas de cadena. Se compararon
27 soluciones nodales complejas, desde DC y 0,01 Hz hasta 1 MHz, incluyendo
410,801759 Hz, con el Jacobiano analítico nativo y el FD independiente.
La peor fracción del gate de reconstrucción fue 0,01210; la del contraste
independiente, 0,00002028. Condición de los autovectores: 3768,90.
Los ocho escalones analíticos cumplen las ecuaciones locales; no son ocho
simulaciones de la trayectoria no lineal. No se encontraron nuevas raíces.

| Tiempo local | Peso pasa bajos en J7, V/V | Fracción de energía destacada |
|---|---:|---|
| 264,582 ms | −1,5103e-9 | 99,8705 % en C10, incidencia 67↔7 |
| 77,373 ms | +0,000287750 | ≈100 % en capacitor 400 µF, incidencia 60↔61 |
| 60,170 ms | +0,000135729 | Repartida: incidencias 26↔frontera, 46↔47 y 60↔61 |
| 36,761 ms | −0,278317 | Repartida principalmente entre 46↔47 y 60↔61 |
| 36,300 ms | +0,238717 | Repartida principalmente entre 46↔47 y 60↔61 |

La tabla es un extracto; el recibo conserva todos los modos, sus signos,
partes complejas, residuos, excitación, observación y 18 fracciones de energía.
El modo más lento tiene un peso minúsculo en esta transferencia BUS→J7.
Su tiempo no justifica por sí solo exigir 265 ms de calentamiento.
La anterior diferencia de historia de C27 sigue siendo un hecho distinto:
este cálculo no atribuye ese desajuste al modo lento de C10.

Los términos se cancelan fuertemente: suma de magnitudes de pesos 18,13262,
ganancia DC exacta del solve 0; término algebraico reconstruido ≈9,12e-9 V/V.
Por eso la suma de magnitudes sirve como envolvente conservadora, no como
ganancia ni nivel sonoro. Para el escalón lineal formal de 1 mV, a 5,25 ms
la respuesta firmada sería +57,39 µV y la envolvente 7794,82 µV.
La envolvente cae por debajo de 1 µV a 231,117 ms. Este tiempo depende de
esa frontera, raíz, amplitud formal y umbral; **no es un bound de la voz
no lineal ni una duración de arranque adoptada para el producto**.

## Recursos recuperados sin borrar evidencia

La reserva de 1 GiB impedía iniciar una nueva campaña temporal. Se aplicó
compresión NTFS transparente solo a tres cachés congelados de laboratorio.
[Recibo](../evidence/voice_joint_cache_compression01.json): 626 archivos,
SHA256 y tamaños lógicos idénticos antes/después; cero archivos borrados
o movidos. Asignación física 292.329.707→156.945.384 bytes: recuperados
135.384.323 bytes (≈129,11 MiB). El espacio libre después fue
1.176.002.560 bytes; es una observación puntual, no una garantía futura.
Los hashes privados anteriores siguen verificando sin adaptadores de lectura.

## Próximo paso operativo

La duración de arranque debe decidirse con carga y estado por ciclo de la
trayectoria conjunta. Ejecutar primero un prefijo desde la raíz condicionada,
con refinamiento y checkpoints; después completar los ciclos desde esa misma
historia. No sustituirlos por esta transferencia local ni por los ciclos ya
admitidos con la historia antigua. No se generó nuevo audio, SPICE ni código
eléctrico en este bloque; los 248 tests nativos se heredan por identidad,
sin reejecutarlos ni contarlos como nuevos.
