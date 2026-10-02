# Forzamiento: intento inicial conservado

Productor/protocolo congelados en `13b7d35`, el 2 de octubre de 2026.
El [protocolo](BIESTABLE_FORZAMIENTO_PROTOCOLO.md) define referencias
condicionadas con memorias propias y extracción de forzamiento del mapa
grueso levantado. Este intento no alcanza una comparación de predictores.

Se publican **1.276 intervalos finos** válidos de **1.278 intentados**:
prefijo/reset/cola completan 128 y 256 con subdivisiones 2/4; ataque se
detiene tras 40 y 84. Máximo KCL **1,11071e-12 A**. Todos conservan los
gates de solve/publicación y el historial entrante.

Las dos detenciones de ataque tienen `dt/dt_previo >2`: la resta de
subtiempos representables al cruzar un crecimiento de paso produce esa
razón pese a una intención de dividir h en partes iguales. La diferencia
máxima registrada respecto a h/N es 3,32373e-19 s; no habilita ignorar el
dominio. Se conservan destinos, intervalos, memorias y error completo.

Las ocho recurrencias forzadas se detienen antes del primer solve: el
adaptador entrega un RHS de forma (94,), pero el solver registrado exige
columnas (94,k). El forzamiento calculado queda archivado; no se declara
ganancia, mejora de predictor ni pase de propagación. La
[variante posterior](BIESTABLE_FORZAMIENTO_RELOJ_PROTOCOLO.md) corrige el
formato y declara otro calendario dentro del dominio, sin modificar estos datos.

[Datos](../evidence/loudness_latch_bdf_static_precision_forced_windows.json.gz):
5.717.651 bytes; SHA comprimido
`b5ce564608d7b3c28c9aae65f1d623bf149f621a6c78dce2ff497afe82e2561c`;
SHA canónico
`5a6b1c0f60838b7c2a63476180993fcd0825fd954bcb7993feb5ef7d8625f27a`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_forced_windows_summary.json)
identifica 149 entradas y cada detención.

El [recibo](../evidence/loudness_latch_bdf_static_precision_forced_windows_validation.json)
conserva una prueba inicialmente fallida: reconstruía el cero de memoria
desde literales en lugar de reproducir su aritmética Decimal, obteniendo
valores iguales con distinta representación de ceros finales en strings.
El test posterior reproduce exactamente la construcción de la memoria
virtual original. No cambia datos, helper, protocolo ni gate.
**4/4 pruebas pasan** en el segundo intento, **12,3310855 s**, incluyendo
todas las publicaciones, 16 replays seleccionados, las dos detenciones,
identidades de forzamiento, testigo racional independiente y carga RC serie.
Se mantienen SHA antes/después idénticos en ambos intentos.

Ni los replays ni el testigo escalar prueban el error temporal del DAE.
El gate global de 1 mV desde DC, identificación física, audio y deadline
siguen abiertos.
