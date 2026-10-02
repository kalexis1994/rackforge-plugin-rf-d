# Consulta independiente de certificado del descriptor

Se declara antes de medir las ocho inversas redondeadas archivadas de la ruta
racional exacta. La eliminación verifica residual racional cero; Decimal80
backward ronda 1e-16, pero el cálculo de residual binary64 por matmul devuelve
aproximadamente 1e-4. El gate de esa inversa redondeada continúa fallido: no
se sustituye su evaluación ni se admite una optimización o un mapa numérico.

Esta consulta aplica la prueba racional de Neumann ya declarada a las mismas
H y X. Su resultado prueba existencia y un recinto de la inversa de H levantada,
independientemente de la evaluación binary64 rechazada. Se archivan ambas
identidades, el fallo y un testigo del peor backward binary64: fila, columna,
productos y residual/denominador racionales exactos de esa H*X.
La prueba usa I-X*H y escalas; el testigo usa I-H*X. No confundir los dos.
Se consultan todos los casos, sin seleccionar por resultado ni relajar gates.

Se aplica el presupuesto Gronwall del modelo lineal congelado sólo si q<1.
El coeficiente del anclaje desconocido queda explícito. Una cota enorme también
se publica; dominio exponencial >4096 se conserva como bloqueo.
No se identifican el operador ideal, variación temporal ni restos no lineales.
La [derivación continua](BIESTABLE_DESCRIPTOR_CONTINUO_PROTOCOLO.md) mantiene
el alcance de esta prueba. Los dos informes fallidos anteriores son entradas
inmutables de la nueva consulta. No se resuelve de nuevo ninguna matriz.
