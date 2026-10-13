# Contraste directo de correcciones, memorias y retornos

Previo al diagnóstico, 2026-10-13. Usar84 pares del mismo packet y
ejecutar el solve completo sobre exactamente cada J/b que recibe Schur
en esos pasos. No incluir esa doble resolución ni logging en el benchmark.
Gates ya declarados:2 nV/2 pA para458 correcciones y backward error1e-11.

En las dos candidatas de cada par, observar ambos LM741 mediante la
API original: cinco memorias y seis corrientes (cinco terminales más
retorno explícito a suelo). Comparar con el solve completo del mismo
paso:4 µV para diferencias de dos nodos de memoria capacitiva (derivadas
del gate2 µV/nodo);2 nA para cada corriente inductiva;20 pA para cada
corriente de terminal/suelo. No confundir la evaluación DC de corrientes
terminales con un solve DC: las candidatas vienen del Radau dinámico.
La memoria y el almacenamiento interior permanecen en el sistema completo.
El diagnóstico compara la misma ley, no es otro oráculo físico; el grafo
Decimal100 contrasta por separado las84 raíces reconstruidas.
Guardar la historia completa en los archivos de raíces y en checkpoints.
