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

## Reloj de los contornos acoplados

El diagnóstico localizó los dos rechazos iniciales de 96 kHz en
las tres iteraciones permitidas para C2/C5. Con hasta ocho, la
pulsación y la liberación de la rama negativa pasaron en bloques
fijos de 96 kHz. El peor error de sus retornos fue 0,00132 pA.
La rama positiva avanzó 6144 ticks desde el ancla antes de que
Newton dejara de reducir el residual del biestable. Los límites
de convergencia de las ecuaciones fueron los mismos.
[Diagnóstico y repeticiones](../evidence/rf_d_pilot_closed_returns04.json).

El controlador conserva los límites de cada muestra a 96 kHz.
Antes de aceptar, contrasta un paso con dos medios pasos y guarda
los dos estados refinados. Si falla el solver o el defecto excede
su presupuesto, reduce el tramo. También reduce el paso cuando
las etapas difieren en el orden de Q26 y Q28, de modo que un
cruce aceptado se pueda fechar con resolución de ocho ticks.
Las factorizaciones de audio se preparan una vez por paso posible.
[Controlador](../tools/rf_d_pilot_contour_clock.rs).

El reloj estricto pasó las tres reservas, con el mismo cruce
**319096–319104** y un error máximo de 0,140 pA en R59/R60.
La comparación de pasos aumentó el coste en el cruce positivo.
Permitir un defecto local de 0,5 µV para todos los nodos redujo
el número de pasos positivos de 776 a 296. Esa variante conservó
R59/R60 y el intervalo del cruce, pero Q26 se desvió 177 µV y
excedió el límite de 20 µV de la reserva.
[Contraste estricto](../evidence/rf_d_pilot_closed_returns05.json),
[rechazo del defecto amplio](../evidence/rf_d_pilot_closed_returns06.json).

Con 20 nV de defecto local para el biestable y 0,5 µV en el resto
de las tensiones, las tres reservas pasaron. En la positiva se
aceptaron 504 pasos, Q26 quedó a 7,50 µV y el intervalo del
cruce se conservó. El peor error de R59/R60 entre las tres
ventanas fue 0,105 pA. El coste máximo observado de 8,63 s
por frame positivo deja este método como banco de referencia.
[Contraste con tolerancias separadas](../evidence/rf_d_pilot_closed_returns07.json).

El control 0.3.2 en Desktop 0.1.36 dio señal en ambos canales
en 18 ventanas de seis notas. RackForge informó 477 callbacks
durante el pase, 481 frames efectivos al final, cero plazos
perdidos y cero errores de stream. Se restauró el instrumento
anterior y se cerró la sesión abierta para la prueba.
[Control de audio en Desktop](../evidence/rf_d_contours_live_control04.json).

## Receptor de audio reducido en las etapas Radau

El receptor conserva las 17 tensiones de capacitor del audio,
incluido C27. El seguidor Q26/Q28 conserva su propia carga del
lado de C5. En la preparación se comprueba que la incidencia de
los capacitores reproduce el stamp de masa y se proyectan las
dos etapas para cada paso posible. Cada etapa usa sus propias
tensiones en R59 y R60. BUS conserva la corriente y la fase del
VCO H128. Las 56 junturas de audio aportan el resto exponencial
alrededor del estado inicial, con sus corrientes de polarización
como escala. El mapa se prepara desde un estado por reserva.
[Código del receptor](../tools/rf_d_pilot_reduced_audio.rs),
[incidencias y tarjetas](../tools/rf_d_reduced_contour_live.py).

El primer generador recuperaba la saturación dividiendo la
corriente polarizada por su exponencial. La juntura del
amplificador con colector a −20 V produjo 0/0 al generar
los coeficientes. La tarjeta ahora entrega directamente
la saturación y el banco reproduce el fallo anterior.
[Rechazo del generador](../evidence/rf_d_pilot_closed_returns08.json).

Pasaron las tres reservas acopladas. La pulsación y liberación
negativas pasaron también a 96 kHz fijos. El reloj adaptativo
conservó **319096–319104** y el peor error entre R59/R60 fue
0,147 pA. En el mismo pase nativo, el máximo positivo fue
3,92 s por frame con el mapa y 5,55 s con el audio nodal.
El mapa reducido se contrastó como parte del banco.
[Comparación del receptor acoplado](../evidence/rf_d_pilot_closed_returns09.json).

