# Corpus del cierre de memoria por partición temporal

El [protocolo](BIESTABLE_MEMORIA_JUNTURAS_PROTOCOLO.md) y productor se congelan
en `b3d34d4`; datos, ocho tests y validator en `0b5f724` antes de validar.
El [resultado](BIESTABLE_MEMORIA_JUNTURAS_RESULTADOS.md) conserva la curva,
P, 22 memorias, reloj y radio 1 µV, control 8 rechazado y partición 16 admitida.
Las alternativas 32/64 quedan declaradas y no medidas, por primera admisión.

## Archivo por celda y soporte

Veintiséis artefactos completos: 24 celdas y dos soportes. Cada celda guarda
residual, forcing punto/L1, RHS de 119 ecuaciones, restos independientes,
acciones/métricas y tres observadores Decimal100. Cada soporte guarda sus
kernels, cierre, memorias y diagnóstico de 22 términos por nodo observado.
Se identifican rutas tipadas, tamaño y SHA comprimido/canónico.

El lanzamiento guarda comando, fuente UTF-8 exacta, salidas, exit=0 y
snapshots idénticos; fuente recuperada desde Git. 548 entradas identificadas
antes de medir. Los archivos parciales no admiten tiempo. El productor
no se repite y todos los datos, helpers y gates anteriores se conservan.

## Reproducción primaria

**Ocho pruebas pasan al primer intento en 309.2078673 s**, snapshots idénticos.
Reconstruyen fuente real elegida, curvas, ledger, dominio e inversa por SHA;
reproducen candidato binary64 y las tres tasas con sus 99 probes LDL.
Verifican que el bloque certificado aplica a la misma curva y tubo en P fija.

Los 24 budgets y 192 subcertificados se reproducen con helper preparado,
control original y archivo, idénticos en todos los bytes canónicos. En el
control 8, RHS/forcing/acciones/métricas también coinciden con la rama
histórica de ancho 1; el cierre se recalcula con otra memoria entrante,
la fuente realmente elegida. No se exige el pico del anclaje anterior.

Las 72 consultas Decimal100 archivadas reconstruyen RHS y restos en el
reloj físico. Cada duración h/n se contrasta sin cambiar h dentro de la
curva. Se verifican interfaces, cada cierre, selección y transporte real
de 22 memorias; el control rechazado no restaura una salida admitida.
El diagnóstico recompone racionalmente nodo 66 como suma de 22 ganancias×
memorias más directo, sin cancelar restos ni atribuir causa física.

Un control exacto con generador cero conserva anclaje, forzamiento total,
memoria final y pico en las particiones 8/16/32/64. Rechaza una partición
incompleta. Otros negativos cubren duración antes de aplicar forcing,
proveedor incompleto, fuente/curva/radio/reloj, recinto/inversa/contexto,
ruta, tipo, índice y hashes alterados. Se mantiene el dominio del kernel.

[Recibo primario](../evidence/loudness_latch_bdf_static_precision_junction_memory_refinement_validation.json)
y [lanzamiento](../evidence/loudness_latch_bdf_static_precision_junction_memory_refinement_launch.json).

## Corpus ampliado

Recibo primario y fuentes archivísticas congelados en `dec395e` antes de
generar. Archivo y resumen congelados en `3a351ca` antes de validar.
Se recuperan **763 entradas de 214 informes**, con **259 hashes propios**,
214 informes y 45 helpers. Se conservan las tres excepciones históricas
LF→CRLF y **20 fuentes históricas**, diecinueve fallidas y una interrumpida.

El fallo propio del corpus anterior, expectativa del nombre de resumen,
se integra ahora al archivo con su fuente exacta, SHA, comando, recibo e
intento. Su versión corregida se recupera desde el blob correspondiente;
no se reescribe ningún recibo histórico ni se borra un intento.

**Dos pruebas pasan al primer intento en 97.6950724 s**, snapshots idénticos.
Recuperan todos los blobs y fuentes históricas, identidades de las celdas,
soportes y fuentes actuales, y rechazan bytes o transformaciones alterados.
Son **diez pruebas nuevas aceptadas**, ambas suites al primero. No hay
fallos nuevos, repetición del productor o cambios de gates. Python y sus
hijos usan -B; no se generan cachés en el repo.

[Archivo](../evidence/loudness_latch_bdf_static_precision_junction_memory_refinement_inputs.json.gz),
[resumen](../evidence/loudness_latch_bdf_static_precision_junction_memory_refinement_inputs_summary.json)
y [recibo](../evidence/loudness_latch_bdf_static_precision_junction_memory_refinement_inputs_validation.json).
Archivo: **500661 bytes**, SHA comprimido
`d954980e8ba85d7c825bf0641d0e1fbad959b0bf30559abe4cfaf559b77c5d16`;
canónico `9e27e30e3da2789a64ecbcb7077a5256f80da920117685acb81ec5db615e72d2`.

Se admiten 34 soportes hasta ≈350 µs, local nuevo ≤0,644 µV y acumulado
≤0,793 µV. No se certifica el soporte siguiente ni se hereda un benchmark.
1 mV global, cobertura completa, identificación física, sonido vintage,
voz, audio y deadline siguen abiertos. Próximo:
[continuación refinada 34–39](BIESTABLE_CONTINUACION_REFINADA_PLAN.md).
