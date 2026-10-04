# Continuación contigua: transporte validado y primer hueco preservado

## Fuentes y objetivo

Modelo nominal documental y parámetros sintéticos sin cambios.
Partir del [primer intervalo certificado](BIESTABLE_TUBO_BLOQUES_RESULTADOS.md)
y conservar su memoria saliente. [Protocolo](BIESTABLE_PREFIJO_CERTIFICADO_PROTOCOLO.md)
y [helper](../tools/loudness_latch_certified_prefix.py) se fijan en `9b59056`;
[productor corregido](../tools/loudness_latch_bdf_static_precision_certified_prefix.py),
en `590ab5e`. Datos y ocho pruebas se congelan en `207d0a7` antes de validar.

El primer lanzamiento falló al localizar el constructor DC en la cadena
de módulos, antes de calcular precondicionadores o métricas. Se conserva
su fuente exacta y SHA en el [recibo de lanzamiento](../evidence/loudness_latch_bdf_static_precision_certified_prefix_launch_attempt.json),
fijado en `2ae93e6` antes de corregir. El primer experimento numérico
completo se ejecuta con la fuente corregida; no se descarta una medición.

## Continuidad y puente de norma

El límite fijado antes de medir era ocho intervalos adicionales, con
parada en el primero sin cierre. Se intenta el segundo intervalo de la
trayectoria: **195,3125→390,625 ns**, h=195,3125 ns, clocks absolutos reales.
La historia previous del endpoint coincide con current anterior. Las
interfaces verifican 94 potenciales, 21 coordenadas lineales y cuatro
voltajes de juntura; Q(v)/S es continua con la misma ley constitutiva.
No se traslada el tiempo a cero ni se fabrica historia o reinicia DC.

Dos modos por radio: retener la métrica saliente o generar una P común
a ocho celdas del nuevo intervalo. La conversión directa certifica
alpha*P_old-P_new >0 con LDL racional y 32 bisecciones. El factor es
normal_old/normal_new*sqrt_upper(alpha). Si la norma es idéntica, el
factor es **uno exacto**, con prueba algebraica sin consulta espectral.
Los seis errores finales del anclaje y forcing anterior se suman y
se convierten a la norma entrante; sólo se transporta memoria certificada.

En el radio de 1 µV, ambas opciones tienen exactamente la misma norma
tras el redondeo fijado de P; sus puentes son identidad y sus resultados
coinciden. En 10 µV, el nuevo candidato exige factor ≈1,000000057539,
con **33 consultas LDL**. El modo retenido conserva identidad.
La cota nodal inicial usada es el pico del intervalo certificado anterior,
≤0,586 µV; es conservadora para su endpoint.

## Resultado y parada

| Radio | Métrica retenida | Nueva métrica | Resultado |
| --- | --- | --- | --- |
| 0,1 µV | Sin recinto nuevo | Sin recinto nuevo | Cota nodal entrante no cabe; rechazo previo |
| 1 µV | Presupuesto ≈7,346913 µV | Presupuesto ≈7,346913 µV | Ambos rechazan inclusión |
| 10 µV | Presupuesto ≈7,082810e283 V | Presupuesto ≈7,082734e283 V | Ambos rechazan inclusión |

Los **16 recintos medios** de los radios elegibles verifican q<1:
q máximo ≈0,05821171 para 1 µV y ≈0,58211784 para 10 µV.
Se calculan ocho precondicionadores candidatos (reutilizados entre radios),
dos candidatos de métrica y **3.168 consultas LDL** para tasas de los
cuatro modos desarrollados. No hay nuevos solves no lineales de circuito.

Ninguna variante cierra el segundo intervalo. El prefijo se detiene
allí: **un intervalo certificado total, cero adicionales**, duración
**195,3125 ns**, primer hueco en índice 1. Se conserva el endpoint
intentado 390,625 ns como alcance de experimento, sin promoverlo a error
real certificado. Los presupuestos rechazados son condicionales; no son
mediciones de error real ni prueba de inestabilidad física.

## Qué limita este intento

Para 1 µV, la parte máxima del anclaje propagado es **≈6,927618 µV**;
la de forcing, **≈0,506179 µV**. El máximo conjunto por nodo es
≈7,346913 µV (celda 7, índice nodal 21). Los máximos separados pueden
ocurrir en nodos distintos, por lo que no se suman indiscriminadamente.
El presupuesto está dominado por memoria entrante y su propagación.

El residual continuo máximo nuevo queda en **≈1,251007 nA**, inferior
al del primer soporte; las restricciones lineales son ≤1,395e-16 V.
La continuidad y el puente no añaden un salto de carga. Esta evidencia
no demuestra que el error real haya crecido: la comparación de seis
grupos asigna el máximo del grupo audio a sus 17 cargas y pierde dirección.
Es una hipótesis concreta para el [siguiente refinamiento](BIESTABLE_MEMORIA_POR_COORDENADA_PLAN.md),
no una justificación para aumentar gates o cambiar el circuito.

## Validación y artefactos

**Ocho regresiones primarias pasan al primer intento en 92,8890656 s**.
Reproducen recintos, residual, métricas y puentes; verifican relojes reales,
continuidad, selección y parada. Un sistema no lineal de solución conocida
recorre dos intervalos con cambio de norma pagado y rechaza un tubo pequeño.
Se verifican puentes identidad/escala/normalización y el lanzamiento fallido
por fuente exacta en Git. Entradas idénticas antes/después.
[Recibo primario](../evidence/loudness_latch_bdf_static_precision_certified_prefix_validation.json).

[Datos](../evidence/loudness_latch_bdf_static_precision_certified_prefix.json.gz):
**15057730 bytes**, SHA comprimido
`045043e61ed809a02956fbde67e92486ec47f393e1e13f0e15d64840b76c575b`,
canónico `3a8ba3bf9b2f8629da2140c69c7bde36ddca8e7c8e45ca167d71a4a041fc621c`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_certified_prefix_summary.json).
[Corpus ampliado](BIESTABLE_PREFIJO_CERTIFICADO_ENTRADAS.md): 484 entradas de
84 informes y trece fuentes fallidas históricas. Sus dos pruebas pasan
al primer intento en 77,4796224 s; diez regresiones nuevas aceptadas.

El primer intervalo y la evidencia anterior permanecen intactos. 1 mV
global, recorrido completo, identificación física, voz audible, motor
nativo y deadline mantienen sus gates abiertos.
