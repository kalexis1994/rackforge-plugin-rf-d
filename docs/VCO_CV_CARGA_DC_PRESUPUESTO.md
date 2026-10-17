# Selección del presupuesto OP

El diagnóstico DC conserva dos decks derivados de los fallos anteriores:
OP directo con semilla analítica y sweep de .01 V con raíz SPICE previa.
Sólo añade itl1=itl2=1000. Ambos resuelven el extremo fallido y pasan los
mismos límites 2e-7 V/2e-10 A; no se cambian tolerancias o leyes físicas.

Seleccionar OP directo con nodeset analítico para los doce puntos y ese
presupuesto. Retirar la continuación de la ruta seleccionada: se conserva
como intento fallido/diagnóstico, no como nueva curva admitida. El límite
de 180 s por proceso permanece; no trasladar este presupuesto al Newton
nativo ni modificar escenarios transitorios. El análisis Decimal y los
contrastes de todas las raíces siguen obligatorios. Compartir una semilla
no demuestra unicidad ni fidelidad al hardware.
