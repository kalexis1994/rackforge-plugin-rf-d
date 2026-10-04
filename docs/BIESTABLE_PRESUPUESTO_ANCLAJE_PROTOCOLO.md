# Protocolo: presupuesto condicional del error entrante

Congelar helper, productor y protocolo antes de medir. Conservar P, norma,
anclaje ponderado común, W, tasas, kernels, conversiones y propagaciones
balanceadas por identidad. No calcular nuevas inversas, tasas o solves.
Evaluar los ocho casos; reset mantiene sus dos rechazos, sin presupuesto nuevo.

## Familia afín por celda y nodo

Reutilizar vectores de pico de la traza y mapas nodales de la métrica fija:
A_kn=sum_b gain_knb*peak_anchor_kb;
F_kn=direct_kn+sum_b gain_knb*peak_forced_kb.
Son superiores no negativos para cada una de ocho celdas y 94 filas nodales.
Reconstruir los máximos publicados por celda exactamente. Guardar 752 pares
por caso aceptado, identidad por celda/fila y SHA de la propagación.
No confundir índice de fila con número de nodo eléctrico.

Conservar el gate T=1/1000 V. Para un anclaje común entrante epsilon>=0 y
un presupuesto nodal adicional R>=0 hipotético, exigir simultáneamente
A_kn*epsilon+F_kn+R<=T. Usar aritmética racional exacta. Si F_kn+R>T en
alguna fila, la familia de majorantes es inviable incluso con epsilon=0.
Una fila con A_kn=0 y F_kn+R<=T no limita el anclaje. Si ninguna lo limita,
registrar no acotado. En otro caso, epsilon_max=min_(A_kn>0)((T-R-F_kn)/A_kn),
guardando todas las restricciones activas. Igualdad con T pasa el gate.

Comparar con la capacidad conservadora (T-R-maxF)/maxA, usando los mismos
casos y reservas. La capacidad pareada no puede ser peor cuando el límite
separado es factible. No sumar máximos de nodos distintos como si estuvieran
correlacionados. Tampoco se afirma que A y F sean magnitudes observadas o
que el máximo afín sea alcanzable físicamente.

## Reservas y pruebas fijadas

Evaluar R=0, T/4 y T/2 en todos los casos. Estas reservas son escenarios
hipotéticos del margen nodal, no cotas calculadas del resto no lineal ni
una relajación del gate. R=0 no afirma que el resto sea nulo.
Registrar presupuesto pareado, separado y todos los bindings. No seleccionar
una reserva después de medir para declarar éxito.

Contrastar familias afines fabricadas con soluciones racionales conocidas,
máximos en filas distintas, coeficiente cero, ties, margen cero e inviabilidad.
Verificar que el presupuesto satisface todas las desigualdades y cualquier
aumento positivo viola una activa. Probar monotonía con reservas y rechazo
de negativos, identidades duplicadas o datos incompletos. Reproducir los
4.512 pares archivados, máximos, capacidades, soporte, W y rechazos.
Congelar datos y tests antes de validar; preservar todos los intentos.

Este corte fija objetivos suficientes para las ventanas seleccionadas del
tangente ideal. No mide el error entrante, no prueba resto no lineal y no
convierte ventanas no contiguas en cobertura desde DC. No hay un anclaje
único real demostrado entre consultas con distintas P. La prueba global
de 1 mV, física vintage, audio y deadline permanecen abiertas.
