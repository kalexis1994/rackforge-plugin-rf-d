# Precisión estática: resultados

El [protocolo previo](BIESTABLE_PRECISION_ESTATICA_PROTOCOLO.md), grafo y
productor se fijaron en `7fbac22`. El grafo independiente contiene 55 ramas
resistivas, dos conductancias equivalentes, 28 BJT y cuatro diodos, con
las mismas fronteras y parámetros condicionados del laboratorio.

## Corrientes y precisión

Las cuatro comparaciones estáticas pasan el gate de 10 pA. La discrepancia
máxima frente al oráculo binary64 es **1,45159×10⁻¹⁷ A**. Decimal80/100
producen los mismos residuos y Jacobianos estáticos redondeados a binary64
y los mismos cuatro mapas nodales redondeados. Esa identidad es una
comprobación de precisión finita, sin cota matemática de error exacto.

Se resuelven **28 matrices J94/B**: cuatro analíticas Decimal80, cuatro
Decimal100 y veinte con FD estático Decimal80. Todas pasan la eliminación
racional y ambos gates hacia atrás de 10⁻¹⁰ después de redondear; el máximo
observado es 1,67525×10⁻¹⁶. Contorno y sellos dinámicos siguen compartidos
con el laboratorio original; la transcripción independiente cubre sólo
el bloque estático de audio de 66 nodos.

## FD en mayor precisión

El gate de derivada por componente es 10⁻³⁰ S + 10⁻⁸|Janalítico|.
Los cinco pasos permanecen publicados, incluyendo los ocho fallos gruesos:

| Paso FD (V) | Máximo normalizado de derivada, cuatro ventanas | Gate de derivada | Mayor diferencia de mapa, cuatro ventanas | Gate de mapa 10⁻⁸ |
| --- | --- | --- | --- | --- |
| 10⁻⁴ | 252,484 | Falla 4/4 | 2,49742×10⁻⁶ | Falla 4/4 |
| 10⁻⁵ | 2,52484 | Falla 4/4 | 6,61668×10⁻⁷ | Falla 4/4 |
| 10⁻⁶ | 0,0252484 | Pasa 4/4 | 3,40944×10⁻¹⁰ | Pasa 4/4 |
| 10⁻⁷ | 0,000252484 | Pasa 4/4 | 5,90308×10⁻¹² | Pasa 4/4 |
| 10⁻⁸ | 0,00000252484 | Pasa 4/4 | 6,03307×10⁻¹⁴ | Pasa 4/4 |

Pasan **12/20 contrastes** de derivadas y mapas dentro del bloque nuevo.
En reset a 10 µV, la diferencia de mapa es mayor que a 100 µV en otras
ventanas: no se presume una ley única de convergencia para la matriz
redondeada. La reducción observada en los tres pasos más finos tiene
alcance numérico local. No se selecciona un nuevo paso FD.

## Comparación con los mapas anteriores

La referencia de esta tabla es el mapa analítico Decimal80:

| Ventana | Diferencia escalada frente al mixto anterior | Frente al FD completo anterior a ±1 µV |
| --- | --- | --- |
| Prefijo | 9,32280×10⁻¹⁰ | 7,19861×10⁻¹⁰ |
| Ataque | **6,94831×10⁻⁷** | **6,95052×10⁻⁷** |
| Reset | **6,74445×10⁻⁷** | **6,74126×10⁻⁷** |
| Cola | 9,43154×10⁻¹⁰ | 6,72803×10⁻¹⁰ |

Ambos mapas anteriores pasan sólo prefijo/cola frente a esta nueva
referencia; ataque y reset fallan 10⁻⁸. La coincidencia mixta/FD anterior
en ataque compartía aproximaciones binary64 y no detectó esta sensibilidad.
Los datos anteriores y su gate original de reset se conservan intactos.

Una inspección posterior de las matrices localiza en fila 27 el sello
resistivo R35 entre PAIR_EMITTER (27) y Q18_COLLECTOR (28): −0,001 S en el
grafo analítico, frente a −0,0010000000001397782 S en el mixto FD. El sesgo
es ≈1,39778×10⁻¹³ S. En ataque/reset, la diferencia de diagonal no coincide
exactamente con la del término cruzado al redondear; sus derivadas BJT a
bases 25/26 son del orden de 8×10⁻¹⁴ S. Es una localización de precisión
y balance de sellos, no una demostración de una causa única del mapa.

Las métricas heredadas de `map_metrics` usan el campo `mixed_value` para
la **referencia analítica** en este informe; `candidate_value` corresponde
al mapa que indica el nombre de la comparación. El denominador es siempre
1+|referencia analítica|. Las matrices completas conservan ambas identidades.

## Inyecciones y regresiones

Las **48 inyecciones hipotéticas** de memorias 7, 10 y C2 completan su único
intervalo con reloj fijo, publicación y memorias intactos. Pasan los 24
contrastes centrales bajo cada predictor: analítico nuevo y mixto anterior,
con gate 10 nV + 10⁻³|predicción|. El máximo normalizado es 0,000148462
para el nuevo y 0,000250473 para el anterior; KCL máxima 6,84751×10⁻¹³ A.
Esa tolerancia no distingue todas las diferencias de mapas de 10⁻⁸;
no se promueve un predictor completo por estas tres direcciones.

- [Evidencia completa](../evidence/loudness_latch_bdf_static_precision.json.gz):
  1.156.917 bytes, SHA256 comprimido
  `feafecf439e5d51fe2ddedf9f0e106fc0ba7978755b27b172ce24e71e90e1da4`.
- [Resumen](../evidence/loudness_latch_bdf_static_precision_summary.json).
- [Recibo](../evidence/loudness_latch_bdf_static_precision_validation.json):
  **5/5 regresiones**, un intento exitoso, 120 entradas identificadas y
  fuentes sin cambios. Incluye conservación/polaridad BJT, las cuatro
  transcripciones, todos los mapas/gates y publicaciones, cuatro FD Decimal
  completos a ±1 µV, doce solves racionales y ocho solves no lineales de replay.

`python tools/validate_bdf_static_precision.py`

## Siguiente gate

Contrastar sellos analíticos estáticos en binary64 frente a esta referencia
Decimal, antes de incorporarlos a un integrador. El experimento debe conservar
las leyes, residuos y memorias, declarar sus gates y retener fallos sin
alterar la referencia. Después repetir ventanas de integración y contraste
temporal completo. Los parámetros físicos, audio y deadline siguen abiertos.

La [auditoría de entradas](BIESTABLE_PRECISION_ESTATICA_ENTRADAS.md)
reconstruye los 124 SHA del corpus ampliado desde Git y tres archivos
históricos exactos, sin modificar estos resultados numéricos.
