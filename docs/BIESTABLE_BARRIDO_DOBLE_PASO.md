# Barrido desde DC con estimador BDF2 de doble paso

## Experimento declarado antes de medir

El [prototipo v4](BIESTABLE_ESTIMADOR_BDF2_DOBLE_PASO.md) se integra en
un controlador nuevo, sin modificar los productores ni los datos anteriores.
Se conserva el circuito documental condicionado de 94 nodos, R61=200 Ω,
BUS=0, perfil sintético `finite_transit`, DC con KEY=0 y salto a KEY=10
en t=0. Destino: 3 ms. No se reinicia la memoria durante el barrido.

| Política | Absoluta nodo/juntura | Relativa nodo/juntura | Incremento de juntura | h·λ+ | Intentos |
| --- | --- | --- | --- | --- | --- |
| D4 | 40 nV | 4×10⁻⁸ | 25 mV | 0,05 | 6000 |
| E4 | 10 nV | 1×10⁻⁸ | 12,5 mV | 0,025 | 12000 |

Las tolerancias son decisiones de experimento numérico, no constantes del
instrumento. Las sondas previas tienen diferencias crudas de hasta 0,684 µV;
este barrido pregunta por acumulación global, que esas sondas no acotan.
Ambas políticas usan máximo 100 µs, mínimo real 1 ps y razón BDF2 ≤2.
El macro requiere ≥2 ps para que sus dos medias etapas estén dentro del
dominio. Si el resto al destino no lo permite, se conserva el fallo;
no se redondea el reloj. No se modifica una política después de medirla.

## Arranque, publicación y rechazo

Sólo mientras falta el historial previo se usa el arranque explícito:
BE completo frente a BE medio + BDF2 medio. Los dos intervalos finos se
publican si pasan los gates. Después se usa exclusivamente el estimador v4,
con KEY constante y ambos historiales aceptados. No hay retorno a BE ante
un fallo, selección alternativa de raíces ni clipping.

Cada intento normal compara un BDF2 completo con dos medios BDF2 desde
los mismos estados entrantes. El segundo medio alcanza exactamente el
tiempo binario del completo. La diferencia cruda se escala por voltajes;
no hay división Richardson. Se publica sólo el candidato completo y se
guardan ambas medias etapas como provisionales.

Las tres rutas conservan cargas compensadas, C10 serie y cargas terminales
Q25/Q15. Sus publicaciones se verifican desde historiales reales con
Decimal80: KCL <10 pA, ecuación de rama <10 fV y restauración exacta.
El residuo del solve y su corrección conservan los gates anteriores.
El control local incluye incremento de juntura y modos congelados de las
tres rutas. Un rechazo conserva el hash de ambos historiales entrantes.

## Comparación y observación

Gate global original: **máximo <1 mV en cualquiera de los 94 nodos**, al
mismo reloj, además de cobertura completa. La diferencia final no sustituye
el máximo. El primer contraste interpola linealmente las mallas aceptadas,
excluyendo los puentes iniciales del salto de fuente. También se conserva
el contraste de cada nueva política con C3, sin identificar una como exacta.

La selección de consultas se fija por regla antes de medir sus valores:
rejilla de 25 µs en 0..3 ms, rejilla de 0,5 µs en 2,4..2,5 ms,
32 puntos medios estratificados por política y el máximo interpolado de
cada uno de los 94 nodos. Se añade el máximo interpolado global.
El observador conserva el tiempo pedido con el dominio de 1 ps y, cuando
corresponde, dos intervalos provisionales desde un anclaje anterior.
Se repiten con Jacobiano totalmente FD los picos interpolado y consultado.
Un conjunto finito de consultas no prueba el máximo continuo.

## Reproducción y archivos

`python tools/loudness_latch_bdf_doubling_survey.py`

`python tools/loudness_latch_bdf_doubling_sampling.py`

`python -m unittest discover -s tests -p test_loudness_latch_bdf_doubling_survey.py -v`

`python -m unittest discover -s tests -p test_loudness_latch_bdf_doubling_sampling.py -v`

Los dos casos se guardan por separado en
`evidence/loudness_latch_bdf_doubling_d4.json.gz` y
`evidence/loudness_latch_bdf_doubling_e4.json.gz`, con resumen
`evidence/loudness_latch_bdf_doubling_survey_summary.json`.
La observación tiene su propio gzip y resumen `...doubling_sampling...`.
Compresión sin pérdida, JSON canónico, SHA256 de fuentes/datos antes y
después, ambiente y serialización completa. Separar casos limita el tamaño
de archivo sin eliminar memorias o rechazos.

## Alcance

Este experimento comparte solver espacial y parámetros sintéticos con los
anteriores. No identifica una población vintage, cargas omitidas ni audio.
El resultado de refinamiento pertenece a su política y observación;
no demuestra error absoluto continuo ni habilita el contorno en Rust.
