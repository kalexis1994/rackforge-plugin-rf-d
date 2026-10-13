# Soporte exacto del residuo, antes del segundo banco

2026-10-13. La variante densa pasa396 sistemas y181368 filas nuevas
con Decimal100, pero su mediana pareada0.908267× no admite utilidad.
Preservar código, métricas, replay y archivo de J/b/correcciones.

Construir una lista de entradas exactamente distintas de cero de cada J,
en orden creciente de fila/columna. Reusar valores, índices y escalas de
fila para cada evaluación del residuo. No umbral, patrón estimado o
truncamiento; seguir observando el Jacobiano completo antes de factorizar.
La lista evita barrer458×458 en cada evaluación y la duplicación de los
recorridos iniciales de finitud/escala. Mantener las operaciones de cada
coeficiente no nulo y el mismo orden de sumas, mul_add, factores y solves.

Capacidad fija4096 entradas, dominio de este laboratorio229. Se observaron
2240 como máximo en396 sistemas; eso no prueba un límite universal.
Si se excede capacidad, rechazar InvalidInput antes de factorizar: jamás
truncar la red. Sin heap nuevo en el solver. Probar el rechazo por capacidad
y conservar dominio y límite explícitos antes de extender la topología.

Exigir identidad por bytes de84 raíces y de toda la traza sparse de
396 J/b/correcciones frente a la variante densa, incluidos rhs y referencia
refinada. Verificar gates Decimal100 o heredar sólo por identidad completa
de esa traza, declarando la herencia. Cinco rondas pareadas con mediana>1,
sin logging o exportación del diagnóstico dentro del timing.
No cambiar el presupuesto de tres refinamientos ni el gate1e-11.