La variante con tangente reutilizada propone una dirección a
partir de la última factorización del mismo tamaño de paso. Sólo
la conserva si el residual real baja al menos a la mitad o
alcanza la tolerancia de la interfaz. Ante un rechazo arma la
tangente de nuevo. Las pruebas de paso del reloj conservan el
estado eléctrico aceptado como punto de partida.

En la reserva positiva, los armados de tangente bajaron de
1.650 a 9. El máximo del mismo pase bajó de 3,55 s a 0,862 s
por frame. Se conservaron el cruce de ocho ticks, las dos
reservas negativas a 96 kHz fijos y el límite de 2 nA. El
peor error de R59/R60 del reloj adaptativo fue 0,146 pA.
[Contraste con tangente reutilizada](../evidence/rf_d_pilot_closed_returns10.json).

Al resolver los mismos intervalos de C2/C5 con una nueva carga,
la última solución de las dos etapas del biestable sirve como
semilla. Las ecuaciones se evalúan desde el mismo estado de
carga anterior. Si la semilla falla, vuelve a usarse el arranque
anterior del solver.

Con esa semilla, el pico positivo del mismo pase bajó de
844 ms a 479 ms por frame. El reloj mantuvo la misma distribución
de pasos y el cruce **319096–319104**. El peor error de R59/R60
en las tres reservas adaptativas fue 0,175 pA. La pulsación y la
liberación negativas pasaron también a 96 kHz fijos. El pico
positivo excede el presupuesto completo de 1,333 ms por bloque
de 128 frames. La prueba física del candidato en Desktop queda
pendiente.
[Contraste con semilla del biestable](../evidence/rf_d_pilot_closed_returns11.json).

## Subpasos del cruce y bloques de 128 frames

El reloj conserva 20 nV de defecto local para los colectores Q26
y Q28. Para los demás nodos del biestable usa el límite local de
0,5 µV del resto del circuito. Si rechaza un tramo y ya resolvió
su primera mitad desde el mismo estado, reutiliza esa solución al
subdividir. En las reservas se siguen aplicando 20 µV a las
tensiones observadas, 2 nA a R59/R60 y el intervalo exacto del
cruce, además del contraste de J7.

En la ventana de un frame centrada en el cruce, los pasos
aceptados bajaron de 295 a 252. En toda la reserva positiva
bajaron de 504 a 466 y las llamadas al solver de 972 a 802.
El peor frame del mismo pase bajó de 480 a 410 ms. El cruce
quedó en **319096–319104** y las dos reservas negativas pasaron.
Aceptar pasos enteros cuando el defecto era pequeño dejó 188
pasos en la ventana, pero el error en Q26 subió a 31,2 µV.
[Contraste de relojes](../evidence/rf_d_pilot_closed_returns12.json).

El banco de 128 frames corre la positiva desde el frame 76.
La negativa comienza en el frame 0 y reproduce la subida
de KEY en el 16 y su bajada en el 96. La medición nativa
acumula el tiempo de todas las resoluciones del bloque,
incluidos los intentos descartados. La preparación de los
mapas y la escritura del trazado quedan fuera de ese tiempo.
El presupuesto para 128 frames a 48 kHz es 1,333 ms con el
mismo margen de las pruebas de tiempo real.

La primera corrida agotó las iteraciones de interfaz de la
positiva al completar 78 frames. La rama negativa agotó las
iteraciones del receptor reducido antes de avanzar su primer
frame. Ambos rechazos se reprodujeron con el mismo trazado.
[Rechazos del bloque](../evidence/rf_d_pilot_closed_returns13.json).

Con un presupuesto mayor de iteraciones de interfaz y el
receptor nodal disponible si se agota el reducido, se
completaron y contrastaron los dos bloques de 128 frames.
El caso positivo tardó 4,31 s con 610 llamadas al receptor
nodal. El negativo tardó 1,11 s con 10 llamadas. Ambas
trayectorias pasaron sus límites y el cruce quedó en
**319096–319104**. El peor error de R59/R60 fue 0,178 pA.
Estos tiempos corresponden a la configuración de diagnóstico.
El tramo positivo de referencia posterior al frame 128 se
calculó con el solver fino y se conservaron sólo los endpoints
del host y los intervalos del biestable.
[Diagnóstico de 128 frames](../evidence/rf_d_pilot_closed_returns15.json).

