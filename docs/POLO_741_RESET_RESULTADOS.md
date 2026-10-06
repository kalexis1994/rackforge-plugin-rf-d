# L2 del macromodelo 741: historia fija y precisión representable

2026-10-06. Se ejecutó el [protocolo congelado](POLO_741_RESET_PROTOCOLO.md).
La [auditoría](../evidence/voice_inductor_observation01.json) reproduce las
mediciones y sus identidades sin nuevos solves. Los
[cuatro recibos](../evidence/voice_inductor_runs01.json) conservan fuentes,
ejecutable, módulo XSPICE, inicialización y exportaciones antes/después.

## Observación admitida en el build local

Se copiaron las 4337 fuentes anteriores y el build configurado en un directorio
privado nuevo. Sólo se extendieron `niiter.c` e `indload.c` con observadores;
las ecuaciones del circuito permanecieron iguales. La compilación usa el
GCC 16.1.0 y las opciones del [build anterior](NEWTON_RESET_RESULTADOS.md).
El árbol anterior, el ejecutable oficial y el audio previo se conservan.

| Escena | Sonda apagada y encendida frente al baseline anterior | Resultado |
| --- | --- | --- |
| BUS cero | 219538 tiempos y seis vectores exactamente iguales | 40 ms completos |
| BUS variable | 7724 tiempos y seis vectores exactamente iguales | Rechazo conservado; último aceptado 2.277414365034117 ms |

Son cuatro solves nuevos. El oficial tiene 223220/7729 filas y otro reloj;
estas observaciones pertenecen al build local. La sonda no explica todavía
la causa del fallo del ejecutable oficial.

## La hipótesis del RHS variable queda refutada en la ventana

Se parearon cargas y solves de L2 por secuencia, rama, corriente anterior,
tiempo y paso; se distinguieron intentos aunque compartan tiempo representado.
En BUS variable hay 2897 pares y 811 grupos con coeficientes e historia fijos.
**Ninguno cambia el RHS histórico estampado.** El último intento tiene
101 iteraciones: el flujo provisional toma 72 valores, mientras historia y
fuente equivalente conservan un único valor. BUS cero confirma cero cambios
en sus 5097 grupos y 11456 pares.

La condición para ensayar la suma histórica directa no se cumple. Esa variante
queda **no medida**, sin parche numérico ni admisión. La suma directa binary64
también conserva el mismo RHS en el último intento; no evita su redondeo.

## Ecuación constitutiva y escala numérica

Decimal con 80 dígitos reconstruye los números binary64 publicados. Se evalúan
la fila `v98-v17-req*i-veq` y la ecuación de flujo publicada, conservando sus
distintas operaciones. Esto observa una fila constitutiva; no mide toda la
KCL no lineal ni proporciona una solución independiente del circuito.

En el último intento, Gear de orden 1 usa h≈5e-18 s y
`req=1.0610000000000002e17 ohm`. El término histórico es aproximadamente
−1.2864461393e10 V, frente a un voltaje terminal final de 1.172216929 mV.
La fuente histórica es un término del sistema discretizado, no un voltaje
físico de alimentación.

| Magnitud | Máximo absoluto en la ventana BUS variable |
| --- | ---: |
| Redondeo del RHS frente a suma histórica Decimal | 0.331973530 µV |
| Residual de la fila estampada | 2.442014444 µV |
| Residual con el flujo publicado | 2.405992949 µV |
| Voltaje equivalente a un ulp de corriente de rama | 2.808443616 µV |
| Mejor residual con corriente binary64 y terminales observados fijos | 1.382425902 µV |

El ulp de corriente final vale 2.64697796017e-23 A. Se busca el mejor valor
entre el representable más cercano a la solución escalar y sus vecinos.
Ese contraste fija los terminales observados: no limita una solución de la
matriz completa donde también cambian los voltajes. Los máximos anteriores
aparecen en el último intento. En su iteración 101, la fila estampada tiene
56.4494195 nV de residual; el flujo publicado tiene 2.252670946 µV.

La [sonda anterior](NEWTON_RESET_RESULTADOS.md) observó una corrección final
de unos 0.2076 mV en el nodo 17, con tolerancia de unos 10.14 nV. La escala
de representación de L2 merece investigarse, pero estos residuales de fila
no atribuyen por sí solos esa corrección ni los rechazos de ambos JFET.
L2 es un elemento del macromodelo TI, no una inductancia física identificada
dentro del 741 vintage.

## Siguiente bloque y límites

Observar KCL y acoplamientos de los nodos 16/17 con G4/EOS, e identificar
el efecto de la escala de incógnitas sobre la matriz completa. Formular un
protocolo nuevo antes de ensayar otra representación de corriente o historial;
exigir equivalencia algebraica, estado DC, control completo y gates anteriores.
Después contrastar builds y volver a cerrar R45/contorno.

Pasan [31 regresiones enfocadas](../evidence/voice_inductor_tests01.json),
incluidos asociación de registros, NaN tardío, tiempos repetidos, Gear 2 y
cancelación escalar con Decimal. No se admite la unión VCO/contorno, física,
tiempo real o audio nuevo. Las fuentes primarias de ngspice quedan fijadas
en el protocolo y el modelo TI conserva su hash anterior.
