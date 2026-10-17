# Ayuda de convergencia OP sin cambiar la raíz exigida

El primer OP frío en CV=-3.1 V/BUS=-.125 V termina con fallo de gmin,
source stepping y transistor JQ7_LEFT; el exit code de ngspice es cero
pero no existe el export. Original/deck/log y replay quedan en native01.
Antes de repetir, añadir nodeset de las 98 tensiones de la semilla analítica
vco1_startup::seed, no de su solve nativo. Las corrientes de rama no se
imponen. OP vuelve a resolver las mismas ecuaciones y Vstartup C1=0;
nodeset no es fuente, condición de igualdad final o modificación de modelo.

Declarar que ambos métodos comparten una semilla analítica de aproximación;
sus búsquedas/incidencias siguen separadas y ninguna raíz nativa inicializa
la búsqueda SPICE. No probar unicidad global por coincidir. Mantener todos
los gates de VCO_CV_CARGA_PROTOCOLO, trims exactos y fronteras. Rechazar
también mensajes error/aborted de ngspice aunque el proceso devuelva cero.
Guardar seed exacta, deck y resultados/replay de toda corrección.
