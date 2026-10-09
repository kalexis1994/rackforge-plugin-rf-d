# Refinamiento de la perturbación de cargas

2026-10-09. Continuación del
[protocolo original](VOZ_CARGAS_RESPUESTA_PROTOCOLO.md).
Se conserva el [rechazo y replay independiente](../evidence/voice_joint_charge_response_reference01.json),
su fuente íntegra y la [medición original](../evidence/voice_joint_charge_response_native01.json).

La comparación central a ±1 mV supera el gate en fila 215, columna 6:
ratio 7,1707132154. No atribuir todavía una causa a la discrepancia.
La hipótesis es error de truncación de la diferencia central, contrastado
al reducir la perturbación sin cambiar las tolerancias.

Nueva pareja ±125 µV y ±62,5 µV en cada una de las 18 restricciones,
para cada memoria. Mantener los mismos gates eléctricos y de respuesta,
solver, fase, controles, circuito, biblioteca y recursos. Caller nuevo:
solo cambiar la pareja de perturbaciones del caller original por bytes.
146 raíces, 36 columnas de respuesta; reproducir ambas raíces originales.

El checker nuevo conserva la implementación original excepto la pareja
de perturbaciones, los nombres de fuentes/recibos y una aclaración de
unidades en el reporte de refinamiento central. Reportar por separado
el máximo de filas de tensión en V/V y de corriente en A/V; el campo del
primer checker mezclaba tipos de coordenadas. No cambiar ningún gate.
El primer reporte fallido no alcanzó a publicar ese campo.

Además, comparar ambas diferencias centrales del banco original con la
misma matriz de tangentes sin exigir su gate ya rechazado. Publicar las
discrepancias y la variación con h. Un refinamiento que no pasa conserva
el rechazo; no ampliar tolerancias ni llamar periódico a S.
La predicción estática sigue pendiente de cierre y ciclos propios.
