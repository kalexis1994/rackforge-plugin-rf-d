# Corpus de continuación con preparación explícita

El [protocolo](BIESTABLE_CONTINUACION_PREPARADA_PROTOCOLO.md) y productor
se congelan en `571190a` antes de medir. Fuente exacta: variante 0 del
prefijo de 24 soportes, resultado real, P, 22 memorias, reloj y plantilla 23.
Las ocho curvas nuevas se construyen desde las historias 24–31. No se
reutiliza el recinto anterior ni se transporta el resultado del benchmark.

## Archivos y lanzamiento

Diecisiete artefactos completos: ocho plantillas condicionadas, una prueba
de bloque y ocho soportes, con rutas tipadas, esquemas, tamaño y SHA
comprimido/canónico. Conservan curvas, cargas/RC/Q, X/RHS candidatos,
residuales, restos, observadores Decimal100, matrices, inversa, tasas,
presupuestos y cierres. Cada celda identifica el contexto completo y estado
de preparación de su bloque; cada soporte identifica su plantilla.

El lanzamiento termina con exit=0 y snapshots idénticos. Conserva comando,
stdout/stderr y fuente UTF-8 exacta del productor, recuperada desde el blob
del HEAD señalado por su recibo. Los archivos parciales no reemplazan un
manifiesto terminado. Destinos frescos; gates y atributos Git intactos.

## Reproducción primaria

Todos los artefactos, manifiesto, resumen, lanzamiento, ocho tests y
validator se congelan en `163a83f` antes de validar. **Las ocho pruebas
primarias pasan al primer intento en 811,5805674 s**, entradas antes/después
idénticas. Reproducen curvas, endpoints, candidato de burbuja, cargas/RC/Q,
RHS y restos mediante consultas Decimal100 por macrocelda; rehacen ledger,
recinto, inversa, tasas, preparación, cada acción y todos los cierres.

Los **64 presupuestos y 512 subcertificados** del dominio nuevo se recalculan
con el helper preparado y con el control original, comparando todos los
bytes canónicos con el archivo. No se sustituye ese gate por comparación
de picos o SHA aislados. Se verifican contextos/sellos en bloque y celda,
linaje real de las 22 memorias, interfaces, selección y parada contigua.

Los negativos incluyen archivo, ruta, SHA, índice/rango, fuente, plantilla,
reloj, duración, recinto/contexto alterado, proveedor incompleto y banco
vacío. Se comprueba que una duración inválida rechaza antes de construir
bloques o aplicar forcing. Se preservan políticas de redondeo, normas,
dominio del kernel y todos los gates numéricos anteriores.

[Recibo primario](../evidence/loudness_latch_bdf_static_precision_prepared_continuation_validation.json)
y [lanzamiento](../evidence/loudness_latch_bdf_static_precision_prepared_continuation_launch.json).

## Corpus ampliado

Recibo primario y fuentes del corpus se congelan en `54a3c1a` antes de generar.
El archivo se congela en `d9e5a12` antes de validar. Recupera **688 entradas
de 159 informes**, con **202 hashes propios** (159 informes y 43 helpers).
Incluye todo el linaje anterior, el último recibo propio de preparación,
los 17 artefactos nuevos, manifiesto, lanzamiento y recibo primario.

Conserva las tres excepciones históricas LF→CRLF y **19 fuentes de tests**:
dieciocho fallidas y una interrumpida, ligadas a fuente exacta, SHA,
comando, recibo e intento. Se guardan sólo hashes después de comprobar bytes;
no se reescriben fuentes, informes o selecciones históricas. Python y sus
subprocesos se ejecutan con -B, sin generar cachés en el repo.

[Archivo](../evidence/loudness_latch_bdf_static_precision_prepared_continuation_inputs.json.gz),
[resumen](../evidence/loudness_latch_bdf_static_precision_prepared_continuation_inputs_summary.json)
y [recibo del corpus](../evidence/loudness_latch_bdf_static_precision_prepared_continuation_inputs_validation.json).
Las **dos pruebas del corpus pasan al primer intento en 114,9983788 s**,
con hashes antes/después idénticos. Recuperan todos los blobs y las fuentes
archivadas y verifican identidades propias y formas alteradas rechazadas.
Son **diez pruebas nuevas aceptadas**, ocho primarias y dos archivísticas,
ambas suites al primero. No hay nuevos fallos, repetición del productor ni
cambios en fuentes o datos anteriores.

Archivo: **457231 bytes**, SHA comprimido
`4d3b38d2a941d7b110ee732abf7aea66b7c0339a307984f19ff56ddaeff1fd0f`;
canónico `56adc7443186f2a8e92b1aea8be05aa4915a9c3e21a46ee2d9cfa9a36ea473e9`.

Se certifican 32 soportes contiguos hasta ≈325 µs, cota acumulada ≤0,793 µV,
con nuevo pico local ≤0,524 µV. La parada es por límite declarado y no
admite el soporte siguiente. Parámetros nominales/sintéticos; identificación
física, 1 mV global, cobertura completa, sonido vintage, voz, audio nativo y
deadline siguen abiertos. Este banco no mide un ahorro de rendimiento nuevo.
