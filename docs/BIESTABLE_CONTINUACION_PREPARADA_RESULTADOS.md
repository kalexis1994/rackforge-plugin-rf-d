# Continuación con acciones preparadas: treinta y dos soportes

El [protocolo](BIESTABLE_CONTINUACION_PREPARADA_PROTOCOLO.md) y productor
se congelan en `571190a` antes de medir. Fuente exacta: variante 0 de la
[continuación compartida](BIESTABLE_CONTINUACION_COMPARTIDA_RESULTADOS.md),
24 soportes, resultado real final, 22 memorias, P y plantilla del soporte 23.
El [benchmark de preparación](BIESTABLE_ACCIONES_PREPARADAS_RESULTADOS.md)
autoriza el helper dentro de su alcance; no aporta el anclaje de esta continuación.

## Banco nuevo y transporte

Ocho referencias curvas nuevas, índices **24–31**, con historias y pasos
reales de ≈12,5 µs. Cada plantilla conserva X/RHS candidatos de burbuja C7,
curva, cargas, RC/Q, restricciones, forzamiento, residual, RHS de 119
ecuaciones, restos independientes y tres observadores Decimal100. Sus
endpoints coinciden con las historias publicadas. Se archivan como plantillas
condicionadas; su existencia no admite tiempo.

El ancho **8** cierra las ocho historias en radio **1 µV**. El radio 0,1 µV
rechaza por la cota entrante. Se detiene el banco en la primera rama completa;
no se miden anchos 4/2/1. Cada alternativa habría partido de la misma fuente,
con parada en primer hueco y selección del prefijo más largo y primero en empate.

**32 soportes contiguos hasta ≈325 µs**, extremo exacto
`5995191823955603/18446744073709551616` s. Cota acumulada
**7,928168411011273e-7 V**, ≤0,793 µV, heredada del prefijo anterior.
`first_gap_index=null`, `stop_reason=declared_limit`: no certifica el soporte siguiente.
Cada soporte paga su duración real y transporta las 22 memorias sin reset.

| Índice | Extremo aproximado, µs | Pico local, µV | Error final real C7, µV |
| --- | --- | --- | --- |
| 24 | 237.5 | 0.423169794 | 0.422774865 |
| 25 | 250.0 | 0.428962139 | 0.428386679 |
| 26 | 262.5 | 0.434839438 | 0.433980641 |
| 27 | 275.0 | 0.441109145 | 0.439554930 |
| 28 | 287.5 | 0.447886100 | 0.445106667 |
| 29 | 300.0 | 0.455678501 | 0.450631311 |
| 30 | 312.5 | 0.464729459 | 0.456121713 |
| 31 | 325.0 | 0.523143645 | 0.461566643 |

El pico local nuevo es **≤0,524 µV**, distinto del acumulado ≤0,793 µV.
El máximo local del soporte 31 está en **nodo 66, celda [1/2,5/8]**;
no es el extremo de C7. C7 termina con **≤461,567 nV**, frente a ≤417,147 nV
de la fuente anterior. El archivo conserva el desglose anclaje/forcing por nodo.
P, pesos, escalas, norma, conversiones y gates conservan su significado.

## Recinto nuevo y dependencia explícita

X se elige en índice **27**, u=1/2, con descriptor Decimal100 e inversa
candidata binary64. Se verifica identidad analítica de stamps y ledger de
**704 rangos completos**, 88 leyes por ocho curvas, incluyendo interiores
Bernstein y tubo futuro. La codificación afín de rangos no es una curva.
El descriptor medio nuevo cumple **q≈0,0584035204<1**; inversa y tasas se
renuevan sobre este dominio. No se reutiliza el recinto de 125→225 µs.

measure_variant recibe explícitamente el módulo de acciones. Después de
certificar cada bloque y radio, crea una preparación inmutable de X, D, E,
q y factores exactos. Contexto completo e integridad del estado se identifican
en bloque y macrocelda y se verifican por budget. Cada RHS firmado, resto,
duración y norma se recalcula. La preparación anterior no se reutiliza.

Contexto: `73b3fd97921e78eda62be490ad67bd72f4b3d81606243ad25766217331f65f9b`.
Estado: `fda9f0818d3f7f2dd58f7862fe22a6b6a5c351b4000ec558276af07839fbc272`.

Se valida cardinalidad y duración física de los ocho RHS/forzamientos por
soporte antes de construir bloques o aplicar forcing. El productor conserva
helper original, preparación y circuito congelados; no reemplaza funciones
históricas mediante estado global. Corrección, cola, intersección, redondeos
dirigidos y refinamientos punto/L1 permanecen íntegros.

## Costes y archivos completos

| Operación nueva | Cantidad |
| --- | --- |
| Candidatos de referencia/burbuja | 8 |
| Candidato de bloque | 1 |
| Recinto uniforme de inversa | 1 |
| Consultas LDL de tasa | 99 |
| Preparaciones exactas | 1 |
| Llamadas budget | 64 |
| Certificados de subcelda | 512 |
| Solves de trayectoria / sistemas nuevos de P | 0 / 0 |

Los nueve candidatos incluyen curvas nuevas y bloque. Preparaciones, budgets
y subcertificados son contadores distintos. Este banco no mide ahorro de
tiempo ni hereda el 24,39 % del banco anterior; no prueba deadline de audio.

**17 artefactos completos**: ocho plantillas, un bloque y ocho soportes;
suman **96351437 bytes**, máximo **11208278 bytes**. Cada soporte identifica
su plantilla y bloque. El manifiesto verifica ruta tipada, esquema, tamaño,
SHA comprimido/canónico e identidad; se conservan todas las matrices y ramas.
Los archivos parciales no reemplazan la publicación terminada.

[Manifiesto](../evidence/loudness_latch_bdf_static_precision_prepared_continuation.json.gz)
y [resumen](../evidence/loudness_latch_bdf_static_precision_prepared_continuation_summary.json):
**1369217 bytes**, SHA comprimido
`a98935f528346c2c4002ec0cea2bc79fb66d41f9c3a02f1bd9292b6e5384af79`;
canónico `094a5bee2613557b2c81b2bebf13214d074c7525ed3a6c2653c3e2e0f739f0e0`.
[Lanzamiento](../evidence/loudness_latch_bdf_static_precision_prepared_continuation_launch.json)
con comando, stdout/stderr, exit=0, fuente UTF-8 exacta y snapshots idénticos.
Datos, ocho tests y validator se congelan en `163a83f` antes de validar.
[Corpus y recibos](BIESTABLE_CONTINUACION_PREPARADA_ENTRADAS.md): diez pruebas
nuevas aceptadas, ocho primarias y dos archivísticas, ambas suites al primero.
688 entradas de 159 informes y 202 hashes propios; 19 fuentes históricas
conservadas, sin fallos nuevos o repetición del productor.

Circuito CA3046 nominal y parámetros sintéticos. Integrador, datos y fuentes
anteriores, gates y atributos Git se conservan. 1 mV global, cobertura
completa, identificación física, sonido vintage, voz, audio nativo y deadline
siguen abiertos. Próximo:
[segundo banco con acciones preparadas](BIESTABLE_CONTINUACION_PREPARADA_SEGUNDA_PLAN.md).
