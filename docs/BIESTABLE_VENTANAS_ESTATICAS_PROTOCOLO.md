# Derivadas estáticas durante cuatro ventanas: protocolo previo

Ampliar los cuatro puntos de `b8eb3f4` a los **16 intervalos originales de
cada ventana** del archivo de memorias: prefix, attack, reset y tail. Son
64 candidatos guardados, sin solves no lineales nuevos, sin retimar E4G8.
Restaurar en cada intervalo el historial doble anterior y el incremento
guardado; reconstruir el candidato con `fsum(high, low, delta)`.

Evaluar el grafo estático independiente con Decimal80 y Decimal100 y las
dos preparaciones binary64 ya fijadas: ordinaria y compensada. Conservar
ambas rutas y todos sus fallos. Gate de corrientes **10 pA**, derivadas
**10⁻³⁰ S + 10⁻⁸|JDecimal80|**. Registrar por separado coincidencia de
Decimal80/100 redondeados; no asumir que demuestra error matemático cero.

Reutilizar contorno, acoplamiento R59 y dinámica anteriores. Reconstruir
sellos dinámicos directamente, sin restarlos de matrices grandes. Para cada
intervalo resolver J94 X = B94×25 mediante fracciones exactas en cuatro
rutas: Decimal80 redondeado, Decimal100 redondeado, binary64 ordinaria y
compensada. Son **256 solves lineales**, con ambos gates de error hacia
atrás **10⁻¹⁰**. Comparar los mapas con Decimal80 bajo **10⁻⁸** de diferencia
por componente dividida por 1+|referencia|. Conservar el mapa mixto histórico
como contraste adicional, sin recalcularlo ni admitirlo por su álgebra.

Archivar matrices, mapas, candidatos, historia anterior por hash, reloj,
todos los resultados y SHA de fuentes antes/después. No seleccionar pasos,
raíces, tolerancias o ventanas después de medir. Los sellos de contorno y
carga siguen compartidos: el grafo estático de audio es independiente,
pero no existe aquí un oráculo espacial completo independiente.

Esta auditoría permite estudiar una variante del integrador después de
archivar resultados. No cambia el residual ni el integrador histórico y
no admite refinamiento temporal, conmutación vintage, audio o tiempo real.

`python tools/loudness_latch_bdf_static_precision_windows.py`
