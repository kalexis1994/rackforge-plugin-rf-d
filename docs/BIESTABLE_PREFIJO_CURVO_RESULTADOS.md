# Continuación curva: dieciséis soportes nominales contiguos

El [protocolo](BIESTABLE_PREFIJO_CURVO_PROTOCOLO.md) y productor se congelan
en `0814518` antes de medir. Modelo documental CA3046 nominal, parámetros
sintéticos y gates intactos. La fuente es el [octavo cierre curva/afín](BIESTABLE_REFERENCIA_CURVA_RESULTADOS.md),
selección [1,1], con sus 22 memorias finales reales y P fija.

## Banco terminado y alcance exacto

Se intentan los ocho soportes declarados, índices 8 a 15, con la misma
receta de burbuja C7 y radios 0,1/1 µV. Todos seleccionan el segundo radio:
1 µV. El control de 0,1 µV rechaza por el pico entrante, sin recintos nuevos.
No se repiten ramas no soportadas de 10 µV ni se eleva su dominio.

**Se certifican dieciséis intervalos contiguos hasta ≈125 µs**, extremo
exacto `4611686018427389/36893488147419103232` s. Error nodal acumulado
**7,928168411011273e-7 V**, ≤0,793 µV, heredado del prefijo anterior.
No se encontró un hueco en este banco: `first_gap_index=null`,
`stop_reason=declared_limit`. Llegar al límite no certifica soportes posteriores.

Las historias reales tienen pasos de ≈12,5 µs después de 25 µs. La lectura
tipada corrige la estimación inicial del plan de 25→50 µs; el primer nuevo
soporte es 25→37,5 µs. Se conserva cada duración racional exacta, incluyendo
los bits del reloj publicado, sin fabricar historia o traducir tiempos.

## Picos locales y transporte

| Índice | Reloj aproximado, µs | Pico local, µV | Error final real C7, µV | Selección |
| --- | --- | --- | --- | --- |
| 8 | 25.0→37.5 | 0.331495377 | 0.331443681 | 1 µV |
| 9 | 37.5→50.0 | 0.336984936 | 0.336932286 | 1 µV |
| 10 | 50.0→62.5 | 0.342703492 | 0.342649775 | 1 µV |
| 11 | 62.5→75.0 | 0.348488449 | 0.348433545 | 1 µV |
| 12 | 75.0→87.5 | 0.354285654 | 0.354229390 | 1 µV |
| 13 | 87.5→100.0 | 0.360077143 | 0.360019251 | 1 µV |
| 14 | 100.0→112.5 | 0.365857065 | 0.365797120 | 1 µV |
| 15 | 112.5→125.0 | 0.371623676 | 0.371561006 | 1 µV |

Los picos locales corresponden a la última celda [7/8,1], nodo 81.
El máximo local nuevo es ≤0,372 µV, distinto del acumulado ≤0,793 µV.
El error final C7 pasa de ≈326,672 nV de entrada a ≈371,561 nV de salida;
las 22 memorias se transportan sin reset. Cada burbuja conserva exactamente
sus endpoints. Su pico candidato disminuye de ≈1,870717 a ≈1,854420 µV.
El error se mide respecto a las referencias curvas por tramos.

En cada soporte se renuevan dirección candidata, 94 potenciales,
21 memorias/cargas/restricciones RC y cuatro Q(v) por piezas. Expansión
exponencial de orden seis con grado doce completo, slopes físicos,
restos uniformes y constitutivos, e incertidumbre de Hbar incluidos.
Se obtienen **72 precondicionadores candidatos**, **64 recintos de inversa**,
**6336 consultas LDL de tasa** y **512 acciones de subcelda**.
Cero solves no lineales o sistemas de métrica nuevos. P y pesos conservados.

## Archivos completos y manifiesto

El banco completo de cada soporte está en un archivo propio. Todos se
identifican por ruta, longitud, SHA comprimido y SHA canónico en el
[manifiesto](../evidence/loudness_latch_bdf_static_precision_curved_prefix.json.gz).
No se omiten matrices o ramas para reducir tamaño. Los ocho archivos suman
130783176 bytes; el mayor tiene 16488730 bytes.

| Soporte | Bytes comprimidos | SHA comprimido |
| --- | --- | --- |
| [8](../evidence/loudness_latch_bdf_static_precision_curved_prefix_interval_008.json.gz) | 16350931 | `9f08a81e4d7b0fc36cdc550278d616c3a5d296c73d745d8733c8146db7707999` |
| [9](../evidence/loudness_latch_bdf_static_precision_curved_prefix_interval_009.json.gz) | 16464676 | `80e4fe720dbca47d740cc185b1160721e518505d8c54cf0fa5838534a81f4603` |
| [10](../evidence/loudness_latch_bdf_static_precision_curved_prefix_interval_010.json.gz) | 16399374 | `d0c69aacdf51989a0a8e25eb175c80ca80738e470c9497c0227adeb565243fc4` |
| [11](../evidence/loudness_latch_bdf_static_precision_curved_prefix_interval_011.json.gz) | 16158277 | `aa611ff9cacea858cd9f00df691ec219885255c1bdc9e4dbefd2983c336fd0ea` |
| [12](../evidence/loudness_latch_bdf_static_precision_curved_prefix_interval_012.json.gz) | 16249099 | `42aaac9687d304c7c5496dce6e0d2f835f9714954eef9e48a0abe1e7822d1773` |
| [13](../evidence/loudness_latch_bdf_static_precision_curved_prefix_interval_013.json.gz) | 16341212 | `c3a6995d46aef3a52c01c3763f32ec61508cd72837af887a3213608969c873c6` |
| [14](../evidence/loudness_latch_bdf_static_precision_curved_prefix_interval_014.json.gz) | 16488730 | `05864d32dd0e1d278d40ce1b7ad54625debb85dabd89445954796931b06ff2be` |
| [15](../evidence/loudness_latch_bdf_static_precision_curved_prefix_interval_015.json.gz) | 16330877 | `60475543937afb5d7da4eb433bbf13ea67cd9d27e61e06c8a258ceb6a8a3ab95` |

Manifiesto: 701922 bytes, SHA comprimido `89f8686a6b50df6989a072dbcdefa5004ea36087ab4782e198237ff557549ab1`,
canónico `7e6a5a7140e1d9ed8a7b335aca7a1f37081899a3e3e08021918b5a9a9a1a1e3e`. [Resumen](../evidence/loudness_latch_bdf_static_precision_curved_prefix_summary.json).
Datos, seis tests y validator se fijan en `25a09e8` antes de validar.
[Corpus y recibos](BIESTABLE_PREFIJO_CURVO_ENTRADAS.md).

## Límites y siguiente bloque

Son cotas del modelo nominal respecto a una reconstrucción explícita.
Circuito, parámetros, integrador y estados publicados permanecen intactos.
La cobertura completa de la trayectoria, meta global 1 mV, identificación
física, sonido vintage, voz, audio nativo y deadline mantienen sus gates.
Siguiente: [recintos compartidos sobre el prefijo conocido](BIESTABLE_RECINTOS_COMPARTIDOS_PLAN.md).
