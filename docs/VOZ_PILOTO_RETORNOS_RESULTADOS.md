# Primera etapa de retornos en el piloto rápido

El piloto FOH admite la tensión que alimenta R59
y la tensión del pin 16 que modula la rama de
R60. R60 y C18 siguen en el circuito del filtro.
El motor devuelve ambas corrientes y conserva
el VCO del piloto, C27 y el FIR. El dominio
actual es ±15 mV alrededor de 2 V en volumen
y ±1 mV alrededor de 0 V en el pin 16.
[Protocolo](VOZ_PILOTO_RETORNOS_PROTOCOLO.md)

Con las 12 leyes iniciales, ambas corrientes
pasaron y el error RMS de J7 llegó a 0,529 % con
los dos controles frente al límite de 0,3 %.
Al conservar también Q18 y el par de señal del
primer VCA, pasaron los tres estímulos contra
Radau a 768 kHz. El peor error RMS de J7 fue
0,0660 %. El mayor error de R59 fue 0,0168 fA
y el de R60, 4,66 pA, frente a 2 nA por retorno.
[Primer contraste](../evidence/rf_d_pilot_returns02.json),
[reserva corregida](../evidence/rf_d_pilot_returns04.json)

El motor rechazó una entrada inválida sin
publicar historia ni salida y reprodujo por bits
el mismo render al usar bloques de 64 o 128. La
escena con ambos controles tuvo máximo de 0,680 ms
sobre 376 bloques, cero excedencias de 1,333 ms
y cero asignaciones. La etapa conserva el piloto
previo como control independiente.

## Frontera de la conmutación

La reserva positiva del solver tiene el extremo
de R59 entre 0,935 V y 1,918 V. Estos valores
quedan fuera del dominio del piloto actual.
La interpolación lineal del diferencial de
colectores a 48 kHz predice el cruce en el
tick 316376,75. El intervalo de referencia es
319096–319104. Esa interpolación adelantaría el
evento alrededor de 13,8 µs. La siguiente etapa
necesita un estado de carga y un detector de
evento del biestable, además de ajustar el
punto de operación de los retornos.
[Reserva cargada](VCO_FAMILIA_BUS_VOZ_RELOJ_RESULTADOS.md)

El banco actual excita las entradas con fuentes
explícitas. La trayectoria propia de C2/C5 y el
biestable quedan pendientes de integración.

## Slot nativo de RackForge

El núcleo RackForge `7a14c68a` cargó el piloto
como paquete nativo. En todos los pases con
retornos activos, sus 48.128 muestras de J7
coincidieron por bits con el banco nativo.
La primera campaña completa dio 1,072 ms y
33,518 ms de máximos en los dos pases activos.
La repetición dio 1,975 y 3,042 ms. En esa
repetición el control a cero también excedió
el margen, con máximo de 8,914 ms. Los picos
se conservan en los recibos.
[Primera campaña](../evidence/rf_d_pilot_returns_rack02.json),
[repetición](../evidence/rf_d_pilot_returns_rack03.json)

Otra campaña offline pasó completa con máximos
de 1,103 y 0,983 ms en los dos pases activos.
El bloque de control de esa campaña quedó en
0,979 ms. Se conservaron los intentos de apertura
física que corrigieron la selección de la
biblioteca y la afinidad heredada del supervisor.
[Campaña offline completa](../evidence/rf_d_pilot_returns_rack05.json)

## Callback físico

La campaña final usó el mismo binario que el
slot offline. ASIO4ALL confirmó 48 kHz y 128
frames efectivos en la salida NVIDIA, con
CPU lógica 9, espera por evento y la condición
previa del banco físico. El driver recibió
silencio mientras RackForge procesaba el piloto.
Se restauraron la frecuencia y la configuración
de búfer al terminar.

| Banco | Callbacks | Máximo de pared | Excedencias de 1,333 ms |
| --- | ---: | ---: | ---: |
| Control silencioso | 1.200 | 0,041 ms | 0 |
| Retornos activos, pase 1 | 4.800 | 0,801 ms | 0 |
| Retornos activos, pase 2 | 4.800 | 0,820 ms | 0 |

Los primeros callbacks, incluida su preparación,
también pasaron. El peor pase activo dejó
0,514 ms respecto del margen. Se registraron
cero plazos perdidos y cero fallos del slot.
La admisión cubre esta etapa de retornos y
la configuración física probada.
[Campaña ASIO](../evidence/rf_d_pilot_returns_rack06.json)

## Retornos en el paquete portable

RF-D Pilot 0.2.0 integra el mapa FOH de 18 leyes en el
paquete MIDI. Los offsets de laboratorio de R59 y pin 16
se exponen en mV, parten de cero y admiten automatización
por muestra. R60 conserva su rama física en el filtro.
El rango de los offsets es ±15 mV y ±1 mV respectivamente.
C2/C5 y el biestable quedan pendientes de acople.

El banco a 192 kHz reprodujo por bits la partición
64/128, sin asignaciones. Las tres escenas eléctricas
pasaron contra Radau a 768 kHz. El peor RMS de J7
fue 0,0660 %, frente a 0,3 %. Los máximos de corriente
fueron 0,0168 fA en R59 y 4,66 pA en R60, frente a
2 nA por retorno. El refinamiento 384/768 kHz pasó.
[Banco eléctrico inicial](../evidence/rf_d_pilot_returns09.json),
[contraste de las fuentes del paquete](../evidence/rf_d_pilot_returns10.json).

