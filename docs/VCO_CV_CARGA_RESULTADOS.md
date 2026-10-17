# VCO calibrado ante CV y carga: resultado

2026-10-17. [Protocolo previo](VCO_CV_CARGA_PROTOCOLO.md),
[banco](../evidence/vco_cv_load_native05.json),
[etapas efectivamente aceptadas](../evidence/vco_cv_load_intervals01.json),
[almacenamiento](../evidence/vco_cv_load_storage01.json) y
[QA](../evidence/vco_cv_load_tests01.json).

## Dominio y raíces

Circuito documental CA3046/SVC-204D, SVC-9 pp.5/19, nominal 25 C,
C4=10 pF, SW6 3/10 y R6=.5. R11=521.3126579373712 ohm y
R8=.2613404652606161 de la calibración archivada, sin corrección por nota.
KEYBOARD [-3.1,-2.1,-1.1,-.1] V, otras cinco líneas -2.1 V. BUS
[-.125,0,.125] V por R45 una vez; NEG4_REF libre con su red y cargas,
carga externa adicional=0 A. Son fronteras eléctricas de laboratorio.

Doce DC propios desde semilla analítica, C1=0 sólo durante arranque,
comparados con OP de ngspice. Error máximo 1.291467111e-08 V en nodos y
1.526204674e-10 A en ramas, gates 2e-7 V/2e-10 A. KCL/constraint y forcing
contrastados con la incidencia original Decimal100; balance <=1e-11 A.
Conservar todas las memorias/retornos de los dos 741 y junturas.

Cuatro esquinas de la matriz, h=4/32 ticks, ocho problemas Radau,
dieciséis raíces de etapa Decimal100 desde la misma historia DC, sin usar
la raíz nativa de la etapa como semilla.
Error nodal máximo 4.425253736e-12 V. Además, cuatro intervalos reales de
las dos historias, ocho comparaciones de raíz y HIGH/LOW completo.
Se deduplican por controles/historia/h: 4 raíces reales
únicas. Total 32 conjuntos únicos/4288 filas: 12 DC,
16 etapas locales y 4 etapas reales únicas. Las réplicas
con el mismo problema coinciden por bits y reutilizan el solve independiente.
No son 4288 leyes distintas o trayectorias completas de la matriz.

## Frecuencia, forma y carga

Ocho transitorios SPICE nuevos de 30 ms, Gear2/125 ns, con BUS=±.125 V,
y Trap2 en KEYBOARD=-2.1 V/BUS=.125 V. Reusar los cuatro BUS=0 de la
calibración. Frecuencia creciente con KEYBOARD en cada carga:

| CV KEYBOARD (V) | BUS −.125 V (Hz) | BUS 0 V archivado (Hz) | BUS +.125 V (Hz) |
|---|---:|---:|---:|
| -3.1 | 220.000058208 | 220.000009328 | 219.999960453 |
| -2.1 | 439.142815360 | 439.142719258 | 439.142623143 |
| -1.1 | 877.841091854 | 877.840905566 | 877.840719254 |
| -0.1 | 1760.000462824 | 1760.000112584 | 1759.999762338 |

La columna BUS=0 conserva el CV alto archivado -3.1+3 =
-0.10000000000000009 V; los nuevos BUS altos usan -.1 V. Diferencia
8.326672684688674e-17 V por construcción binaria. Se conserva y etiqueta,
sin modificar datos o gates. [Fallo de enlace](../evidence/vco_cv_load_curve_binding_failure01.json)
y [corrección](../evidence/vco_cv_load_curve_binding_correction01.json).
La diferencia de carga es un resultado, no un gate de invariancia.
Las pequeñas variaciones de frecuencia no quedan identificadas por encima
de la incertidumbre de método en toda la matriz. Tampoco representan
curva MIDI o posición real de teclado/panel. Los puntos intermedios
mantienen los errores de laboratorio reservados, sin ajuste por nota.

Gear/Trap en el punto reservado cargado difieren
6.11719194e-05 cent;
extremos de salida por debajo de 1.4 uV. Fase definida por resets reales,
sin alineación extra, ajuste de ganancia o retirada de DC.

