# Nivel, cutoff y transición local corregida

2026-10-31. [Protocolo](CHARGE_CONTROL_PROTOCOLO.md),
[reservas](../evidence/charge_control_native01.json),
[referencia fina](../evidence/charge_control_refinement01.json),
[corrección exponencial](CHARGE_CONTROL_EXPONENCIAL.md),
[análisis](../evidence/charge_control_exp_analysis01.json) y
[QA](../evidence/charge_control_tests01.json).

## Tres puntos locales y mapa de nivel

Perfil R61=200/L1, cutoff .49/.50/.51 desde -10 V, sin convertirlo a Hz.
VCA1/2=2 V, range=.1, resto del circuito68 anterior intacto, SVC-9
Fig.9-11/9-8/9-17. Puerto OSC1 impuesto Ibus=(BUS-.5*U)/39250 A una vez.
No VCO/H128, contornos, controles continuos o R61=200000 nuevos admitidos.

Tres DC propios HIGH/LOW y G/M,99 transferencias complejas y24 pasos
lineales independientes. Misma incidencia18 y eliminación50, sin
interpolar matrices, truncar capacitores o ajustar con las reservas.

Veinte historias no lineales de4 ms:18 estáticas de nivel/cutoff y dos
dinámicas,500/250 ns. Entrada a*(sin137 Hz+.3*sin1103 Hz). Todas ejecutan
con los gates anteriores; la aceptación del aproximado se informa aparte.

| Amplitud a | Peor error nodal estático (250 ns) | Resultado del modelo |
|---|---:|---|
| .01 V | 48.011 nV | seis reservas pasan, tres cutoff/dos pasos |
| .1 V | 4.341 uV | seis reservas rechazadas por1 uV |
| 1 V | 232.874 uV | seis reservas rechazadas, también falla audio |

A .1 V, J7 todavía pasa RMS .001/pico .003, pero los nodos rechazan;
no se admite el nivel por conservar sólo la salida. Nodo21 de recuperación
domina .01/.1 V; a1 V dominan TAIL/Q28_COLLECTOR. No son THD estacionaria,
una medición de saturación vintage o dominio universal de amplitud.
Los14 rechazos iniciales (12 de nivel y2 dinámicos) conservan replay
nativo idéntico por SHA. Ningún gate fue relajado para ampliar nivel.

## Memoria entre puntos

Estado de18 voltajes de capacitor A*x, incluyendo su DC, en HIGH/LOW.
Los offsets de riel fijo no cambian aquí. Cada modelo recibe delta
respecto de su propio DC y publica salida absoluta, no sólo perturbación.
Seleccionar índice conserva por bits esas coordenadas; no descarga
capacitores. La entrada de prueba conserva su ley/fase absoluta.

Ensayo: cutoff .50→.51→.49→.50 en1/2/3 ms, a=.01 V. La continuidad
de carga pasa: máximo error de voltaje2.17e-19 V en el rebasing Python.
Un reset a DC altera hasta3.584 mV de estado y es detectado. El endpoint
exacto del salto conserva el marcador izquierdo; las etapas posteriores
usan el índice derecho. No se presenta ese marcador como raíz algebraica
resuelta después del cambio.

Conservar memoria no basta para reproducir la constitución. El candidato
al mismo paso fino queda en4.584 uV (nodo15) y RMS J7 .0013197, ambos
fuera de1 uV/.001. La conmutación de puntos locales **queda rechazada**.

## Referencia temporal antes de atribuir el error

La comparación250/125 ns cambia hasta107.804 uV en la transición. Se
refina sin tocar candidato, dispositivos o gates:62.5/31.25/15.625/7.8125 ns.
El último par pasa:315.177 nV en todos los68 nodos comunes, RMS J7
1.776e-6, pico9.514e-5, corriente3.799 fA. Se exporta al mismo reloj250 ns;
el replay250 ns coincide por bytes con el original. No semilla desde
la solución del reducido. Son comparaciones medidas, no cota matemática
del error exacto o evidencia de otro ejemplar físico.

