# Soporte real de LU y bloques exactamente nulos

Variante numérica del modelo vintage CA3046 cargado, sin constantes audibles nuevas. Base `ca7e574e7b647b16735215ffb64aa76e7be679a2`; QA `voice_extended_tests01.json`. El costo alto de las sustituciones triangulares y del recorrido CSR motiva acelerar recorridos de ceros exactos. Se preservan conexiones, masa, puertos, LU, pivotes, Schur, refinamiento y controlador temporal.

## Transformación y puertas previas

La variante recoge índices no nulos de los factores LU reales, después de factorizar y comprobar finitud. Orden ascendente de las mismas columnas, sin umbral ni patrón de preset. Solo omite huecos de coeficientes ±0 cuando el acumulador es distinto de cero y los operandos resueltos son finitos. Si el acumulador es ±0, ejecuta los huecos originales para conservar su signo. Cada fila resuelta comprueba finitud: overflow/NaN rechazan con la misma clase; con diagonal finita no nula una fila no finita no puede recuperarse en la sustitución posterior.

CSR examina bloques de ocho entradas del Jacobiano real; solo omite el bloque si todas sus entradas comparan iguales a cero. NaN/Inf no satisfacen ese predicado y mantienen el rechazo anterior. Coeficientes no nulos, floor y orden de suma son idénticos. Se reconstruye el soporte en cada matriz; sin cache de topología, poda ni cambio de ley física.

Banco propio: 78 pares previos más 90 coarse/mid/end seleccionados de la liberación extendida, 168 pares. Cada comparación abarca 1834 f64, counters nuevos y 211138 campos de stamp. Pruebas directas de LU contra la versión densa con ±0, subnormales, RHS extremos, errores y diferentes incidencias. Seis fixtures de rechazo de la red completa. Sin relajar puertas eléctricas anteriores.

Utilidad prefijada para esta transformación limitada a dos costos parciales: mediana de cinco rondas alternadas ≤0,95 de la referencia pública; peor ronda ≤1,05. El 5 % se fija antes de medir porque las sustituciones representan aproximadamente el 10 % del costo del perfil anterior; el gate anterior de otro candidato permanece histórico. Laboratorio y biblioteca pública requieren mediciones propias. Un candidato que falla utilidad queda conservado sin promoción.

Si pasa, recorrido público pareado de 4 ms por resolución en el tramo propio 68,442→72,442 ms de `extended-release01`, con seed real de esa rejilla. Comparar cada Accepted completo, observaciones, calendario, HIGH/LOW, checkpoints y nueve balances orientados; contraste del prefijo existente. Esa igualdad permite heredar únicamente las ecuaciones seleccionadas correspondientes. No produce duración eléctrica ni WAV nuevos.

## Recursos y alcance

Reserva 1 GiB y productos privados nuevos ≤96 MiB. Compilaciones ≤120 s, banco ≤300 s, recorrido por perfil ≤850 s y proceso ≤900 s, campaña ≤1900 s. Stack de laboratorio 32 MiB, sin Cargo/cache nueva. Rechazos y fuentes se conservan, con replay sin cambios antes de reparar. Medir memoria fija del solver; no admitir heap/deadline, fidelidad física ni RT por estas comprobaciones. Prioridad posterior: duración útil con el candidato que pase todas sus puertas.