La variante siguiente conserva la última propuesta del receptor
reducido si su criterio de desplazamiento no converge. Comprueba
KCL y la corrección con los límites que ya usa el receptor nodal,
0,2 pA y 2 nV, en esa propuesta. La comprobación cuenta en la
medición y se conserva el estado sólo si pasa.

Los bloques tardaron 4,20 s y 1,14 s. La comprobación admitió
610 propuestas en la rama positiva y 9 en la negativa, sin
iteraciones de rescate del receptor nodal. Se contrastaron los
128 endpoints de cada bloque, con 0,178 pA como peor error de
R59/R60. El cruce quedó en **319096–319104**. Ambos tiempos
superan el presupuesto y la prueba física del candidato en
Desktop queda pendiente.
[Medición a 128 frames](../evidence/rf_d_pilot_closed_returns16.json).

## Coste de la dirección del biestable

El perfil de dos bloques completos separó el tiempo del
receptor de audio y de los contornos. En el positivo,
los contornos consumieron 3,71 s de 4,40 s. El armado de
Schur y la resolución lineal representaron 1,97 s de ese
tiempo. En el negativo sumaron 0,485 s de los 0,912 s de
contornos. [Perfil nativo](../evidence/rf_d_pilot_closed_returns18.json).

El armado disperso omite productos con ceros en la reacción
de los nodos algebraicos. Recorre esos nodos en el mismo
orden y usa el pivoteo escalado del LU disperso existente.
En la comparación instrumentada, las salidas de los dos
bloques fueron idénticas bit a bit. El positivo bajó de
4,01 a 3,71 s y el negativo de 1,10 a 1,03 s. Ambos
pasaron el contraste de 128 frames contra el solver.
[Comparación del armado](../evidence/rf_d_pilot_closed_returns19.json).

Se ensayó reutilizar el LU anterior con una evaluación del
residual real que exigía reducirlo al menos a la mitad. Se
conservaron el cruce y los límites eléctricos, pero el positivo
pasó de 3,85 a 4,10 s y el negativo de 1,09 a 1,13 s.
Se retiró la variante y se conservó el recibo con sus fuentes.
[Ensayo de reutilización](../evidence/rf_d_pilot_closed_returns20.json).

En la búsqueda de paso de Newton, cuando el criterio es
reducir el residual, basta evaluar las mismas corrientes
y los mismos incrementos de carga. La variante evita
construir las matrices de esa evaluación y mantiene la
tangente completa para comprobar la convergencia. Se
comparó sobre el armado disperso, sin instrumentación.
En el primer pase el positivo bajó de 3,66 a 3,54 s y el
negativo pasó de 1,03 a 1,06 s. Los dos bloques conservaron
su salida bit a bit y pasaron los límites contra el solver.
[Comparación del residual](../evidence/rf_d_pilot_closed_returns21.json).

Con el candidato primero, el positivo pasó de 3,90 a
3,42 s y el negativo de 1,06 a 0,965 s. El ahorro en la
rama positiva se observó en los dos órdenes. El efecto
en la negativa cambió de signo. Las dos salidas volvieron
a coincidir bit a bit. El peor error de R59/R60 frente al
solver fue 0,178 pA y el cruce conservó los ocho ticks
319096–319104. La variante queda disponible en el banco
con `--blocks --verify-reduced --compare-residual`. Los
bloques siguen fuera del margen de 1,333 ms y la prueba
del candidato en Desktop queda pendiente.
[Comparación en orden inverso](../evidence/rf_d_pilot_closed_returns22.json).

## Dos estados de carga a 96 kHz

La reducción del camino de audio empieza por C2 y C5 en
la revisión nominal CA3046, con los controles y el decay
de las reservas cargadas. Se conserva un voltaje por
capacitor de 10 µF y los seis caminos resistivos
x8/x11/x0 de 1/10/10 kΩ y x44/x47/x29 de 0,1/1/10 kΩ.
Los valores y el alcance provienen de los
[contornos cargados](CONTORNOS_CADENA_PROTOCOLO.md) y del
[stamp de temporizadores](../tools/rf_d_pilot_contours.rs).