## Corrección de integración en producción

El primer banco SDIRK384 kHz rechaza tiempo real y transición. Para
separar método y constitución se prepara la transición exponencial FOH
de las mismas matrices fuera de audio. No se modifica el kernel salvo
el vínculo a F/U0/U1. G/M/DC, Xq/Xu, cargas y guardas son idénticos.

Diagonalización condicionada416.96–483.45; semigrupo<=2.49e-14,
identidades auxiliares dentro del gate. [Defecto en endpoints reales](../evidence/charge_control_step_defect01.json)
contra la MISMA ODE local: SDIRK717.359 uV, exponencial7.38e-14 V.
Esto prueba una corrección temporal; no error tan pequeño contra el
circuito no lineal o hardware.

Una recta entre potenciales rápidos introduce por sí misma errores
aparentes de milivoltios y no estima ese defecto temporal. Se conserva
el diagnóstico anterior, etiquetado. La [consulta parcial exponencial](CHARGE_CONTROL_DENSE.md)
parte de estados Rust y la entrada FOH, sin usar la referencia como
semilla. No cambia audio ni certifica antialias de las transiciones.
Contra el circuito fino: nodos retenidos4.660 uV y RMS J7 .00131912;
el rechazo constitutivo continúa. Puertos completos, nodos dispersos.

Rust/Python:1537 estados por método,18 coordenadas y68 nodos,
gates1e-11 V/1e-15 A. Salidas coinciden por bits con la reconstrucción.
Ocho rechazos/reintentos y seis cambios de índice conservan bits por
método, ceros con signo incluidos. Ninguna unidad de prueba nueva ni
repetición de los276 tests heredados.

## Coste y alcance de admisión

Ryzen5 5600X/Windows11, Alto rendimiento verificado al cierre,
compiler/rlib congelados y opt-level2 genérico. Cada banco incluye familia
con cambios discretos, compensación de cargas, tres puertos/corriente y
FIR384→48 kHz; generador y preparación de matrices fuera del intervalo.
1200 bloques128 por método, primero incluido, presupuesto2.6667 ms.

| Método | Mediana | P99 | Máximo | Deadlines perdidos |
|---|---:|---:|---:|---:|
| SDIRK | .69055 ms | 3.16344 ms | 10.899 ms | 16/1200 |
| Exponencial FOH | .46440 ms | .62432 ms | .66250 ms | 0/1200 |

El segundo banco pasa el objetivo50% observado, el primero no. No se
elige otra repetición ni se atribuye la diferencia de coste al método:
el núcleo recorre las mismas operaciones con coeficientes distintos y
el banco no aísla variación del entorno. Estado304 bytes, FIR6168 bytes;
cero heap.3.2 s procesados por banco,1228800 entradas/153552 salidas,
primera entrega80 y siguientes128 por latencia1 ms. No WCET o RT de voz.

Admisión: reservas estáticas .01 V en los tres puntos y corrección
temporal exponencial de la ODE local. No se promueve cutoff dinámico,
constitución grande, alias general, contornos, H128 o la voz completa.

## Recursos y siguiente bloque

Los exports se retiran de tmp/lab-current después de SHA, métricas
completas y verificación de puertos/estados seleccionados cada64 filas,
eventos y peor caso. Packs5,197,156 y2,011,788 bytes; no reconstruyen
la rejilla ausente. Todos los procesos<=240 s y exports<=32 MiB.
Sin Cargo/rlib/cache/SPICE/WAV;8769 inputs y escucha anterior intactos.
Los rechazos anteriores de la voz siguen vigentes.

Siguiente: corregir la ley constitutiva de recuperación y ladder/control
antes de extender matrices por nivel o cutoff. El error restante ya está
separado de la transición temporal local. Mantener las18 cargas y el
oráculo completo; no ocultar discrepancias reseteando memorias, recortando
J7 o cambiando gates para conseguir una voz aparentemente funcional.
