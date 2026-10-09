# Ciclos desde dos memorias de carga

2026-10-09. [Protocolo](VOZ_CICLOS_SEMILLAS_PROTOCOLO.md),
[raíces/checkpoints](../evidence/voice_joint_seed_cycles_inputs01.json),
[ejecución](../evidence/voice_joint_seed_cycles_native01.json),
[contraste](../evidence/voice_joint_seed_cycles_reference01.json) y
[QA](../evidence/voice_joint_seed_cycles_tests01.json).

## Cuatro trayectorias admitidas

Las raíces id/guess=0 del condicionador se restauran por bytes a reloj
cero. Memoria 0 conserva las 18 cargas del lift histórico; memoria 1
cambia exclusivamente C27 y conserva las otras 17. No se vuelven a resolver
raíces ni se cambia la física. El lift de Scene no inicializa el motor.
Se conserva cada historia anterior con su admisión original.

| Memoria | Máxima media etapa | Intervalos | Frecuencia observada | ΔC27 por fase | ΔC10 por fase | ΔJ7 por fase |
|---|---|---:|---:|---:|---:|---:|
| 0 | 125 ns | 23866 | 410.801759221 Hz | +225.063560 µV | +36.518917 µV | -223.000775 µV |
| 0 | 62.5 ns | 44742 | 410.801758782 Hz | +225.063566 µV | +36.518917 µV | -223.000778 µV |
| 1 | 125 ns | 23855 | 410.801786461 Hz | +5.826833 µV | +49.587428 µV | -199.636469 µV |
| 1 | 62.5 ns | 44730 | 410.801784508 Hz | +5.826859 µV | +49.587428 µV | -199.636473 µV |

Cada perfil completa 5,25 ms/2.752.512.000 ticks: 137193 intervalos y
274386 medios endpoints publicados en total. Dos resets por perfil
delimitan un periodo observado; estas cuatro observaciones no constituyen
periodos consecutivos asentados. Las diferencias de fase son interpolaciones
Decimal100, no soluciones adicionales de la DAE. Las 18 cargas y las 200
coordenadas de fase se reportan completas, sin convertir refinamiento
temporal en tolerancia de periodicidad.

Los cuatro endpoints de 2 µs coinciden por bytes con la liberación anterior.
Hay 23 checkpoints por perfil (inicial, 2 µs y 21 anclas de 250 µs).
Ocho replays exactos de restore a 250 µs/2,25 ms, excluidos de contadores
e integrales. 200 coordenadas a 22 relojes no iniciales por memoria:
2 µs y anclas; peor ratio de anclas 0.0296115495. Diferencia máxima de
frecuencia 8.22925619e-06 cent; extremos 4.03371774e-07 V.

19200 ecuaciones nuevas en 96 puntos de etapa seleccionados, 16 LTE y
96 corrientes de terminales en 32 endpoints. Peor residuo independiente
0.00121994831 y corrección 7.12459308e-06; máxima diferencia de corriente
5.54627932e-16 A frente a 2e-11 A. Se contrastan candidatos nativos;
no se buscan raíces ni una trayectoria completa independiente.

## Medias de Radau y balance de C27

| Memoria | Máxima media etapa | Media saw | Media BUS | Media entrada 6 | Media 0,5·saw−BUS |
|---|---|---:|---:|---:|---:|
| 0 | 125 ns | -73.131624 mV | -0.276634 mV | 1.960326321 V | -36.289178 mV |
| 0 | 62.5 ns | -73.131626 mV | -0.276634 mV | 1.960326321 V | -36.289179 mV |
| 1 | 125 ns | -74.027681 mV | -36.074319 mV | 1.960764070 V | -0.939522 mV |
| 1 | 62.5 ns | -74.027686 mV | -36.074319 mV | 1.960764070 V | -0.939525 mV |

Cada media corresponde al intervalo entre endpoints reales de los dos
eventos. Las integrales usan las etapas y pesos Radau 3/4 y 1/4 de esa
historia; no se sustituyen por trapecios. Los brackets y estados de eventos
coinciden con trace y pares de etapas seleccionados contrastados.
Se guardan acumulados de saw/BUS/entrada 6/corriente del panel/desbalance.

El balance C1 de terminales completos Qa/Q10/Q7 entre eventos tiene peor
ratio relativo 1.44498346e-15. Las ocho comprobaciones C27 (periodo y
recorrido completo por perfil) verifican `ΔQ+∫I_cursor→BUS dt=0`, peor
error 1.74762512e-24 C, gate 1e-12 A por duración. Identidad media del panel:
peor diferencia 6.44886201e-18 V, gate 1e-9 V. Las identidades también
se verifican en todos los endpoints. El ledger completo conserva una
cuadratura nativa; no es una segunda integral independiente de todas las
etapas. La condición de media cero sigue siendo necesaria, no suficiente.

## Comparación de historias y alcance

En la resolución de 62,5 ns, cambiar solo C27 reduce su deriva por fase
38.625 veces: de +225.063566 a
+5.826859 µV. Sin embargo, C10 pasa de
+36.518917 a +49.587428 µV y J7
todavía cambia -199.636473 µV.
El cambio aislado de C27 no cierra la memoria de toda la cadena.

El contraste conserva los valores de la historia del lift y del DC conjunto
retenido, además de ambos nuevos objetivos a las dos resoluciones. Una
reducción de deriva puede orientar la siguiente memoria; no transforma
la liberación de fase en encendido físico ni la semilla en órbita periódica.
La tabla de fase y las medias permiten refutar la aproximación de sesgo
de entrada 6 y distinguirla de la media saw. No se cambia un componente
para compensar una condición inicial.

La siguiente decisión es corregir la memoria a partir de estas corrientes
medias y las demás cargas, y exigir periodos consecutivos antes de la
escucha de voz completa. No elegir por amplitud de salida ni declarar
asentamiento solo porque C27 tenga menor deriva. Controles/contornos y
fuentes restantes mantienen sus brechas; tampoco hay admisión de RT.

## Coordenadas y rieles

La [errata de notación](VOZ_CARGAS_RIELES_NOTA.md) conserva el protocolo
anterior y contrasta 72 cargas físicas. Los objetivos son coordenadas
`Eᵀx`; la carga absoluta es `Q=C·(Eᵀx−v_fijo)`. El terminal PLUS del
capacitor de índice 11 está a +10 V de laboratorio. Con el riel constante,
su referencia se cancela en cambios de carga; las raíces y trayectorias
permanecen iguales. El nuevo banco distingue terminal físico de la columna
eliminada del solver. No sustituye PLUS por una conexión física a masa.

## Recursos e identidad

Campaña serial de 4601.089625 s; outputs nuevos 48161802 bytes.
Disco mínimo muestreado 1104171008 bytes, reserva 1 GiB, muestreo 250 ms.
Stack 32 MiB de laboratorio y biblioteca física congelada; solo compilación
del caller. Se recuperaron 81749453 bytes de asignación mediante
[compresión binaria](../evidence/voice_joint_seed_cycles_compression01.json)
y [ASCII](../evidence/voice_joint_seed_cycles_compression02.json), reforzada
durante la campaña con [exports anteriores](../evidence/voice_joint_seed_cycles_compression03.json)
y [bibliotecas anteriores](../evidence/voice_joint_seed_cycles_compression04.json).
15 registros protegidos en total: hashes y tamaños conservados, sin borrar
o mover. Las bibliotecas comprimidas no se recompilan.
248 tests Rust heredados por identidad; cero nuevos/re-ejecutados.
Sin nuevo audio, SPICE, raíz independiente, prueba física o deadline.
