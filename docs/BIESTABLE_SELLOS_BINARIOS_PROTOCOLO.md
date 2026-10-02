# Sellos analíticos binary64: protocolo previo

Se parte del grafo estático y cuatro candidatos guardados del experimento
Decimal (`d1aa511`). No se evalúan estados físicos nuevos ni se cambia el
integrador. Las constantes, corrientes Ebers-Moll/Shockley y topología
permanecen iguales; el grafo se prepara fuera de cualquier callback de audio.

Se comparan dos rutas, declaradas antes de ejecutar:

1. Recíproco resistivo ordinario, redondeado a binary64. Cada contribución
   de derivada se conserva hasta una suma final con `math.fsum`.
2. El mismo recíproco más su resto de redondeo: levantar R binary64 a
   fracción exacta, calcular 1/R, guardar `high=float(1/R)` y
   `low=float(1/R−high)`. Ese cálculo racional se realiza sólo en preparación.
   El Jacobiano acumula ambos términos mediante `fsum`; las corrientes
   evaluadas son las mismas en ambas rutas. Se archiva el resto exacto no
   representado por high+low. No se presenta como una implementación de audio.

Evaluar cada ruta en los **cuatro puntos** del informe estático: ocho
Jacobianos de audio. Comparar corrientes con Decimal80 bajo **10 pA** y
Jacobianos bajo **10⁻³⁰ S + 10⁻⁸|JDecimal|**. Registrar identidad y cantidad
de componentes binary64 distintos, sin usar identidad como gate universal.
Las exponenciales y cocientes de los BJT se calculan en binary64 en ambas
rutas; no se introduce Decimal durante esa evaluación.

Sustituir sólo el bloque 66×66 de una copia del sistema J94 diagnóstico
anterior, conservando sus otros sellos y B. Resolver ocho mapas con el
solver racional y gates algebraicos **10⁻¹⁰**. Compararlos con el mapa
analítico Decimal80 bajo **10⁻⁸**, conservando todos los resultados de
ambas rutas aunque uno falle. No elegir una ruta por conveniencia de un gate.

Reutilizar las 48 inyecciones hipotéticas archivadas para 24 respuestas
centrales, comparando ambos mapas: **48 contrastes de predicción**, sin
solves no lineales nuevos. Mantener **10 nV + 10⁻³|predicción|**; ese gate
no admite una precisión del mapa de 10⁻⁸ ni ventanas más largas.

Conservar fuentes/hashes antes/después, grafos preparados, matrices, todos
los fallos y gates abiertos. Las rutas son candidatas de laboratorio,
sin modificación del solver, admisión de raíz, cota temporal, hardware,
audio o deadline. El fallo original de reset permanece archivado.

`python tools/loudness_latch_bdf_static_precision_binary.py`