Para cada estado, el equivalente resistivo define una
constante de tiempo C/ΣG. El núcleo integra la carga
con la respuesta exponencial de ese polo. La prueba
conserva los límites de 20 µV en los temporizadores y
2 nA en cada una de sus seis corrientes resistivas
observadas con los voltajes de carga impuestos.

La interpolación lineal de los seis voltajes a 96 kHz
pasó los dos flancos negativos. En la ventana positiva,
el error de C2 llegó a 1,907 mV. Dividir el intervalo
usando los ticks 319096–319104 del solver lo redujo a
0,489 mV. Incluso la interpolación lineal cada ocho
ticks excedió 2 nA en el camino de 1 kΩ en la positiva.
El banco repitió las salidas rechazadas por bits.
[Contraste de la interpolación](../evidence/rf_d_pilot_timer_rc01.json).

El banco alternativo proyecta por separado los seis
voltajes sobre el peso exponencial de cada capacitor.
Compone las dos evaluaciones de carga de cada paso de
Radau fino, con pesos proporcionales a 4,5 y 1,5 + hΣG/C.
Después aplica la caída exponencial al acumularlas en
un intervalo de 96 kHz. Con ese voltaje efectivo, el
núcleo ejecuta una sola transición por capacitor.
El banco obtiene esos voltajes del solver y usa el
estado del capacitor de la referencia sólo al arrancar.
[Modelo](../tools/rf_d_pilot_timer_rc.rs),
[banco](../tools/check_rf_d_pilot_timer_rc.py).

El avance con voltajes efectivos pasó las tres reservas
a 96 kHz. El mayor error de temporizador fue inferior a
1e−15 V frente a las etapas del solver. En 2.000 bloques
nativos de 128 frames a 48 kHz, la mediana del par fue
1,1 µs y el máximo 3,7 µs. El tiempo incluye dos avances
por frame y mide sólo el par RC con las entradas ya
disponibles. [Contraste y coste](../evidence/rf_d_pilot_timer_rc02.json).

La siguiente pieza es obtener la carga transferida del
modelo de conmutación y de los puertos cargados. Los
ocho ticks quedan como referencia del biestable. El
contraste de R59/R60 y J7, el plazo de la voz completa
y la prueba en Desktop corresponden al candidato acoplado.

## Generación de corriente de ataque desde los colectores

Los transistores PNP de ataque toman los colectores x26
y x40 y el voltaje instantáneo de C2 o C5. El modelo
devuelve la corriente que entra a cada capacitor y la
que vuelve al colector por 3,3 kΩ. Se eliminan x6/x7/x8
y x43/x44 de las incógnitas externas. Se mantienen
la fuente de 9,3 V, el resistor de base de 560 Ω y
el camino de 1,1 kΩ o 100 Ω hacia el capacitor. Los
valores proceden de los [stamps del gatillo cargado](../tools/rf_d_pilot_trigger.rs)
de la revisión CA3046 de la [voz de referencia](CONTORNOS_CADENA_PROTOCOLO.md).

El transporte nominal conserva la juntura inversa
también en saturación. Despejar la corriente directa
a partir del colector convierte la ecuación de base
en una raíz escalar monótona. Su variable es el logit
de la posición del colector entre el límite inferior
del capacitor y el límite de saturación. Newton con
bracket tiene un máximo de 16 iteraciones y rechaza
entradas fuera de 0–9,3 V en el colector del biestable
y 0–8 V en C2/C5. El dominio corresponde a los
dispositivos nominales a 298,15 K y al ajuste nominal
de ambos ataques.

El barrido dio un error KCL máximo de 3,39 fA en
12.231 puntos por celda. Con los colectores y
capacitores de la referencia fina, el peor error
de las corrientes devueltas fue 1,22 fA. Proyectar
esas dos cargas generadas a 96 kHz conservó los
resultados de C2/C5 en las tres ventanas. Retener
un voltaje de ataque por paso excedió el límite de
2 nA al liberar KEY en la negativa y durante el
cruce positivo. [Contraste de las dos celdas](../evidence/rf_d_pilot_timer_rc03.json).

La actualización a reloj fijo retiene la corriente de
ataque, evaluada con el estado propio de C2/C5, y
conserva las resistencias de los otros dos puertos de
cada capacitor. El banco impone esos cuatro puertos
y entrega los colectores al inicio de cada paso de
96 kHz. Pasaron ambos flancos negativos. El C5 positivo
también pasó, pero el error de C2 en esa ventana fue
1,052 mV al retener la corriente a través de la caída
del camino de ataque de volumen.

