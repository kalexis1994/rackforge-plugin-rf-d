# Continuación por coste medido

2026-10-08. [Campaña original](VOZ_PRIMER_CICLO_PROTOCOLO.md).
El perfil de medio máximo125 ns completó5,25 ms en842,17 s.
El perfil62,5 ns proyectaba más de900 s; se detuvo cooperativamente tras
7875 intervalos, reloj515440640 (0,983125 ms), con todos los endpoints,
checkpoint final y sus balances guardados. No fue un rechazo eléctrico.
El [recibo de parada](../evidence/voice_joint_cycles_resource01.json) fija
la razón antes de crear el archivo de parada. El proceso y sus hashes
permanecen en [native01](../evidence/voice_joint_cycles_native01.json).

No reejecutar el perfil completo ni el prefijo fino. Restaurar high/low,
reloj y propuesta por bytes; conservar parámetros del mismo builder y
la librería física medida. El caller de continuación solo amplía1800 s
por proceso/2100 s globales, añade restore inicial y traslada los conteos
de dos cruces/dos restores al flujo completo concatenado. Newton, LTE,
puertas físicas, objetivo final y presupuesto total de intervalos no cambian.
El balance de carga se comprueba por segmento y también con la suma
de integrales frente al ΔV del estado inicial/final de todo el perfil.

Cada segmento tiene cabecera propia. Verificar igualdad por SHA256 del
checkpoint de salida/entrada, continuidad de clocks y todos los endpoints;
omitir únicamente el checkpoint inicial duplicado de la continuación al
construir el banco común de21 relojes. Las integrales y conteos se suman
sin duplicar etapas. Se conserva también un intervalo adicional junto a
la frontera restaurada para contraste nodal independiente.

Reserva1 GiB y estimación28 MiB nuevos: ejecutar solo el tiempo restante,
reusar la librería anterior y quitar metadata de depuración del nuevo
ejecutable con `strip=symbols`. Flags y hashes se registran; no se recompilan
ni optimizan leyes físicas. La nueva ejecución se queda dentro del
presupuesto restante48000−7875 intervalos del perfil fino. Los criterios
del ciclo y refinamiento se aplican después de unir los segmentos.
