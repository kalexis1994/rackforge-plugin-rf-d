# Retorno desde la raíz condicionada: C27

2026-10-11. Model D clásico CA3046. Memoria corregida 0,
máximo del calendario original 125 ns, misma escena R61=200 Ω.
[Protocolo previo](VOZ_RETORNO_CONDICIONADO_PROTOCOLO.md),
[inputs](../evidence/voice_conditioned_return_inputs01.json),
[nativo](../evidence/voice_conditioned_return_native01.json),
[oráculo](../evidence/voice_conditioned_return_reference01.json),
[QA](../evidence/voice_conditioned_return_tests01.json).

## Unión del origen con ambos resets

La raíz de 218 filas desde seed frío reproduce por bits el estado
HIGH/LOW y sus 18 corrientes de retención de
[la base admitida](VOZ_BASE_CARGAS_CORREGIDAS_RESULTADOS.md).
También reproduce las 3924 entradas de B218×18. La fase inicial x43=0
y las 18 coordenadas objetivo definen el dominio; la liberación elimina
las corrientes artificiales del condicionador. Las leyes del circuito
y la biblioteca nativa permanecen idénticas.

Se propagan las 18 columnas desde t=0 por 42544 medios pasos hasta
el segundo bracket. Cada uno de los siete observables reproduce la
traza anterior por bits. Seis fixtures completos y las primeras dos S
(14400 coordenadas) coinciden por bits. Los resets usan los endpoints
20188/20189 y 42542/42543, observador x43=−2 creciente interpolado.
Ambas proyecciones de 18 RHS coinciden por bits con dos lotes de nueve
(7272 respuestas); controles nulos en 20 pasos y ambos eventos.

T=t2−t1 y D=Z2−Z1 se diferencian conservando el término de fase.
La columna de C27 es la 5 del objetivo condicionado, unidades de tensión
de rama inicial. Se permite que BUS y nodos algebraicos se restauren;
el [intervalo anterior](VOZ_INTERVALO_RETORNO_RESULTADOS.md) partía antes
del primer bracket con inyección aislada 139 y BUS fijo. Son derivadas
de dominios distintos, por lo que sus valores no son intercambiables.

## Historias propias y contraste

Cuatro raíces perturbadas nuevas, ±epsilon y ±epsilon/2 en objetivo 5,
mantienen los otros 17 objetivos y fase. Cada una recorre sus 42544
pasos desde su propio origen: 170176 solves no lineales perturbados.
Se conservan raíces/corrientes y ambos brackets completos. Las cinco
raíces suman 1090 ecuaciones auditadas. El oráculo evalúa candidatos
nativos; no busca raíces no lineales independientes.

epsilon=2.70816191782e-06 V y gain=3.69254140021.
La reducción incluye Bx inicial y todas las 400 coordenadas de todas
las etapas nativas, con escalas 1e−5 V y 1e−8 A. El auditor verifica
los límites en las muestras; no recalcula el máximo de todos los pasos.
Los dos tamaños contrastan raíz, estado en fase, cada tiempo de reset,
periodo y deriva. La respuesta escalada de rampa proyectada≤1e−18 V.

20 operadores preseleccionados: 360 direcciones/144000 coordenadas y
8000 ecuaciones dinámicas. DC VCO Decimal100, cadena Python heredada,
masa antigua y Jacobiano de etapas independientes. Sólo los dos primeros
pasos propagan una base independiente propia; las demás muestras reciben
U nativa. La FD completa admite únicamente C27. Las otras 17 columnas
tienen operadores contrastados y respuesta nativa, sin FD completa.

| Contraste | Peor ratio frente a gate 1 |
|---|---:|
| Base condicionada | 4.55280363e-05 |
| FD de raíces | 3.28056822e-06 |
| Operadores seleccionados | 0.00221320845 |
| first_event | 5.45699603e-06 |
| second_event | 2.18239955e-06 |
| first_time | 0.00232012185 |
| second_time | 0.00600304268 |
| period | 0.00429571625 |
| drift | 7.63939551e-06 |
| capacitor_drift | 2.35613902e-09 |

Al tamaño completo, el cambio previsto de periodo es
-1.12773679113e-14 s,
1127.73679
veces el piso absoluto de 1e−17 s. El cambio previsto de deriva J7 es
1.73056138838e-09 V,
0.173056139
veces el piso de 1e−8 V. Pasar un gate dominado por su piso no resuelve
esa respuesta relativa: el recibo conserva cambios observados/predichos
y ratios efecto/piso para J7, periodo y las 18 ramas, en ambos tamaños.

