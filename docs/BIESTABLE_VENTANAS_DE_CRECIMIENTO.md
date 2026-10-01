# Ventanas con memoria E4 común y dos heurísticas de crecimiento

El [barrido D4/E4](BIESTABLE_BARRIDO_DOBLE_PASO.md) conserva 7,81 mV
de máximo consultado y un contraejemplo exacto al umbral de crecimiento
0,25. Este experimento nuevo compara umbrales **0,25 y 0,125** en cuatro
ventanas cortas, manteniendo la política E4 y el estimador v4. Ambos
umbrales son heurísticas; el cúbico no calibra el DAE.

Antes de medir se fijan estos límites de anclaje y duraciones:

| Región | Límite de anclaje E4 | Duración desde el anclaje |
| --- | --- | --- |
| Prefijo | 2,3 ms | 10 µs |
| Ataque | 2,42 ms | 0,25 µs |
| Reset | 2,44205 ms | 20 ns |
| Cola | 2,5 ms | 20 µs |

Se restaura el último estado E4 aceptado no posterior a cada límite,
incluyendo ambos historiales, sus fuentes y el intervalo anterior. Ambas
rutas empiezan con la misma propuesta: el siguiente macro aceptado E4.
El destino es el tiempo real del anclaje más la duración declarada.
Se permiten 600 intentos por ruta; los fallos permanecen registrados.
No hay arranque BE ni reinicio DC en las ventanas.

El circuito, tolerancias absolutas/relativas de 10 nV/10⁻⁸, incremento
12,5 mV, producto modal 0,025, máximo 100 µs y mínimo real 1 ps siguen
iguales. Se publica el BDF2 completo y se conservan los medios
provisionales, con gates originales de KCL/ramas y razón ≤2.
Sólo cambia el umbral de error para proponer duplicar h. Los límites
de incremento y producto modal para crecimiento siguen en la mitad.

Se comparan cobertura, número de intentos/rechazos, memorias publicadas y
máximo condicional de los 94 nodos. Se consulta conservativamente el
instante de ese máximo interpolado, si tiene cobertura por ambas rutas.
Las consultas y el contraste de ventanas son diagnósticos finitos;
no reemplazan el gate fallido desde DC ni identifican el error exacto.

`python tools/loudness_latch_bdf_growth_windows.py`

Datos propios: `evidence/loudness_latch_bdf_growth_windows.json.gz` y
`evidence/loudness_latch_bdf_growth_windows_summary.json`. Se fijan los
hashes de E4 y las fuentes antes/después, y se comprueba almacenamiento
canónico sin pérdida. Los informes anteriores quedan intactos.

El primer intento completó las cuatro ventanas y guardó el informe íntegro,
pero el adaptador de resumen esperaba un campo `startup` ausente. Se
conservan el gzip, productor original y hashes en `...windows_attempt1...`
y `...growth_attempts.json`. La corrección declara `startup=false` para
estas continuaciones. Se repite el productor y se contrastan los datos
numéricos con el intento conservado, sin cambiar gates o controles.

## Resultado y alcance

Las ocho continuaciones completan sus destinos. Se integran **335
intervalos publicados** y **670 medios provisionales aceptados**:

| Región | Aceptados/rechazos con 0,25 | Aceptados/rechazos con 0,125 | Máximo interpolado condicional | Consulta de ese pico |
| --- | --- | --- | --- | --- |
| Prefijo | 13 / 0 | 13 / 0 | 0 V | No solicitada: máximo en el anclaje idéntico |
| Ataque | 4 / 0 | 6 / 0 | 733,856071 µV | 2,993161274×10⁻¹³ V |
| Reset | 53 / 1 | 53 / 0 | 0 V | No solicitada: máximo en el anclaje idéntico |
| Cola | 90 / 32 | 103 / 0 | 10,159139 µV | 0,587542 µV |

Prefijo y reset conservan los mismos estados completos aceptados, incluidos
sus pares compensados. El rechazo de reset cambia el costo de intentos,
sin cambiar la trayectoria aceptada. Hay cuatro consultas válidas en total,
dos por pico no nulo. Una consulta del máximo interpolado no localiza el
máximo continuo ni sustituye una rejilla completa de observación.

En la cola los intentos bajan de **122 a 103**, con trece intervalos
aceptados más; en las cuatro ventanas suman 193 frente a 175. Esto mide
cantidad de intentos, sin medir latencia ni deadline de audio. No determina
que 0,125 sea un controlador universal ni que pase el barrido global.

Cada publicación y medio aceptado se contrasta contra los historiales reales.
Máximo KCL guardado entre esos intervalos: **1,574734 pA**, con el gate
original de 10 pA. La mínima media etapa es **81,787112 ps**; todas siguen
en el dominio de 1 ps. Hay cero arranques BE o reinicios de memoria.

**6/6 regresiones pasan** en 13,903 s, el 2026-10-01. Reconstruyen cada
propuesta/halving y las dos reglas de crecimiento, comprueban anclajes E4,
publicación de carga, consultas, hashes y reproducción del intento original.
La comparación de ambos intentos es exacta tras añadir exclusivamente
`startup=false`; el fallo del primer resumen queda conservado.

`python -m unittest discover -s tests -p test_loudness_latch_bdf_growth_windows.py -v`

Siguiente gate: estudiar el controlador en la trayectoria desde DC y la
acumulación del defecto temporal, conservando los 7,81 mV fallidos y el
gate original. Las ventanas son experimentos condicionados a memoria E4;
no admiten refinamiento global, física, audio ni un cambio al motor Rust.
