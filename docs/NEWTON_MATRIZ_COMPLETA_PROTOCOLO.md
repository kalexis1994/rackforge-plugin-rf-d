# Matriz Newton completa antes de otra reformulación

2026-10-06. Tras rechazar la fila equivalente, volver al build original
`newton-build04` y preservar el candidato `newton-build05`. Este corte sólo
observa y postprocesa; no cambia un componente o tolerancia.

Capturar el sistema disperso A y RHS **antes de factorizar**, su solución
después del solve y la iteración anterior, con nombres/tipos de incógnitas,
orden, modo, tiempo y paso. Seleccionar antes de medir las iteraciones 100/101
del intento BUS variable con h≤1e-17 s en la ventana 2.2773–2.2775 ms.
Conservar todos los datos del sistema, incluidos RHS y filas auxiliares;
una matriz ya factorizada no es el A original.

Exigir nuevamente identidad exacta de las dos trayectorias, con sonda
apagada/encendida, incluido el control completo de 40 ms. Si falta una
iteración seleccionada, el banco debe declararlo y no sustituirla por otra.

Resolver offline el sistema lineal capturado desde los valores binary64
exactos, con precisión elevada y refinamiento comprobado. Identificar unidades
de cada fila e incógnita; verificar residual A*x−b por fila y diferencias de
voltajes/corrientes frente al solve real. Las escalas usadas para diagnosticar
no se convierten en una modificación del solver o un gate nuevo.

Una solución más precisa de ese A no es una raíz independiente del circuito
no lineal: A/RHS ya contienen evaluación y redondeo de los dispositivos.
Separar error de factor/solve, precisión de los sellos y convergencia Newton.
Sólo después de ese contraste formular otra intervención, con control completo,
historia/DC y gates anteriores. No heredar causalidad al binario oficial ni RT.
