# Prefijo contiguo con forcing dirigido y primer soporte sin certificar

## Fuentes y banco

Modelo documental CA3046 nominal con parámetros sintéticos intactos.
Fuente declarada: certificado secundario [1,1] del cuarto intervalo,
direct_and_memory de radio 1 µV. La selección primaria anterior [1,0]
permanece intacta. Se conservan P, pesos, normalización, 22 memorias,
pico entrante, reloj e interfaces de potenciales y cargas.

[Protocolo](BIESTABLE_PREFIJO_DIRIGIDO_PROTOCOLO.md),
[helper](../tools/loudness_latch_directed_prefix.py) y
[productor](../tools/loudness_latch_bdf_static_precision_directed_prefix.py)
se congelan en `a3489f8`. Datos, diez tests y validator, en `16e5053`.
Límite previo: ocho intervalos adicionales, radios 0,1/1/10 µV,
una variante direct_and_memory y selección del primer radio aceptado.
Se intentan tres soportes; dos cierran y el siguiente detiene la cadena.

## Cierre real y presupuestos locales

| Índice del intervalo | Endpoint aproximado | Pico local del tubo de 1 µV | Resultado |
| --- | --- | --- | --- |
| 4, quinto | 3,125 µs | 82,34834162 nV | Aceptado, radio índice 1 |
| 5, sexto | 6,25 µs | 324,0874412 nV | Aceptado, radio índice 1 |
| 6, séptimo | 12,5 µs | 1290,396602 nV | No cierra; primer soporte sin certificar |

El prefijo real contiene **seis intervalos contiguos desde t=0+ hasta
aproximadamente 6,25 µs**, con **error nodal exterior ≤0,754 µV**.
El máximo total sigue siendo ≈753,2987539 nV del prefijo anterior.
El tiempo exacto certificado es 7378697629483821/1180591620717411303424 s;
el endpoint intentado es 7378697629483821/590295810358705651712 s.
No se transporta la memoria saliente del séptimo tramo rechazado.

Los picos nuevos están en la celda 7, nodo índice 81. En el séptimo:
anclaje ≈323,9003508 nV y forcing ≈966,4962508 nV en ese mismo nodo.
La contribución del grupo 20, C7, suma ≈1290,396586 nV y domina la cota;
el término algebraico directo allí es ≈1,5982857e-14 V. La acción dirigida
ha eliminado el límite algebraico anterior, pero no basta para cubrir
este forcing de memoria. Estos números son presupuestos condicionales
del tubo, no error observado de una unidad física.

## Recintos renovados y coste

Se calculan **24 precondicionadores candidatos, 48 recintos de inversa,
4752 consultas LDL de tasa y 384 certificados de acción de subcelda**.
Cero solves de trayectoria y cero métricas nuevas. Cada soporte tiene
sus propios recintos y tasas: conservar P no reutiliza una contracción
futura. En radio 1 µV, q máximo crece aproximadamente de 0,058211703069
hasta 0,058211703111; la tasa balanceada interna de junturas permanece
≈−20,0874 millones/s. Una tasa interna negativa no cierra el tubo completo.

Cada acción mantiene las 119 ecuaciones, polinomios firmados, restos
uniformes y corrección constitutiva independientes, defecto y cola.
Se intersectan presupuestos del mismo término/soporte y se propagan
memorias individuales con kernels de endpoint y pico. No hay reset,
retiming, regularización, eliminación de corrientes ni cancelación de restos.

## Otros radios y límites del registro

El radio 0,1 µV no admite el pico entrante y se descarta en los tres
soportes. El radio 10 µV del quinto tramo produce una cota racional
enorme y rechaza inclusión; su diagnóstico binary64 muestra una etiqueta.

Las ramas de 10 µV de los soportes sexto y séptimo encuentran el límite
predeterminado de **4300 dígitos al convertir un entero a texto en Python**.
El cierre conserva la excepción y devuelve una rama no admitida; **no se
publica un presupuesto final de esas dos ramas ni se afirma escape
matemático a partir de la excepción**. Sus recintos, tasas y acciones
anteriores al fallo quedan archivados. La reproducción fija ese límite
para verificar el intento exacto. Ninguna alimenta el prefijo certificado.
La [repetición separada de los cierres](BIESTABLE_CIERRES_ENTEROS_RESULTADOS.md)
fija una política explícita sin límite decimal y obtiene ambos presupuestos
exactos: los dos exceden el tubo de 10 µV. Conserva estos intentos y sus
fuentes; no reescribe los informes, selecciones o gates anteriores.

## Evidencia y alcance

[Datos](../evidence/loudness_latch_bdf_static_precision_directed_prefix.json.gz):
94127787 bytes; SHA comprimido
`46e7bf265d5f2cf509ef7395596e48e7d8c367b88394125b5d46265297df4c12`,
canónico `44a08fb7a2520d13fa720f6e8288ec116b5eabd57b68698ce60e4e889c82f451`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_directed_prefix_summary.json),
[recibo primario](../evidence/loudness_latch_bdf_static_precision_directed_prefix_validation.json)
y [corpus completo](BIESTABLE_PREFIJO_DIRIGIDO_ENTRADAS.md).

Las diez regresiones primarias pasan al primer intento en **504,8150407 s**,
con entradas idénticas antes/después. La validación reproduce todas las
inversas, recintos, RHS, acciones, tasas,
conversiones, cierres y la sucesión, además de controles exactos de
matriz variable, restos independientes, cambios de paso y memoria dirigida.
El corpus recupera 535 entradas de 94 informes y 130 hashes propios.
Sus dos pruebas pasan al tercer intento, conservando ambos fallos y sus
fuentes; las catorce primarias pasan al primero. Son dieciséis pruebas
nuevas aceptadas. El [siguiente plan](BIESTABLE_FORCING_MEMORIA_PLAN.md) estudia C7 y su
acción temporal sobre el mismo primer hueco. Trayectoria completa, meta
global de 1 mV, parámetros físicos, sonido, motor nativo y deadline siguen abiertos.