Gates heredados: raíz/base 1e−6 V/V o 1e−10 A/V +3e−4 relativo;
cambios de etapa/evento/deriva 1e−8 V o 1e−11 A +1e−4 relativo;
tiempo/periodo 1e−17 s +1e−4 relativo; ramas 2e−8 V +1e−4 relativo.
Las raíces pasan sus 218 filas, fase/cargas≤1e−11 V; el estado observado
pasa 1e−13 V o 1e−16 A y alpha≤2e−15. No se relajaron gates.

## Valores medidos

| Magnitud | Valor | Unidad |
|---|---:|---|
| Periodo observado | 0.00243426399764324 | s |
| Respuesta del primer reset | -4.21351716526e-09 | s/V objetivo |
| Respuesta del segundo reset | -8.37773195504e-09 | s/V objetivo |
| Respuesta del periodo | -4.16421478978e-09 | s/V objetivo |
| Deriva base J7 | -0.000224263234611 | V |
| Respuesta de la deriva J7 | 0.000639016957219 | V/V objetivo |

Se reportan las 18 ramas, no sólo J7. El riel fijo cancela en diferencias;
la coordenada de incidencia absoluta contra PLUS no es tensión física
de rama. Para derivadas respecto de carga C27 en coulombs, dividir la
columna por 10 µF. ΔQ=C·Δv, sin redefinir el origen del objetivo.

| Rama | C en F | Deriva base V | Respuesta V/V objetivo C27 |
|---|---:|---:|---:|
| 0 | 6.8e-08 | 0.000422605576071 | 9.4764359654e-05 |
| 1 | 6.8e-08 | 0.000975599923424 | -0.0022461036367 |
| 2 | 6.8e-08 | 0.000886711084763 | -0.00443078956081 |
| 3 | 6.8e-08 | 0.000237921356059 | -0.00439982894481 |
| 4 | 0.00022 | 1.67740575858e-06 | 0.000261372378866 |
| 5 | 1e-05 | 2.13791727091e-06 | -0.00599567391915 |
| 6 | 2.2e-07 | 0.000118709450916 | 0.000641463918394 |
| 7 | 2.2e-07 | -0.000121365079546 | -0.00068974974452 |
| 8 | 0.0001 | 0.000673634167496 | 0.00377045120033 |
| 9 | 3.3e-07 | 0.00385971569042 | 0.0208259730889 |
| 10 | 0.00022 | 5.69874070914e-06 | 3.03486578048e-05 |
| 11 | 0.00022 | 6.67950250271e-08 | 4.82892831834e-07 |
| 12 | 1e-05 | 0.000922366139793 | 0.00488594156487 |
| 13 | 2.5e-06 | 0.000503801875802 | 0.0026258316377 |
| 14 | 2.2e-10 | -0.00277608970747 | 0.00856386194565 |
| 15 | 0.0004 | 7.62194162565e-05 | 0.000396658106433 |
| 16 | 1e-10 | 0 | 2.88056700926e-31 |
| 17 | 1e-05 | 6.52825781258e-05 | 0.00035773982253 |

## Alcance y siguiente bloque

Admitida la respuesta de C27 desde la raíz condicionada de esta memoria
hasta ambos resets, en el calendario y observador declarados. Todavía
no se admite corrección dinámica de las 18 cargas, mapa de Poincaré,
memoria periódica asentada, evento continuo o selección adaptativa.
El recibo conserva también la matriz nativa 18×18 de respuesta de deriva
y los dos tiempos/periodo para todas las columnas, rotulados sin FD
completa. Sirven para formular una dirección de corrección como hipótesis;
la siguiente campaña debe contrastar esa dirección mediante sus raíces
e historias propias y medir la deriva del candidato antes de admitirlo.
La comparación entre perfiles sigue pendiente.

Nativo 3816.045711 s; oráculo 26.812044 s; salidas nativas
6932018 bytes e input 3139168 bytes. Reserva 1 GiB, estimación 64 MiB,
stack 32 MiB, vigilancia 250 ms; compile≤120 s, run≤4400 s,
éxito≤4560 s, administrativo≤9000 s, auditor≤300 s. Sin rechazos/replays.
248 tests Rust heredados por identidad; sin nueva biblioteca, audio o
SPICE. Esta conformidad numérica no acredita fidelidad física ni RT.
