# Segundo banco preparado: primer hueco en la memoria de junturas

El [protocolo](BIESTABLE_CONTINUACION_PREPARADA_SEGUNDA_PROTOCOLO.md) y productor
se congelan en `af2c923` antes de medir. Fuente: variante 0 del
[banco 24–31](BIESTABLE_CONTINUACION_PREPARADA_RESULTADOS.md), 32 soportes,
22 memorias reales, P fija y plantilla 31. No se reinicia su cota.

## Tiempo admitido, intentado y condicionado

Se construyen y archivan ocho referencias nuevas 32–39, hasta ≈425 µs,
con curvas C7, cargas/RC/Q, restricciones, residual, forcing, RHS firmado de
119 ecuaciones, restos independientes y consultas Decimal100. Es un banco
condicionado: no admite ese tiempo por existir.

Los cuatro anchos predeclarados **8/4/2/1** admiten el soporte 32 y rechazan
el33. Cada rama parte de la misma fuente a ≈325 µs y se detiene en el primer
hueco. El radio 0,1 µV rechaza por el anclaje; radio 1 µV permite comparar
el soporte completo y rechaza cuando su cota sale del tubo. No se cambia.

| Ancho | Pico local32, µV | Cota rechazada33, µV | Contracción q del primer bloque |
| --- | --- | --- | --- |
| 8 | 0.791334312 | 1.189484541 | 0.065337164 |
| 4 | 0.775339719 | 1.166735568 | 0.059219604 |
| 2 | 0.773597513 | 1.164261153 | 0.058502281 |
| 1 | 0.773165172 | 1.163855757 | 0.058323951 |

Se elige ancho 8: mismo prefijo más largo y primero en empate, según protocolo.
No se elige la rama por tener la menor cota. Su resultado real completo es
la fuente para el siguiente experimento, con sus propias 22 memorias.

**33 soportes contiguos hasta ≈337,5 µs**, extremo exacto
`1556444031219243/4611686018427387904` s; acumulado
**7,928168411011273e-7 V**, ≤0,793 µV. Local nuevo ≤0,792 µV.
C7 termina con **≤466,951 nV**. `first_gap_index=33`, `stop_reason=first_gap`.
El soporte rechazado termina a ≈350 µs; sus endpoint/memorias no se admiten.
Plantillas34–39 permanecen no alcanzadas. No se extrapola hasta ≈425 µs.

## Máximo interior y sus términos

La fuente31 conserva ocho diagnósticos exactos, con máximo en nodo 66,
[1/2,5/8]: anclaje0,109957330 µV y forcing0,413186315 µV.
Los nuevos máximos32/33 siguen en esa celda y nodo. Para ancho 8:

| Soporte | Anclaje nodo 66, µV | Forcing nodo 66, µV | Parte del grupo 21 en forcing, µV | Término directo, V |
| --- | --- | --- | --- | --- |
| 32 admitido | 0.131795449 | 0.659538863 | 0.659536791 | 1.628125494e-12 |
| 33 rechazado | 0.153913224 | 1.035571317 | 1.035568098 | 2.556567923e-12 |

El grupo 21 reúne las cuatro junturas en norma P; las otras 21 coordenadas
se transportan individualmente. La validación reconstruye la suma racional
exacta de ganancias×memorias para anclaje y forcing y añade el término directo.
Se mantienen polinomios precondicionados, restos independientes, primera
corrección y cola por subcelda, con SHA completo de RHS/acción.

La cota del forcing propagado domina aquí frente al directo. Esto identifica
un presupuesto numérico para investigar; no una causa física ni el error
verdadero de la trayectoria. Un q<1 certifica inversa y dominio; los cinco
recintos pasan, pero ninguno permite cerrar el segundo soporte a radio 1 µV.

## Certificados y costes

Cinco bloques: uno por ancho 8/4/2 y dos por ancho 1. Cada bloque renueva ledger
de polinomios completos, dominio futuro y tubo, candidato binary64, inversa,
tasas y preparación explícita; cada celda identifica contexto y estado.
El primer bloque usa índice35, u=1/2, y 704 rangos de 88 leyes×8 curvas.
El segundo bloque de ancho 1 tiene q≈0,058388183. No se toma el recinto anterior.

| Operación nueva | Cantidad |
| --- | --- |
| Candidatos de referencia / bloque | 8 / 5 |
| Inversas / preparaciones | 5 / 5 |
| Consultas LDL de tasa | 495 |
| Budgets / subcertificados | 64 / 512 |
| Solves de trayectoria / nuevos sistemas P | 0 / 0 |

Los presupuestos incluyen soportes rechazados. No se asume que 64 budgets
signifiquen ocho soportes admitidos ni se hereda el ahorro del benchmark.

**21 artefactos completos**, ocho plantillas, cinco bloques y ocho soportes,
suman **102567386 bytes**, máximo **11958270 bytes**. No se borra ninguna rama.
[Manifiesto](../evidence/loudness_latch_bdf_static_precision_prepared_continuation_second.json.gz)
y [resumen](../evidence/loudness_latch_bdf_static_precision_prepared_continuation_second_summary.json):
**3345488 bytes**, SHA comprimido
`8ee7eb08b29f58bc12e4b661ec1b44eda98a31a65fcf3ad036aeabe53271a317`;
canónico `b6d5ca38f882c5aa694e61d14159606da6c4e2d56e6a5f8a7fab63e1f32ac5aa`.
[Lanzamiento](../evidence/loudness_latch_bdf_static_precision_prepared_continuation_second_launch.json)
con exit 0, fuente UTF-8 exacta, salidas y snapshots idénticos, 518 entradas
identificadas antes de medir. Datos, nueve tests y validator congelados en
`7501d8a`. La [validación y corpus](BIESTABLE_CONTINUACION_PREPARADA_SEGUNDA_ENTRADAS.md)
registran cada intento y recuperan las fuentes históricas.

Circuito nominal/sintético y laboratorio offline. Integrador, helpers,
fuentes/datos anteriores, atributos Git y gates intactos. Cobertura completa,
1 mV global, identificación física, sonido vintage, voz, audio y deadline
siguen abiertos. Próximo:
[refinar comparación de memoria en el hueco](BIESTABLE_HUECO_MEMORIA_JUNTURAS_PLAN.md).
