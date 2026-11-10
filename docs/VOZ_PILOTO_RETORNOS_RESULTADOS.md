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

## Panel PLAY del piloto 0.3.0

El paquete de audición añade dos faders y cuatro
knobs. El ensayo en Edge con un anfitrión simulado
comprobó el arrastre del knob, las flechas del fader,
la actualización desde la telemetría y el ajuste
del panel a 376 px. Los seis controles cambiaron
el audio individualmente en el ABI portable.
El preset restableció los valores de fábrica y el
estado rechazó una restauración con un valor inválido.

Con los controles nuevos en sus valores de fábrica,
la salida de 0.2.0 se reprodujo por bits con los trims
en reposo y con la automatización previa. En RackForge,
los dos pases offline con 633 eventos y 376 bloques a
128 frames coincidieron por bits con los componentes
escalar y SIMD. Los máximos fueron 0,949 y 1,016 ms.
El peor dejó 0,318 ms respecto de 1,333 ms, con cero
fallos de slot, plazos perdidos o eventos descartados.
[Recibo de admisión](../evidence/rf_d_playable_pilot12.json).

Se conserva el rechazo de empaquetado por exigir
branding con el esquema 2, la comparación de
`+0` y `-0` al silenciar la salida y la campaña
con un bloque de 1,500 ms.
[Empaquetado](../evidence/rf_d_playable_pilot08.json),
[comparación y replay](../evidence/rf_d_playable_pilot10.json),
[primer pase después del ajuste](../evidence/rf_d_playable_pilot11.json).

## Perfil Raspberry Pi 0.3.1

En la Pi 4, el paquete 0.3.0 tardaba unos 5 ms
por período de 128 frames, frente a 2,666 ms
disponibles. RackForge recuperaba XRUN de forma
repetida. El perfil 0.3.1 mantiene la salida del host
a 48 kHz y baja el reloj del circuito de 192 a
96 kHz. Regenera los mapas FOH a esa tasa y conserva
las 18 leyes, las cargas, R59/R60 y el límite de
residuo de 2e−13. La dirección de Newton se arma
por grupos 4/2/3 como precondicionador y vuelve a
la dirección completa si hace falta. Reutiliza la
realimentación ya calculada del último paso aceptado.
[Planta](../tools/rf_d_pilot_return_plant.rs).

El FIR de 193 coeficientes conserva el corte de
22 kHz, la ventana Kaiser original y 48 frames
de retardo. La banda de paso hasta 20 kHz quedó
dentro de 0,001 dB y el rechazo desde 24 kHz superó
102 dB. Contra Radau a 768 kHz, el peor RMS de J7
fue 0,064 %. Las dos corrientes quedaron dentro de
2 nA. En la partitura completa con seis controles,
la diferencia RMS respecto de 0.3.0 fue 0,244 %.
[Generador y comprobaciones](../tools/check_rf_d_pi_pilot.py).

En la Scarlett, el primer intervalo registró un
XRUN y cinco excesos. En cinco intervalos
siguientes, incluidos dos tonos sostenidos con
ajustes distintos, el máximo fue 2,146 ms y se
registraron cero XRUN y cero excesos en esas
ventanas. El paquete usa el mismo panel y el mismo
formato de estado. Los contornos físicos continúan
en el laboratorio.
[Medición física](../evidence/rf_d_pi_live01.json).

## Cierre nominal de C5, sustain y reset hasta R60

El banco `--loaded-filter` calcula ambos sustain, el
reset y el seguidor desde C5 hasta Q26/Q28 y R60.
C5 recibe las corrientes de ataque, descarga y base
Q22. El diodo de x48 devuelve su corriente a x17
dentro de la misma resolución del biestable. Se
conservan 100 pF en x48 y x34, 10 nF entre x52 y x39
y las cargas de juntura x39/x40 y x41/x42. Los
divisores x12 y x51 se sustituyen por sus equivalentes
de Thévenin. Amount y los demás controles permanecen
en el punto nominal de la reserva.
[Stamps de origen](../crates/rf-d-circuit/src/prepared_contour_residual.rs),
[seguidor y Amount](../crates/rf-d-circuit/src/prepared_filter_residual.rs),
[banco](../tools/check_rf_d_pilot_contours.py).

La eliminación algebraica baja el sistema de 44 a
32 incógnitas por etapa. Al contrastar su dirección
con el sistema completo, la mayor fracción del
límite fue 7,03e−10. Con fronteras finas, el
biestable cambió en **319096–319104** y el peor
error de tensión fue 0,119 µV. Los máximos de
corriente fueron 0,029 pA en R59, 0,0000036 pA en
R60 y 1,261 pA en el diodo de sustain, frente al
límite de 2 nA por rama. El primer ensayo sin la
carga de juntura x41/x42 había excedido 5 nA en
ese diodo aunque conservaba el cruce.
[Rechazo y replay](../evidence/rf_d_pilot_contours04.json),
[cierre intermedio](../evidence/rf_d_pilot_contours05.json),
[contraste del seguidor y R60](../evidence/rf_d_pilot_contours08.json).

