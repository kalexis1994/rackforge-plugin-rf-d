# Matrices del rechazo en la nota larga

2026-10-06. Deriva del [protocolo de observación](VOZ_NOTA_LARGA_MATRIZ_PROTOCOLO.md)
y del [protocolo de raíces](VOZ_NOTA_LARGA_RAICES_PROTOCOLO.md).

## Observación sin alterar la trayectoria

Build09 deriva de build08: sólo cambia la selección del observador a
15,94035–15,94045 ms, pasos ≤1e-17 s, iteraciones 100/101 y máximo 16
capturas. Se verifican 4338 archivos fuente; sólo cambia `niiter.c`.
`RFLinearSolve`, dispositivos, tolerancias, stamps e historia permanecen
idénticos. GCC UCRT64 y flags son los mismos; el ejecutable tiene SHA propio.

La primera preparación asumió una declaración `static` que no existía.
El control de anclajes rechazó antes de copiar, compilar o lanzar SPICE.
Se conserva el [recibo inicial](../evidence/voice_full_note_matrix_preflight_rejection01.json)
y el helper fallido; el reintento sustituye exclusivamente ese literal.

| Control | Resultado |
| --- | --- |
| Gear500 corto, observador desactivado | 40 ms completos; 191714 filas, reloj y 18 vectores exactamente iguales al candidato anterior |
| Trap125 largo, observador activado | Mismas 155680 filas, mismo reloj, 18 vectores y mensaje de aborto; cuatro matrices completas |

La [auditoría](../evidence/voice_full_note_matrix_validation01.json)
admite el observador local. El aborto Trap conserva su rechazo: no se
completan 350 ms y no se obtiene una nota admitida.

## Dos raíces independientes de la misma matriz efectiva

Se elige la última pareja completa 100/101, con tiempo, paso, orden y modo
idénticos. Ambas matrices tienen 226 incógnitas y 973 entradas CSC,
tiempo **15,94042072898988 ms**, paso **1,25e-18 s**, orden 1, modo 257
y gmin diagonal cero. Se conserva la matriz efectiva después del gmin,
el RHS, mapa V/A, factor KLU y vector publicado.

Las raíces Decimal 80/120, con datos binary64 convertidos exactamente,
pasan acuerdo y residual de alta precisión. Son cuatro factorizaciones
diagnósticas sobre dos sistemas; no son nuevos pasos físicos ni nuevas
evaluaciones de los dispositivos. El [replay de raíces y pares](../evidence/voice_full_note_matrix_roots_validation01.json)
verifica los residuales compilados, las tres correcciones compensadas y
la publicación final sin nuevas factorizaciones.

| Error máximo de voltaje frente a la raíz | Iteración 100 | Iteración 101 |
| --- | ---: | ---: |
| SMP/KLU original | ≈180,535 mV | ≈180,539 mV |
| Una corrección | 6,847405 mV | 6,847551 mV |
| Dos correcciones | 259,710993 µV | 259,716550 µV |
| Tres correcciones | 9,850418 µV | 9,850629 µV |

La tabla separa voltaje de corriente; no usa un máximo mezclado de unidades.
En la iteración 101, `f4_emphasis_pin7` todavía tiene aproximadamente
9,851 µV frente a un gate de 0,164 µV. `f4_recover_r7_r3` también falla.
La corriente `vpos10#branch` conserva ~10,046 nA frente a su gate de
~0,729 nA. Los [datos completos](../evidence/voice_full_note_matrix_roots01.json)
conservan todas las filas, errores y límites.

**Resultado:** la aritmética compilada reproduce sus fórmulas y mejora
mucho estas soluciones, pero tres correcciones no alcanzan el gate
lineal en estas capturas. El error pequeño del laboratorio anterior de
133 incógnitas no se extrapola a esta red. El mensaje sobre Q7 no
identifica por sí solo la causa de toda la matriz o del aborto.

El [ensayo de seis correcciones](VOZ_NOTA_LARGA_SEIS_CORRECCIONES_PROTOCOLO.md)
primero conserva la publicación original y calcula tres pasos adicionales
sobre una copia con el mismo factor real. Un resultado favorable sólo
admitiría las matrices observadas; después exige candidato activo y
trayectorias propias. No se relajan los gates ni se cambian tarjetas.
