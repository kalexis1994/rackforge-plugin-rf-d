# C7 y máximos de sensibilidad: respuesta finita

[Protocolo](BIESTABLE_DIRECCIONES_EXTREMAS_PROTOCOLO.md) y productor
fijados en `b638fb2` antes de medir, el 2 de octubre de 2026.
Los seis vectores por ventana conservan norma doble 1 y se inyectan a
1 / 0,5 / 0,25 uV con ambos signos, sin cambiar circuito ni gates.

## Resultado

Las **144 continuaciones** completan **9.216 solves no lineales nuevos**,
con historia propia, reloj fijo y todas las publicaciones válidas. Se
heredan 256 intervalos base y sus mapas; cero solves nuevos de mapa.

| Ventana | Casos completos | Central aprobado | Ambos signos aprobados | Máx. KCL publicado |
| --- | --- | --- | --- | --- |
| prefix | 36/36 | 18/18 | 18/18 | 2,03253 pA |
| attack | 36/36 | 18/18 | **0/18** | 2,79205 pA |
| reset | 36/36 | 18/18 | 18/18 | 0,00731873 pA |
| tail | 36/36 | 18/18 | 18/18 | 0,104626 pA |

Pasan **72/72 respuestas centrales**, pero sólo **54/72 comparaciones
individuales de ambos signos**. Los 18 fallos de ataque afectan nodos;
las memorias pasan sus gates individuales. Gate intacto por coordenada:
10 nV + 1e-3 |predicción|. Máximo central normalizado nodal: 0,461339;
máximo individual: **21,3972**, frente a 1. No se declara el predictor
lineal válido para esos casos de ataque.

## Por qué importa medir ambos signos

En ataque, la dirección de máximo nodal a 1 uV produce una respuesta
central nodal máxima de **2,04665 mV**. Su error central máximo es
0,714575 uV, mientras la respuesta par alcanza **36,5742 uV**.
El promedio (plus-minus)/2 cancela esa parte par y puede pasar aunque
cada respuesta individual difiera demasiado del predictor.

El peor cociente individual está en nodo 67, índice 13, tiempo
2,422253418 ms, signo negativo. La respuesta es -1,649681277 mV y
la predicción -1,614912691 mV. Con la misma dirección, el error
normalizado individual aún falla a 0,5 uV (10,5213) y 0,25 uV (5,16980).
No se cambia la tolerancia ni se reemplazan estos registros por amplitudes
más favorables. C7 común/diferencial y las otras direcciones de máxima
norma también conservan los tres fallos de ataque.

El siguiente bloque separado debe incluir continuación **sin inyección**
para comprobar reproducción de la base, y niveles menores declarados
para estudiar respuesta individual/par en estas seis direcciones de ataque.
Eso puede delimitar una selección de pequeña señal, sin certificar una
bola de las 50 coordenadas ni elegir una tolerancia de integración.

Las inyecciones siguen siendo memorias hipotéticas, no estados físicos
anteriores aceptados. No ejecutan el estimador adaptativo. Este resultado
no deriva defecto temporal ni explica exclusivamente el fallo de **1 mV
desde DC**, que permanece abierto. No admite fidelidad vintage, audio
ni deadline.

## Reproducción

[Datos](../evidence/loudness_latch_bdf_static_precision_memory_extrema.json.gz):
58.209.676 bytes; SHA comprimido
`36a1cb40db85dececaa371303d229614e7d9aaa095fb0caeef58f84259ac3637`;
SHA canónico
`11d95aa6325d63acbab5b841df58e4f92b24557174682f75e433664e58cac87f`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_memory_extrema_summary.json):
142 entradas, todos los niveles y fallos.

El [recibo](../evidence/loudness_latch_bdf_static_precision_memory_extrema_validation.json)
conserva **4/4 pruebas**, un intento exitoso de 68,849 s, entradas
idénticas antes/después: selección congelada y testigos de norma;
144 inyecciones; los 9.216 pasos con linaje, publicación, diferencias,
predicciones y métricas centrales/individuales/pares; 96 replays nuevos
seleccionados y presupuestos fallidos inmutables; almacenamiento y alcance.
Los fallos de comparación son resultados numéricos esperados, no fallos
ocultados de la suite. No se repite la suite histórica.

```
python tools/loudness_latch_bdf_static_precision_memory_extrema.py
python tools/validate_bdf_static_precision_memory_extrema.py
```
