# Corrección del presupuesto de norma integrada

La primera consulta Neumann certifica las ocho inversas de H levantada.
Su presupuesto de Gronwall usó max_i integral |f_i| como si encerrara
integral max_i |f_i|. Esa desigualdad es falsa: dos filas activas en mitades
disjuntas pueden tener integrales 1 cada una y norma integrada 2.
Las ocho cotas uniformes de memoria/voltaje de ese informe son inválidas;
se conservan como intento fallido. Sus certificados de inversa, medida
logarítmica, presupuesto por fila y forzamiento puntual permanecen válidos.

Se declara antes de medir el reemplazo común para los ocho casos:
`integral ||f||inf <= sum_j max_i |Fr_ij| L1(r_j)
                    + sum_j max_i |Fd_ij| L1(d_j)`.
El máximo de columnas está sobre las 25 tasas de memoria; suma ambas
familias de forzamiento con sus unidades. Encerrar primero cada entrada con
la prueba de Neumann anterior. No resolver matrices nuevas ni cambiar H,
X, escalas, datos, medidas logarítmicas, exponentes, tolerancias o gates.
Gronwall usa este presupuesto agregado y su mismo coeficiente de anclaje.
Conservar el máximo de integrales por fila como diagnóstico, explícitamente
inapto para esa cota uniforme, y el motivo de rechazo de las cotas anteriores.

Tres regresiones nuevas: contraejemplo temporal racional con soportes
disjuntos, presupuesto RC independiente, replay de los ocho presupuestos y
fuentes/bytes/scope. La suite original se conserva: no detectó este error
matemático. Un test passing no sustituye derivación. Continúan pendientes
matriz ideal, variación temporal, resto no lineal, anclaje y cobertura.
