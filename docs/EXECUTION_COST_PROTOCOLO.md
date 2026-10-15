# Perfil comparable antes de elegir otra transformación

Mismos motores, ecuaciones, fuentes, semilla, dominio y gates que el
[cierre afín](AFFINE_NEWTON_RESULTADOS.md). No cambiar el motor activo.
Copias instrumentadas generadas por sustituciones exactas, conservando
los bytes de las fuentes originales. No son implementaciones de audio.

Medir una rama completa 40–100 ms a máximo 32 µs en el directo y en el
candidato afín. Timers inclusivos por función y por tramos declarados,
contadores de llamadas y errores, incluyendo replays. Separar full/J,
residual, preparación, factores, solve/refinamiento y backward. En afín,
separar además kernel, padre, binding, CSR físico, álgebra local y proyección.
No sumar padres con hijos. El solve directo incluye su preparación; el
solve afín ocurre después de preparar. Declarar ambos límites.

Los GRID/ROOT/SOLVER/AFFINE y estados finales deben ser idénticos a sus
controles admitidos o numéricamente verificados. Conservar heap cero,
replays y rechazos atómicos. Un reloj puede cambiar el costo y el inlining:
el perfil localiza trabajo, no acredita ahorro, RT o promoción.

Si surge un cambio concreto, fijar su contrato antes de implementarlo y
medirlo después sin timers frente a un directo fresco; costo ≤0,90 con
los mismos gates de trayectoria y auditoría. No relajar 1 pA/2 nV.

Fuentes por commit/ruta/SHA e imágenes de cambios; recibos ≤8 MiB sin QA.
Un solo tmp/lab-current vacío al finalizar, rustc/rlib congelados, sin Cargo,
WAV, caches nuevos o inputs privados de sonido. Fallos con fuente, entrada
y replay sin cambios antes de corregir. Tests heredados por identidad,
sin afirmar que se reejecutaron ni añadir fidelidad física.
