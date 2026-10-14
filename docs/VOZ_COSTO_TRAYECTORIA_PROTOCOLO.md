# Trayectoria ampliada de la voz con solver optimizado

Previo al solve, 2026-10-14. Variante `sparse_ordered_voice`: mismo
circuito, DC condicionado, Newton, Radau, historial compensado y controles
de VOZ_DOS_CONTORNOS_PROTOCOLO. Sólo cambia orden de factor y reutilización
de memoria, con sustituciones triangulares que omiten únicamente ceros
exactos de los factores recién calculados; ninguna matriz futura se filtra
mediante el patrón que sugirió el orden.

Dos escenas desde DC propio hasta 24 ms, medio paso máximo 2/1 us. KEY
0/10/0 en 1/6 ms, sin nuevos eventos posteriores. C11/C12 ausentes y S abierto.
El reloj pasa por 8 ms y continúa con el mismo estado y propuesta, sin
reset ni conversión de capacitores. Grid común 125 us: 192 observaciones.
El prefix de 8 ms contrasta contra ambas trazas anteriores; la extensión
compara las dos resoluciones y el circuito original en las parejas nuevas
seleccionadas. No se prolonga la historia antigua de 164 ms.

Gates de VOZ_COSTO_PROTOCOLO y VOZ_DOS_CONTORNOS_PROTOCOLO intactos,
incluidos balance BUS 20 pA, original 251 nodos y slots MNA separados.
Registrar todos los reordenamientos y la identidad de fuentes binarias.
24 ms no acreditan una nota sostenida, panel general o tiempo real.

Si se exporta una ráfaga audible, usar exclusivamente esta nueva trayectoria
admitida completa. Duración 24 ms, sin repeticiones. Grid 8 kHz, resampling
sinc con ventana Hann de 64 taps, banda nominal 2.8 kHz y destino 48 kHz.
Monitor fijo 4 muestras/V, sin normalización por pico, DC conservado;
PCM16 mono, fades de 0.5 ms sólo en los bordes. Rechazar clipping; declarar
esta adaptación y su ancho de banda. No tomarla como fidelidad vintage.

≤600 s por escena, ≤300 s auditor, 1 GiB libre y 32 MiB nuevos de la
campaña. Mantener intentos/fuentes/replay; biblioteca y evidencias anteriores
intactas. Sólo después de completar ambos relojes y auditorías se admite
la extensión o su export. La siguiente prioridad sigue siendo duración útil
y una reducción mayor del motor; este cambio no satisface deadlines.
