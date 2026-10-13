# Validar conexiones desde el soporte sparse real

Antes de medir. El Jacobiano por cuadrantes pasa identidad y utilidad en el
laboratorio, pero [su biblioteca pública](../evidence/voice_block_library01.json)
sólo mejora7.04 % y no cumple10 %. Conservar código/biblioteca/banco de esa
versión; no admitirla por el resultado de otra forma de compilación.

Prepared ya recorre toda la matriz para construir CSR, validar finitud,
capacidad4096 y floor original. Después vuelve a recorrer filas/columnas
densas para verificar que interiores sólo conectan al mismo bloque o sus
puertos. Nuevo candidato sustituye sólo ese segundo recorrido por todas
las entradas CSR no nulas, con masks OWNER y ALLOWED derivadas de los mismos
INNER/PORTS/CONTOUR/CHAIN/EXTERNAL. Verificar ambas incidencias de cada arista:
OWNER[fila] & !ALLOWED[columna] y OWNER[columna] & !ALLOWED[fila].

No asumir un patrón de presets o cache entre matrices. CSR se reconstruye
de J real en cada preparación; cero exacto tiene la misma definición que
antes, sin umbral. Las masks incluyen ambos stages y todos los puertos
compartidos. Validación de matriz no finita/RHS, capacidad, LU, Schur,
corrección, refinamiento y gates se mantienen. No cambiar ecuaciones,
coefficients, cargas, pivotes, estructura o uso de memoria dinámica.

Mismos78 pares/16.5M entradas y5 rondas, gates≤.90 de medianas y≤1.05 peor
ronda. Agregar auditor de política sobre todas209764 posiciones: predicado
denso original y masks deben coincidir exactamente para una arista presente;
incluir prueba de la dirección entrante y saliente, puertos compartidos y
exterior/interior. Es política estructural, no nuevo solve independiente.
Sólo si pasa en la biblioteca pública, comparación portable completa4 ms
por resolución. Gates numéricos intactos; no reusar un tiempo de laboratorio
para admitir costo portable o deadlines. Alcances finitos y fallos preservados.