Los dos caminos de ataque más C2/C5 tardaron 63,3 µs
de mediana y 90,7 µs de máximo en 2.000 bloques de
128 frames. Se conserva la reproducción exacta del
rechazo positivo. Queda modelar la carga integrada
durante la caída del ataque de volumen, contrastar
el evento del biestable y cerrar R59/R60 y J7 antes
de medir la voz completa y probar en Desktop.
[Banco a 96 kHz](../evidence/rf_d_pilot_timer_rc04.json).

## Carga de ataque durante el cruce

En la ventana positiva se compararon dos rampas de
corriente de ataque separadas por la conmutación.
Las pendientes se obtuvieron de los intervalos
adyacentes a 96 kHz. Cortar en el centro de los ocho
ticks de referencia dejó 74,4 µV de error en C2.
El promedio ponderado de ataque fue 4,581 mA en
esa variante, frente a los 4,652 mA de referencia.

Ajustar sólo el área ponderada del pulso con la
referencia dejó 1,49 nV de error de C2 en toda la
ventana. Para el modelo de dos rampas, esa área
equivale a cortar 131,7 ns después del centro del
intervalo del cruce. Es una medida de la carga que
transfiere la transición en esta reserva. El
intervalo del evento del biestable sigue en
319096–319104. Falta obtener esa área del estado
eléctrico durante la caída del ataque y validarla
con otras cargas.
[Contraste del área de ataque](../evidence/rf_d_pilot_timer_rc05.json).

## Cola de ataque en coordenadas del colector Q25

Durante la subida monótona de x26 se usa ese voltaje
como coordenada. La única memoria del colector en
el stamp nominal es la juntura BC de Q25. La ecuación
local es `dt/dx26 = −dQcolector/dx26 / I_dc`.
El término de corriente incluye Q25, la base de Q17,
la rama de 33 kΩ y la reacción de la celda de ataque
por 3,3 kΩ. La capacitancia diferencial conserva la
depleción y difusión del [modelo de junturas](../tools/latch_charge_driver.rs).
El área se pondera con la misma respuesta de C2
a 96 kHz. La integración rechaza una densidad de
tiempo no positiva. [Modelo del colector](../tools/rf_d_pilot_attack_orbit.py).

Las dos reservas nuevas cambian las memorias iniciales
de C2/C5 en +50/−50 mV y −50/+50 mV, respectivamente.
El solver de referencia mantiene el resto de la voz y
las cargas de R59/R60. La discrepancia algebraica del
ancla se registra aparte. La comparación de los puertos
de ataque comienza en la primera etapa resuelta. En
las reservas desplazadas, la forma de las trayectorias
se toma de la nominal y se traslada usando sólo sus
voltajes en el cruce. El banco todavía suministra ese
estado e instante, las rampas exteriores y las demás
cargas de los temporizadores.

El primer ensayo con el paso de 40,69 ns dejó 7,79 µV
en C2 nominal. Trasladar la forma completa a C2 bajo
produjo densidad de tiempo negativa antes del cruce.
Se conserva también la comparación de las anclas
perturbadas antes de resolver sus nodos algebraicos.
[Primer ensayo](../evidence/rf_d_pilot_timer_rc06.json).

Con el paso de referencia de 13,56 ns, todos los
cruces quedaron dentro de sus brackets de ocho ticks
anteriores, incluido **319096–319104** en nominal.
Integrar sólo la cola posterior al cruce evitó la
densidad negativa de la forma trasladada. Con 16
tramos, el nominal dio 1,16 µV de error de C2 y las
reservas trasladadas dieron 2,12 y 0,033 µV. El
límite de corriente de 2 nA en el resistor de 1 kΩ
equivale a 2 µV con el resto de sus puertos impuestos.
[Referencia refinada](../evidence/rf_d_pilot_timer_rc07.json).

Con 24 tramos y ocho evaluaciones por tramo, la misma
forma nominal de la cola pasó los tres casos refinados.
El error máximo en C2 fue 0,712 µV en nominal, 1,687 µV
con C2 alto y 0,501 µV con C2 bajo. La variante de 32
tramos también pasó. Queda pendiente generar el estado
y el instante del cruce en el motor, contrastar R59/R60
y J7 en el candidato acoplado y medir el bloque de voz
completa antes de probarlo en Desktop.
[Comparación de tramos y reservas](../evidence/rf_d_pilot_timer_rc08.json).

