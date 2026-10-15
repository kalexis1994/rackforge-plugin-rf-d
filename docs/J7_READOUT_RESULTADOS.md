# Búfer offline de J7 y precisión temporal

## Lectura y memoria

[Protocolo](J7_READOUT_PROTOCOLO.md), escena nominal heredada del
[arranque propio](CHAIN_STARTUP_RESULTADOS.md). La nueva
[API](../crates/rf-d-circuit/src/j7_audio_readout.rs) lee únicamente J7
desde las dos mitades fine admitidas, sin realimentar estados interpolados
al circuito. Polinomio cuadrático en incrementos HIGH/LOW y extremos
directos; reloj racional n/48000 s sin acumulación de periodos.

Buffer fijo del llamador, 4801 valores en voltios entre 0 y 100 ms
inclusive. Las muestras 48/3600 coinciden con KEY ON/OFF; 4800 es el final.
Los cambios de KEY conservan los estados completos. No hay ganancia,
normalización ni cambio de cargas, puertos, fuente periódica o Newton.
Accepted debe proceder del solver admitido; el lector comprueba su
continuidad, dominio y capacidad, sin sustituir una auditoría eléctrica.

## Fallo conservado y diagnóstico

[Primer ensayo](../evidence/j7_readout_native01.json): los perfiles 32/8 us
completan la nota, pero fallan los gates fijados de lectura: RMS relativo
0,00981380635 frente a <=0,001 y máximo relativo 0,0192533841 frente a
<=0,003. Diferencia RMS 40,0954 uV y máxima 247,0926 uV. La media sí pasa.
Se conserva el [replay](../evidence/j7_readout_failure_replay01.json) del
gate con las mismas entradas y la repetición nativa de 8 us, idéntica en
muestras y resultados eléctricos salvo tiempo de ejecución.

El [diagnóstico sobre la grilla común](../evidence/j7_readout_grid_diagnostic01.json)
de 125 us también falla el gate anterior al comparar 32/8 us: RMS relativo
0,00980796. No es una discrepancia exclusiva del interpolante. La anterior
pareja 64/32 us producía casi la misma selección adaptativa y no bastaba
para acreditar precisión de salida bajo una reducción mayor. Se conserva
esa evidencia histórica en su dominio; no se reescriben sus resultados.

En el perfil 32 us, GRID/ROOT/eventos/DC/final coinciden por bits con la
campaña admitida de arranque. Esta prueba de pasividad sigue siendo útil,
aunque dicho perfil no alcance la precisión de audio requerida aquí.
Se reduce el máximo eléctrico a 4/2 us y se mantienen todos los gates.


[Segundo ensayo](../evidence/j7_readout_native02.json), 4/2 us: RMS relativo
0,00148667476 y máximo relativo 0,00331682148; sigue fuera de los mismos
gates. RMS 6,07393 uV, diferencia máxima 42,5997 uV. Su
[replay](../evidence/j7_readout_failure_replay02.json) conserva el fallo y
la trayectoria 2 us idéntica en muestras/estados. El perfil de 2 us se
reutiliza sin simularlo por tercera vez al contrastar con 1 us.


Los 4801 valores incluyen un ancla final: representan puntos 0..100 ms,
no 4801 frames de un bloque semiabierto de 100 ms. Para concatenación o
exportación futura de bloques, usar muestras [0,4800) como cuerpo y
conservar 4800 como frontera; no repetir la frontera al unir bloques.


## Admisión nominal 2/1 us

[Referencia fina](../evidence/j7_readout_native03.json): RMS relativo
0.000649866862243 (0,0649867 %), diferencia máxima/pico
0.00145128736357 (0,145129 %), media 2.53818577614e-09 V.
Diferencia RMS 2.65509617 uV y máxima
18.6445816 uV. Todos pasan los gates originales.
Pico de referencia 0.01284692616 V, sin normalización.
Se admite máximo full de **2 us** para esta escena y lectura; 1 us es el
control más fino ejecutado. Esto es convergencia entre perfiles, no una
cota matemática del error frente a una solución exacta.

50579/100151 pasos; mínimo full 3,90625 ns, sin violar MIN_DT. Newton
máximo entre ambos: 0,999845 pA/1,996803 nV. Cincuenta y dos pares de
rechazo/retry del lector a 4/2 us y 101 sobre el par admitido 2/1 us; heap
cero en lectura y solver. Cada trayectoria principal conserva seis replays
del solver y cinco rechazos atómicos. Dos tests Rust nuevos pasan:
polinomio y extremos; capacidad, inicialización y rechazo con recuperación.

Procesamiento del solver 115,003216/225,133066 s por 100 ms simulados
(no incluye todo el costo de lectura/exports del banco); sigue offline.
No se presenta como una nueva optimización ni como capacidad RT.

## QA y siguiente bloque

[QA global](../evidence/j7_readout_tests01.json) protege 4263 fuentes
anteriores y 8769 inputs privados. Los 255 tests anteriores se heredan por
identidad; dos nuevos se ejecutan. Cinco trayectorias principales nuevas,
dos repeticiones nativas de fallos y reutilización explícita del miembro
2 us. No se ejecutó una nueva auditoría de ecuaciones originales en los
perfiles finos; la pasividad exacta del perfil 32 us conserva su evidencia
previa. Los gates de Newton del motor seleccionado permanecen intactos.

Temporales retirados, sin WAV, cache, Cargo, rlib ni carpetas de muestras
nuevas. El modelo/solver/inicializador conservan bytes; sólo se agrega
lectura pasiva y una condición de precisión numérica para esta escena.
Siguiente: nota offline de duración útil y conversión/antialias verificados
antes de una única exportación para escucha. Leer a 48 kHz no prueba banda
limitada ni parecido con hardware; no se admite todavía plugin o RT.
