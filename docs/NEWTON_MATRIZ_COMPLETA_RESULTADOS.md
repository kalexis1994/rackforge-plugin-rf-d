# Sistema Newton completo: error lineal observado

2026-10-06. [Protocolo congelado](NEWTON_MATRIZ_COMPLETA_PROTOCOLO.md).
Se retorna al original `newton-build04`; el candidato de fila equivalente
`newton-build05` permanece rechazado y sin modificar. El nuevo build06 sólo
añade observación a NIiter y al interfaz KLU. Componentes, evaluación de
dispositivos, memoria, tolerancias y método de integración siguen iguales.

## Captura admitida

Se conservó el [rechazo de preparación](../evidence/voice_matrix_preflight_rejection01.json):
el ancla inicial de `klu_factor` coincidía también con CIDER. Ocurrió antes
de copiar, aplicar cambios, compilar o medir. El helper inicial sigue
intacto; el segundo añade la línea del argumento real Ax al ancla.

La [auditoría](../evidence/voice_matrix_observation01.json) reconstruye los
dos parches, inventaría 4337 archivos originales y verifica fuente, binarios,
compilador, log de build, runtime, decks y helpers. Los
[cuatro recibos](../evidence/voice_matrix_runs01.json) conservan todos los
tiempos y seis vectores exactamente iguales a build04:

| BUS | Captura apagada | Captura encendida | Cobertura |
| --- | --- | --- | --- |
| Cero | 219538 filas, idénticas | 219538 filas, idénticas | 40 ms completos |
| Variable | 7724 filas, idénticas | 7724 filas, idénticas | Rechazo original en 2.277414365034117 ms |

Se capturaron exactamente las iteraciones 100 y 101 previstas, sin sustituir
otra: t=2.277414365034122 ms, h=4.9999999999999996e-18 s, orden 1, modo 257.
Cada sistema tiene **133 incógnitas y 531 entradas CSC**. Se registra Ax
inmediatamente antes de `klu_refactor`, después de la eventual carga de
diagonal; diagGmin observado es cero. KLU usa escala 2, ordenación 0 y
pivot tol 0.001. Se conserva el mapa NewToOld usado realmente por SMPsolve,
nombre/tipo de cada incógnita, RHS, x anterior y solución publicada.
La matriz completa y los logs están en el corpus privado, fuera de Git.

## Solve de precisión elevada

Los textos C con 17 cifras se restauran a binary64; `Decimal.from_float`
convierte **esos valores exactos**, sin tratar el texto decimal como dato
matemático exacto. LU con pivoteo parcial a 80 y 120 dígitos y un paso de
refinamiento por precisión concuerdan bajo el chequeo declarado por fila.
El máximo residual a 120 dígitos tras refinar es 1e-109 en ambas capturas;
se reportan unidades por fila, sin sumar amperios y voltios.

| Iteración | Máxima diferencia de voltaje, solve real menos preciso | Máxima diferencia de corriente | Máximo residual lineal en filas de voltaje | Máximo residual lineal en KCL |
| --- | --- | --- | --- | --- |
| 100 | −101.983089 µV, xic3.16 | −1.667825 µA, rama VNEG10 | −0.182836 µV, rama L2 | −3.476948 µA, R78_RC_MID |
| 101 | +83.692285 µV, xic3.7 | −3.417841 µA, rama VNEG10 | +0.056449 µV, rama L2 | −3.476948 µA, R78_RC_MID |

En v16/v17 las diferencias son −101.983089 y +83.692285 µV. EOS transmite
esa diferencia a xic3.7. Los máximos de error relativo componente por
componente son 1.974e-11 y 7.562e-12; son diagnósticos del sistema lineal,
no gates físicos. En R78_RC_MID el residual de 3.477 µA coexiste con una
diferencia de voltaje de sólo 1.74e-15 V: magnitudes y escalas de fila
importan. Un residual pequeño tampoco limita el error de voltaje del polo.

La [descomposición posterior](../evidence/voice_matrix_rounding01.json)
verifica para v16 entre las dos capturas:

`207.585542 µV = 21.910169 µV + 185.675374 µV`.

Son, respectivamente, cambio publicado, cambio entre raíces precisas de
los dos sistemas y cambio de sus errores lineales. La identidad usa
**dos matrices distintas**: no es una trayectoria Newton recalculada ni
prueba que refinar haga converger el circuito.

## Publicación binary64 y límites

Redondear cada raíz de 120 dígitos una sola vez deja error de incógnitas
≤8.57e-16 V y ≤1.19e-18 A en estas capturas. Aun así, los máximos residuales
de la fila L2 son 1.061954 y 0.504574 µV, mayores que los del solve real.
Las KCL máximas quedan en 1.314025 y 1.298729 µA. Coeficientes grandes
amplifican el redondeo al publicar. Mejorar la solución y mejorar todo
residual por separado no son la misma condición.

Este contraste demuestra error en la solución del **A/RHS estampado**.
No identifica errores de evaluación/estampado, raíz no lineal independiente,
inductancia física del 741, causa del oficial o fidelidad vintage. No se
admite reset completo, unión VCO/contorno ni tiempo real; no hay audio nuevo.

Pasan [62 regresiones](../evidence/voice_matrix_tests01.json), incluyendo
12 de captura, precisión, publicación y alcance, más las 50 anteriores.
QA no ejecuta nuevos solves SPICE; preserva entradas físicas y WAV previo.
Próximo: [refinamiento lineal con matriz e historia originales](NEWTON_REFINAMIENTO_LINEAL_PROTOCOLO.md).
