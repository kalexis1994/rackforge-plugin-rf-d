# Primer tubo no lineal: reconstrucción y resultados

## Alcance y fuentes congeladas

Modelo nominal documental CA3046 y parámetros sintéticos del laboratorio.
El [protocolo](BIESTABLE_PRIMER_TUBO_PROTOCOLO.md),
[helper](../tools/loudness_latch_startup_tube.py) y
[productor](../tools/loudness_latch_bdf_static_precision_startup_tube.py)
se congelan en `fbc5de1`; datos, suite y validator en `cf6b215`.
Se usan dos estados reales del arranque publicado, separados por
**195,3125 ns**: origen derecho de KEY y primer endpoint. No hay solves
no lineales nuevos; ocho inversas binary64 candidatas se reutilizan en
los tres radios. Sus defectos se incluyen en la prueba ideal.

## Reconstrucción y anclaje

94 potenciales y 21 coordenadas lineales son afines entre estados high+low.
En las cuatro junturas la memoria es **Q(v_afín)/S**, con tasa C(v)*v'.
Los cuatro polinomios cero internos evitan duplicar el sello dinámico;
no describen cargas físicas nulas. Las discrepancias con Q almacenada
pueden reconstruirse del soporte ligado por hash y de la ley constitutiva;
el arranque anterior conserva además su diagnóstico independiente:
`rows[0].independent_discrete.decimal100_junction_coordinate_mismatch_upper_v`
vale **14,535 pV** en ese endpoint. Ese campo pertenece al
[soporte original](../evidence/loudness_latch_bdf_static_precision_post_key_startup.json.gz)
ligado por hash; no se sustituye la trayectoria Q(v) por Q almacenada.

El anclaje inicial incluye la discrepancia constitutiva y la caja de cargas
DC. Su cota ponderada es **147,953 pV**. Los pesos son idénticos al DC:
21 unos y 1/8, 1/4, 1/256, 1/512; conversión de norma **uno**. El evento
publicado aporta también su cota nodal inicial de **37,505 nV**.
No se importan anclajes de ventanas históricas de otra trayectoria.

## Inversas aceptadas, tubos rechazados

Cada radio tiene ocho celdas. Los recintos inflados cubren el descriptor
medio entre reconstrucción y raíz ideal, incluyendo exponentes y
capacitancias. Escala de tasas del descriptor: **2^-30 s**. Los **24/24**
recintos verifican q<1 y encierran las inversas ideales de 119 columnas.

| Radio potencial | Máximo q | Superior de norma logarítmica /s | Presupuesto nodal condicional | Cierre |
| --- | --- | --- | --- | --- |
| 0,1 µV | 0,00582117 | 7,64502e7 | 0,391133 V | Rechazado |
| 1 µV | 0,0582117 | 8,13597e7 | 1,028715 V | Rechazado |
| 10 µV | 0,582118 | 1,58901e9 | 6,33492e128 V | Rechazado |

En el primer radio, 0,089308 V proceden del anclaje propagado y
0,301825 V del forzamiento. La comparación escalar ponderada crece
demasiado para quedar estrictamente dentro del tubo supuesto.
**Estos presupuestos no son errores reales certificados.** Un superior
positivo de norma logarítmica tampoco demuestra inestabilidad del circuito.
La duración de error continuo certificado sigue siendo **cero**.

El residual continuo máximo encerrado es **1,876535 nA**; las restricciones
lineales alcanzan **2,006e-16 V**. El interpolante continuo no tiene el mismo
residual que los endpoints BDF aceptados con KCL de 10 pA. Las exponenciales
usan grado seis y resto exterior, con ocho subceldas internas por celda;
las tasas constitutivas se encierran por monotonía antes de sellar.
Cinco consultas Decimal80/100 son diagnósticos, nunca certificados exteriores.

## Validación y trazabilidad

La suite reproduce residual, anclaje, los 24 recintos, inversas y métricas;
contrasta un descriptor puntual independiente y un ejemplo no lineal
con solución conocida que acepta un tubo suficiente y rechaza uno pequeño.
Las ocho regresiones pasan en el cuarto intento (**73,596331 s**), con
entradas idénticas antes y después en los cuatro intentos. Los intentos se conservan en el [recibo primario](../evidence/loudness_latch_bdf_static_precision_startup_tube_validation.json).

El primer fallo comparaba una consulta Decimal redondeada con una cota
racional exacta en el nodo 61. El segundo guard de la prueba omitía su
carga lineal. El tercer fallo extendió el mismo problema a la conversión de restricciones.
Las tres fuentes fallidas quedan archivadas antes de corregir.
La prueba vigente verifica KCL racional exacta de resistencia y carga,
y reproduce aparte la aritmética Decimal con su cancelación; las restricciones
se cotejan racionalmente y su conversión se verifica por separado. No se
cambian datos, helper, protocolo, parámetros ni gates por esos fallos.
El núcleo de propagación conserva sus etiquetas de comparación condicional;
el wrapper exige además el anclaje conocido y el cierre no lineal estricto.
Los tres wrappers reales rechazan la promoción.

[Datos](../evidence/loudness_latch_bdf_static_precision_startup_tube.json.gz):
9178830 bytes, SHA comprimido
`b7c9028e2f8a6b4ed5d4e6bdbff0f85d0c58174e5f76bd3dd04992ce4e56a11b`,
canónico `5d13b556c8d08261ffcd21485833cb2b3731ad9640499e1700619dfad909465e`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_startup_tube_summary.json).

Las diez regresiones nuevas están aceptadas: ocho primarias y dos de corpus.
El [corpus ampliado](BIESTABLE_PRIMER_TUBO_ENTRADAS.md) conserva todas las
versiones e identidades. Próximo experimento: [comparación por bloques](BIESTABLE_PRIMER_TUBO_BLOQUES_PLAN.md).
1 mV global, identificación física, voz audible, motor nativo y deadline
siguen abiertos y separados de este resultado numérico.
