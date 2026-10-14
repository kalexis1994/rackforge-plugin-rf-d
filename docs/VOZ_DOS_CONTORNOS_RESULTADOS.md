# VCO real, ambos contornos y cadena en una sola voz

2026-10-14. [Protocolo previo](VOZ_DOS_CONTORNOS_PROTOCOLO.md).

## Cierre funcional

250 incógnitas simultáneas, 251 en el original con cursor Amount. VCO1
CA3046 genera la sierra, frecuencia y reset desde sus dispositivos; el BUS
comparte C27 y la carga real del ladder. Se retiraron OSC1 de OnMixer y la
sinusoide del laboratorio. R6/R45 del panel siguen dentro del VCO. Ambas
redes de contorno, gatillo, Q26/Q28 y C18 permanecen únicas y cargadas.
No se impone una onda ni una frecuencia periódica a la entrada del filtro.

Las otras ramas están omitidas del subgrafo ON del mixer; este banco no
recrea sus contactos OFF. Alimentaciones ideales, segundo VCA a 2 V y
panel fijo permanecen como fronteras. CV del VCO son voltajes de placa
nominales, no notas MIDI calibradas ni capturas de una unidad física.

Arranque DC nuevo con RAMP_C1=0 V condicionado: corriente de restricción
-16,399949 uA, retirada al iniciar el transitorio. Todos los capacitores
parten de esa solución, incluido el acoplamiento C27. Semillas aisladas
no se publicaron como historia conjunta. La raíz original de 251 nodos
admite ese arranque; no prolonga los anteriores 164 ms o sus WAV.

## Trayectorias y evidencia

Dos escenas completas de 8 ms, máximos de medio paso 2/1 us. KEY cambia
a 10 V a 1 ms y se retira a 6 ms; contacto S abierto, C11/C12 ausentes.

- 9904 y 11485 Accepted: 21389 pasos, 42778 extremos de medios pasos.
- 64 clocks comunes para las 250 incógnitas y corrientes R59/R60.
- 24 parejas Radau seleccionadas y dos DC: 12550 filas originales.
- KCL original máximo 0,066629 pA en etapas; máxima fracción del gate
  de corrección 7,12456e-6. Slots MNA conservan sus unidades y gates propios.
- Fracción máxima de refinamiento de nodos 0,002246945; cargas 2,47137e-6.
- Seis rechazos de entradas conservan el estado completo.
- Balance BUS en todos los extremos: máximo <0,001 pA.

[Banco nativo](../evidence/dual_voice_native02.json),
[referencia original y refinamiento](../evidence/dual_voice_reference01.json),
[observaciones](../evidence/dual_voice_observations01.json).

La partición lineal conserva dos LM741 de 64 incógnitas de dos etapas,
cadena/contornos de 234 y exterior de 138. Sólo BUS de ambas etapas une
la cadena con el VCO. Guardas de estructura y refinamiento heredados se
aplican sobre la matriz nueva. Dos matrices efectivas de 500 x 500 se
comparan contra el original, eliminando únicamente sus dos cursores Amount:
500000 entradas, fracción máxima 0,006599183. Comparador suplementario
con piso numérico 2e-9 en la unidad fila/columna y relativo 2e-5; las filas
KCL y MNA no se interpretan todas como conductancias.

Direcciones Schur/denso difieren como máximo 4,749e-17 del gate de
corrección; residual lineal relativo 2,558e-22. Esta comparación finita
no acredita todas las matrices futuras ni deadlines. Oráculo VCO Decimal100
con historia exacta de floats más cadena original y su cursor explícito;
audita candidatos nativos, sin búsqueda transitoria independiente de raíces.

## Señales sin adaptación

Extremos del grid de 125 us, escena 1 us; no cotas continuas.

| Señal | Mínimo, V | Máximo, V | A 8 ms, V |
| --- | ---: | ---: | ---: |
| Sierra del VCO | -1,762596 | 1,849361 | 0,728341 |
| BUS | 0,890751 | 0,928817 | 0,904732 |
| C2 | 0,860201 | 3,065774 | 3,064850 |
| C5 | 0,860557 | 5,250694 | 5,130095 |
| Base del VCA | -0,276838 | 1,774867 | 1,774030 |
| J7 | -0,00343667 | 0,000926550 | 0,000672056 |

BUS conserva el DC y la historia propia de C27; no se elimina ni se
normaliza. Retirar KEY no equivale a liberar inmediatamente ambos
contornos: R60/C7 mantienen el gatillo. Los 2 ms finales no acreditan
la liberación completa ni una nota sostenida. No se exporta una escucha
nueva de 8 ms ni se repiten ciclos para aparentar una nota larga.

## Intentos y siguiente trabajo

Dos fallos del preparador quedan conservados con fuente y replay: título
heredado de una partición anterior y sustitución de dimensiones que también
tocaba IDs físicos. La reparación excluye los mapas nuevos de esas
sustituciones y exige partición completa sin duplicados. El primer intento
de compilación usaba un módulo privado de la rlib; se conserva su replay y
se usa el helper VCO previamente congelado por bytes, sin recompilar la
biblioteca. No cambiaron dispositivos o gates numéricos.

Las escenas tardan 186,4/207,0 s por 8 ms de señal. El circuito funcional
ya está unido, pero este motor detallado sigue siendo una referencia de
laboratorio. Próximo trabajo: reducir costo contra esta voz cargada,
conservando puertos, estados relevantes y error medido, para extender la
trayectoria a una nota audible. Panel general, MIDI, fidelidad física,
heap/deadlines y tiempo real permanecen pendientes.
