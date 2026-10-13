# Confirmar la medición antes del recorrido

2026-10-13, antes de repetir. El benchmark de extensión pasa84 pares por
bits y tiene mediana1.0811×, pero el wall de la referencia varía de3.743
a1.269 s dentro del mismo proceso. Esa variación justifica una segunda
medición con el mismo ejecutable, datos, warmup y cinco rondas alternadas.
No modificar código, tolerancias ni campos. Registrar ejecutable y datos
por SHA. Exigir también mediana>1 en la confirmación antes de seleccionar
la variante para los cuatro perfiles. Conservar ambas mediciones y sus
rangos; no sumar cocientes de campañas históricas como benchmark pareado.
Límite300 s. Esta repetición resuelve incertidumbre de costo, no añade
casos independientes de física ni evidencia RT.
