# LU con soporte exacto del pivote

Declaración previa, 2026-10-13. Base444a962, voz229 CA3046 condicionada.
La matriz Radau tiene458 filas. Se conserva el reuso local del trial.

## Propuesta y dominio

Después de elegir/intercambiar el pivote, listar en orden creciente las
columnas posteriores cuyo coeficiente no es exactamente cero. Actualizar
sólo esas columnas en cada fila activa de eliminación. Reconstruir la
lista para cada pivote: el fill-in no tiene un patrón impuesto. Mantener
escalas, búsqueda de pivote, umbral1e-12, factor, RHS y sustitución hacia
atrás del solver de referencia. No descartar coeficientes pequeños, cambiar
orden de incógnitas, matriz física, masa, puertos o criterios de Newton.
Arrays de tamaño fijo; sin heap nuevo en el kernel.

La omisión de operaciones con cero puede afectar ceros con signo o casos
IEEE extremos. No afirmar equivalencia universal para toda matriz finita.
Admisión condicionada a identidad por bits en el dominio medido, más
pruebas de regresión de solver para fill-in, pivotes, coeficientes pequeños,
singularidad y cero con signo. Un rechazo se conserva y repite antes de
reparar; no se aflojan gates para adoptar el algoritmo.

## Medición y contraste

Reusar los84 pares congelados de referencia: coarse/mid/end de ON/OFF,
h2/1 µs, gatillo y reset. Warmup y cinco rondas alternadas en un proceso.
Comparar candidatos, incrementos, ratios, iteraciones y trials por bits
con kernel de reuso y datos originales. Instrumentar ensamblados/solves
y tiempo de cada operación; contar actualizaciones matriciales sólo en
una fase diagnóstica separada, sin contadores en el runner ni benchmark
pareado de producción del laboratorio. Exigir mediana de aceleración>1.

Repetir los cuatro recorridos de3.004 ms con cada seed propio. Comparar
todos los archivos de perfil por bytes contra newton-reuse01. Incluyen
OBS, STEP/LTE, corrientes, ledgers, raíces guardadas, checkpoints, restores
y rechazos inducidos. Si coinciden, heredar38472 ecuaciones por identidad
sin reejecutarlas; no extender cobertura a campos no guardados.

120 s compilación,300 s benchmark,900 s/perfil,4000 s campaña;
64 MiB privados nuevos, reserva1 GiB, stack32 MiB. Proteger3064 fuentes
y7611 privados de la QA previa. Comparación histórica de wall separada
del benchmark pareado.248 tests Rust heredados, no reejecutados.
Sin nueva duración, biblioteca, SPICE, audio o admisión RT.
