# Semillas conjuntas con carga prescrita

2026-10-09. [Protocolo](VOZ_CARGAS_SEMILLA_PROTOCOLO.md),
[objetivos](../evidence/voice_joint_charge_seed_targets01.json),
[ejecución](../evidence/voice_joint_charge_seed_native02.json),
[contraste](../evidence/voice_joint_charge_seed_reference01.json) y
[QA](../evidence/voice_joint_charge_seed_tests01.json).

## Resultado funcional

El condicionador de laboratorio resuelve 200 incógnitas conjuntas y 18
corrientes de capacitor. Conserva cada carga prescrita mientras restaura
los nodos algebraicos con fase C1 retenida. Retirar la fase y las cargas
prescritas libera el motor conjunto original: no quedan fuentes extra,
cambios de leyes eléctricas ni restricciones artificiales en la trayectoria.
La biblioteca de física no se recompiló ni se cambió código de producción.

| Memoria | Cargas heredadas conservadas | C27 inicial | BUS inicial | J7 inicial |
|---|---:|---:|---:|---:|
| 0: carga del lift histórico | 18 | 1,961207633 V | +10,397838 mV | ≈0,101 nV |
| 1: C27 guiado por media saw | 17 | 1,997773446 V | −25,740776 mV | ≈0,104 nV |

La diferencia prescrita de C27 es +36,565813 mV/+365,658129 nC.
Los demás 17 objetivos son iguales por bytes. Las diferencias de nodos
respecto del lift se reportan en las 200 coordenadas; conservar carga no
exige conservar cada tensión a masa. No se ha encontrado una órbita periódica.

La media saw de endpoints históricos entre resets es −73,1316258 mV en
fine, con diferencia coarse/fine 1,29427 nV. Esa cuadratura trapezoidal
solo orienta la semilla; no es la integral Radau ni una media asentada.
Se conserva explícitamente la aproximación de entrada 6 por su sesgo DC
histórico. El circuito resuelto puede mover ese nodo junto con BUS.
Las corrientes de C27 en la fase retenida son −23,136840/−24,046042 µA:
son corrientes instantáneas; su signo no decide la deriva neta de un ciclo.

## Contraste y liberación

Cuatro raíces nativas: dos objetivos y dos guesses cada uno. Todas
convergen en cinco iteraciones/cuatro trials. Incidencia de rango 18,
reconstrucción de masa y 872 ecuaciones de acondicionamiento contrastadas
con DC VCO Decimal100 y cadena Python/FD. Peor fracción del gate de
residuo independiente 9,75330e-7 y corrección 1,16985e-8. Error máximo
de voltaje de carga 3,69779e-32 V; fase C1 dentro del gate de 1e-11 V.
No son búsquedas independientes de raíces.

Cuatro perfiles liberados durante 2 µs/1.048.576 ticks: medias etapas
máximas 125/62,5 ns para cada memoria. 14/20 intervalos por objetivo,
68 intervalos/136 medios endpoints en total. Cuatro replays de restore
exactos, excluidos de esos contadores. Dos entradas NaN rechazadas.

Se contrastan 9600 ecuaciones dinámicas en 48 puntos de etapa seleccionados
(first/last, full/mid/end). Peor residuo independiente 0,00121995 del gate
y corrección 7,12459e-6. Ocho LTE seleccionados admitidos. Diferencias de
las 200 coordenadas al reloj final: 0,000716382/0,000716380 del gate
2 µV/2 nA. Máximo LTE nativo ≈0,476187; KCL BUS ≤2,372e-20 A y C1
≤2,202e-14 A. Las cargas se comprueban al inicio; después evolucionan.

La compilación del caller y campaña exitosa consumen 4,50989 s. Stack
32 MiB de laboratorio; disco mínimo medido 1.123.778.560 bytes, reserva
1 GiB. Recursos muestreados entre procesos, no cota continua. Se reutiliza
la biblioteca admitida. 248 tests Rust heredados por identidad, ninguno
nuevo ni reejecutado. Sin medición nueva de heap, deadline, audio o SPICE.

## Correcciones preservadas

El [intento 1 de compilación](../evidence/voice_joint_charge_seed_native01.json)
falló y se repitió sin cambios: faltaba pasar el objetivo inmutable al
evaluar un trial. Sus fuentes, stderr y replay quedan congelados. El
intento 2 corrige solo ese argumento en el generador y caller; gates iguales.

La [errata detectada](../evidence/voice_joint_charge_seed_links_before01.json)
conserva cuatro enlaces inválidos del resultado anterior y su repetición.
El [snapshot](../evidence/voice_joint_charge_seed_before01.json) conserva
sus bytes: el formateador anterior separó números de nombres de recibos
y de componentes. El documento actual restaura esos enlaces y nombres.
El nuevo QA audita destinos locales de los documentos cambiados; el QA
anterior validaba identidades y enlaces RACE, y no detectó esta errata.

## Siguiente decisión

Las dos semillas están disponibles para su propia campaña de ciclos.
Medir deriva de las 18 cargas, media del panel y J7 entre fases iguales,
con ledger Radau y refinamiento, antes de elegir o corregir una memoria.
La liberación de 2 µs acredita el condicionador y la trayectoria corta;
no acredita asentamiento, encendido físico o parecido sonoro. No sustituye
las historias anteriores ni admite todavía audio nuevo de voz completa.
