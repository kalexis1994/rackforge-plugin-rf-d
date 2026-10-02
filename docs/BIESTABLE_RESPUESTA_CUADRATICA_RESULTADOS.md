# Respuesta cuadrática en amplitudes reservadas

El [protocolo](BIESTABLE_RESPUESTA_CUADRATICA_PROTOCOLO.md) y
[productor](../tools/loudness_latch_bdf_static_precision_memory_quadratic_response.py)
quedaron congelados en `f7670f8` antes de medir, el 2 de octubre de 2026.
Los [coeficientes de circuito](BIESTABLE_CURVATURA_RESULTADOS.md) ya estaban
fijados en `98a02c2`: no se ajustan a estas respuestas ni se vuelven a resolver.

## Cobertura y resultados

Se completan cuatro ventanas de 64 pasos, seis direcciones, tres amplitudes
reservadas (**0,75 / 0,375 / 0,1875 uV**) y ambos signos. Son **144 casos**,
**9.216 solves no lineales nuevos**, cada uno con sus propios dos historiales
y el reloj base congelado. Todos publican con los gates originales de KCL,
corrección, ramas y roundtrip tipado. KCL máximo: **2,73025e-12 A**, frente
a 1e-11 A. Los coeficientes congelados permanecen intactos.

| Ventana | Lineal individual | Cuadrático individual | Cuadrático par |
| --- | --- | --- | --- |
| Prefijo | 18/18 | 18/18 | 18/18 |
| Ataque | 0/18 | 18/18 | 18/18 |
| Reset | 18/18 | 18/18 | 18/18 |
| Cola | 18/18 | 18/18 | 18/18 |
| Total | 54/72 | 72/72 | 72/72 |

Cada contraste individual exige pasar nodos y memoria en **ambos signos**.
El error se divide por `10 nV + 1e-3 * abs(predicción)` en cada componente;
se aplica la misma fórmula a la predicción par. Se conservan los 18 fallos
lineales nuevos de ataque, todas las amplitudes y todos los errores.

La predicción es `signo * a * variación1 + a² * variación2 / 2`.
La parte par es `(respuesta positiva + respuesta negativa) / 2`, después
de restar la trayectoria base de cada respuesta. El término cuadrático
tiene el mismo signo para ambas inyecciones y deriva de corrientes y cargas,
incluida la curvatura de publicación. No se infiere sólo del contraste central.

En ataque, el máximo error nodal individual cuadrático es **0,305006 uV**;
máximo cociente de gate **0,259137**. El máximo error nodal par es
**4,23007 nV**, con máximo cociente **0,165532**. En memoria los máximos
cocientes son **0,00433997** individual y **0,000316239** par.

Como ejemplo, la dirección congelada de máxima ganancia nodal da:

| Amplitud (uV) | Máximo gate lineal nodal | Cuadrático nodal | Cuadrático par nodal |
| --- | --- | --- | --- |
| 0,75 | 15,9305 | 0,259134 | 0,165522 |
| 0,375 | 7,83829 | 0,0641687 | 0,0190373 |
| 0,1875 | 3,84131 | 0,0157583 | 0,00150023 |

Son contrastes finitos reservados; no demuestran un radio uniforme de
validez, una ley asintótica ni una cota para cualquier perturbación.
No se alteran el integrador, el controlador, la trayectoria base o los
fallos históricos. El gate temporal de **1 mV desde DC** sigue abierto:
predecir mejor una perturbación de memoria no acota el defecto temporal.
Tampoco se identifica hardware vintage, sonido físico ni deadline de audio.

## Reproducción

[Datos](../evidence/loudness_latch_bdf_static_precision_memory_quadratic_response.json.gz):
90.322.950 bytes; SHA comprimido
`3aa2307d2cbc3c1081a9fdd97e369c9fe0db81bd000cacc93f26f18eda6420f3`;
SHA canónico
`62012d6006d76d1ce7162dce93ad1c6bd478f9794b1c93db58f1f13f16da6d47`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_memory_quadratic_response_summary.json)
conserva 149 entradas, resultados por ventana/dirección/amplitud y alcance.

La [suite](../tests/test_loudness_latch_bdf_static_precision_memory_quadratic_response.py)
valida las 9.216 publicaciones e historiales, predicciones y métricas,
96 reproducciones no lineales seleccionadas, cuatro testigos de presupuesto
inválido, identidad de coeficientes y almacenamiento. El
[recibo](../evidence/loudness_latch_bdf_static_precision_memory_quadratic_response_validation.json)
registra **4/4 pruebas**, primer intento, **76,4858803 s**, SHA antes/después
idénticos. Ese tiempo corresponde a validación offline, no a tiempo real.

```powershell
python tools/loudness_latch_bdf_static_precision_memory_quadratic_response.py
python tools/validate_bdf_static_precision_memory_quadratic_response.py
```

Para reconstruir el experimento se necesita el corpus exacto de entradas;
los commits de contexto por sí solos no describen todas las materializaciones
históricas LF/CRLF. La auditoría ampliada conserva esas diferencias y las
versiones fallidas de pruebas.