Las entradas restantes son x2/x4 y las cargas de
audio VCA_BASE y TAIL. Interpolar x2 o x4 desde
96 kHz pasó las reservas en la ventana positiva.
La misma interpolación en VCA_BASE llevó el
error de R59 a 11,43 nA. En TAIL, la corriente
de R60 pasó y el error del colector x37 llegó
a 2,52 mV. El avance fino del candidato alcanzó
189,5 ms en un frame de laboratorio. Quedan
pendientes la reducción temporal y la ampliación
del rango de R59 para integrar la planta audible
y contrastar su J7.

Al inicio del bloque, el motor de la Pi reportó
1.501 bloques a 48 kHz y 128 frames del paquete
0.3.1 con máximo de 2,158 ms y cero plazos
perdidos en la ventana consultada. El equipo
dejó de responder por SSH y HTTP antes del
nuevo pase con MIDI. La medición disponible
corresponde al paquete de audición.
[Observación de la Pi](../evidence/rf_d_pi_contour_control01.json).

## Compatibilidad de bloques en Desktop 0.3.2

Desktop 0.1.36 prepara la instancia a 4.096 frames,
independientemente del período solicitado al driver.
Con el piloto 0.3.1, la capacidad de 256 muestras
estéreo provocaba un rechazo al pedir 960 muestras
(480 frames) o 8.192 muestras (4.096 frames).
El banco reprodujo ambos rechazos dos veces con
el mismo mensaje.

0.3.2 admite hasta 4.096 frames a 48 kHz y conserva
el perfil interno de 96 kHz. Cada callback se divide
en tramos de hasta 128 frames con offsets locales
para MIDI y automatización. La planta, el FIR y
la memoria se conservan entre tramos. La partitura
de 633 eventos a 127, 128, 256, 480, 512, 1.024
y 4.096 frames produjo los mismos bits que 0.3.1.
[Rechazos y contraste](../evidence/rf_d_host_blocks01.json).

El paquete se instaló y activó en Desktop, con la
salida WASAPI y las preferencias existentes. Una
nota MIDI virtual produjo señal en ambos canales.
El host informó 483 frames en la ventana medida,
sin plazos perdidos ni errores de stream. Se
restauró el instrumento que estaba seleccionado.
[Medición en Desktop](../evidence/rf_d_desktop_live01.json).

## Puerto de audio para C2/C5 a 96 kHz

El receptor de laboratorio toma la tensión de x3 por R59 (68 kΩ)
y la del colector x37 por R60 (680 Ω). Devuelve las corrientes con
los signos del circuito de referencia. El seguidor de C5 conserva
Q26/Q28 y su capacitor de 100 pF. El receptor conserva 17 estados de
carga de audio, incluida C27. El reparto viene del circuito de ladder,
VCA y salida en SVC-9, pp. 19, 13 y 10. [Circuito](../crates/rf-d-circuit/src/circuit66.rs),
[proyección](../tools/prepare_rf_d_pilot_returns.py).

La reserva positiva cubre 1,8955–1,9180 V para R59 y 1,3227–1,3339 V
para el colector de R60. Para aislar el receptor se ensayó un bloque
de 128 frames de host con señales independientes dentro de
1,91 ± 0,015 V y 1,33 ± 0,010 V. A 96 kHz el piloto local superó
el límite de 2 nA en R60 y quedó en 9,17 % RMS de error en J7.
Subir a 192 kHz y usar la misma interpolación en Radau reprodujo el
desvío. Al conservar las ocho junturas BE y las ocho BC que faltaban
en el ladder, a 96 kHz el error bajó a 2,95 pA en R60 y 0,0079 %
RMS en J7. La prueba conserva el límite de 2 nA en ambos retornos y
el de 0,3 % RMS en J7. El punto de reposo de la rama negativa aún
necesita un anclaje. [Banco y replay](../evidence/rf_d_pilot_split_returns01.json).

La repetición del solver acoplado conservó el cruce **319096–319104**
y ninguna conmutación en las dos reservas negativas. En esa ventana
positiva, reconstruir los puertos por interpolación lineal a 96 kHz
desplazó x3 hasta 0,856 mV y el colector hasta 2,523 mV. Con los nodos
receptores fijados a sus valores de referencia, equivalen a 12,6 nA
en R59 y 3,71 µA en R60. Esta prueba mide el error de imponer
tensiones interpoladas con la carga congelada. El cierre dinámico
requiere devolver ambas cargas y resolver la transición localmente.
[Reserva de los contornos](../evidence/rf_d_pilot_contours08.json),
[contraste de puertos](../evidence/rf_d_pilot_split_returns01.json).

