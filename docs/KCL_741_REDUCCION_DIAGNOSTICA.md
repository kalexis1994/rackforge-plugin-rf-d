# Reducción de tres ecuaciones con controles fijados

2026-10-06. Postproceso declarado antes de analizar el banco con alias corregido.
No ejecuta un circuito nuevo ni cambia el solver. Conservar los registros
completos del [protocolo KCL](KCL_741_RESET_PROTOCOLO.md).

Fijar solamente para este diagnóstico `v98`, `v3`, `v49`, `req`, `veq`,
`gR` y `gm` a los valores observados de un solve. Las tres ecuaciones
lineales L2/R13/G4 dan `i*=-gm*(v3-v49)`,
`v17*=v98-req*i*-veq`, `v16*=v17*-i*/gR`.
Con `rL=v98-v17-req*i-veq` y `r17=gR*(v17-v16)-i`, se cumple:

`v16-v16* = -(req+1/gR)*(i+gm*(v3-v49)) - rL - r17/gR`.

Reconstruir esa identidad con Fraction desde los valores binary64 exactos;
exigir igualdad racional en cada registro. Separar las tres contribuciones
y el máximo en ventana/último intento. Verificar orientación y una raíz
exacta mediante casos escalares independientes antes del banco.

La reducción fija entradas que la red completa puede cambiar. Su brecha no
es un error de la solución acoplada, una cota de convergencia, ni una causa
demostrada del reset. Sirve para cuantificar la amplificación de pequeños
residuales de corriente hacia voltajes. Cualquier reformulación efectiva
del macromodelo necesita otro protocolo, historia/DC y los gates completos.
