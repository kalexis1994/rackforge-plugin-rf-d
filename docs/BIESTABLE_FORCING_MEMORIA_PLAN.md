# Próximo bloque: forcing de C7 y registro de cotas enormes

El [prefijo dirigido](BIESTABLE_PREFIJO_DIRIGIDO_RESULTADOS.md) certifica
seis intervalos hasta ≈6,25 µs. Mantener como fuente el último resultado
aceptado, record índice 5, radio 1 µV, sus 22 memorias, P y pico nodal.
El primer hueco es índice 6 hasta ≈12,5 µs. No reiniciar desde DC.

## Preparación antes de otra medición

1. Conservar la [política de registro ya comprobada](BIESTABLE_CIERRES_ENTEROS_RESULTADOS.md):
   enteros decimales exactos sin límite artificial, dominio de kernels
   intacto y los dos intentos fallidos históricos. Ambos presupuestos de
   10 µV ya rechazan matemáticamente. No repetirlos para modificar el
   prefijo ni volver a interpretar una excepción de texto como escape.
2. Auditar el forcing del grupo 20, C7, sobre el séptimo soporte fijo.
   Separar polinomio dirigido, defecto de descriptor y restos independientes,
   forcing del tramo y memoria entrante. Las cifras del nodo 81 apuntan
   a memoria, con término directo ≈16 fV; no justifican eliminar C7.
3. Conservar signos y dependencia temporal demostrada antes de integrar
   una respuesta forzada. Derivar una cota de convolución que incluya
   incertidumbre de tasa/acoplamientos y restos; no usar la integral firmada
   de un candidato como prueba de respuesta del descriptor medio variable.
   Declarar variantes y controles antes de medir, mantener las 119 filas.
4. Si una mejora conserva normas y soporte, intersectar únicamente cotas
   del mismo término. Pagar toda conversión entre coordenadas, endpoint
   y pico; transportar las 22 memorias conocidas y exigir cierre estricto.
5. Probar forcing afín con solución escalar exacta, cambio de signo,
   control sin cancelación, incertidumbre variable de matriz y restos
   independientes adversos. Reproducir el banco completo y sus fallos,
   registrar costes y ampliar corpus. Sólo después intentar continuidad.

Este plan conserva el circuito nominal CA3046, parámetros sintéticos y
meta global de 1 mV. Un presupuesto más estrecho no identifica hardware,
no produce una voz completa ni admite audio o deadline.
