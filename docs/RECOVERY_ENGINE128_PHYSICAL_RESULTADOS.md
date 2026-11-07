# Salidas HD Audio y margen a 128 frames efectivos

2026-11-07. ASIO4ALL volvió a enumerar ocho canales `HD Audio
output` antes de cualquier escritura en el registro. Con ese par
se completaron dos campañas O2. La ruta volvió después a
`Not Connected` y el primer banco O3 terminó sin abrir un stream.
Se conservaron las consultas y el rechazo de enlace inicial
con su replay.
[Recuperación transitoria](../evidence/recovery_engine128_endpoint01.json),
[desconexión](../evidence/recovery_engine128_endpoint02.json),
[O3 sin salida física](../evidence/recovery_engine128_smt08.json)

Las dos interfaces probadas de Realtek dejaron `Not Connected`.
Al habilitar la interfaz del monitor NVIDIA en el perfil del
banco, ASIO4ALL enumeró `High Definition Audio 1/2` con cuatro
bytes por muestra. Se conservó esa selección en el perfil del
banco tras verificarla con dos consultas independientes. Los
demás perfiles conservaron sus valores.
[Pruebas de dispositivos](../evidence/recovery_engine128_endpoint03.json),
[selección del monitor](../evidence/recovery_engine128_endpoint04.json),
[configuración por aplicación](https://asio4all.org/about/developer-resources/user-registry-settings/)

## Pases físicos a 48 kHz

Cada pase de la tabla contiene 4800 callbacks con avance de
128 muestras y alternancia del búfer. El driver recibió
silencio. El límite de pared se mantuvo en medio período
(1,333333… ms), con la preparación incluida en el primero.
Los bancos usaron afinidad fija tras verificar inactividad
en ambos hermanos SMT. La captura ligera eliminó sondeos
del supervisor durante el stream y lecturas de CPU por hilo.

| Paquete y ruta | Pase | Mediana (ms) | P99 (ms) | Máximo (ms) | Sobre margen | Plazos perdidos |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| O2, ocho salidas | 1 | 0,8657 | 1,2942 | 1,5184 | 28 | 0 |
| O2, ocho salidas | 2 | 0,8658 | 1,0805 | 1,3761 | 2 | 0 |
| O2 ligero, ocho salidas | 1 | 0,8612 | 1,0049 | 1,4080 | 7 | 0 |
| O2 ligero, ocho salidas | 2 | 0,8579 | 1,2172 | 1,4472 | 31 | 0 |
| O3 ligero, monitor NVIDIA | 1 | 0,8123 | 0,8673 | 1,3509 | 1 | 0 |
| O3 ligero, monitor NVIDIA | 2 | 0,8134 | 0,9113 | 1,3397 | 1 | 0 |

El primer control silencioso de NVIDIA registró
`kAsioResetRequest` (máscara 8). Los dos pases O3 de esa
campaña quedaron libres de avisos, fallos de slot y
asignaciones de render.
[O2](../evidence/recovery_engine128_smt06.json),
[O2 ligero](../evidence/recovery_engine128_smt07.json),
[O3 ligero](../evidence/recovery_engine128_smt09.json)

En el replay O3, el control y el segundo pase agotaron la
ventana de preselección de 40 s sin cumplir el mínimo de
inactividad. El primer pase del replay sí procesó 4800
callbacks físicos a 128 frames efectivos. Su máximo fue
3,8951 ms, con 805 callbacks sobre margen, 126 plazos
perdidos y 52 intervalos superiores a 1,5 períodos. La
salida NVIDIA siguió presente en las dos consultas finales.
El perfil volvió a 44,1 kHz y al búfer original. ASIO4ALL
actualizó los offsets de latencia del perfil al abrir la
nueva salida.
[Replay O3](../evidence/recovery_engine128_smt10.json),
[consultas finales](../evidence/recovery_engine128_endpoint05.json)

Los binarios O2 y O3 coincidieron por hash con sus paquetes
de referencia. Cada versión conservó las tres reservas
eléctricas y la igualdad exacta en 9288 frames del FIR. La
captura de 2048 frames del motor RackForge fue idéntica
muestra por muestra. El banco mantuvo el VCO y los contornos
fuera de la ruta medida.
[Reservas O2](../evidence/recovery_engine128_reserve08.json),
[FIR O2](../evidence/recovery_engine128_broadcast_fir08.json),
[reservas O3](../evidence/recovery_engine128_reserve07.json),
[FIR O3](../evidence/recovery_engine128_broadcast_fir07.json),
[auditoría](../evidence/recovery_engine128_physical_tests01.json)

**Resultado:** la ruta física del monitor quedó recuperada
en el perfil del banco. El margen de 1,333 ms sigue
pendiente de confirmación en dos pases físicos.

El replay reconstruyó el ejecutable y la biblioteca nativa
del banco. Sus hashes difirieron. Se verificaron los mismos
comandos, bibliotecas del host, fuente generada y paquetes
Wasm. La auditoría conserva el rechazo de la comparación
inicial de todos los binarios.
