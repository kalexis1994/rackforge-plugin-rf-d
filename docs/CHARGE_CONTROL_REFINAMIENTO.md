# Separar error de transición y referencia temporal

Ampliación previa a nuevas mediciones, 2026-10-31. La familia lineal
conserva cargas pero rechaza la transición. Antes de atribuir ese error
a constitución, refinar la referencia no lineal dinámica de250 a125 ns;
si no pasa1 uV en TODOS los nodos comunes, añadir62.5/31.25/15.625/7.8125 ns
hasta pasar o agotar esa secuencia. Mismos gates
Newton/corrección y sin modificar ningún dato de la familia.

Exportar al reloj común250 ns desde los pasos finos, conservar SHA del
export completo y medir antes de compactar. Cada export sigue<=32 MiB;
fuentes/compiler congelados y un tmp/lab-current. El250 ns repetido debe
ser idéntico al original por bytes. Retener puertos completos y estados
dispersos/peor caso, con límites explícitos de recuperación.

Comparar nodos <=1 uV y J7 RMS .001/pico .003/media1 uV (fallback1 nV),
sin relajar gates si falla. El candidato a cada paso se integra en su
rejilla real antes de muestrearlo a250 ns. El contraste de producción
384 kHz es separado, con todos los puertos pero nodos dispersos.

El banco Rust registró incumplimientos de deadline: mantener el rechazo
de coste, sin repetir para elegir un tiempo más favorable. El primer
bloque, dispersión y máximos observados se conservan. No atribuir picos
al SO u otro proceso sin medición que lo aísle.
