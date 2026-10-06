# Preparación del refinamiento lineal

2026-10-06. Complementa el [protocolo previo](NEWTON_REFINAMIENTO_LINEAL_PROTOCOLO.md)
sin cambiar sus tres correcciones, NIconvTest, historia o gates eléctricos.

Build07 conserva la primera preparación y compilación, sin runs SPICE.
Su harness aritmético inicial rechazó al compilar sin el PATH UCRT64; el
helper y log original se conservan. El segundo suministra ese PATH y prueba
el mismo header/flags. Build08 copia build06 y añade un replay de laboratorio
a la misma variante; build07 no se reutiliza ni elimina.

El producto FMA acepta operandos cero o con magnitud en [2^-400,2^400].
Este dominio mantiene producto y error exacto por encima del underflow y
por debajo del overflow. La suma de pares sigue siendo una aproximación
de dos palabras, contrastada con datos binary64 exactos a 160 dígitos.
Se verifican finitud, dimensiones y que SMPsolve no cambia los bytes de A.
Fuera del dominio se informa error, sin saturar ni volver silenciosamente
al solver anterior. El código no introduce un parámetro físico.

Se reserva scratch por solve en esta ruta de laboratorio; no es RT. A
efectivo se copia tras factorizar y antes de SMPsolve: KLU conserva Ax;
la observación anterior captura los mismos valores antes de factorizar.
El residual usa Ax/b originales y x como par de doubles. Las correcciones
usan SMPsolve sobre un RHS temporal y los mismos factores del solve real.
No hay cargas de dispositivo o NIintegrate adicionales.

Orden congelado: dos runs apagados exactos, replay BUS variable exacto,
control activo completo y, sólo si pasa, BUS variable activo. El replay
se habilita con `RF_D_REFINE_REPLAY=1` y `RF_D_MATRIX_TRACE=1`, sólo para
las iteraciones 100/101 ya seleccionadas. Ejecuta tres correcciones sobre
los factores reales y registra r/dx/x, pero publica el solve original.
El resultado final se contrasta con la raíz precisa de **la misma matriz**;
no se usa un LU distinto como precondicionador. Si falla identidad o el
contraste por las escalas diagnósticas del protocolo, no activar la variante.

Antes de medir, fijar 600 s de presupuesto de proceso en un runner separado,
idéntico al de 240 s salvo ese timeout. Se prevé el costo de tres backsolves
y residual por cada solve. No aumenta itl4, reltol, abstol, vntol, gmin o paso.
Conservar timeout como fallo de cobertura, separado de aborto numérico.
Todos los flags anteriores quedan desactivados fuera de su run declarado.