RackForge recibió 531 eventos por pase, ocho de la
partitura y el resto de CC20/21 enlazados a los puertos.
La salida de cada pase coincidió por bits con las 48.128
muestras estéreo del componente directo con los mismos
estímulos. El componente SIMD coincidió también por bits
con el escalar. La salida con controles neutros fue
distinta de la salida con retornos activos.

| Variante a 128 frames | Máximo del pase 1 | Máximo del pase 2 |
| --- | ---: | ---: |
| Escalar sin Binaryen | 1,950 ms | 1,361 ms |
| Escalar con Binaryen 132 | 1,147 ms | 1,451 ms |
| SIMD por pares de filas y Binaryen 132 | 0,980 ms | 1,140 ms |

Los dos pases finales de 376 bloques a 48 kHz quedaron
dentro de 1,333 ms, con cero eventos descartados,
fallos de slot y plazos perdidos. El peor bloque dejó
0,193 ms de margen offline. La admisión deja
`artifacts/rf-d-pilot-0.2.0.rfplugin` para importar.
La medición física corresponde a una etapa posterior.
[Primer intento portable](../evidence/rf_d_playable_pilot04.json),
[ensayo de Binaryen](../evidence/rf_d_playable_pilot05.json),
[campaña admitida](../evidence/rf_d_playable_pilot06.json).

## C2, C5 y biestable con cargas impuestas

El candidato de laboratorio conserva dos estados de carga
de 10 µF. Cada temporizador resuelve un sistema de dos etapas
a partir de `C dV/dt = Σ (Vpuerto − V) / R`. C2 usa los
puertos x8/x11 del biestable y la rama de placa de 10 kΩ
hacia Q3. C5 conserva los caminos de ataque y descarga
x44/x47 y la corriente de base de Q22. La receta es la
nominal con decay habilitado, sin C11/C12 opcionales y
con los controles congelados de la reserva. Las leyes y
valores provienen de los stamps de la voz cargada.
[Volumen](../crates/rf-d-circuit/src/prepared_volume_residual.rs),
[filtro](../crates/rf-d-circuit/src/prepared_filter_residual.rs),
[contornos cargados](../crates/rf-d-circuit/src/prepared_contour_residual.rs).

La salida de volumen resuelve Q3/Q2 junto con R59 a
68 kΩ y realimenta la carga de Q3 hacia C2. La rama
Q26/Q28 reconstruye R60 a 680 Ω con la carga TAIL y el
sumador del filtro impuestos. C5 realimenta la base
de Q22. Quedan impuestos los demás terminales del
seguidor, los dos sustain, las dos cargas de reset
y los extremos del circuito de audio. El contraste
usa dos flancos negativos y una transición positiva.
[Modelo](../tools/rf_d_pilot_contours.rs),
[retornos](../tools/rf_d_pilot_contour_ports.rs),
[banco](../tools/check_rf_d_pilot_contours.py).

Con las fronteras a paso fino, las dos corrientes
quedaron bajo 2 nA de error y el biestable cambió
entre 319096 y 319104. Interpolar sólo las cuatro
entradas de carga de C5 desde 192 kHz conservó
el cruce con error de C5 de 7,48 µV en el peor
punto. Interpolar todas las fronteras adelantó
el cruce 80 ticks y elevó el error de R59 a 7,77 nA.
La primera etapa cerraba C2 alrededor del
biestable con la base de Q3 impuesta. El segundo
contraste incorporó las dos ramas de retorno y
la carga de base de Q22.
[Primera etapa](../evidence/rf_d_pilot_contours01.json),
[contraste con corrientes](../evidence/rf_d_pilot_contours02.json).

En el barrido individual, interpolar x48 (sustain del
filtro) adelantó por sí solo el cruce 80 ticks y dejó
3,34 nA de error en R59. Interpolar x14, x41 o x52
conservó el intervalo pero excedió 20 µV en los
nodos del biestable. Las cuatro cargas requieren
conservar su reacción cerca de la transición.
Con fronteras finas los peores errores de corriente
sobre las tres ventanas fueron 0,029 pA en R59
y 0,195 pA en R60.
[Barrido de puertos](../evidence/rf_d_pilot_contours03.json).

En la ventana positiva, R59 pide 1,8955–1,9180 V
en su extremo de contorno. El extremo baja a unos
−0,277 V en los dos flancos negativos. Sujetar el
extremo al rango 1,985–2,015 V del piloto y conservar
la tensión de base del solver introduciría hasta
1,316 µA de error en la ventana positiva, frente
a 2 nA. El contraste de J7 sigue pendiente del
acople al modelo de audio sobre ese dominio.

El avance a ocho ticks durante toda la ventana
positiva consumió 45,6 ms de cálculo en su frame
más caro. El candidato queda como referencia
offline para condensar la transición y extender
la planta de audio por regiones de polarización.
La repetición en RackForge corresponde al paquete
portable 0.2.0, con los mismos bytes y el mismo
J7 que en el banco anterior. A 48 kHz y 128 frames
efectivos, los dos pases de 376 bloques dieron
0,965 y 1,104 ms de máximos. Quedaron 0,229 ms
respecto de 1,333 ms, con cero excesos, fallos de
slot o eventos descartados.
[Control offline de RackForge](../evidence/rf_d_playable_pilot07.json).