Dos historias nativas completas desde su DC propio en ese mismo punto,
30 ms con máximos aceptados 250/125 ns. Pasos:
156542/275572; tiempos completos
1365.00/2340.80 s
en este banco. No es tiempo real. Diferencia temporal de frecuencia
2.56652125e-08 cent. Peor comparación nativo/SPICE:
9.37880698e-05 cent y 3.221809933e-06 V de extremos (gates 1 cent/5 mV).
Ambos métodos SPICE y ambas resoluciones nativas pasan los armónicos
1–8 <=2 %, DC <=5 mV, dispersión <=1e-5 y balance Qa/Q10/C1 <=.002.
Este último excluye Q7 y cuadratura, sin convertirlo en balance continuo.
[Alcance de los oráculos](VCO_CV_CARGA_ALCANCE_ORACULOS.md): compartir
historia para contrastar etapas no crea otra trayectoria independiente.

La forma y frecuencia nacen aquí del VCO de circuito, sin fuente de fase
impuesta. Se conservan cargas, flujos, HIGH/LOW, estimador y Newton del
motor completo admitido. Se deriva fine/linear/Radau sólo por enlace de
datos; no cambia su aritmética. No se extrapola este único punto dinámico
a todos los CV/cargas o a cambios de CV dentro de una trayectoria.

## Fallos y convergencia

[Preflight](../evidence/vco_cv_load_preflight_failure01.json): un path de
Windows no coincidía con la clave POSIX de un input heredado. Se conserva
fuente/replay y corrección exclusiva de la representación del path.
[Native01](../evidence/vco_cv_load_native01.json) conserva el OP frío fallido,
con exit code cero y export ausente. [Native02](../evidence/vco_cv_load_native02.json)
resuelve nueve OP con nodeset analítico y falla en el extremo alto.
[Native03](../evidence/vco_cv_load_native03.json) y
[native04](../evidence/vco_cv_load_native04.json) conservan dos pasos de
continuación DC que tampoco resuelven el rango. Todos tienen replay.

El [diagnóstico](../evidence/vco_cv_load_dc_diagnostic01.json) cambia sólo
itl1/itl2 a 1000; OP directo y sweep resuelven el extremo y pasan los
mismos errores. Seleccionar OP directo con nodeset de la semilla analítica
de 98 tensiones, nunca de la raíz nativa, para los doce casos.
[Decisión](../evidence/vco_cv_load_dc_budget_decision01.json) y
[contrato](VCO_CV_CARGA_DC_PRESUPUESTO.md). Tolerancias, ecuaciones y
presupuesto Newton nativo siguen iguales. El fallo de convergencia SPICE
no demuestra ausencia de raíz o defecto físico del circuito. Compartir
una semilla aproximada tampoco demuestra unicidad global de la raíz.

## Almacenamiento y alcance

Una sola área temporal, vacía al terminar. Exports y ejecutable retirados;
sin carpetas por escena, Cargo/cache, librería nueva o WAV nuevo. La única
escucha actual sigue por hash y corresponde al adaptador de fase anterior.
No injertar estas formas/trims en aquel perfil nominal R8=.5/R11=500.

El recibo guarda ventanas exactas de los últimos dos ciclos con contexto
y todos los cruces asentados; el prefijo retirado sólo es regenerable,
no reanalizable por estados. El flujo nativo compacto no conserva todos
los 134 estados de cada endpoint; las etapas seleccionadas sí los guardan.
[Codec](VCO_CV_CARGA_ALMACENAMIENTO.md): diferencias uint64 modulares de
orden dos, barajado de bytes y XZ en un único pack. Cada float64 y el JSON
previo completo se reconstruyen por bytes. No se quita ninguna muestra
o precisión de las ventanas para comprimir. Pack 21436660 bytes;
JSON reducido de 86447032 a 3223171 bytes.
Todo el pack cuenta en el presupuesto 32 MiB, excluyendo QA.

No se reejecutan los 272 tests heredados ni las trayectorias anteriores;
no se añaden unit tests que dupliquen este banco. Se comprueban nuevas
fronteras mediante raíces, filas originales, métodos y resoluciones.
Sin hardware de referencia, esto contrasta el modelo documental nominal;
no identifica parámetros de un ejemplar vintage ni demuestra parecido audible.
Siguiente: construir una familia estacionaria reducida dependiente de CV
y BUS, con puertos/corrientes y puntos reservados frente a estos oráculos.
Extender períodos nativos completos ante discrepancias concretas. La
respuesta a cambios temporales de CV conserva su admisión separada.
