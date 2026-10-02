# Curvatura direccional derivada de las leyes de circuito

El [protocolo](BIESTABLE_CURVATURA_PROTOCOLO.md),
[helper](../tools/loudness_latch_directional_curvature.py) y
[productor](../tools/loudness_latch_bdf_static_precision_memory_quadratic.py)
quedaron fijados en `60d71b2` antes de medir, el 2 de octubre de 2026.
No se ajustaron coeficientes a las respuestas finitas anteriores.

## Cobertura y gates

El grafo estático amplía las leyes existentes a **94 nodos**, 82 resistencias,
dos conductancias, 38 BJT y ocho diodos. R59 es una rama única entre audio
y contorno; no se duplican sus cargas a tierra. Topología y parámetros
siguen compartidos con el laboratorio: no es un oráculo físico independiente.

Se completan cuatro ventanas de 64 pasos, seis direcciones cada una:
**256 solves espaciales con seis RHS**, **1.536 segundas variaciones**,
**cero solves no lineales nuevos**. Se propagan ambos historiales de
primera y segunda variación; segunda variación inicial cero. Se conservan
curvaturas de residual y publicación de carga, incluyendo el factor 1/2
que deberá aplicarse al construir la predicción cuadrática.

| Comprobación | Resultado |
| --- | --- |
| Curvatura Decimal80/100 | Todas las 1.536 direcciones pasan en residual y publicación |
| Solve de segunda variación | Los 256 lotes pasan ambos errores hacia atrás; máximo 9,65075e-11 frente a 1e-10 |
| Corriente estática, 12 puntos | Máximo 2,31557e-17 A frente a 1e-11 A |
| Solve racional, 12 lotes / 72 columnas | Residuo racional cero; todos pasan mapa; máximo normalizado 1,24406e-17 |
| FD de segunda derivada | 216/216 residuales y 216/216 publicaciones pasan; máximo normalizado 0,00240759 frente a 1 |

FD usa tres pasos epsilon fijados y comparte grafo/leyes con la fórmula
analítica. El solve racional verifica la matriz/RHS binary64 recibidos,
sin volverlos parámetros físicos exactos. Los puntos seleccionados no
auditan el resto de Taylor ni todas las trayectorias posibles.

## Qué cambia y qué sigue abierto

Se deriva la contribución par del circuito que el predictor lineal no
representa. Para amplitud a y signo s, la predicción será:

`s a node1 + a² node2 / 2`, análogo para memoria.

Los coeficientes provienen sólo de la trayectoria base y las leyes de
corriente/carga. Se reservan **0,75 / 0,375 / 0,1875 uV** y ambos signos
para nuevos solves no lineales. Hasta completar ese contraste, esta
derivación no demuestra mejora de respuesta individual ni resolución de
los fallos de ataque anteriores. No se altera el integrador.

El gate temporal de **1 mV desde DC** sigue abierto. No se deriva un defecto
temporal exacto, cota global, identificación vintage, audio o deadline.

## Reproducción

[Datos](../evidence/loudness_latch_bdf_static_precision_memory_quadratic.json.gz):
10.463.349 bytes; SHA comprimido
`0db9f58dc33070dd9334137f1d36c857c2d56114efadf8afa9ea52c52b530c86`;
SHA canónico
`ec5b79bc249b90b74a25bf5bea26edf9578c358895cce5142b5eeba6d3ee7386`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_memory_quadratic_summary.json):
146 entradas, cobertura, cada auditoría y alcance.

El [recibo](../evidence/loudness_latch_bdf_static_precision_memory_quadratic_validation.json)
conserva la primera prueba fallida: pedía curvatura cero con todos los
voltajes de nodo a cero, polarización fuera del guard exponencial.
Se corrige sólo el testigo auxiliar, usando una polarización base válida
y comprobando que la polarización inválida sigue rechazándose. Datos,
fórmulas, fuentes congeladas y gates permanecen intactos.

Pasan **5/5 pruebas** en el segundo intento, 43,476 s, con entradas
idénticas antes/después de ambos intentos. Las cinco pruebas verifican grafo/R59/direcciones; todas las recurrencias,
curvaturas y errores algebraicos; 216 FD de cada vector y cuatro replays
racionales; ramas de carga, polaridad, conservación y guard; almacenamiento,
SHA y separación de niveles reservados. No se repite la suite histórica.

```
python tools/loudness_latch_bdf_static_precision_memory_quadratic.py
python tools/validate_bdf_static_precision_memory_quadratic.py
```
