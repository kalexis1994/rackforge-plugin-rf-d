# Memoria por coordenada y segundo intervalo certificado

## Fuentes y alcance

Mismo modelo nominal documental CA3046 y parámetros sintéticos.
[Protocolo](BIESTABLE_MEMORIA_COORDENADA_PROTOCOLO.md),
[helper](../tools/loudness_latch_coordinate_memory.py) y
[productor](../tools/loudness_latch_bdf_static_precision_coordinate_memory.py)
se congelan en `1b513d8`; datos, ocho pruebas y validator en `ff4006d`,
antes de validar. Se reutilizan **24 inversas exteriores** con certificado
completo y SHA: ocho del primer soporte certificado y dieciséis del
segundo intento previo. También se ligan por SHA las cotas de tasa de
junturas correspondientes. No hay nuevos solves, precondicionadores,
métricas o consultas LDL de tasa; la reconstrucción y residual no cambian.

## Refinamiento con soporte realmente probado

Para las 21 cargas lineales se propaga cada error inicial ponderado con
su diagonal firmada y forcing L1. Los acoplamientos desde las demás cargas
se cubren con los picos del primer intervalo **ya certificado**; las
junturas usan las conversiones duales de P^-1. No se usa el segundo
intervalo rechazado como prueba del anclaje entrante.

Cada celda da una cota escalar exterior de endpoint. Se intersecta con
la cota original del grupo sólo porque ambas describen el mismo error
en la misma norma. Se conservan bruto, original, mínimo, kernels y todos
los términos de inyección. Son **168 refinamientos** (21×8).
Las junturas conservan su cota cuadrática original.

**16 de 21 coordenadas lineales mejoran**. El grupo audio anterior daba
≈2,935804 nV para cada uno de sus 17 miembros; las coordenadas 0..13 y 15
quedan en aproximadamente 0,074..0,150 nV, la 16 en ≈0,02505 nV.
La 14 conserva su cota anterior. C10/C2/C4/C7 y la norma de junturas
no mejoran por este refinamiento; se conserva su valor conocido.

## Partición de 22 grupos y banco completo

Las 21 coordenadas lineales son grupos individuales; las cuatro junturas
forman un único grupo cuadrático con la **misma P y normalización**.
Se recalculan todos los acoplamientos, forcing L1 y ganancias nodales
para esta partición, manteniendo diagonales firmadas y normas duales.

Dos entradas por radio, en orden fijado antes de medir: anclaje agrupado
anterior levantado a 22 grupos; anclaje refinado por coordenada. Ambas
usan exactamente las mismas métricas finas, inversas, residual y P.

| Radio | Anclaje anterior, 22 grupos | Anclaje refinado, 22 grupos | Cierre |
| --- | --- | --- | --- |
| 0,1 µV | Sin comparación nueva | Sin comparación nueva | Cota nodal entrante no cabe |
| 1 µV | Presupuesto ≈0,587002 µV | Presupuesto total ≈0,585674 µV | Ambos aceptan |
| 10 µV | Presupuesto ≈1,336461e263 V | Presupuesto ≈1,300501e263 V | Ambos rechazan |

El orden selecciona **[1 µV, anclaje anterior]**, no el resultado más
pequeño observado después. Su cota exterior publicada redondeada hacia
arriba es **≤0,588 µV**. Cierra el segundo soporte **195,3125→390,625 ns**
y su unión con el primero: **dos intervalos contiguos certificados**, desde
t=0+ hasta **390,625 ns**. No se extrapola más allá de ese endpoint.

La partición fina permite cerrar aun con la entrada agrupada anterior:
el presupuesto de seis grupos era ≈7,346913 µV sobre el mismo radio.
Por tanto el cambio de comparación, sin cambiar circuito, anclaje, norma
ni residual, resuelve el hueco de este corte. El refinamiento saliente
aporta una mejora adicional, pero no era necesario para este cierre.

## Anclaje y forcing: qué cambia

En 1 µV, la parte máxima del anclaje es ≈0,585036 µV con entrada agrupada
y ≈0,0314013 µV con entrada refinada; el forcing permanece idéntico,
≈0,502006 µV. Los picos se suman por nodo antes de maximizar, no como
máximos independientes de nodos distintos.

El presupuesto **local** del segundo soporte refinado es ≈0,502270 µV
(celda 7, nodo índice 28); al incluir el pico nodal entrante del primer
certificado, su presupuesto **total** es ≈0,585674 µV. Esa distinción
explica por qué el refinamiento reduce mucho el anclaje, mientras el
máximo global de ambos soportes cambia poco.

Ambos modos aceptados publican 22 cotas de memoria final en sus normas.
El modo refinado conserva la dirección y será un soporte explícito del
[siguiente intento de prefijo](BIESTABLE_PREFIJO_22_GRUPOS_PLAN.md). Su uso
futuro no cambia la selección primaria ya archivada de este experimento.
No reiniciar DC ni intercambiar memorias de normas distintas sin puente.

## Validación y evidencia

**Ocho regresiones primarias pasan al primer intento en 104,4604078 s**:
reconstrucción de 24 inversas; identidad de cotas de tasa y P^-1;
168 refinamientos y perfiles conocidos; métricas completas de 22 grupos;
solución escalar analítica; conversiones duales manufacturadas; sucesión
no lineal conocida, anclaje anisótropo y forcing tardío; reproducción de
propagación, cierres y selección. Fuentes idénticas antes y después.
[Recibo](../evidence/loudness_latch_bdf_static_precision_coordinate_memory_validation.json).

[Datos](../evidence/loudness_latch_bdf_static_precision_coordinate_memory.json.gz):
**14487594 bytes**, SHA comprimido
`6553b5d2ed93b49591494f26db8605dab458f5bdb0bff74cc69a9532dbd2ca8d`,
canónico `1fc8f003a87264ffd3423da870c46e2b2373975b4eaa3a1b8c8719c996752e2a`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_coordinate_memory_summary.json).
[Corpus ampliado](BIESTABLE_MEMORIA_COORDENADA_ENTRADAS.md): 495 entradas
de 86 informes y trece versiones fallidas históricas; sus dos pruebas
pasan al primer intento en 79,6181683 s. Diez pruebas nuevas aceptadas
en total, sin cambiar fuentes o datos para obtener el resultado.

Los presupuestos de 10 µV siguen siendo comparaciones condicionales,
no errores reales certificados. Este avance prueba precisión del modelo
nominal; 1 mV global, trayectoria completa, identificación física, audio,
motor nativo y deadline mantienen sus gates separados.
