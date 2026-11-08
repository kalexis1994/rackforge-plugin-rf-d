# Ampliación de retornos y núcleo de conmutación

## Retornos del piloto

Conservar el mapa de cargas y abrir una banda
más amplia alrededor del punto nominal. Los
ensayos iniciales de ±120 mV en volumen y ±12 mV
en el pin 16 pasaron el límite de 2 nA para
R59/R60. El error RMS de J7 en filtro aislado
fue 0,862 %, frente a 0,3 %.

Las cuatro junturas BE/BC de Q26/Q28 redujeron
el desvío de corriente de R60 de 0,784 nA a
0,665 pA en el ensayo combinado. El filtro
aislado siguió fuera del límite de J7, con
0,869 % RMS. Se conservaron ambos intentos y
los mismos límites para la banda siguiente.
[Primer rango](../evidence/rf_d_pilot_returns05.json),
[rango con Q26/Q28](../evidence/rf_d_pilot_returns06.json)

La banda de ±120 mV en R59 y ±3 mV en el pin 16
pasó los tres ensayos tanto con 22 leyes como
con 18. Para el mapa de 18 leyes, el peor RMS
de J7 fue 0,221 % y los errores máximos fueron
1,69e−17 A en R59 y 53,54 pA en R60. R60 y
C18 siguieron en el modelo. En la escena
combinada, el solver recorrió 2,062–2,344 µA
en R59 y 6,807–6,852 µA en R60. El banco nativo
de 18 leyes obtuvo un máximo de 1,178 ms y
coincidencia exacta al dividir en bloques de
64 y 128 frames. RackForge reprodujo J7 con
identidad f32 en los pases offline.
[Banda con 22 leyes](../evidence/rf_d_pilot_returns07.json),
[banda con 18 leyes](../evidence/rf_d_pilot_returns08.json)

En ASIO4ALL con salida NVIDIA y el mapa de
22 leyes, un pase físico del piloto no llegó
a medir por falta de un núcleo SMT calificado.
El otro alcanzó 3,635 ms, con 214 bloques
sobre el margen. Con 18 leyes, el primer
intento obtuvo 1,111 ms y 1,483 ms en los
dos pases de 4.800 callbacks, con 0 y 2
excedencias. El control de esa campaña
tampoco superó la precalificación de SMT.
La repetición en CPU 9 rechazó el control y
el primer piloto por precalificación. El
segundo piloto midió 1,467 ms y una excedencia.
Se repitió en CPU 7 por los rechazos de SMT,
con el mismo mapa recompilado y la misma calificación.
El control y un piloto quedaron sin medir. El
otro piloto alcanzó 1,645 ms y dos excedencias.
La banda ampliada queda validada eléctricamente.
El margen físico de dos pases sigue abierto.
Los pases válidos midieron 128 frames efectivos
a 48 kHz con la salida silenciada.
[Campaña de 22 leyes](../evidence/rf_d_pilot_returns_rack07.json),
[primera campaña de 18 leyes](../evidence/rf_d_pilot_returns_rack08.json),
[repetición en CPU 9](../evidence/rf_d_pilot_returns_rack09.json),
[campaña en CPU 7](../evidence/rf_d_pilot_returns_rack10.json)

## Biestable de volumen

El núcleo resuelve C4_LEFT y las dos bases y
colectores de Q25/Q15. Conserva C4 entre sus
dos terminales, los incrementos de carga
BE/BC y los retornos por R28, R40, CR6, CR8 y
base de Q17. Avanza sus cinco estados desde
un único punto inicial. El cambio de orden de
colectores sale del estado resultante.

Con las fronteras finas del solver, el cruce
positivo ocurrió en 319096–319104, con 2,83 nV
de peor error nodal. Los dos bordes negativos
de KEY conservaron el orden de los colectores.
La comparación de stamps dio 6,24 aA de error
máximo de corriente y 9,28e−24 C en carga.

Con los cinco puertos interpolados desde
192 kHz y el mismo paso fino de 8 ticks, los
bordes negativos siguieron pasando. En la
ventana positiva se agotó Newton antes de la
inversión, alrededor de la muestra 77,809.
El replay reprodujo el rechazo. Esta prueba
mantiene el reloj del núcleo fijo y aísla el
efecto de la frontera muestreada.
[Protocolo del biestable](VOZ_PILOTO_BIESTABLE_PROTOCOLO.md),
[contraste de cinco nodos](../evidence/rf_d_pilot_latch01.json)

El barrido mixto encontró un único conjunto
mínimo de entradas finas para la ventana
positiva. Son x17 (reset), x6 (base de
ataque), x9 (emisor de decaimiento) y x24
(ánodo de CR8). La rama CR6 toleró x4
interpolado a 192 kHz.
[Barrido de fronteras](../evidence/rf_d_pilot_latch02.json)

La eliminación de R36/CR8 conserva la
corriente de la rama y toma el colector de
Q20 como frontera. Con x18 a paso fino, el
cruce conserva el intervalo 319096–319104 y
el peor error nodal positivo es 3,10 nV.
Al interpolar x18 y x4 a 192 kHz, el cruce
se adelanta ocho ticks y el error nodal
llega a 0,457 V. El piloto de RackForge
mide retornos con excitación externa. El
núcleo del biestable todavía requiere
fronteras finas producidas por el solver de
laboratorio. La siguiente frontera física de
CR8 es el gatillo Q20/Q12 con C7, que también
alimenta el reset de R28. Queda cerrar los
excitadores del biestable y C2/C5
antes de medir la voz con ambos contornos y
el biestable integrados.
[Contraste R36/CR8](../evidence/rf_d_pilot_latch04.json)

## Resultados del núcleo compartido

Con los seis puertos a paso fino, el cruce
positivo coincidió en 319096–319104. El peor
error nodal fue 0,118 µV en el colector Q25.
El error máximo de los stamps fue 0,433 fA
en corriente y 4,39e−23 C en carga. Los dos
flancos negativos conservaron el orden de
los colectores. Sin el predictor refinado,
Newton agotó sus iteraciones después del
cruce positivo.
[Primer rechazo](../evidence/rf_d_pilot_trigger01.json),
[búsqueda con residuo y corrección](../evidence/rf_d_pilot_trigger02.json),
[predictor refinado](../evidence/rf_d_pilot_trigger04.json)

Con los seis puertos interpolados desde
192 kHz, el cruce se adelantó 80 ticks y el
error nodal llegó a 8,03 V en la transición.
En el barrido completo, x4 fue el único
puerto que se pudo interpolar conservando
los límites del cruce positivo. C2, ambos
sustain y las dos cargas de reset del filtro
siguen requiriendo frontera fina. El banco
de 19 nodos es una validación eléctrica local.
La voz del piloto todavía no genera esas
cinco fronteras y no pasó a la prueba física.
[Barrido de fronteras](../evidence/rf_d_pilot_trigger05.json)
