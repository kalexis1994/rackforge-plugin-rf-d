# Segunda propuesta: extensión contigua del pivote

Antes de medición, 2026-10-13. La lista indexada de soporte pasa84 pares
por bits, pero su benchmark tiene variación que domina la pequeña mejora
mediana del wall. Se conserva el intento, sus fuentes y recibos.

Probar un recorrido contiguo desde col+1 hasta la última columna no nula
del pivote actual. Se omiten sólo ceros finales, sin patrón estático de
fill-in. Separar mediante split_at_mut la fila pivote de las posteriores;
zip de slices conserva el orden de cada producto/resta y permite al
compilador tratar las filas como disjuntas. Mantener búsqueda, escalas,
umbral, factor, RHS y sustitución hacia atrás. Sin unsafe, heap o nuevo
parámetro físico. No prometer equivalencia universal de ceros con signo.

Mismos84 pares, cinco rondas alternadas, criterios por bits y mediana>1
del protocolo anterior. La comparación pareada de esta segunda propuesta
usa como referencia el kernel de reuso444a962, no el intento indexado.
Sólo la variante elegida repetirá los cuatro recorridos completos.
Regresiones de solver y conteo de actualizaciones en fase diagnóstica
separada. Mismos budgets, tolerancias y límites de alcance del
[protocolo original](LU_SOPORTE_PROTOCOLO.md).