## Predicción desde el colector en subida

Se detecta el primer estado aceptado donde x26 pasa
0,35 V en subida y todavía está por debajo de x28.
El predictor ajusta la forma nominal de los nodos
vecinos a esa observación, busca x26 = x28 e integra
el tiempo con la KCL de Q25. El tramo previo y la
cola usan la misma ley de transporte y la reacción
de ataque. Los dos flancos de la rama negativa
carecieron de un disparo por ese umbral.

Con la forma nominal de 24 tramos, la observación
antecedió el evento entre 115 y 123 ns. La predicción
cayó dentro de los ocho ticks en nominal y en las
dos reservas de carga. El peor error fue 0,22 ns
frente al cruce interpolado del solver refinado. Al
usar ese estado e instante para calcular la cola,
el peor error en C2 fue 1,59 µV. El error máximo
en los cuatro voltajes predichos fue 0,629 mV. El
banco sigue suministrando la observación temprana,
las rampas exteriores y las demás cargas de C2/C5.
[Predicción y cola](../evidence/rf_d_pilot_timer_rc09.json).

El núcleo Rust usa tablas de tamaño fijo, ocho puntos
por tramo y la capacitancia de juntura de la biblioteca
del circuito. Reproduce el instante y el área de la
variante de laboratorio y pasó los mismos tres
contrastes. En 2.000 repeticiones por caso, las medianas
fueron 94,5–97,6 µs y el máximo observado fue 141,3 µs
por evento, incluyendo la búsqueda del cruce y la
integración de la cola. Es el coste del evento aislado.
Sigue pendiente generar su estado de entrada dentro
del piloto y verificar R59/R60, J7 y el plazo del
bloque completo antes de probar en Desktop.
[Núcleo Rust](../tools/rf_d_pilot_crossing.rs),
[contraste y coste](../evidence/rf_d_pilot_timer_rc10.json).

## Reloj de C4 hasta el umbral del colector

Se genera la observación previa al cruce desde un
estado del borde de 96 kHz. Se parametrizan por x26
el voltaje entre placas de C4 y las tensiones vecinas.
El tiempo hasta x26 = 0,35 V se obtiene de la ley de
R28/C4, con R28 de 10 kΩ y C4 de 10 nF. En cada tramo
lineal se integra exactamente la razón entre el
cambio de carga y la caída x23 − x17. Los valores
proceden del [stamp cargado](../tools/rf_d_pilot_trigger.rs)
y de la [referencia CA3046](CONTORNOS_CADENA_PROTOCOLO.md).
El estado generado alimenta el núcleo Rust que
predice el cruce e integra la cola de ataque.

La familia se calibra con la escena nominal y
perturbaciones independientes de ±75 mV de C2 y C5.
Las dos reservas combinadas de ±50 mV se excluyen de
la calibración. El banco lee las observaciones
eléctricas a 96 kHz del solver y usa dos bordes
anteriores para estimar la rampa de ataque. Para
aislar el efecto en C2, conserva las otras cargas
de referencia y mide el error de la corriente
ponderada del intervalo del evento.

En el primer ensayo, la familia lineal ubicó los tres
eventos dentro de sus brackets de ocho ticks. El
error de C2 en el intervalo fue 9,20 µV en nominal
y 2,97 y 9,02 µV en las dos reservas. Los dos flancos
negativos carecieron de un disparo falso.
[Primer contraste](../evidence/rf_d_pilot_precursor01.json).

Con 65 puntos se mejoró la interpolación del
estado inicial con tres puntos locales. La familia
cuadrática por carga pasó los tres casos a 96 kHz.
El peor error temporal fue 1,58 ns y los errores de
C2 fueron 0,184, 1,135 y 1,053 µV. La familia lineal
con 257 puntos siguió fuera del límite de C2 en las
reservas. El término mixto se contrastó con otras
dos perturbaciones de calibración y la variante
cuadrática por carga pasó sin depender de ese término.
[Contraste del reloj de C4](../evidence/rf_d_pilot_precursor02.json).