En Desktop, el paquete de control 0.3.2 produjo señal en ambos
canales con una nota MIDI virtual. El host reportó 480 frames
efectivos a 48 kHz, cero plazos perdidos y cero errores de stream
en sus contadores acumulados. La Pi agotó el tiempo de espera
por SSH y HTTP. La prueba física del receptor con los contornos
queda pendiente.
[Control físico](../evidence/rf_d_contours_live_control02.json).

## Cierre bidireccional a la resolución del solver

El banco separa los contornos cargados y la cadena de audio en las
dos etapas de Radau. La etapa de audio conserva la carga de C27,
el VCO H128 sobre BUS y las reacciones de R59 y R60. C2 entrega x3
al VCA y C5 entrega x37 al ladder. Audio devuelve la base del VCA y
TAIL a los mismos terminales que usa la ecuación de cada contorno.
Se resuelve también x4 con R24, R27 y CR6. El colector x2 conserva
R15 y las corrientes de Q2 y Q3. [Circuito](../crates/rf-d-circuit/src/prepared_volume_residual.rs),
[receptor acoplado](../tools/rf_d_pilot_closed_returns.rs).

Cada ventana comienza en un único estado reservado, incluidas las
cargas de los capacitores y la fase del VCO. El candidato avanza
con los valores de KEY de la escena. Las tensiones del solver de
referencia se usan al comparar la salida. En el primer intento
TAIL seguía fijo en el seguidor de C5 y R60 excedió 10 µA de error
en la reserva positiva. Corregir el terminal dejó un error de
238 µV en x3 con x2/x4 fijos. [Primer rechazo](../evidence/rf_d_pilot_closed_returns01.json),
[contraste con TAIL corregido](../evidence/rf_d_pilot_closed_returns02.json).

Con x2 y x4 cargados, pasaron la inversión positiva y ambas
reservas negativas de KEY. El cruce positivo volvió a quedar en
**319096–319104** y el peor error en cualquiera de los retornos
fue de 0,146 pA frente al límite de 2 nA. El mayor error absoluto
de J7 fue de 3,96 pV.
[Reservas acopladas](../evidence/rf_d_pilot_closed_returns03.json).

El avance directo a 96 kHz pasó la reserva de pulsación negativa.
Agotó las iteraciones en el primer paso de la reserva positiva
y en el de liberación negativa. El reloj fino es una prueba de
laboratorio. Aún hace falta una reducción que pueda correr en
RackForge y conservar los mismos eventos y corrientes.

El control 0.3.2 en Desktop sostuvo señal en ambos canales en tres
lecturas durante una nota, con 480 frames efectivos a 48 kHz y cero
plazos perdidos o errores de stream entre las consultas. La Pi agotó
el tiempo de espera por SSH y HTTP. [Control en hosts](../evidence/rf_d_contours_live_control03.json).

## Arranque del receptor en la rama negativa

El generador parte del estado inicial negativo de la referencia y
resuelve el punto de reposo del receptor con R59 a −0,28 V,
colector de R60 a 1,45 V y estímulo de BUS nulo. El residual fue
de 2,0 × 10⁻¹⁸ A. La continuación desde el punto positivo volvió
a rechazar ese estado. [Arranque y contraste](../evidence/rf_d_pilot_off_anchor02.json).

En la proyección de carga, forzar las columnas de defecto con 1 A
produjo un residual de 1,26 × 10⁻⁶. Cerca del corte del VCA esas
columnas piden cancelaciones del orden de 10⁹. En el nuevo mapa,
la corriente de polarización de cada juntura multiplica su columna
de incidencia y el núcleo evalúa el resto exponencial adimensional.
El producto representa la misma corriente. El residual bajó a
7,45 × 10⁻¹⁷ con los límites previos. [Proyección](../tools/prepare_rf_d_pilot_returns.py),
[rechazo reproducido y mapa normalizado](../evidence/rf_d_pilot_off_anchor02.json).

El receptor aislado a 96 kHz pasó un bloque de 128 frames de host
contra Radau a 384 y 768 kHz. Las excitaciones independientes
cubrieron ±5 mV en R59 y ±1 mV en el colector de R60. El error de
R60 fue 0,032 pA y el RMS relativo de J7 fue 0,0044 %. El J7 de
referencia tuvo 50 pV de pico en esta prueba de corte. La
conmutación de la voz completa sigue bajo el banco acoplado.
[Contraste del receptor negativo](../evidence/rf_d_pilot_off_anchor02.json).
