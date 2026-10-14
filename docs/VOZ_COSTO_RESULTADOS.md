# Menor costo del solver y voz continua de 24 ms

2026-10-14. [Protocolo de costo](VOZ_COSTO_PROTOCOLO.md) y
[trayectoria ampliada](VOZ_COSTO_TRAYECTORIA_PROTOCOLO.md).

## Medición e intervención

En las 24 parejas seleccionadas anteriores, Parts cuesta aproximadamente
0,3 ms y el solve lineal 0,8 ms por evaluación. Estos puntos incluyen KEY
0/10 V y pasos entre 0,98 ns y 1 us; no representan todo el panel.
[Perfil](../evidence/voice_cost_profile01.json).

Se probaron dos variantes, conservando ambas fuentes y sus bancos:

| Variante | Ratio mediano del solver | Peor ratio observado |
| --- | ---: | ---: |
| Orden de cadena + matriz prestada + memoria reutilizada | 0,72998 | 0,85377 |
| La anterior + sustitución triangular con ceros exactos | 0,63424 | 0,69388 |

La segunda reduce aproximadamente un 37 % el costo **del solver en este
banco**. No es una reducción medida del 37 % de toda la voz ni un deadline.
120 mediciones alternadas de 16 solves, calentamiento explícito, en cada
variante. [Primer banco](../evidence/voice_order_bench01.json) y
[variante admitida](../evidence/voice_sparse_bench01.json).

El orden se sugiere con grado mínimo desde dos matrices iniciales admitidas.
Sólo cambia la permutación de 234 filas/columnas de la cadena: cada matriz
futura se copia completa, sin truncar valores pequeños. Su patrón observado
no se convierte en una máscara de omisión. La memoria Prepared se reutiliza
y recibe la matriz por referencia. Las listas triangulares se reconstruyen
desde todos los coeficientes no nulos del factor recién calculado, en orden
creciente de columna. Se mantienen guardas y refinamiento 1e-11.

No cambian componentes, cargas, controles, arranque, Radau, Newton o LTE.
48 Parts de la variante final coinciden por bits con los anteriores:
6048000 campos f64. Direcciones y todos los voltajes/corrientes de las
etapas pasan sus gates. El signed zero no se usa como criterio de fidelidad
de una dirección; la equivalencia por bits se limita a Parts.

Cinco rechazos —NaN, RHS infinito, conexión fuera del bloque, fila singular
y exceso de capacidad— permiten reutilizar después la misma memoria con
dirección válida idéntica por bits. [Prueba](../evidence/voice_sparse_reuse01.json).
Estos casos no son una admisión general de heap o audio thread.

## Trayectorias completas

La voz conserva 250 incógnitas: VCO real/BUS/ambos contornos/ladder/dos
VCA/J7. Dos trayectorias nuevas de 24 ms desde DC propio, máximos de medio
paso 2/1 us, KEY 0/10/0 a 1/6 ms. Continúan sin reset al pasar por 8 ms.

- 26669 y 31916 Accepted: 58585 pasos, 117170 extremos de medios pasos.
- 192 clocks comunes de todos los nodos/corrientes y ambas cargas R59/R60.
- El prefix de 8 ms pasa contra las dos voces anteriores: 128 comparaciones
  de clock; máxima fracción de gate de nodo 2,32028e-6.
- 24 parejas nuevas y dos DC: 12550 filas originales de 251 nodos.
  KCL original máximo 0,0666291 pA; fracción de corrección 7,12456e-6.
- 500000 entradas de tangente efectiva; máxima fracción 0,006599183.
  Dirección densa/Schur y residual lineal pasan; balance BUS <0,001 pA.
- Máxima fracción de refinamiento de nodos 0,002246945, cargas 2,49586e-6.

[Banco](../evidence/voice_sparse_native01.json),
[original y refinamiento](../evidence/voice_sparse_reference01.json),
[prefix anterior](../evidence/voice_cost_prefix01.json).
Tiempo real del laboratorio: 406,9/459,1 s por 24 ms. No comparar esos
tiempos directamente con los de 8 ms como un benchmark de escenas iguales.

La liberación eléctrica se observa conservando R60/C7 y las cargas:

| Clock | C2, V | C5, V |
| --- | ---: | ---: |
| 6 ms, retirada de KEY | 2,077807 | 5,239187 |
| 8 ms | 3,064850 | 5,130095 |
| 16 ms | 2,900450 | 2,830885 |
| 24 ms | 2,744489 | 1,763883 |

C2 continúa atacando después de retirar KEY y luego cae. No se fuerza la
fase ni se acredita liberación completa en esta ventana. El estado nuevo
no prolonga la antigua historia de 164 ms.

## Ráfaga de escucha

Export local `references-local/voice-cost-listening01/voice24.wav`,
[recibo](../evidence/voice_cost_listening01.json). 24 ms reales de J7,
1152 frames mono PCM16 a 48 kHz. Sin repeticiones o concatenación.
Entrada del adaptador: grid 8 kHz, sinc/Hann de 64 taps y banda nominal
2,8 kHz; padding constante en los extremos y ganancia DC unitaria del kernel.
Monitor fijo 4 muestras/V, sin normalización por pico o retirada de DC;
fades de 0,5 ms únicamente en los bordes. Pico 0,013695 FS, sin clipping.
Es una ráfaga corta y tenue del laboratorio; no una nota sostenida ni un
instrumento listo para tocar, y no prueba parecido con una unidad vintage.

## Siguiente prioridad

La optimización conserva el circuito detallado y mejora parcialmente su
costo. Se necesitan una reducción mayor y duración útil para un motor
audible y utilizable. Usar esta voz cargada como referencia para medir
error de salida, frecuencia, contornos y reacción de los puertos; mantener
separados ese error musical, precisión interna y deadlines. Sin nueva
admisión de MIDI, panel general, hardware, heap/deadlines o tiempo real.
