# Auditoría de retornos de VCO1

Fecha: 2026-10-05. Fuentes primarias: SVC-9 Fig. 9-3 PDF p. 5 y
SVC-204D Fig. 9-3 PDF p. 61, ambas revisadas visualmente con detalle de
los símbolos, uniones y ambas barras inferiores. No se modifican valores.

| Elemento | Lectura anterior | Lectura cotejada |
| --- | --- | --- |
| R14, extremo inferior | 9B | -10 V |
| R29, extremo inferior | 9B | -10 V |
| R23, extremo inferior | 9B | -10 V |
| R44, extremo inferior | 9B | -10 V |
| R35, extremo inferior | 9B | -10 V |
| Q12, emisor | 9B | -10 V |
| Q2, base | Q3; corrección intermedia a reset | Q3 / SCHMITT_DRIVE |

La barra superior de los dos trazos inferiores viene de -10 V y tiene
puntos en los retornos de los formadores. La inferior termina en 9B.
R34 cruza -10 V sin punto y continúa hasta 9B; R33 cruza -10 V y tiene
su punto en 9B. El panel conserva su puente de 57 kohm 9B–21B.
R23 es un retorno a -10 V, no otro puente.

El primer solve, commit 9e3dee9, produjo oscilación pero un triángulo
7.8–8.8 V. Fue rechazado por topología. Su [recibo original](../evidence/vco1_circuit_rejected_q2.json)
conserva también el primer diagnóstico de Q2, que luego fue refutado:
ese texto es historial, no la conclusión vigente.
La corrección intermedia de Q2, commit 593e0a0, también se rechazó:
[recibo](../evidence/vco1_circuit_rejected_intermediate.json). El trazado
completo establece los seis retornos anteriores y restaura la base real.
Los hashes y las trazas originales permanecen sin reescritura.

Los tests previos sólo contrastaban código con la misma transcripción
incorrecta. Se corrigen grafo, helpers, documentos y pruebas de retornos.
El contraste funcional de amplitud/forma complementa la revisión de
nodos; nunca sustituye ésta ajustando parámetros para forzar el resultado.
