# Historias compartidas y alcance de los oráculos

Los OP de ngspice y el arranque nativo comparten una aproximación
analítica de tensiones, no una raíz final. Se contrasta la raíz y las
ecuaciones; no se demuestra unicidad de cuenca de atracción.

En las etapas locales se comparte la historia DC nativa HIGH/LOW, ya
contrastada. Decimal100 empieza desde esa historia y vuelve a resolver
las dos etapas sin recibir sus raíces nativas. En los intervalos reales
también se comparte la historia aceptada anterior. Son problemas locales
con las mismas condiciones iniciales, no otras trayectorias completas
independientes. Las dos trayectorias nativas completas usan sus propios
DC y resoluciones, mientras SPICE aporta los métodos Gear/Trap.

Deduplicar cada problema local por los bytes canónicos de controles,
historia HIGH/LOW normalizada y paso; el máximo de la trayectoria no
cambia por sí solo el problema de una etapa. En este VCO autónomo, el
tiempo absoluto tampoco modifica sus ecuaciones. Una tupla repetida
reutiliza la raíz Decimal y exige la misma raíz nativa por bits. Informar
comparaciones y raíces/filas únicas por separado, sin sumar réplicas.

Los BUS ±.125 V son estímulos de laboratorio; el antecedente positivo
aparece en fixtures de vco1_stamp_reference.py. No son una especificación
de excursión física admisible del instrumento. El ensayo mantiene R45
y mide una carga de BUS con voltaje impuesto, no toda impedancia variable
o reacción temporal de una voz conectada.

La forma por fase conserva DC y toma los resets de cada historia. No
acredita error de reloj absoluto o una transición CV del instrumento.
Las pequeñas diferencias de frecuencia de la matriz de carga no se
declaran resueltas por encima de la incertidumbre de método en cada punto.
Todos los parámetros de dispositivo siguen nominales/documentales.
