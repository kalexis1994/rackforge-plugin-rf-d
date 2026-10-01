# B3 y C3 desde los mismos dos historiales aceptados

## Experimento declarado

El [contraste desde DC](BIESTABLE_TERCERA_MALLA_BDF2.md) mezcla diferencias
acumuladas en el prefijo con diferencias generadas durante la región rápida.
Este experimento condiciona ambas políticas a **la misma memoria doble C3**,
sin modificar los informes originales ni interpretar C3 como solución exacta.

Antes de medir se fija el límite del anclaje a 2,3 ms, el fin a 3 ms y el
gate a **1 mV máximo en los 94 nodos**. Se elige el último extremo C3 aceptado
que no supera ese límite: índice 343, tiempo **2,2968750000000016 ms**.
Se conservan corriente/voltaje de ambos estados, 21 memorias lineales,
cuatro cargas BE/BC, colas compensadas, intervalo anterior de 3,125 µs,
fuentes KEY=10 V y firma del circuito. La propuesta inicial común es 3,125 µs.

Se mantienen R61=200 Ω, BUS=0 V, perfil sintético `finite_transit` y los
parámetros/topología del [BDF2 sobre carga](BIESTABLE_BDF2_CARGA.md).
No se recalcula DC ni se arranca Euler. B3 usa sus tolerancias originales:
25 µV absolutos, 2,5e−5 relativos, incremento BE/BC máximo 25 mV, producto
h·λ+ máximo 0,05, h máximo 100 µs, mínimo 1 ps y 3000 intentos.
Cada rechazo conserva ambos historiales. KCL <10 pA, corrección <10 nV,
ecuación de rama <10 fV y crecimiento real de intervalo ≤2 permanecen iguales.

El tramo C3 posterior al anclaje **se hereda** del informe existente.
Se verifica otra vez cada publicación directamente con Decimal80 y su
linaje. No se cuenta como integración nueva. Fijar los historiales también
fija sus intervalos numéricos y la primera propuesta; el contraste no aisla
un único voltaje físico del prefijo ni permite sumar linealmente máximos.

## Resultados

| Dato | Resultado |
| --- | ---: |
| Intervalos B3 nuevos | 1992, todos BDF2 |
| Rechazos B3 nuevos | 33, voltaje/incremento de juntura |
| Intervalos C3 heredados y verificados | 4019 |
| KCL máxima B3 publicada | 9,91743 pA |
| Cobertura común | 2,296875..3 ms |
| Reinicios de historial / raíces alternativas elegidas | 0 / ninguna |

Ambos tramos terminan en 3 ms. La comparación incluye el anclaje y 6007
tiempos de la unión de extremos; no hay salto de fuente inicial que excluir.

| Comparación | Máximo interpolado | Diferencia final |
| --- | ---: | ---: |
| B3 original / C3 original, misma ventana | 126,367797 mV | 39,8792 µV |
| B3 desde memoria común / C3 heredado | 28,945598 mV | 57,7053 µV |

El nuevo máximo está en `ATTACK_OUT`, nodo 67, a 2,422167969 ms.
Una consulta conservativa al mismo instante reduce ese punto a **2,122804 mV**.
Ese valor sigue por encima de 1 mV y **no es el máximo continuo ni el máximo
de todos los puntos consultables**. El siguiente corte observa los máximos
de cada nodo y la rejilla retenida para evitar seleccionar sólo el pico
dominado por interpolación. El gate condicional interpolado permanece fallido.

Los cruces interpolados C3−B3 común dan +0,1235 ns en ATTACK_OUT=4 V
ascendente y −4,8477 ns en RESET_COLLECTOR=0,5 V descendente. En el contraste
original desde DC eran −14,5780 ns y −22,8504 ns. Son diferencias muestreadas
sin cota de incertidumbre temporal; no son errores respecto de hardware.

## Reproducción y regresión

Productor: `tools/loudness_latch_bdf_common_history.py`.

Datos nuevos: `evidence/loudness_latch_bdf_common_history.json.gz`.

Resumen: `evidence/loudness_latch_bdf_common_history_summary.json`.

`python tools/loudness_latch_bdf_common_history.py`

`python -m unittest discover -s tests -p test_loudness_latch_bdf_common_history.py -v`

Seis pruebas verifican el anclaje completo, todos los intervalos nuevos,
los 4019 heredados, conservación en rechazos, decisiones locales seleccionadas,
comparaciones al reloj original, consulta del pico, fuentes y almacenamiento
canónico sin pérdidas. La memoria C3 heredada no se duplica en el nuevo
archivo: su origen queda identificado por hash e índice.

## Alcance

El resultado distingue sensibilidad al historial entrante y sensibilidad
posterior entre estas dos políticas. No identifica una solución exacta,
no valida el prefijo desde DC y no demuestra fidelidad de conmutación vintage.
El contraste original de 126,37 mV conserva su fallo. No se admiten una cota
global/continua, trayectoria completa desde DC, física ni audio.
