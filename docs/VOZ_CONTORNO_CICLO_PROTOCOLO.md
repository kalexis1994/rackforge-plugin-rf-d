# Ciclo del VCO con contorno229: continuación exacta

Antes de medición, 2026-10-12. Continúa
[ventana con reset](VOZ_CONTORNO_RESET_RESULTADOS.md), CA3046 condicionado,
sin hardware. No se cambian red, dispositivos, controles de panel,
cargas, controlador, límites h2/1 µs, Newton ni tolerancias.

## Historia y calendario

Inicio4423942144 ticks de125 ns/65536 (8.438 ms). Cada ON/OFF y máximo
1048576/524288 retoma su propio final anterior; no copia el fino sobre
el grueso. Se conservan por bits458 componentes, reloj, settings20,
próximo full, KEY0 y S abierto. Sólo cambian magic y fase de receta.
Codec3720 bytes/magic RFCYCT01 separa esta continuación sin regenerar
los parámetros físicos del checkpoint.

Reposo4 µs, KEY10/S sostenido1.5 ms, KEY0/S abierto1.5 ms:3.004 ms
nuevos hasta11.442 ms. Cortes al fin del reposo y cada300 µs; no se
asignan voltajes de envolvente. Comparación de229 coordenadas al mismo
reloj,2 µV/2 nA. Cada accepted conserva la ley coarse2h/dos finosh,
LTE≤1, duplicación≤.25,20 intentos/min full8 ticks.

## Ciclo y unión

El reset sigue la convención rampa43 creciente a−2 V. Exigir≥1 reset
nuevo por perfil, mismo conteo por pareja y diferencias interpoladas≤10 ns.
Unir los endpoints observados anteriores y nuevos sin huecos ni solapar
pasos; la semilla puede repetir el reloj como metadata, no como OBS nuevo.
Probar el estado y la receta de la unión por bytes.

Tomar último reset del recorrido anterior y primer reset nuevo: orden
estricto, intervalo positivo y ciclo completo del circuito entre ambos.
Periodo y frecuencia son descriptivos de ese ciclo transitorio; exigir
distancia de periodos entre máximos≤10 ns, sin inferir periodicidad
asintótica. Medir extremos finitos de saw/BUS/J7/C2/LOUDNESS entre
ambos brackets, sin presentar muestras/interpolación como cotas continuas.
Los controles de gatillo pueden cambiar dentro del ciclo.

Primer/último accepted por tramo y los que cruzan reset, deduplicados:
grafo/FD y Q Decimal100,20 pA/0.2 nV, corrección1 µV/1 nA.
Balances C2/C18/C27/C7/C4 y cargas Q25/Q15 por tramo/total a1 pA×duración;
sólo cuadratura fina publicada. Contrastar etapas, corrientes, LTE y clocks.
Restore en comienzos, primer corte interior y reset: prefijos de hasta16
accepted por bits, sin atribuir replay completo de1.5 ms. Cuatro
corrupciones y rollback de destino/presupuesto por perfil. Rechazos
guardan checkpoint entrante y destino exacto.

Presupuestos900 s/perfil,4000 s/campaña,120 s/compilación,300 s/auditor,
64 MiB privados, reserva1 GiB y stack32 MiB. Rechazos/replay preservados
antes de reparar. Bibliotecas y archivos anteriores protegidos por SHA.
248 tests heredados por identidad, no reejecutados. Sin audio nuevo,
SPICE, parámetros físicos identificados, nuevas cargas de placa2,
contorno desde silencio, nota de duración musical o RT.
