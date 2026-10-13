# Invariante finita de sustitución, antes del último banco de este bloque

2026-10-13. Soporte de fronteras con cuatro comprobaciones por producto
no pasa utilidad (mediana0.914858×). Preservar su traza exacta y benchmark.
Acotar el experimento: ensayar esta variante y consolidar los resultados,
sin añadir otras intervenciones de costo en este bloque.

Partir de nuevo del solver estable previo, sin directivas de constructores
ni cambio de validación de fronteras. En Lu::solve, comprobar al cerrar
cada fila que el valor obtenido es finito. En la sustitución hacia atrás,
comprobar después de dividir. Rechazar SingularJacobian si falla.
Así los valores x[col] ya calculados usados por la próxima fila son finitos.

Omitir un producto por coeficiente exactamente cero sólo si el acumulador
es distinto de cero. Cuando el acumulador es finito, restar cualquier cero
con signo conserva sus bits. Si es ±0, ejecutar la operación original.
Si se vuelve no finito dentro de una fila, no puede volver a un valor finito
mediante las restas y división por un diagonal finito: rechazar al cerrar
esa fila. La variante anterior también rechazaba, al observar el vector
final no finito. Esta equivalencia necesita controles de overflow,
NaN/Inf y ceros con signo; no se afirma como regla para otros algoritmos.

Se trasladan comprobaciones del producto al cierre de fila; no se cambia
el orden de los productos ejecutados ni se usan umbrales. Mantener también
el check final existente. Factores, pivotes, puertos, masa, historia,
capacidad4096, refinamientos y gate1e-11 permanecen iguales.
Exigir toda la traza por bytes,84 raíces, doce regresiones de estructura
y nueve casos de sustitución frente al Lu::solve anterior. Benchmark y
confirmación siguen el contrato de costo. La admisión temporal queda fuera
de este experimento acotado, aun si pasa utilidad.
