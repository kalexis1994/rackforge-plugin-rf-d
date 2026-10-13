# Jacobiano Radau ensamblado por cuadrantes

Antes de medir, mantener gates de utilidad/numeración del protocolo de
pivotes. [Banco/perfil](../evidence/voice_pivot_bench01.json) pasó identidad,
pero el guard de pivote no pasó costo: ratio mediano1.0308176. No promoverlo.
Tiempos anidados: initialize56.07 % de step, parts36.01 %, joint_parts27.60 %;
la diferencia initialize−parts corresponde a loops de residual/Jacobiano y
overhead/copia, no una fase pura aislada. Solver37.60 %, prepare34.39 %.

Nuevo candidato: reindexar sólo el llenado del Jacobiano458×458 en cuatro
cuadrantes229×229. Para cada(i,j,a,b), asignar exactamente
`B[i][j]*q[j].mass_over_h[a][b] + (i==j ? q[i].dc_jacobian[a][b] : 0)`
en fila i·229+a/columna j·229+b. Misma multiplicación seguida de suma,
incluido +0 en off-diagonal; ninguna reducción o umbral de sparsity. Q,
cargas, puertos, residuo, candidatos, solver, Newton y controller quedan
idénticos. No paralelizar sumas ni cambiar orden de acumulación física.

Usar mismo banco78 y5 rondas alternadas. Comparar además cada entrada
del stamp completo en todos los pares y1834 campos finales/contadores:
residuo458, Jacobiano209764 y candidatos916 f64 por caso. No interpretar
esa comparación entre implementaciones como ecuaciones independientes.
Gate de mediana≤.90 y peores rondas≤1.05, mismo gate sin relajar.
Después, sólo si pasa, campaña pareada4 ms por resolución y promoción
portable condicionada descritas en el protocolo previo. Conservar banco,
perfil y candidato de pivotes rechazado por utilidad, sin editar su recibo.
