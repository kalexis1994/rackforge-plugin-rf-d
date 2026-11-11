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

El núcleo Rust reproduce el reloj cuadrático de C4
y alimenta directamente el predictor y la cola.
El banco recorre 256 observaciones por bloque de
128 frames a 48 kHz, con un cruce y un estado
asentado al completar el bloque. En 2.000 bloques
por cada uno de los tres casos, las medianas fueron
98–101 µs y el máximo observado fue 145,4 µs.
El tiempo cubre C4, la búsqueda del cruce y la
cola. Las observaciones a 96 kHz provienen del
solver. Queda generarlas en la voz y contrastar
R59/R60, J7 y el plazo del bloque de audio antes
de probar en Desktop. [Medición nativa](../evidence/rf_d_pilot_precursor03.json).

## C4 desde un único estado inicial

El banco avanza entre los bordes de 96 kHz con la
corriente de R28 y el voltaje entre las placas de C4.
Al atravesar un tramo se integra el tiempo de manera
analítica. Para un borde dentro del tramo se invierte
esa misma expresión y se conserva la carga resultante.
El modelo genera el colector, sus vecinos y los
voltajes de los temporizadores sobre la curva cargada.
Las dos corrientes de ataque que forman la rampa
del evento se obtienen de esos estados generados.

Parametrizar la curva por x26 pasó en nominal, pero
la variante densa dejó 31,29 ns de error al arrancar
la reserva de C2 bajo desde el ancla original. El
voltaje del colector aún reflejaba el estado previo a
la perturbación de carga. La reserva pasó al arrancar
medio frame después. [Arranque indexado por x26](../evidence/rf_d_pilot_precursor04.json).

La curva indexada por el voltaje de C4 se calibra con
las mismas escenas y usa una sola observación inicial.
Con 65 puntos y los términos cuadráticos de C2 y C5,
pasaron las tres escenas desde el ancla original y
desde medio frame después. El peor error temporal
fue 4,03 ns y el peor error de C2 atribuible al
intervalo del evento fue 1,921 µV. Los dos flancos
negativos no activaron el recorrido de subida.
[Contraste con memoria de C4](../evidence/rf_d_pilot_precursor05.json).

El límite de 2 µV anterior se aplica al aporte de
ataque en el intervalo del evento, con las demás
cargas del contraste fijadas. El máximo sobre los
bordes generados antes del evento fue 4,933 µV en
el voltaje de C2 y 38,962 µV en el de C4. La
comparación de la trayectoria completa queda
separada de la aceptación del intervalo del cruce.

El núcleo Rust conserva el estado de C4 entre llamadas
y entrega al predictor el umbral dentro de su intervalo.
Los seis recorridos reprodujeron los estados y el área
del banco. Los dos anclajes de la rama negativa
quedaron sin evento en Rust. En 2.000 repeticiones por
recorrido positivo, las medianas del arranque a la cola
fueron 99,0–102,3 µs y el máximo fue 164,4 µs. La
medición incluye la inicialización, el avance hasta el
umbral, el cruce y la carga de ataque. La voz acoplada
con R59/R60, J7 y el bloque de audio sigue pendiente.
[Núcleo de C4](../tools/rf_d_pilot_c4_clock.rs),
[contraste y coste](../evidence/rf_d_pilot_precursor06.json).

## C2 y C5 con sus propias corrientes

El modelo transporta dos voltajes de capacitor a
96 kHz. Las celdas PNP calculan el ataque a partir
de x26/x40 y de los voltajes que realmente lleva
cada capacitor. Los puertos resistivos de descarga
y seguidores se generan sobre la curva cargada de
C4 antes del cruce. Sus incidencias conservan los
caminos x11/x0 de 10/10 kΩ y x47/x29 de 1/10 kΩ.
Los valores salen del [modelo de temporizadores](../tools/rf_d_pilot_timer_rc.rs)
de la [referencia CA3046 cargada](CONTORNOS_CADENA_PROTOCOLO.md).

El intervalo de conmutación usa el área de ataque
del núcleo Rust y una proyección de los cuatro
puertos resistivos posteriores al cruce. Esa curva
se calibra con las mismas perturbaciones de ±75 mV
y se contrasta en las dos reservas de ±50 mV. La
curva se referencia al evento predicho por el
modelo. Cada candidato parte de una sola semilla.
Las comparaciones miden C2 y C5, los ocho ticks y
las corrientes en los bordes previos al evento.

En el primer pase, proyectar el intervalo del
evento pasó desde las anclas asentadas. Retener las
cargas durante el cruce dejó hasta 42,7 µV de error
en C5 nominal. Con perturbaciones desde el ancla
original, interpolar las cargas sólo entre los
bordes de 96 kHz dejó hasta 16,6 µV antes del
evento. [Primer contraste](../evidence/rf_d_pilot_precursor07.json).

Para el arranque perturbado se proyectan las cargas
sobre cada tramo de la curva de C4. La proyección
pondera cada tramo por su duración y por la respuesta
exponencial del capacitor que lo recibe. Al comparar
corrientes se registra aparte el ancla artificial
anterior a la resolución algebraica de los puertos.
Los voltajes se contrastan desde el primer intervalo.

Con 65 puntos, el peor error en los dos voltajes
quedó por debajo de 2 µV desde ambas anclas.
El error del puerto de descarga x47 alcanzó 27,93 nA
en los bordes resueltos. El criterio conjunto exige
2 nA por camino, además de 2 µV y los ocho ticks.
[Proyección por tramos](../evidence/rf_d_pilot_precursor08.json).

La tabla uniforme de 257 puntos bajó el error máximo
de corriente de 27,93 a 1,928 nA y conservó los ocho
ticks en los seis casos. Cinco pasaron también el
límite de voltaje. En la reserva de C2 alto desde
el ancla asentada, el error de C2 en el borde
posterior al cruce fue 2,013 µV frente al límite de
2 µV. [Comparación de densidades](../evidence/rf_d_pilot_precursor09.json).

La variante de 161 puntos concentra el espaciado
de 1/256 en el primer cuarto de la curva de C4
y usa 1/128 en el resto. Con la proyección hasta
el umbral durante el intervalo del cruce, pasó los
seis recorridos. Los máximos al cerrar el evento
fueron 1,976 µV en C2 y 0,119 µV en C5. El peor
error de corriente en los bordes previos resueltos
fue 1,963 nA. Todos los eventos quedaron dentro de
sus ocho ticks. Proyectar hasta el umbral redujo
el error de C5 respecto de extrapolar las cargas
previas durante todo el intervalo.

El banco ejecuta la actualización de los
temporizadores y su proyección en Python. Las
celdas de ataque y el evento se evalúan en Rust.
Queda trasladar la actualización al motor nativo,
extenderla a la rama negativa y medir R59/R60, J7
y la voz completa antes de probar en Desktop.
[Arranque y proyección hasta el umbral](../evidence/rf_d_pilot_precursor10.json).

### Avance nativo de los temporizadores

Rust recorre los mismos 161 puntos de C4 con el
espaciado de arranque y proyecta los segmentos de
carga dentro de cada muestra. Conserva la memoria
de C2 y C5 hasta el borde posterior al cruce.
Los seis resultados de voltaje en ese borde fueron
idénticos bit a bit a Python. Las corrientes y los
ocho ticks volvieron a pasar contra el solver. El
replay previo de C4 también conservó su salida.

En 2.000 repeticiones por caso, el recorrido aislado
desde la semilla hasta el cierre del evento tuvo
medianas de 112,3–124,5 µs y un máximo de 198,9 µs.
El banco no ejecuta la voz ni la salida de audio.
Las anclas negativas no disparan el núcleo positivo.
[Medición nativa](../evidence/rf_d_pilot_precursor11.json).

### Rama negativa gobernada por C7

Para los flancos negativos de KEY, la coordenada de
memoria es el voltaje x21 de C7 de 100 nF. Se usa
la KCL original con R55 de 47 kΩ desde x20 y el
camino de 100 kΩ a x22. El puerto x22 se resuelve
con el diodo de KEY y su corriente inversa.
[Stamp del gatillo](../tools/rf_d_pilot_trigger.rs).

La curva parametrizada por C7 genera los colectores
de ataque y las cargas de decay y seguidores a partir
de una sola semilla. C2 y C5 conservan sus voltajes y
avanzan por sus corrientes. Se calibraron ambos
sentidos de KEY con perturbaciones independientes de
±10 mV en C2 y C5. Las reservas combinadas de ±5 mV
se mantienen fuera de la calibración. La comparación
abarca dos frames de host por caso a 48 kHz, con
avance interno a 96 kHz. Se compara la corriente
desde el primer borde resuelto después del flanco.

Los seis casos conservaron el orden de ambos
biestables. El peor error fue 2,04 nV en C2/C5,
3,22 pA en sus corrientes y 15,01 nV en C7. Rust
reprodujo los voltajes de C2/C5 y comparte con la
rama positiva la actualización de corrientes y la
proyección de cargas. En 2.000 repeticiones por
caso, las medianas fueron 15,5–16,4 µs y el máximo
fue 140,9 µs por flanco aislado. La medición incluye
la inicialización y los cuatro intervalos internos
del contraste. Queda validar R59/R60 y J7 en la
voz acoplada y medir el plazo del bloque de audio.
[Contraste de laboratorio](../evidence/rf_d_pilot_negative_timers01.json),
[contraste y coste en Rust](../evidence/rf_d_pilot_negative_timers02.json).

Al compartir la actualización de corrientes con el
tramo de C7, la repetición positiva conservó la salida
binaria de los seis recorridos y los ocho ticks. Las
medianas fueron 112,6–124,4 µs y el máximo observado
fue 605,1 µs, con un p99 de hasta 157,1 µs por caso.
[Repetición con el actualizador compartido](../evidence/rf_d_pilot_precursor12.json).

## Lectura de R59/R60 desde los relojes de carga

La lectura reutiliza las celdas físicas de Q3/Q2 y
Q26/Q28. En volumen, C2 alimenta la celda y x2 se
resuelve con R15. En filtro, los relojes de C4 y C7
generan x34, la entrada de Q26. En el primer borde
posterior al cruce positivo, x34 sale del perfil
calibrado respecto del evento predicho por el
biestable. Así se puede contrastar x3 y x37 en el
mismo reloj de 96 kHz que los temporizadores.
[Stamps de las celdas](../tools/rf_d_pilot_contour_ports.rs),
[protocolo de circuito](CONTORNOS_CADENA_PROTOCOLO.md).

El banco fija x4, la base del VCA y TAIL a sus
valores de Radau. Las dos celdas empiezan con sus
voltajes nodales del ancla y usan su propia solución
anterior para inicializar la siguiente. El voltaje x2
de Radau sólo inicializa Newton. El control usa C2 y
x34 de Radau con las mismas cargas y las mismas
celdas. Se exige un error máximo de 2 nA en cada
retorno en los bordes resueltos. Los dos flancos de
KEY y sus reservas de ±5 mV pasaron, con máximos de
0,286 fA en R59 y 0,233 fA en R60. Los seis recorridos
de los temporizadores conservaron su salida binaria.
[Contraste negativo](../evidence/rf_d_pilot_negative_timers03.json).

Los seis recorridos positivos, desde el ancla
original y desde el primer borde asentado, pasaron
hasta el primer borde posterior al cruce. El mayor
error fue de 28,6 pA en R59 y 53,2 pA en R60. El
error máximo en x34 fue de 20,7 nV. Se conservaron
los ocho ticks de cada reserva y las salidas
binarias de los temporizadores. El control con C2 y
x34 de Radau quedó por debajo de 0,001 fA en ambos
retornos. [Contraste positivo](../evidence/rf_d_pilot_precursor13.json).

La lectura mide los retornos con el receptor fijado
a la referencia. Queda realimentar el receptor con
esos retornos, devolver base y TAIL a los contornos,
y contrastar J7 y el plazo de la voz completa.

## Receptor de audio cerrado sobre R59/R60 a 96 kHz

El banco reutiliza el mapa reducido de Radau de la
voz CA3046 con el ancla transitoria, 17 voltajes de
capacitor y la fase del VCO H128. El VCO sigue viendo
BUS. Las dos etapas del receptor devuelven base del
VCA y TAIL a Q3/Q2 y Q26/Q28. El receptor recibe x3 y
x37 por los caminos de 68 kΩ y 680 Ω. x4 queda fijado
a la trayectoria del solver en este contraste.
[Cadena y fuentes](CONTORNOS_CADENA_PROTOCOLO.md),
[mapa de audio](../tools/rf_d_pilot_reduced_audio.rs).

Se comparan las etapas exactas de C2/x34, sus bordes
a 96 kHz interpolados al tercio de paso y los bordes
generados por C4/C7 con la misma interpolación. Los
límites son 2 nA en cada retorno, 20 µV en los cuatro
nodos de interfaz y 0,1 % RMS, 0,3 % de pico relativo
y 1 µV de media absoluta en J7. El cierre local exige
100 pV de diferencia máxima entre las tensiones
recibidas y las devueltas en las dos etapas.

La iteración directa se agotó en los seis casos
negativos durante el primer paso. En los positivos se
agotó entre el segundo y tercer paso, por la iteración
de interfaz o por la iteración interna del mapa. Los
rechazos se reprodujeron por bytes incluso al usar
C2 y x34 del solver en ambas etapas.
[Rama negativa](../evidence/rf_d_pilot_audio_readout_neg01.json),
[rama positiva](../evidence/rf_d_pilot_audio_readout_pos01.json).

La corrección conjunta usa cuatro tensiones de carga,
base y TAIL en las dos etapas. La dirección se obtiene
del mapa lineal de Radau y de la respuesta local de
cada celda a 1 µV. El residual se vuelve a medir con
la respuesta no lineal. El peor cierre aceptado usó
cinco iteraciones. Un candidato que agotó la iteración
interna del mapa se acepta únicamente si pasa las
tolerancias del stamp nodal y su corrección lineal.

En los seis positivos con puertos generados, el máximo
de J7 fue 0,0192 % RMS relativo, con 2,60 pA en R59 y
53,2 pA en R60. Los ocho ticks se conservaron.
Con C2/x34 exactos en ambas etapas, los seis negativos
también pasaron J7, con un máximo de 0,0126 % RMS. La
interpolación desde bordes de los puertos generados
dejó dos reservas negativas en 0,191 % y 0,180 % RMS,
frente a 0,1 %. Las corrientes sí pasaron. Interpolar
los bordes del solver reprodujo el rechazo, lo que
localiza la diferencia en la primera etapa del paso.
[Positivos](../evidence/rf_d_pilot_audio_readout_pos02.json),
[negativos](../evidence/rf_d_pilot_audio_readout_neg02.json).

El mayor tiempo nativo en 200 repeticiones por caso
positivo fue 1,227 ms para una ventana de cuatro pasos
a 96 kHz. Incluye las celdas y el receptor con H128.
El mapa está preparado y los puertos de contorno ya
están disponibles al empezar la medición.

En la rama negativa, x34 se evalúa en C7 al primer
tercio del paso, con la misma ley que en los bordes.
C2 conserva la interpolación entre bordes. Así pasaron
los seis casos, con 0,0126 % RMS de J7 como máximo y
0,138 pA de error máximo en R60. La salida binaria de
C2/C5 se conservó en ambas ramas. En las tres ventanas
positivas que usaron la verificación nodal se aceptó
una propuesta por ventana. La negativa no la necesitó.
[Etapa directa de C7](../evidence/rf_d_pilot_audio_readout_neg03.json).

El cierre local permite contrastar el receptor de
referencia bajo ambas ramas. Quedan el cierre de x4,
la transición entre ventanas y la reducción del coste
antes de medir una voz continua a 128 frames.

## Una iteración conjunta para audio y retornos

La proyección de Radau separa el término de historia,
las cuatro excitaciones de R59/R60 y los defectos de
juntura y BUS. En cada iteración se calcula una sola
respuesta de audio. Las cuatro diferencias de carga
se corrigen con el complemento de Schur de la
respuesta lineal. Las celdas se vuelven a evaluar
con las cargas corregidas, desde la misma historia
de capacitores y fase. x4 sigue fijado por el solver.

El primer pase alternó 200 ventanas por caso con
cada implementación, usando el mismo mapa y las
mismas entradas. Los seis cruces positivos pasaron,
con medianas entre 2,05 y 2,41 veces más rápidas.
Pasaron los dos flancos negativos nominales. Las
cuatro reservas negativas perturbadas fueron
rechazadas en el primer paso por la auditoría nodal,
que se ejecutó aparte de la medición. Se conservaron
las entradas y el replay de esos rechazos.
[Positivos](../evidence/rf_d_pilot_audio_readout_pos03.json),
[negativos](../evidence/rf_d_pilot_audio_readout_neg04.json).

El segundo pase incluyó la comprobación nodal en la
medición. Cuando la respuesta reducida se asentaba,
se resolvía la dirección de la KCL original con la
factorización ya disponible. Las correcciones se
acoplaban a las cuatro cargas por el mismo Schur.
Los seis positivos volvieron a pasar. Las reservas
negativas avanzaron uno o dos pasos y quedaron
limitadas por 2,38–2,84 nV de corrección nodal frente
a 2 nV. Se conservan las métricas y los replays.
[Positivos con comprobación incluida](../evidence/rf_d_pilot_audio_readout_pos04.json),
[rechazos negativos](../evidence/rf_d_pilot_audio_readout_neg05.json).

En el tercer pase, la iteración conjunta resuelve las
celdas a 2 fA y 2 pV antes de calcular el Schur. La
derivada del voltaje de salida respecto de cada carga
se obtiene resolviendo el Jacobiano ya factorizado
con 1/R59 o 1/R60 en la fila del puerto. Así se conserva
la realimentación de Q3/Q2 y Q26/Q28 sin el sondeo de
1 µV del primer pase. Las tolerancias de aceptación
de la KCL y del contraste con Radau se mantuvieron.

Pasaron los 12 casos. Los máximos de J7 fueron
0,0192 % RMS en el positivo y 0,0126 % en el negativo.
El error máximo fue de 2,60 pA en R59 y 53,2 pA en
R60. La diferencia de carga llegó a 1,98 pV, frente a
100 pV. En las reservas negativas se aplicaron hasta
cuatro correcciones nodales por ventana. La salida de
los temporizadores y del banco anidado se conservó
bit a bit. Los ocho ticks quedaron en sus intervalos.

| Ventanas a 96 kHz | Factor de mejora de la mediana | Pico anidado | Pico conjunto |
| --- | ---: | ---: | ---: |
| Positivas | 1,81–2,30 | 1,289 ms | 0,600 ms |
| Negativas | 1,16–1,81 | 0,992 ms | 0,820 ms |

La medición alterna 200 ventanas por caso y modo.
Cada ventana cubre tres o cuatro pasos, con el mapa
preparado, los contornos calculados y x4 impuesto.
El tiempo del candidato incluye el cierre de KCL.
Queda medir el recorrido continuo a 128 frames.
[Positivos](../evidence/rf_d_pilot_audio_readout_pos05.json),
[negativos](../evidence/rf_d_pilot_audio_readout_neg06.json).

## Cierre del divisor x4 y CR6

La celda de volumen resuelve x3 y x4 juntos. R24 de
6,8 kΩ estampa ambas filas. R27 de 16,9 kΩ conecta
x4 a −10 V y CR6 devuelve corriente hacia el cátodo
x27. La fila de x4 y su derivada reutilizan la ley de
la referencia CA3046. El Jacobiano de cinco nodos
devuelve la tangente de R59 al cierre de audio.
[SVC-9 Fig. 9-7 p. 9 y topología](CONTORNO_VOLUMEN_CIRCUITO.md),
[stamp](../tools/rf_d_pilot_contour_ports.rs).

El primer contraste usa el cátodo exacto del solver
y luego el generado por C4/C7 en ambas etapas. Se
mantienen los límites de J7 y R59/R60 y se exigen
20 µV en x4 y 2 nA en CR6 en las dos etapas. Los
seis negativos pasaron, con 0,431 nV de error en
x4 y −10 nA de CR6. En los positivos J7 y ambos
retornos pasaron, pero x4 llegó a 335 µV de error
también con x27 exacto. Se conservaron los replays.
[Negativos](../evidence/rf_d_pilot_cv_readout_neg01.json),
[rechazo positivo](../evidence/rf_d_pilot_cv_readout_pos01.json).

La prueba de conducción directa usa los vectores DC
de C2 a 9,3 V, x27 a 0,01 V y 0,7 V y R61 a 200 Ω.
El cierre reproduce 495,36 µA y 362,62 µA de CR6 con
un error inferior a 1 pA. Un bracket escalar de x4
con la celda original de cuatro nodos confirma los
voltajes y la derivada de R59 frente a una diferencia
central. [Vectores de referencia](../evidence/circuit71_port_vectors.json),
[contexto de las cargas de reset](PUERTO_CONTORNO_CADENA_71.md).

En positivo se proyectan las cargas resistivas y de
ataque de C2 hasta el primer tercio del paso con los
segmentos de C4. Se conserva el avance de C2/C5
hasta el borde y el instante del biestable. Así se
elimina el error de interpolar C2 a través del
evento. El peor error de C2 en la primera etapa
fue 76,8 nV. Los seis positivos pasaron con x27
generado, con 1,41 µV en x4, 2,63 pA en R59, 53,2 pA
en R60 y 0,0192 % RMS en J7.
[Contraste positivo](../evidence/rf_d_pilot_cv_readout_pos02.json).

La repetición negativa pasó los seis casos y dio
0,431 nV en x4. Las dos campañas conservan por bytes
las salidas de C2/C5 y del banco con x4 impuesto.
CR6 devolvió −10 nA en las ventanas dinámicas,
igual que la referencia. Los máximos del receptor
fueron 0,559 ms en positivo y 0,823 ms en negativo
para ventanas de tres o cuatro pasos a 96 kHz, con
el mapa preparado y los contornos ya calculados.
Quedan la realimentación de CR6 hacia el estado de
Q15 en conducción directa, la transición entre
ventanas y la medición continua a 128 frames.
[Repetición negativa](../evidence/rf_d_pilot_cv_readout_neg02.json).

## Retorno de CR6 a las junturas de Q15

El bloque de dos nodos integra la base x27 y el
colector x28 con sus cargas BE/BC. En cada etapa
resuelve Q3/Q2 y x4 por el seguidor de cinco nodos.
La corriente de CR6 sale de x4 y entra en x27.
R56, R38, R39, CR8 y los terminales de Q15 mantienen
sus ramas. El complemento de Schur conserva la
derivada del cátodo a través de x4 y R24.
[SVC-9 Fig. 9-7 p. 9 y topología](CONTORNO_VOLUMEN_CIRCUITO.md),
[stamp completo](../crates/rf-d-circuit/src/prepared_volume_residual.rs).

Cada recorrido local parte de una única solución DC
y dura 128 frames a 48 kHz. C2, la base del VCA, la
base y el colector de Q25 y el ánodo de CR8 se
imponen como puertos suaves. El oráculo conserva
los siete nodos sin condensar y usa la misma ley de
carga de Q15. Los límites son 20 µV y 2 nA, además
de 20 zC de diferencia en las cargas al mismo reloj.
El primer adaptador del oráculo llevó al PNP Q16
fuera de dominio en filas ajenas al puerto. Se
repitió el rechazo y se corrigieron sus terminales
fijos. [Rechazo de inicialización](../evidence/rf_d_pilot_q15_return01.json).

A 96 kHz pasaron los recorridos de polaridad fija
contra el oráculo refinado a 768 kHz. El máximo
error de x27 en inversa fue 3,33 µV. En directa
CR6 condujo entre 338 y 366 µA, con un máximo error
de 33,6 fA. En la trayectoria mixta el modelo reducido
coincidió al mismo reloj, pero el error temporal
de x28 llegó a 12,75 mV y el de CR6 a 10,85 nA.
[Contraste a 96 kHz](../evidence/rf_d_pilot_q15_return02.json).

El recorrido mixto a 3,072 MHz quedó en 20,68 µV
frente al límite de 20 µV en x28. A 6,144 MHz pasó,
con 3,03 µV y 3,58 pA en CR6 contra Radau a
24,576 MHz. Las dos inversiones de orden quedaron
en los mismos intervalos de 32 ticks del candidato.
[Rechazo a 3,072 MHz](../evidence/rf_d_pilot_q15_return03.json),
[contraste a 6,144 MHz](../evidence/rf_d_pilot_q15_return04.json).

El reloj fino caracteriza la referencia local. Los
peores bloques nativos de 128 frames del candidato
a 96 kHz fueron 1,48 ms en inversa y 2,20 ms en
directa, con los otros puertos ya disponibles.
Queda conectar este retorno a la dinámica de Q25
y al receptor de audio en una voz continua.

El Jacobiano reducido se contrastó con el Schur
del stamp completo en las dos etapas de cada paso.
El peor error de conductancia fue 5,21 aS. Las
cargas y las matrices de capacitancia coincidieron
en los tres recorridos. El rechazo inicial se
reprodujo con entradas de 176 bytes y conserva el
hash del recorrido completo.
[Auditoría](../evidence/rf_d_pilot_q15_audit01.json).

La regresión de la voz con x4 cerrado repitió los
doce casos. C2/C5 y los receptores con x4 impuesto
y calculado conservaron sus salidas bit a bit.
Se mantuvieron J7, R59/R60 y los ocho ticks de las
reservas positivas.
[Control positivo](../evidence/rf_d_pilot_cv_readout_pos03.json),
[control negativo](../evidence/rf_d_pilot_cv_readout_neg03.json).

## Q25 y Q15 con C4 y el retorno de CR6

El modelo integra x25, x26, x27, x28 y x23.
Conserva las dos cargas BE/BC y la carga orientada
de C4 de 10 nF. R28 de 10 kΩ conecta x23 al reset,
R38 de 10 kΩ y R56 de 33 kΩ cierran los retornos
entre los dos transistores. R40 de 3,3 kΩ lleva la
carga de ataque desde x6 y la base de Q17 ve x9.
El seguidor, R59 y CR6 se resuelven en cada etapa.
[Topología SVC-9, Fig. 9-7 p. 9](CONTORNO_VOLUMEN_CIRCUITO.md),
[modelo](../tools/rf_d_pilot_bistable_return.rs).

El banco conserva C2, base del VCA, x17, x24, x6
y x9 como fronteras. En dos recorridos de 128 frames
con una semilla DC, el candidato a 96 kHz pasó
contra el stamp de diez nodos y su refinamiento a
768 kHz. El error nodal máximo fue 12,63 nV. En
directa, CR6 condujo entre 336 y 364 µA, con un
error máximo de 0,178 pA. Los picos nativos fueron
2,49 ms en inversa y 3,22 ms en directa.
[Recorridos controlados](../evidence/rf_d_pilot_bistable_return_active01.json).

El replay de las cinco reservas de la voz usa una
sola semilla transitoria por ventana y las etapas
refinadas del solver en los seis puertos. Pasó en
ambas etapas, con 28,7 nV de error nodal máximo.
Los tres positivos conservaron sus intervalos de
ocho ticks y ambos negativos su orden. Al usar
96 kHz con los mismos puertos, los tres positivos
se detuvieron en el cuarto paso. Se conservaron
las entradas y la repetición de esos rechazos.
[Reservas](../evidence/rf_d_pilot_bistable_return_windows01.json),
[regresión de Q15](../evidence/rf_d_pilot_q15_audit02.json).

### Eliminación de la placa x23

Con `v = x23 − x25` y `β = R28·C4/h`, las dos
etapas satisfacen `(I + βB) Δv = x17 − x25 − v_anterior`.
Se reconstruye x23 en cada etapa y se conserva su
valor junto con x25 al aceptar el paso. La corriente
que entra en la fila de x25 se obtiene de R28,
incluidas las derivadas entre etapas. El sistema
de Newton pasa de diez a ocho incógnitas.

Las cinco reservas pasaron de nuevo con las mismas
entradas y los mismos intervalos de ocho ticks.
El error máximo en la carga de C4 frente a la voz
de referencia fue 1,25 aC. Los tres positivos
volvieron a detenerse en el cuarto paso a 96 kHz.
[Contraste de reservas](../evidence/rf_d_pilot_bistable_return_windows02.json).

Los recorridos de polaridad fija pasaron a 96 kHz.
En 100 repeticiones alternadas por caso, las medianas
bajaron 11,0 % en inversa y 6,5 % en directa. Los
máximos fueron 2,47 ms y 2,92 ms para 128 frames
del bloque aislado con los seis puertos impuestos.
Queda cerrar x6 y x9 y contrastar la voz continua
con el receptor de audio.
[Coste y contraste eléctrico](../evidence/rf_d_pilot_bistable_return_active02.json).

## Cargas de ataque y decay en el colector de Q25

Q16 resuelve x6 y x8 con R41 = 560 Ω, R40 = 3,3 kΩ
y R42/R13 de 100 Ω/1 kΩ en serie. Devuelve a x26
la corriente de R40 y su tangente a C2 fijo. El
banco también comprueba la corriente que entra a C2.

El decay resuelve x9, x10 y x11 con Q17/Q18, R43
de 10 kΩ a −10 V, R44 de 4,7 kΩ y R16 de panel
de 10 kΩ a C2. Se resuelve el Jacobiano local contra
la derivada de la fila de emisor de Q17 para devolver
a x26 la corriente de base con su tangente cargada.
La corriente de R16 sale de C2 hacia x11 con el signo
usado en el contraste. El estado de carga del
biestable y C4 sigue en las dos etapas de Radau.

Los valores corresponden al panel nominal del
[stamp de referencia](../tools/rf_d_pilot_trigger.rs)
y a la [topología SVC-9, Fig. 9-7 p. 9](CONTORNO_VOLUMEN_CIRCUITO.md).
Q16 mantiene su dominio de 0–9,3 V en x26 y 0–8 V
en C2. El contraste cubre las cinco reservas de la
referencia numérica a temperatura nominal. Quedan
por caracterizar las tolerancias físicas y el
recorrido completo de los potenciómetros.

Las dos variantes parten de una semilla por ventana.
El cierre de ataque retira x6 de las entradas de
etapa. El cierre conjunto retira además x9. C2,
la base del VCA, x17, x24 y el emisor de sustain
x14 siguen impuestos en el cierre conjunto. El
caso conjunto pasó a 73,728 MHz con 0,689 µV de
error máximo en los puertos cerrados y 0,689 nA
en la corriente de R13. R40 quedó en 15,5 pA y
R16 de panel en 13,2 pA. Los tres cruces positivos
quedaron en los intervalos de ocho ticks y ambos
negativos conservaron su orden.
[Ataque](../evidence/rf_d_pilot_bistable_return_attack01.json),
[ataque y decay](../evidence/rf_d_pilot_bistable_return_loads02.json).

Los dos negativos también pasaron el contraste
a 96 kHz. Los tres positivos repitieron el rechazo
en el cuarto paso. Se guardaron las entradas de
replay, y también el primer fallo de compilación
del oráculo por alcance de la configuración Rust.
El cierre eléctrico se usa como referencia local
para el piloto. El reloj positivo a 96 kHz y su
integración con el receptor de audio quedan abiertos.
[Compilación inicial](../evidence/rf_d_pilot_bistable_return_loads01.json).

Los recorridos controlados de CR6 con las cargas
impuestas conservaron sus entradas y salidas bit
a bit a 96, 384 y 768 kHz.
[Regresión de polaridad fija](../evidence/rf_d_pilot_bistable_return_active03.json).

### Cuarto paso positivo a 96 kHz

Se aisló el intervalo que contiene el cruce para
cada una de las tres reservas positivas. El banco
arranca con el historial del solver a 73,728 MHz.
Repetir ese historial como semilla en ambas etapas
agotó el presupuesto de Newton en los tres casos.
Al usar además los dos estados finos como semillas
de etapa, los tres casos convergieron y conservaron
el orden de los nodos antes y después del cruce.

Los estados convergidos todavía difirieron del
solver fino. El peor error fue 106,03 mV en x28,
23,13 mV en x26 y 5,99 µA en R40. Estas diferencias
exceden los límites de 20 µV y 2 nA. El contraste
a reloj fino y los diagnósticos previos conservaron
sus entradas y salidas. El ensayo con semillas de
oráculo se limita al laboratorio. Para el piloto
queda contrastar un avance que trate el evento
dentro del paso con el reloj de C4.
[Diagnóstico del cruce](../evidence/rf_d_pilot_bistable_return_seeded01.json).

### Transferencia desde el reloj de C4

El reloj de C4 arranca con el estado inicial de
la ventana y predice el cruce y los voltajes de
C2/C5. La curva posterior usa la edad desde el
cruce y los dos pesos de carga inferidos por el
reloj. Se construye con la trayectoria nominal y
las cuatro perturbaciones axiales de ±75 mV. Las
dos perturbaciones diagonales de ±50 mV quedan
reservadas. La interpolación usa el voltaje
entre placas de C4 como coordenada de estado.
Al retomar Radau, ese voltaje vuelve a entrar
como historia de carga. Q16, Q17/Q18 y el
seguidor se resuelven con el C2 generado en la
transferencia. La continuación recibe C2, base
del VCA, x17, x24 y x14 de la referencia.

Los tres eventos quedaron en sus ocho ticks.
El peor error temporal fue 0,117 ns y el de
C2/C5 en el borde, 1,78 µV. La curva de 33
puntos superó 20 µV en x25 con C2 bajo. Con
129 puntos, las tres transferencias pasaron y
el peor error nodal fue 7,73 µV. En C2 bajo,
el primer paso posterior dio 47,34 µV de error
en x25. Con el estado exacto del solver dio
44,45 µV. Las dos ramas negativas pasaron sin
eventos. El error de continuación acota este
ensayo de panel nominal y las reservas medidas.
[Contraste del reloj y la transferencia](../evidence/rf_d_pilot_bistable_handoff02.json).
El primer intento se detuvo al elevar al cuadrado
una lista de pesos en Python. Se guardó el
resultado parcial y se corrigió el adaptador.
[Registro del primer intento](../evidence/rf_d_pilot_bistable_handoff01.json).

El ensayo con dos pasos de 192 kHz en el primer
intervalo posterior superó el límite en nominal
y con C2 bajo. En C2 bajo, el mayor error fue
60,38 µV en x23 y 2,20 nA en R40.
[Dos medios pasos](../evidence/rf_d_pilot_bistable_handoff03.json).

La segunda variante proyecta un intervalo
adicional sobre la trayectoria posterior al
evento. Usa 129 puntos sobre dos periodos de
96 kHz con más densidad cerca del cruce. Las dos
etapas de ese intervalo resuelven sus cargas
algebraicas con las fronteras impuestas. Radau
retoma en el borde siguiente con el voltaje
entre placas de C4 y las cuatro tensiones de
Q25/Q15 de la curva. El paso vuelve a ser de
96 kHz durante el resto de la ventana.

Pasaron las cinco reservas. Los tres cruces
quedaron en sus ocho ticks. Las dos etapas del
intervalo proyectado quedaron en 3,31 µV y la
continuación en 4,42 µV. El error de corriente
máximo en esos dos tramos fue 0,446 pA. Las
salidas del reloj previo se reprodujeron bit
a bit. Queda portar la proyección de estado a
Rust y contrastar C2, R59/R60 y J7 acoplados.
La prueba usa ventanas de hasta cinco frames
y deja abierta la medición de 128 frames en el
host.
[Transferencia un intervalo más tarde](../evidence/rf_d_pilot_bistable_handoff04.json).

### Transferencia y continuación nativas

El banco ejecuta en un mismo proceso Rust el reloj
de C4, la transferencia en el borde del cruce,
las dos etapas del intervalo proyectado y el
reinicio de Radau a 96 kHz. La proyección evalúa
sólo los dos puntos vecinos de cada edad. Valida
las tablas al cargarlas y limita los pesos al
dominio del reloj. Conserva x23 − x25 al reconstruir
las dos tensiones de la placa de C4.

Las tensiones y corrientes coincidieron bit a bit
con el adaptador Python en las tres escenas
positivas. Los dos negativos quedaron sin cruces.
La prueba cronometró 2.000 repeticiones por escena
positiva. Las medianas de la ruta nativa fueron
192,5–198,3 µs y el máximo observado fue 317,1 µs
por ventana de cinco frames. Las fronteras del
bloque siguen impuestas durante el intervalo
adicional y la continuación. Esta medición
excluye el receptor y el plazo de RackForge.
[Contraste y coste nativos](../evidence/rf_d_pilot_bistable_handoff05.json).

### C2 calculado durante el intervalo proyectado

El C2 de 10 µF parte del voltaje que entrega el
reloj de C4 al final del cruce. Las dos etapas
del intervalo siguiente satisfacen
'Vᵢ = V₀ + (h/C2) Σⱼ Aᵢⱼ Iⱼ', con la matriz
de Radau de dos etapas. La corriente que entra
a C2 suma las ramas de x8, x11 y x0 por
1 kΩ, 10 kΩ y 10 kΩ. En cada iteración se
vuelven a resolver Q16, Q17/Q18 y el seguidor.
El cierre admite hasta cuatro iteraciones y
acepta las tensiones de etapa con 1 pV de
residuo máximo en el balance. El banco retira
ambas entradas de C2 de ese intervalo y calcula
el residuo de carga de forma independiente.
[Red nominal y puertos](CONTORNO_VOLUMEN_CIRCUITO.md).

Pasaron las cinco reservas con los tres cruces
en sus intervalos de ocho ticks. El mayor error
de C2 en las dos etapas nuevas fue 1,777 µV.
El desequilibrio de carga máximo fue 0,418 aC.
El control con C2 impuesto reprodujo las salidas
del ensayo nativo anterior bit a bit.

En 2.000 repeticiones por escena, las medianas
fueron 200,1–217,8 µs por ventana de cinco
frames. El pico fue 2,597 ms en C2 alto.
La rama negativa, los demás puertos y el C2
posterior al intervalo proyectado conservan
las fronteras del banco. Queda acoplar el
receptor y medir J7, R59/R60 y el plazo
en RackForge.
[Contraste de C2 y coste](../evidence/rf_d_pilot_bistable_handoff06.json).

### J7 con las etapas del biestable nativo

El receptor usa las dos etapas de C2 y x27 del
reloj nativo hasta el cruce y del bloque Q25/Q15
desde el borde del evento. Conserva una sola
semilla de audio al inicio de cada ventana.
La rama negativa aporta x27 del bloque cargado
y recibe C2 de la referencia. En ambos casos
x34 se impone en las dos etapas. El receptor
resuelve R59/R60 y CR6 en su propia red. La
base del VCA que recibe el biestable todavía
se impone desde la referencia.

Pasaron las cinco reservas a 96 kHz con las
mismas entradas y salidas del banco de C4/C2.
En J7, el error máximo fue 0,320 µV. El pico
relativo entre las escenas positivas fue
0,00862 %. Los mayores errores de corriente
fueron 2,36 pA en R59 y 1,65 fA en R60.
El receptor solo tuvo medianas de 1,054–1,119 ms
en las ventanas de cinco frames y un máximo de
1,722 ms. La prueba no mide el plazo de RackForge.
[Contraste de J7 y las corrientes](../evidence/rf_d_pilot_bistable_handoff07.json).

### Retorno de la base del VCA por R59

El receptor expone x3 y la base del VCA en las
dos etapas de Radau. El banco repite la ventana
desde la misma semilla y devuelve esos voltajes
de base al bloque Q25/Q15. En positivo, el
retorno se aplica desde el borde del cruce.
El reloj de C4 sigue generando el tramo previo
y la primera etapa del intervalo del cruce.
En negativo, el retorno se aplica a las dos
etapas de cada paso. La corriente de cada
bloque se compara con el mismo signo físico,
de x3 a la base del VCA a través de 68 kΩ.

Pasaron las cinco reservas con una o dos
evaluaciones de la ventana. El mayor desacuerdo
de base fue 88,1 pV y el de corriente por R59
entre los dos bloques fue 1,30 fA. Contra el
solver, los errores máximos fueron 0,320 µV
en J7, 2,36 pA en R59 y 1,65 fA en R60.
El banco unilateral conservó sus salidas
bit a bit. Los tres cruces conservaron sus
intervalos de ocho ticks.

El contraste ejecuta las dos partes en procesos
de laboratorio y deja x34 impuesto en ambas
etapas. C2 se genera hasta el fin del intervalo
proyectado en positivo. La continuación de
C2 y la rama negativa usan las fronteras
de referencia. El coste del receptor y el
cierre por etapa en el motor quedan pendientes.
[Retorno recíproco de R59](../evidence/rf_d_pilot_bistable_handoff08.json).

### Cierre de R59 en cada paso del receptor

Las dos bases del VCA de cada candidato del
receptor alimentan al biestable dentro del
mismo paso de Radau. El biestable vuelve a
evaluar sus dos etapas desde el mismo estado
anterior. C2 y x27 vuelven al receptor, que
comprueba la solución nodal y las corrientes.
Se aceptan juntas las historias de audio y
del biestable. En positivo, el reloj previo
suministra el evento y sus etapas anteriores.

Pasaron las cinco reservas y los tres cruces
conservaron sus intervalos de ocho ticks. La
diferencia máxima entre las dos evaluaciones
de la corriente de R59 fue 1,47 aA. Contra
la referencia, los máximos de J7, R59 y R60
fueron 0,320 µV, 2,36 pA y 1,65 fA.

En 200 repeticiones por escena, las medianas
positivas fueron 1,495–1,716 ms y el máximo
fue 1,830 ms para cinco frames, sin sumar el
reloj previo de C4. Cada ventana positiva
evaluó el biestable entre 44 y 58 veces.
El ensayo usa x34, x17, x24 y x14 impuestos,
y C2 de referencia tras el intervalo
proyectado y en la rama negativa.
[Contraste y coste por paso](../evidence/rf_d_pilot_bistable_handoff10.json).
El primer ensamblado falló por un alias del
módulo de carga. El registro conserva ese
fallo de compilación.
[Compilación inicial](../evidence/rf_d_pilot_bistable_handoff09.json).

### Reuso del biestable durante la iteración del receptor

Las iteraciones preliminares usan C2 y x27 de
la primera evaluación del paso. La comprobación
nodal vuelve a resolver el biestable con ambas
bases del VCA. Si al refrescar cambian los
puertos, el receptor verifica el candidato
exacto antes de avanzar cualquiera de las dos
historias. El criterio de corriente de R59
sigue evaluándose en ambas etapas.

Pasaron las cinco reservas y se reprodujo bit
a bit el control con evaluación en cada
iteración. Entre variantes, la diferencia
máxima fue 0,066 fV en J7 y 0,210 aA en las
corrientes de salida R59/R60. En las ventanas
positivas se hicieron 14 evaluaciones del
biestable, frente a 44–58 en el control.

En 200 repeticiones alternadas por variante y
escena, la mediana positiva bajó entre 18 y
25 %. El peor tiempo de la variante fue
1,621 ms por cinco frames. La medición
excluye el reloj previo de C4 y el host.
El receptor aún excede en esas ventanas
el presupuesto de 1,333 ms de un bloque
de 128 frames.
[Contraste y tiempos alternados](../evidence/rf_d_pilot_bistable_handoff11.json).

### Perfil del receptor con el biestable reutilizado

La compilación de perfil separa el armado de
historia, biestable, retornos, defectos de
juntura y BUS, producto de la respuesta,
comprobación nodal y corrección de la interfaz.
Las cifras de plazo provienen de una compilación
sin cronómetros internos.

En 200 ventanas por escena, el producto de la
respuesta tomó entre 44,4 y 46,1 % del tiempo
instrumentado en positivo. La comprobación
nodal tomó entre 22,8 y 25,0 %. El producto se
ejecutó entre 81 y 87 veces por ventana de
cinco frames. En negativo fue también el
tramo más costoso, con 38,3–43,0 %. El control
y las cinco reservas reprodujeron sus salidas.
[Perfil por sección](../evidence/rf_d_pilot_bistable_handoff12.json).

### Producto de la respuesta en grupos de cuatro filas

El banco prepara bloques con cuatro filas
contiguas para cada columna de defectos. Cada
coeficiente de juntura o del BUS multiplica
las cuatro entradas juntas. La suma de cada
fila conserva su orden y usa los mismos
coeficientes. El armado de bloques se hace
antes de cronometrar el cierre por paso.

Pasaron las cinco reservas. Las salidas del
receptor y del biestable y los contadores de
iteración coincidieron bit a bit con el control.
En 200 repeticiones alternadas por escena, la
mediana positiva cayó 31–33 % y quedó en
0,834–0,868 ms por cinco frames. El peor p99
positivo fue 1,209 ms y el mayor pico fue
1,550 ms. El ensayo excluye el reloj previo de
C4, la preparación de la matriz y el host.
[Comparación de las dos disposiciones](../evidence/rf_d_pilot_bistable_handoff13.json).

### Semilla por extrapolación del estado aceptado

Se extrapoló la diferencia entre los dos últimos
estados aceptados a las fracciones 1/3 y 1 del
paso de Radau. La semilla sólo modifica el punto
de arranque. La historia del capacitor, el cierre
del biestable y la comprobación nodal final siguen
con sus criterios anteriores. El paso del cruce
usa la semilla habitual.

Pasaron las cinco reservas y los tres cruces
conservaron sus intervalos de ocho ticks. Se
usaron 30 semillas en las cinco ventanas, sin
reintentos. La variante dejó igual el número
total de iteraciones en cuatro casos y sumó
una en C2 alto. Las medianas positivas fueron
0,839–0,878 ms y el control fue 0,837–0,872 ms
en las mediciones alternadas. Se conserva la
variante como diagnóstico de laboratorio.
[Contraste de la semilla extrapolada](../evidence/rf_d_pilot_bistable_handoff14.json).

### Aceleración con residuos del mismo paso

Se ensayó una mezcla de las dos últimas respuestas
del mapa, después de corregir sus puertos. Si
'r' es el residuo de la respuesta actual y 'd'
es su cambio respecto al anterior, el peso es
'(r·d)/(d·d)'. Se aplica únicamente entre −1 y 1
y cuando el residuo predicho baja en norma máxima.
La comprobación nodal y las tolerancias finales
se conservan. Si el paso falla, el banco lo repite
desde la misma historia con la iteración habitual.

Las cinco reservas pasaron y los tres cruces
conservaron sus intervalos de ocho ticks. Hubo
4, 6 y 8 iteraciones menos en positivo. En negativo
se observó una iteración adicional en el ataque
y el mismo número en la liberación. No hubo
reintentos. Contra el control, J7 difirió como
máximo 25 fV y R59/R60 2,71 fA.

El coste de calcular la mezcla absorbió buena
parte del ahorro de iteraciones. Las medianas
positivas fueron 0,848–0,911 ms para cinco frames,
con una variación de −1,9 a +0,2 % frente al
control alternado. El pico de la variante fue
1,444 ms. Se conserva como variante del banco.
La comprobación nodal sigue en la ruta y queda
medir el bloque completo en RackForge.
[Contraste de la mezcla de residuos](../evidence/rf_d_pilot_bistable_handoff15.json).

### Desglose de la comprobación nodal

El perfil se repitió con el producto agrupado
del receptor. Los tiempos del residuo y del LU
son subtotales dentro de la comprobación nodal.
En las ventanas positivas de cinco frames,
armar el residuo ocupó 25,9–27,3 % del tiempo
instrumentado y resolver el LU, 6,5–6,8 %.
El residuo tomó 235–239 µs por ventana y el
LU, 59 µs. La compilación sin instrumentación
reprodujo bit a bit las cinco reservas.
[Perfil del residuo y del LU](../evidence/rf_d_pilot_bistable_handoff16.json).

### Vectores de corriente y carga para la verificación

El receptor reúne dos vectores por etapa antes
de aplicar las incidencias de R59, R60 y BUS
y combinar las cargas con Radau. El armado
preparado se comparte con la interfaz de stamp.
El banco también admite una interfaz que
devuelve únicamente corriente y carga. Ambos
caminos conservan las mismas leyes, el LU y
las tolerancias de aceptación.

Pasaron las cinco reservas con salidas bit
a bit iguales al control. El residuo positivo
del perfil anterior tomó 235–239 µs por
ventana. En la nueva compilación, el control
que devuelve el stamp tomó 127–129 µs y la
interfaz vectorial, 127–134 µs. El LU se
mantuvo cerca de 58 µs. La mejora observada
entre compilaciones se comparte entre las
dos rutas actuales.

Las medianas alternadas de ambas rutas
quedaron en 0,733–0,766 ms por cinco frames.
La salida vectorial tuvo un máximo de
1,115 ms y una diferencia de mediana
menor a 0,5 % en las cinco escenas. La
medición cubre ventanas cortas sin el reloj
previo de C4 ni el host.
[Primer contraste](../evidence/rf_d_pilot_bistable_handoff17.json).
[Perfil de las dos rutas en la misma compilación](../evidence/rf_d_pilot_bistable_handoff18.json).

### Bloque nativo de 128 frames con C4 y receptor

Se midió la reserva positiva de C2 bajo a
48 kHz. Cada repetición genera el cruce con el
reloj de C4 y ejecuta los 256 pasos internos
a 96 kHz con el biestable y el receptor.
La preparación de tablas queda fuera del
cronómetro. x34, x17, x24, x14 y el C2
posterior a la proyección provienen de la
referencia.

El solver refinado entrega 513 filas en
memoria. En la ventana corta, la selección de
filas coincidió bit a bit con la captura
completa. El receptor de cinco frames
reprodujo también la salida admitida anterior.
Los intermedios se retiraron al terminar.

En los 128 frames, el cruce quedó en el
intervalo 319224–319232. Los máximos de
error fueron 0,976 µV en J7, 0,871 pA en R59
y 2,14 fA en R60. El mayor error nodal del
biestable fue 8,09 µV. El receptor alcanzó
el límite de 16 iteraciones en al menos un
paso y completó el bloque.

En 64 repeticiones la mediana fue 26,271 ms
y el máximo 27,065 ms. Son 19,7 y 20,3
veces el presupuesto de 1,333 ms. Es la
medición nativa del banco para una reserva
positiva. Queda cerrar las fronteras e
integrar un candidato de menor coste en
RackForge.
[Bloque y contraste eléctrico](../evidence/rf_d_pilot_bistable_block01.json).

La primera repetición completó el bloque
pero su recibo se detuvo al serializar un
booleano de NumPy. El rechazo se reprodujo
con una entrada mínima. La repetición
anterior convirtió ese valor a un booleano
de JSON y conservó los límites eléctricos.
[Registro del adaptador](../evidence/rf_d_pilot_bistable_block_adapter01.json).

### Corrección nodal anticipada en el bloque completo

Se contrastó el inicio de la corrección nodal después de
1, 2, 4 y 8 iteraciones del receptor. La dirección emplea
el LU preparado del mismo circuito. Se conservan el
residuo máximo de 0,2 pA, la dirección de 2 nV y el
cierre de cargas de 0,1 nV antes de aceptar cada paso.
Cada candidato se repitió por bytes y se midió en
64 bloques alternados con el control.

Pasaron los cuatro candidatos en la reserva positiva
de C2 bajo. El mayor error de J7 siguió en 0,976 µV
y el cruce conservó el intervalo de ocho ticks.
El máximo de iteraciones bajó de 16 a 14, pero las
reevaluaciones del biestable subieron de 506 a
2124, 1862, 1354 y 628, respectivamente.

Las medianas fueron 79,136, 72,550, 59,017 y
34,136 ms. El control tomó 26,258 ms en su pase
separado. Frente a cada control alternado, los
candidatos costaron entre 1,29 y 3,01 veces más.
Se conservan como ensayos de banco. Sigue pendiente
una ruta de menor coste para el piloto jugable y
su medición en RackForge.
[Umbrales y controles alternados](../evidence/rf_d_pilot_bistable_block02.json).

### Reutilización del biestable durante la corrección anticipada

La segunda serie conserva el candidato provisional del
biestable durante las correcciones del receptor y
lo recalcula con las cargas exactas antes de aceptar
cada paso. Si cambian sus tensiones, se repite el
cierre conjunto. La comprobación nodal y sus límites
se mantienen. La opción de banco `--defer-latch`
requiere un umbral de corrección explícito.

Los cuatro umbrales pasaron de nuevo la reserva
positiva de C2 bajo, con 506 evaluaciones del
biestable por bloque. J7 conservó un error máximo
de 0,976 µV, R59 de 0,871 pA y R60 de 2,02 fA.
El error nodal máximo del biestable fue 8,09 µV.
El cruce coincidió con el mismo intervalo de ocho
ticks y los replays fueron idénticos por bytes.

Las medianas de los umbrales 1, 2, 4 y 8 fueron
58,478, 54,989, 48,302 y 32,507 ms. Cada variante
costó entre 1,23 y 2,23 veces su control alternado.
El control separado tomó 26,717 ms, con un máximo
de 27,254 ms en 64 bloques. Diferir las cargas
redujo el coste del ensayo anterior, pero anticipar
la corrección siguió siendo más lento que el
receptor admitido.

La conclusión queda limitada a esta reserva, con
x34, x17, x24, x14 y el C2 posterior a la proyección
impuestos. El banco conserva estos ensayos para
contraste. El siguiente candidato de producción
debe aprovechar el mapa de cargas del piloto
rápido, con el bloque completo como referencia de
J7, R59/R60 y evento. Su admisión requiere después
medir el motor de RackForge.
[Corrección con cierre diferido](../evidence/rf_d_pilot_bistable_block03.json).


## Cargas y coste del receptor FOH positivo

El receptor reducido de 17 estados de carga y 34 junturas
entrega ahora las tensiones de base del VCA y TAIL. Son
los valores usados por sus ecuaciones de R59/R60 en el
estado aceptado. Permiten devolver las cargas a los
contornos desde el mapa FOH. La lectura extendida reprodujo
por bits los seis canales anteriores y su replay completo.

A 96 kHz pasó el bloque positivo de 128 frames contra
Radau a 768 kHz, junto al refinamiento 384/768 kHz.
Los máximos de error de las cargas fueron 0,526 pV en
la base del VCA y 2,01 nV en TAIL, frente a 20 µV.
Las identidades de corriente de ambos puertos cerraron
con desacuerdo observado nulo. J7 tuvo 0,00787 % RMS
de error, R59 0,00774 fA y R60 2,95 pA. Las fuentes
estuvieron en 1,91 ± 0,015 V y 1,33 ± 0,010 V.

En 64 repeticiones nativas, la mediana fue 1,102 ms
y el máximo 1,216 ms. Hubo cero asignaciones. El margen
frente a 1,333 ms fue 0,118 ms en el peor bloque. El
cronómetro incluye el arranque del receptor desde DC
y 256 pasos internos. La señal y las tensiones de
contorno están impuestas. Los generadores, contornos,
FIR y RackForge requieren medición al integrarse.
[Puertos y banco de 128 frames](../evidence/rf_d_pilot_split_returns02.json).


### Dirección agrupada para las 34 junturas

La variante extiende los grupos 4/2/3 del piloto con
un grupo de ocho pares para el ladder superior.
Las dos primeras direcciones usan ese precondicionador.
Ante un fallo de factorización, y desde la tercera
iteración, se usa la dirección completa. La aceptación
conserva el residuo de las 34 leyes y todos los límites
anteriores de audio y cargas.

Pasaron el refinamiento y el contraste positivo. Los
errores máximos de las dos cargas fueron los mismos
0,526 pV y 2,01 nV del ensayo anterior. J7 quedó en
0,00787 % RMS, con los retornos dentro de 2 nA.
En 64 bloques nativos la mediana fue 1,026 ms y el
máximo 1,216 ms, con cero asignaciones. Son pases
independientes del control de dirección completa.
La medición sigue cubriendo el receptor con fuentes
impuestas y deja 0,118 ms frente al margen del banco.
[Variante de dirección](../evidence/rf_d_pilot_split_returns03.json).

El control de interfaz volvió a contrastar el piloto
nativo de 18 junturas a 192 kHz. Pasaron las escenas
de volumen, filtro y ambas entradas contra Radau y
su refinamiento. La partitura de 48.128 frames
reprodujo por bits la partición en bloques de 64/128,
con cero asignaciones. El hash de J7 f32 coincidió
con el control anterior de este perfil. La admisión
del receptor acoplado y su coste en RackForge siguen
pendientes.
[Regresión del piloto](../evidence/rf_d_pilot_returns14.json),
[control anterior](../evidence/rf_d_pilot_returns13.json).


### Transferencia desde una trayectoria cargada

El receptor positivo importa las 17 coordenadas de
capacitor desde los nodos compensados del circuito.
Reconstruye los restos de las 34 junturas, la entrada
anterior y la realimentación que usa el precondicionador.
La importación de DC reprodujo por bits la trayectoria
previa. Los cuatro controles de entrada inválida se
rechazaron con replays idénticos.

La referencia avanzó 128 frames desde DC antes de
entregar su estado. En la importación, las 17 cargas
relativas al anclaje coincidieron con las incidencias
originales, con desacuerdo observado nulo frente al
límite de 1e−20 C. La mayor carga importada fue
11,7 nC. La continuación de otros 128 frames pasó
contra Radau a 768 kHz y su refinamiento a 384 kHz.
El error RMS de J7 fue 0,0454 %, con máximo de
63,8 nV. R59 quedó en 0,0110 fA y R60 en 3,21 pA.
Las cargas de base del VCA y TAIL difirieron como
máximo 0,746 pV y 2,18 nV. Las identidades de
corriente cerraron con desacuerdo observado nulo.

El control que reinició la memoria tuvo 32,95 % RMS
de error en J7 y fue rechazado por los mismos límites.
La continuación importada difirió de la trayectoria
ininterrumpida del receptor en 0,000713 % RMS.
En 64 bloques nativos, la mediana fue 1,044 ms y el
máximo 1,172 ms, con cero asignaciones. La transferencia
se preparó antes del cronómetro. Las tres fuentes
siguen impuestas y queda medir el acople con los
contornos y el host.
[Transferencia y controles](../evidence/rf_d_pilot_receiver_handoff01.json).

El receptor agrupado anterior, compilado con su
configuración habitual, volvió a pasar. Sus coeficientes
y los ocho canales de salida reprodujeron los mismos
bytes del recibo anterior. Este pase tuvo mediana
1,035 ms y máximo 1,093 ms, con cero asignaciones.
[Regresión de la ruta previa](../evidence/rf_d_pilot_split_returns04.json).


### Transferencia de la rama negativa normalizada

La misma importación se contrastó en la rama negativa,
con el anclaje directo y la normalización de defectos
que ya usa ese receptor. La fuente de R59 permaneció
en −0,28 ± 0,005 V y la del colector de R60 en
1,45 ± 0,001 V. El snapshot se tomó después de
128 frames y se continuaron otros 128 frames.

Pasaron el refinamiento 384/768 kHz, las 17 cargas,
los puertos y los cuatro rechazos de entrada. Las
cargas tuvieron desacuerdo observado nulo frente a
1e−20 C. La importación de DC y los replays fueron
idénticos por bytes. J7 tuvo 0,000169 % RMS de error
contra Radau a 768 kHz, con máximo de 1,06 fV.
R60 difirió 40,6 fA. El mayor error de TAIL fue
27,6 pV y ambas identidades de corriente cerraron
con desacuerdo observado nulo.

El control que reinició la memoria fue rechazado,
con 107,9 % RMS de error en J7. La continuación
importada difirió de la trayectoria ininterrumpida
del receptor en 0,00310 % RMS. En 64 bloques nativos,
la mediana fue 0,768 ms y el máximo 1,566 ms, con
cero asignaciones. Ese máximo excedió el margen de
1,333 ms y deja abierto el gate temporal de esta
campaña. La prueba conserva las fuentes impuestas
y prepara la importación antes del cronómetro.
[Continuidad negativa y exceso temporal](../evidence/rf_d_pilot_receiver_handoff02.json).


### Trial y tangentes de carga del receptor rápido

La interfaz entrega un estado candidato, sus puertos y
las cuatro derivadas de base del VCA y TAIL respecto
de las fuentes R59/R60. La historia anterior se copia
y permanece fija durante el trial. El Jacobiano usa
las 34 leyes completas y sus derivadas BE/BC. El
llamador confirma el candidato después de cerrar sus
puertos vecinos.

En la rama positiva pasaron las diferencias centradas
de 10/5 µV durante los 256 pasos internos. La mayor
diferencia analítica frente a la perturbación del
propio receptor fue 1,73e−10 V/V. La primera matriz
pasó además contra el receptor nodal original con
interpolación FOH y refinamiento 384/768 kHz. El
máximo de ese contraste fue 5,58e−9 V/V, dentro del
límite de 1e−6 V/V más 0,1 % de la referencia.
Las dos derivadas directas iniciales fueron
0,909366 V/V en la base del VCA y 0,315500 V/V
en TAIL.

Los ocho canales reprodujeron por bits la ruta que
avanza sin solicitar las tangentes. Esa ruta conservó
también los mismos bytes de entrada y salida de la
transferencia positiva anterior. Los límites de J7,
R59/R60 y conservación de las 17 memorias volvieron
a pasar.

En 64 bloques, consultar la matriz en cada paso tuvo
mediana 2,987 ms y máximo 3,698 ms. Consultarla una
vez al inicio del bloque tuvo mediana 1,054 ms y
máximo 1,134 ms. Ambas mediciones tuvieron cero
asignaciones. El control de avance ordinario dio
1,077 ms de mediana y 1,240 ms de máximo en su
pase separado. Estos tiempos cubren el receptor.
La frecuencia de actualización de la tangente y
el cierre dinámico con los contornos requieren
validación conjunta.
[Trial, derivadas y coste](../evidence/rf_d_pilot_receiver_handoff03.json).


### Tangentes en la rama negativa y regresión del piloto

La rama negativa normalizada pasó las cuatro derivadas.
Las diferencias centradas del propio receptor durante
256 pasos difirieron como máximo 3,55e−10 V/V de la
matriz analítica. El contraste de la primera matriz
contra el receptor nodal original a 768 kHz tuvo un
máximo de 1,58e−6 V/V, dentro de 1e−6 V/V más
0,1 % de la referencia. Pasaron los refinamientos
de tasa y de perturbación. Las derivadas directas
iniciales fueron 1,000000 V/V en la base del VCA
y 0,842629 V/V en TAIL.

La consulta conservó los ocho canales por bits y la
ruta ordinaria reprodujo la entrada y salida de la
transferencia negativa anterior. El nuevo pase tuvo
0,782 ms de mediana y 0,919 ms de máximo en el avance
ordinario. La campaña anterior conserva su exceso
observado de 1,566 ms.

Consultar las tangentes en cada paso tuvo mediana
2,725 ms y máximo 2,959 ms. Una consulta al inicio
del bloque tuvo mediana 0,771 ms y máximo 0,976 ms.
Se observaron cero asignaciones en ambas rutas.
La frecuencia de consulta requiere validación dentro
del cierre de contornos. Estas cifras corresponden
al receptor con fuentes impuestas.
[Contraste de la rama negativa](../evidence/rf_d_pilot_receiver_handoff04.json).

La regresión del piloto de 18 junturas volvió a pasar
las tres escenas eléctricas y el refinamiento contra
Radau. La partitura completa reprodujo por bits los
bloques de 64/128 y el hash anterior de J7 f32. Hubo
cero asignaciones. Las máximas nativas fueron 0,745 ms
con controles neutros y 0,567 ms con retornos activos
a 128 frames. Este control usa el perfil de 192 kHz.
[Regresión tras el cambio de interfaz](../evidence/rf_d_pilot_returns15.json).


## R59 cerrado entre el seguidor y el receptor FOH

El candidato positivo resuelve la salida de Q3/Q2 con
la base del VCA devuelta por el receptor. Reúne R15,
R16, R24, R27 y CR6 en el mismo cierre. La historia
de las 17 memorias de audio permanece fija durante
los trials y se confirma junto con el seguidor.
C2, la base de reset a 0 V, la señal y el colector
de R60 son entradas explícitas de este banco.

La referencia une 73 incógnitas por etapa y conserva
las dos incidencias cruzadas de R59. Pasaron el
refinamiento 384/768 kHz y los 256 frames, incluidos
128 de calentamiento. Con tangente renovada por
bloque, el error RMS de J7 fue 0,0373 % y su máximo
64,2 nV. Los errores máximos fueron 0,0944 fA en
R59 y 3,29 pA en R60. Las siete tensiones de carga
y seguidor quedaron dentro de 20 µV.

Ambas políticas necesitaron como máximo dos trials
por paso. La política por bloque calculó dos tangentes
en los 256 frames y la política por paso calculó 512.
El cierre tuvo desacuerdo máximo de 70,8 pV y de
1,04 fA entre las corrientes de R59. Pasaron el
contraste entre políticas, los replays por bytes
y la partición 64/128 idéntica.

En 64 repeticiones del bloque posterior al calentamiento,
la política por bloque tuvo mediana 2,622 ms y máximo
2,843 ms. La política por paso tuvo mediana 4,427 ms
y máximo 5,324 ms. Hubo cero asignaciones. El cierre
con tangente por bloque sigue por encima de 1,333 ms.
Quedan pendientes las dinámicas propias de C2/C5,
el biestable y su integración en RackForge.
[Cierre positivo y coste](../evidence/rf_d_pilot_fast_r5902.json).

El primer intento se detuvo en compilación por una
sustitución que alteró rangos de Rust y por una conversión
de error del adaptador. Las fuentes y el rechazo quedaron
conservados. La repetición anterior corrigió ambos errores
antes del contraste eléctrico.
[Rechazo de compilación](../evidence/rf_d_pilot_fast_r5901.json).


### Continuación de junturas y rama negativa de R59

Los trials posteriores del mismo paso usan las junturas
del trial previo como semilla. La memoria física aceptada
permanece fija y se verifica de nuevo el residuo completo
de 2e−13. Un rechazo de la semilla devuelve el predictor
anterior. La semilla provisional se descarta después
del paso.

La repetición positiva pasó los mismos gates y conservó
un máximo de dos trials. La salida de R59 recorrió
1,895366–1,924634 V, dentro del dominio del mapa.
La política por bloque tuvo mediana 2,144 ms y máximo
2,516 ms. La política por paso tuvo mediana 3,936 ms
y máximo 4,244 ms. Los pases se midieron por separado
de la primera versión del cierre.
[Continuación positiva](../evidence/rf_d_pilot_fast_r5903.json).

La rama negativa normalizada pasó el refinamiento y
los dos caminos de tangente contra el circuito unido.
R59 recorrió −0,284874 a −0,275126 V, dentro de su
dominio. J7 tuvo 0,00294 % RMS de error y 22,7 fV
de máximo. R60 difirió 57,2 fA. El cierre máximo fue
95,5 pV y 1,41 fA entre ambos lados de R59. Hubo
como máximo dos trials por paso y dos tangentes en
los 256 frames con la política por bloque. Pasaron
los replays, la partición 64/128 y el contraste con
la política por paso.

En 64 bloques, la política por bloque tuvo mediana
2,027 ms y máximo 2,128 ms. La política por paso
tuvo mediana 3,840 ms y máximo 3,940 ms. Ambas
rutas tuvieron cero asignaciones. Los dos cierres
siguen excediendo 1,333 ms. C2, reset y el colector
de R60 permanecen como entradas explícitas en esta
etapa, con las dinámicas del biestable pendientes.
[Cierre negativo y coste](../evidence/rf_d_pilot_fast_r5904.json).

La voz previa de 18 junturas volvió a pasar las tres
escenas eléctricas y su refinamiento. La partitura
conservó los mismos bits al usar bloques de 64/128
y el hash de J7 f32 del control anterior. Hubo cero
asignaciones y un máximo de 0,718 ms en el pase de
retornos activos a 128 frames del perfil de 192 kHz.
[Regresión del solver compartido](../evidence/rf_d_pilot_returns16.json).


### Historia preparada y predictor del seguidor

El receptor prepara F·q y N0·defecto una vez por paso
y conserva el estado aceptado dentro de un contexto
inmutable. Los trials usan esa misma historia. El
seguidor usa su Jacobiano para predecir los cinco
voltajes ante la nueva carga y verifica después las
cinco filas originales con los límites previos.

La rama positiva pasó el circuito unido, su refinamiento,
ambas políticas de tangente y la partición 64/128.
Se mantuvieron dos trials como máximo por paso y un
desacuerdo máximo de R59 de 1,04 fA. El error RMS
de J7 fue 0,0373 %, con máximo de 64,2 nV.

En 64 bloques, la tangente por bloque tuvo mediana
1,960 ms y máximo 2,264 ms. La tangente por paso tuvo
mediana 3,781 ms y máximo 3,889 ms. Se observaron
cero asignaciones. El margen de 1,333 ms sigue abierto.
[Historia compartida y predictor](../evidence/rf_d_pilot_fast_r5905.json).


### Exponencial compartida y productos de cuatro filas

El ensayo de exponencial compartida pasó las pruebas
de cero, umbral, polarización inversa y CR6 en directa.
Reprodujo los mismos bytes del cierre positivo. Su
mediana fue 1,939 ms, cercana a los 1,960 ms del pase
anterior. Se conserva como opción explícita del banco.
[Ensayo numérico](../evidence/rf_d_pilot_fast_r5906.json).

La primera representación agrupó F, N0, N1, P y ZH
en cuatro filas. Conservó los bytes completos del
control y una relación de medianas de 0,741 en los
pares alternados. La mediana inicial fue 1,449 ms y
el máximo observado en sus tres lotes de 64 bloques
fue 2,034 ms.
[Primer producto agrupado](../evidence/rf_d_pilot_fast_r5907.json).

La segunda representación agrupó también XQ, XU y XD
para reconstruir las seis salidas. En ambas ramas,
los 256 frames y todos los diagnósticos coincidieron
por bits con el control escalar de la misma compilación.
Pasaron el contraste nodal, el refinamiento y la
partición 64/128. Se conservaron las dos tangentes
por trayectoria y dos trials máximos por paso.

En positivo, la mediana inicial fue 1,417 ms y las
medianas de los pares adicionales fueron 1,430 y
1,421 ms. La relación frente al control alternado
fue 0,730, una reducción aproximada del 27 %.
El máximo entre los tres lotes fue 1,559 ms.
[Reconstrucción agrupada positiva](../evidence/rf_d_pilot_fast_r5908.json).

En negativo, las medianas fueron 1,303, 1,306 y
1,328 ms. La relación frente al control fue 0,713,
una reducción aproximada del 29 %. El máximo fue
1,749 ms. Hubo cero asignaciones en ambas ramas.
Los picos conservan abierto el margen de 1,333 ms.
La mejora corresponde al cierre R59 con C2, reset
y el colector de R60 impuestos, sin medición del host.
El agrupado queda como candidato por defecto del banco.
[Reconstrucción agrupada negativa](../evidence/rf_d_pilot_fast_r5909.json).

La voz previa de 18 junturas pasó de nuevo las tres
escenas eléctricas, su refinamiento y la partición
por bits 64/128. El hash de J7 f32 coincidió con el
recibo anterior y se observaron cero asignaciones.
[Regresión tras preparar la historia](../evidence/rf_d_pilot_returns17.json).


### Reconstrucción del receptor al aceptar R59

El cierre provisional resuelve las 34 junturas y evalúa
la base del VCA. La reconstrucción de las 17 cargas y
las seis salidas ocurre una vez por paso aceptado.
La corriente de R59 se comprueba con los puertos
entregados por ese paso.

Las ramas positiva y negativa conservaron por bits
la trayectoria, los diagnósticos y las 17 cargas
finales frente a la reconstrucción en cada intento,
el control escalar y la partición 64/128. Coincidieron
también los hashes de trayectoria de los pases 08 y 09.
Pasaron el refinamiento de Radau, el contraste nodal y
la comparación de tangentes. El desacuerdo máximo de
R59 fue 1,04 fA en positivo y 1,40 fA en negativo.

En positivo, los dos pares alternados dieron una
reducción del 4,25 % en la mediana frente a reconstruir
en cada intento. La mediana inicial fue 1,405 ms y el
pico de los cinco lotes de 64 bloques fue 1,767 ms.
[Reconstrucción diferida positiva](../evidence/rf_d_pilot_fast_r5910.json).

En negativo, la mediana pareada bajó un 4,84 %. La
mediana inicial fue 1,278 ms y el pico de los cinco
lotes fue 1,444 ms. Ambas ramas registraron cero
asignaciones. Los picos excedieron 1,333 ms a 128
frames. La medición es nativa con C2, reset y el
colector de R60 como entradas explícitas.
[Reconstrucción diferida negativa](../evidence/rf_d_pilot_fast_r5911.json).

La voz de 18 junturas volvió a pasar las tres escenas
y conservó el hash de J7 f32. La entrega del estado
cargado y la tangente completa de R59/R60 pasaron el
contraste independiente. El mayor error de la
tangente frente a Radau fue 5,58e−9 V/V.
[Regresión de la voz](../evidence/rf_d_pilot_returns18.json).
[Estado cargado y tangentes](../evidence/rf_d_pilot_receiver_handoff05.json).


### Agrupado de la corrección impar de Newton

El candidato agrupó cuatro filas impares, con el mismo
residual inicial y el mismo orden de multiplicaciones
y restas por fila. En ambas ramas coincidieron por
bits las salidas, los diagnósticos y las 17 cargas
finales. Pasaron la partición 64/128 y el contraste
contra Radau.

La mediana pareada subió 3,02 % en positivo y bajó
0,66 % en negativo. Los picos de los cinco lotes por
rama fueron 1,759 ms y 1,750 ms, respectivamente.
El banco conserva la corrección original por defecto
y el ensayo agrupado queda reproducible con
`--packed-odd`.
[Corrección impar positiva](../evidence/rf_d_pilot_fast_r5912.json).
[Corrección impar negativa](../evidence/rf_d_pilot_fast_r5913.json).


### Perfil de las etapas del cierre R59

En los dos perfiles coincidieron por bits la trayectoria,
los diagnósticos y las 17 cargas de la compilación sin
instrumentar. Hubo 512 raíces del receptor por bloque de
128 frames a 48 kHz, dos por cada paso de 96 kHz.

La raíz consumió en promedio 0,934 ms por bloque en
positivo y 0,858 ms en negativo. Representó cerca del
64 % de la suma de las etapas en ambas ramas. Los dos
cierres del seguidor sumaron 0,412 ms y 0,382 ms,
respectivamente. La tangente del receptor, calculada
una vez por bloque, consumió menos de 0,008 ms.
La compilación instrumentada se usó para atribuir coste.
[Perfil positivo](../evidence/rf_d_pilot_fast_r5914.json).
[Perfil negativo](../evidence/rf_d_pilot_fast_r5915.json).


### Predictor del nuevo voltaje con feedback del intento previo

Con la misma historia de cargas, el reintento usa el
predictor recalculado para su nueva fuente y el
feedback no lineal que convergió en el intento previo.
Ambas ramas pasaron Radau, los límites de cierre y la
partición 64/128. La mayor diferencia de J7 entre
semillas fue 3,14e−18 V y la de las cargas finales
fue 6,04e−23 C.

En positivo, las dos semillas requirieron 94.016
evaluaciones de raíz en 64 bloques instrumentados.
La mediana pareada subió 0,76 % y el pico nativo del
candidato fue 1,704 ms entre los cinco lotes.
[Predictor en positivo](../evidence/rf_d_pilot_fast_r5916.json).

En negativo, el total bajó de 96.512 a 81.920
evaluaciones. La mediana pareada bajó 12,44 % y el
pico nativo fue 1,319 ms en los cinco lotes.
La opción `--feedback-seed` conserva el resultado
reproducible en el banco con C2 y R60 impuestos.
[Predictor en negativo](../evidence/rf_d_pilot_fast_r5917.json).


### Reúso de la evaluación en las mismas junturas

En 64 bloques, el reintento de cada rama reaprovechó
16.384 evaluaciones de defecto, pendiente y P·defecto.
El número de evaluaciones del residual se conservó.
Las salidas, los diagnósticos y las 17 cargas finales
coincidieron por bits con el control. Pasaron el
contraste de Radau y la partición 64/128.

La mediana pareada bajó 3,17 % en positivo y 5,79 %
en negativo. Un lote positivo registró 10,616 ms de
pico y el máximo negativo fue 1,814 ms. La repetición
positiva bajó la mediana pareada 5,01 % y registró un
pico de 1,696 ms. Se conservan ambos pases positivos.
[Primer pase positivo](../evidence/rf_d_pilot_fast_r5918.json).
[Pase negativo](../evidence/rf_d_pilot_fast_r5919.json).
[Repetición positiva](../evidence/rf_d_pilot_fast_r5920.json).

El predictor de feedback en negativo volvió a obtener
81.920 evaluaciones frente a 96.512 del control.
La mediana pareada bajó 11,32 % y el pico fue
1,505 ms. Así, el primer pico de 1,319 ms quedó
por debajo del margen y la repetición lo excedió.
Ambas variantes quedan disponibles como opciones
de laboratorio. Hubo cero asignaciones en los pases.
[Repetición del predictor](../evidence/rf_d_pilot_fast_r5921.json).

La voz de 18 junturas pasó de nuevo las tres escenas
y conservó el hash de J7 f32.
[Regresión de la voz](../evidence/rf_d_pilot_returns19.json).


### Eliminación del reset en el Jacobiano del seguidor

La primera prueba incluyó una semilla con cátodo de
1,2 V que agotó el presupuesto de Newton. La repetición
usó los dos puntos DC de CR6 con referencia previa.
Ambos validaron las cinco corrientes, la corrección
completa y la respuesta a R59 contra el LU de cinco
incógnitas. Los límites permanecieron en 2e−15 A
y 2e−12 V.
[Primer intento](../evidence/rf_d_pilot_fast_r5922.json).

Las trayectorias positiva y negativa y sus 17 cargas
finales coincidieron por bits con el control de cinco
incógnitas. Pasaron Radau, el refinamiento 384/768 kHz
y la partición 64/128. El solve reducido se usó en
los 49.152 cierres de cada perfil.

En positivo, la media instrumentada de los cierres
del seguidor bajó de 0,401 a 0,345 ms por bloque.
La mediana pareada del bloque nativo bajó 5,45 % y
el máximo entre los siete lotes fue 1,858 ms.
[Rama positiva](../evidence/rf_d_pilot_fast_r5923.json).

En negativo, el coste de los cierres bajó de 0,376 a
0,316 ms. La mediana pareada del bloque bajó 7,15 %
y el máximo fue 1,511 ms. Hubo cero asignaciones.
El candidato se conserva como opción de laboratorio
`--schur-follower`, con el margen de 1,333 ms
pendiente en ambas ramas.
[Rama negativa](../evidence/rf_d_pilot_fast_r5924.json).


### Semilla del seguidor desde las tangentes aceptadas

Con el cátodo a 0 V, el predictor evitó los 16.384
cierres iniciales de cada perfil después del
calentamiento. Se resolvieron los 32.768 cierres con
carga en cada rama. Hubo cero reintentos completos y
cero asignaciones. Se conservó la partición 64/128
por bits y ambas ramas pasaron Radau.

Frente al control de cierre inicial, la mayor
diferencia en J7 fue 1,01e−16 V, la mayor diferencia
de corriente R59 fue 2,45e−19 A y la mayor diferencia
de carga final fue 5,99e−21 C. R60 coincidió por bits.
La rama negativa conservó por bits las cargas finales.

En positivo, con la reducción de cuatro incógnitas y
el reúso de la ley del receptor, el predictor redujo
la mediana pareada 8,96 %. El primer lote dio una
mediana de 1,228 ms y el pico entre los nueve lotes
fue 1,649 ms.
[Predictor positivo](../evidence/rf_d_pilot_fast_r5925.json).

En negativo, con la reducción de cuatro incógnitas
y el predictor de feedback del receptor, la mediana
pareada bajó 11,28 %. El primer lote dio 1,050 ms y
el pico entre los nueve fue 1,434 ms. El margen de
1,333 ms a 128 frames sigue abierto en el banco
nativo. El cátodo variable usa el cierre inicial y
queda por contrastar con el biestable acoplado.
[Predictor negativo](../evidence/rf_d_pilot_fast_r5926.json).


### Tangente del cátodo con CR6 en directa

Las cinco componentes de la tangente del cátodo
pasaron las diferencias centradas en los dos
puntos DC de CR6. La modulación impuesta mantuvo
CR6 entre 0,3060 y 0,3090 V en directa y R59
dentro de su dominio en las dos ramas. En cada
perfil se evitaron los 16.384 cierres iniciales
después del calentamiento.

En positivo, el contraste de audio contra Radau
pasó y la mediana pareada bajó 7,77 %. La diferencia
máxima de las cargas finales frente al control fue
1,61e−20 C, por encima del límite de 1e−20 C.
El pase queda rechazado por esa diferencia.
[Reserva de carga positiva](../evidence/rf_d_pilot_fast_r5927.json).

En negativo, las cargas finales coincidieron por
bits y el contraste contra Radau pasó. La mediana
pareada bajó 7,05 % y el pico de los siete lotes
fue 1,471 ms. Ambas escenas usan un cátodo impuesto.
[Reserva de carga negativa](../evidence/rf_d_pilot_fast_r5928.json).


### Precisión del seguidor con cátodo variable

Se repitieron los mismos estímulos con una corrección
de Newton máxima de 2e−14 V para el seguidor en todos
los ejecutables. El límite de carga final siguió en
1e−20 C. Las dos ramas pasaron Radau y conservaron
la partición 64/128. El predictor evitó todos los
cierres iniciales medidos en ambos perfiles.

En positivo, la diferencia de carga final bajó de
1,61e−20 a 4,67e−22 C. La mayor diferencia en J7
frente al control fue 1,04e−17 V. La mediana pareada
bajó 10,10 % y el pico de los siete lotes fue
1,952 ms.
[Repetición positiva](../evidence/rf_d_pilot_fast_r5929.json).

En negativo, las cargas finales volvieron a coincidir
por bits. La mediana pareada subió 2,21 % en esta
repetición y se registró un pico de 11,259 ms.
Los resultados temporales corresponden al banco
nativo con un cátodo modulado externamente.
[Repetición negativa](../evidence/rf_d_pilot_fast_r5930.json).

Al combinar la tangente del cátodo con el reúso de
junturas en positivo y el predictor de feedback en
negativo, ambas ramas volvieron a pasar la reserva.
Se reprodujeron los errores máximos de carga de
4,67e−22 C y 0 C, respectivamente. En los perfiles
no hubo cierres iniciales ni reintentos completos.

Las primeras medianas nativas fueron 1,261 ms en
positivo y 1,060 ms en negativo. Frente al control
de cátodo, las medianas pareadas bajaron 10,32 %
y 12,31 %. Los picos de los nueve lotes por rama
fueron 1,850 ms y 8,136 ms. El plazo de 1,333 ms
sigue abierto. El biestable y los contornos autónomos
quedan pendientes de este banco de retornos.
[Combinación positiva](../evidence/rf_d_pilot_fast_r5931.json).
[Combinación negativa](../evidence/rf_d_pilot_fast_r5932.json).


### Cruces de polaridad de CR6 con R59 cerrado

Los cambios de signo coincidieron con Radau a
384 y 768 kHz en ambas ramas. En positivo se
registraron en los índices 184 y 367 a 96 kHz.
En negativo se registraron en 183 y 365. Los
índices se cuentan desde cero e incluyen el
calentamiento. Cada bloque medido incluyó un cruce.

La corriente de CR6 recorrió aproximadamente
−9,81 nA a 446 nA. El error máximo frente a Radau
fue 2,02 fA en positivo y 0,51 fA en negativo.
La diferencia de las 17 cargas finales frente al
control fue 4,70e−21 C en positivo y cero en
negativo. Se conservaron el dominio de R59 y la
partición 64/128 por bits.

Las medianas iniciales fueron 1,263 ms y 1,082 ms.
Los picos entre los nueve lotes de cada rama fueron
5,702 ms y 1,383 ms. El cátodo se impuso externamente
durante ambos cruces.
[Cruces positivos](../evidence/rf_d_pilot_fast_r5933.json).
[Cruces negativos](../evidence/rf_d_pilot_fast_r5934.json).


### Corriente y tangente de CR6 vistas desde Q15

El puerto devuelve la corriente que entra en la base
de Q15 por CR6 y las derivadas respecto de C2 y del
cátodo con R59 cerrado. Las dos columnas se comprobaron
en 512 ticks por rama con diferencias centradas a 10
y 5 µV desde el mismo estado previo. El error máximo
de la tangente fue 22,55 fS y el refinamiento difirió
hasta 73,02 fS, dentro del límite de 20 pS.

El ejecutable de consulta conservó por bits la
trayectoria y las cargas finales en ambas ramas.
La corriente frente a Radau difirió como máximo
2,02 fA en positivo y 0,51 fA en negativo. La
tangente respecto del cátodo fue negativa en todos
los puntos de ambas escenas.

En los pases nativos del motor, las medianas
iniciales fueron 1,269 y 1,083 ms y los picos
1,858 y 1,444 ms. La consulta de la tangente se
midió por separado del motor. Queda pendiente el
cierre dinámico de Q15 con esta corriente de retorno.
[Tangente positiva](../evidence/rf_d_pilot_fast_r5935.json).
[Tangente negativa](../evidence/rf_d_pilot_fast_r5936.json).


### Primer cierre dinámico de Q15 por CR6 y R59

El trapecio resolvió la corriente de retorno de CR6
y las cargas de Q15 desde la misma historia en cada
intento. Pasaron los límites de audio, el residual
de Q15 y la partición 64/128 en ambas ramas. El
mayor error de base frente a Radau fue 48,0 µV en
positivo y 40,9 µV en negativo. La diferencia de
carga llegó a 3,18e−16 C. Los dos pases quedaron
rechazados por el contraste temporal.

Las medianas nativas a 128 frames fueron 10,532 ms
y 9,866 ms, con cero asignaciones. El montaje
usa Q25, CR8, C2 y R60 impuestos. El primer intento
se detuvo en compilación por un alias de módulo
que quedó corregido en los dos pases medidos.
[Compilación inicial](../evidence/rf_d_pilot_fast_r5937.json).
[Trapecio positivo](../evidence/rf_d_pilot_fast_r5938.json).
[Trapecio negativo](../evidence/rf_d_pilot_fast_r5939.json).

El arranque por Euler implícito y la continuación
BDF2 redujeron el error máximo de base frente a
Radau a 1,081 µV en positivo y 0,772 µV en negativo.
Pasaron los límites de audio, los cruces y las
corrientes. El mayor error de CR6 fue 0,263 pA.

Al reconstruir los estados publicados con el stamp
completo, el mayor residual fue 2,77e−16 A y el
incremento de carga coincidió por bits en ambas
ramas. La suma de incrementos difirió de la carga
respecto del origen en menos de 1,22e−27 C.
Frente a Radau a 768 kHz, el máximo temporal de
carga fue 7,17e−18 C en positivo y 4,34e−18 C
en negativo. El límite de 2e−20 C se cumple para
la reconstrucción al mismo reloj y con la misma
historia. Los errores temporales quedan registrados
por separado.

Con tangente exacta del receptor en cada intento,
las medianas a 128 frames fueron 10,505 ms y
10,044 ms, con picos de 11,374 y 10,912 ms.
Hubo cero asignaciones y hasta cuatro intentos.
[BDF2 positivo](../evidence/rf_d_pilot_fast_r5940.json).
[BDF2 negativo](../evidence/rf_d_pilot_fast_r5941.json).

Al reutilizar la tangente del receptor, las salidas,
diagnósticos y cargas de ambas ramas coincidieron
por bits con el control de tangente exacta. Los dos
ejecutables pasaron la auditoría nodal. Las medianas
pareadas bajaron 57,07 % en positivo y 59,78 % en
negativo, a 4,496 y 3,950 ms por bloque. Los máximos
del candidato en los tres lotes fueron 4,842 y
4,365 ms, con cero asignaciones. El plazo de 1,333 ms
sigue abierto para este cierre dinámico.
[Tangente reutilizada positiva](../evidence/rf_d_pilot_fast_r5942.json).
[Tangente reutilizada negativa](../evidence/rf_d_pilot_fast_r5943.json).

El banco previo de Q15 pasó sus tres auditorías del
stamp completo tras extraer las ecuaciones de
conducción compartidas.
[Regresión de Q15](../evidence/rf_d_pilot_q15_audit03.json).


### Semilla de Q15 con la respuesta de reset

El predictor usa la tensión de reset y sus
tangentes del estado aceptado. Resuelve Euler/BDF2
con esa aproximación y verifica después el sistema
completo. Frente al arranque anterior, los cierres
de audio por bloque medido pasaron de 820 a 420 en
positivo y de 819 a 419 en negativo.

Pasaron Radau, la auditoría nodal, los cruces y la
partición por bits. Frente al control al mismo reloj,
la mayor diferencia de carga fue 1,29e−23 C en Q15
y 8,84e−24 C al final del receptor.

La mediana pareada bajó 39,20 % en positivo y
37,39 % en negativo. Los máximos de los tres lotes
fueron 3,008 y 3,714 ms, con cero asignaciones.
[Semilla positiva](../evidence/rf_d_pilot_fast_r5944.json).
[Semilla negativa](../evidence/rf_d_pilot_fast_r5945.json).


### Reúso del cierre provisional de R59 entre intentos de Q15

Con las cargas del paso fijas, la proyección del
seguidor y la raíz anterior redujeron las iteraciones
de R59 de 840 a 676 en positivo y de 838 a 675 en
negativo. El número de cierres de audio de cada
bloque se mantuvo en 420 y 419, respectivamente.

Pasaron Radau, los cruces, la auditoría del stamp
completo y la partición 64/128. La mayor diferencia
de carga con el control fue 2,53e−27 C en Q15 y
1,15e−22 C en el receptor. El mayor residual de la
auditoría fue 2,77e−16 A.

La mediana pareada bajó 21,88 % en positivo y
16,34 % en negativo. Las medianas fueron 2,185 y
2,001 ms. Los picos de los tres lotes fueron 3,094
y 2,344 ms a 128 frames, con cero asignaciones.
El cierre sigue por encima de 1,333 ms en este
banco con Q25, CR8, C2 y R60 impuestos.
[Reintentos positivos](../evidence/rf_d_pilot_fast_r5946.json).
[Reintentos negativos](../evidence/rf_d_pilot_fast_r5947.json).


### Lectura provisional de la base del VCA

Proyectar al reset una lectura FOH de la base del
VCA conservó la trayectoria, los diagnósticos y las
cargas por bits. Los cierres de audio y las
iteraciones de R59 fueron idénticos al control.
El coste de la lectura subió la mediana pareada
5,93 % en positivo y 5,32 % en negativo. El ensayo
queda como opción reproducible de laboratorio.
[Lectura positiva](../evidence/rf_d_pilot_fast_r5948.json).
[Lectura negativa](../evidence/rf_d_pilot_fast_r5949.json).


### CR6 no lineal en la semilla de Q15

La nueva semilla conservó la ley de CR6 y usó la
conductancia del resto del circuito desde el punto
aceptado. Los cierres de audio bajaron de 420 a 259
en positivo y de 419 a 258 en negativo por bloque.
Las iteraciones de R59 fueron 515 y 514.

Las dos ramas pasaron Radau, la auditoría nodal,
los cruces y la partición. La mayor diferencia
contra el control fue 1,39e−23 C en Q15 y
9,26e−23 C en las cargas finales del receptor.

Las medianas pareadas bajaron 16,73 % y 17,17 %,
a 1,959 y 1,672 ms. Se observaron máximos de
6,914 y 2,107 ms al incluir el primer lote. El
plazo sigue abierto.
[CR6 en la semilla positiva](../evidence/rf_d_pilot_fast_r5950.json).
[CR6 en la semilla negativa](../evidence/rf_d_pilot_fast_r5951.json).


### Seguidor provisional con respuesta afín del receptor

El cierre de R59 pasó de 515 a 259 iteraciones
en positivo y de 514 a 258 en negativo por bloque.
Ambas ramas pasaron Radau y la auditoría nodal.
Con 1e−10 V de tolerancia en R59, la diferencia de
carga en el receptor positivo fue 4,58e−20 C y el
pase quedó rechazado por la reserva de 1e−20 C.
En negativo la diferencia fue 3,31e−24 C y el
pase eléctrico completo quedó aprobado.

Las medianas pareadas fueron 1,666 y 1,408 ms.
Los máximos de los tres lotes fueron 2,331 y
1,529 ms, con cero asignaciones.
[Carga positiva fuera de reserva](../evidence/rf_d_pilot_fast_r5952.json).
[Semilla afín negativa](../evidence/rf_d_pilot_fast_r5953.json).

Con 2e−12 V en R59 para candidato y control, la
diferencia positiva bajó a 1,77e−20 C y siguió
fuera de la reserva. El candidato conservó una
iteración de R59 por cierre en el bloque medido.
La rama negativa volvió a pasar con 3,31e−24 C
de diferencia y un pico de 1,500 ms.
[Tolerancia de 2e−12 V positiva](../evidence/rf_d_pilot_fast_r5954.json).
[Tolerancia de 2e−12 V negativa](../evidence/rf_d_pilot_fast_r5955.json).

Con 2e−13 V, ambas ramas pasaron la reserva de
carga de 1e−20 C. Las diferencias de carga final
fueron 4,29e−21 C y 3,31e−24 C. Pasaron la
auditoría nodal, Radau, los cruces y la partición.

En positivo, las iteraciones bajaron de 515 a
448. La mediana pareada fue 1,878 ms, un 0,46 %
por encima del control, y el pico fue 2,908 ms.
En negativo bajaron de 514 a 258. La mediana
pareada fue 1,395 ms, un 15,83 % por debajo del
control, y el pico fue 1,555 ms. Hubo cero
asignaciones. El margen de 1,333 ms sigue abierto.
[Reserva final positiva](../evidence/rf_d_pilot_fast_r5956.json).
[Reserva final negativa](../evidence/rf_d_pilot_fast_r5957.json).

### Proyección de junturas en los reintentos de R59

Ambas ramas conservaron el cierre de 2e−13 V,
la auditoría nodal, los cruces de CR6 y la
partición 64/128. En positivo, la diferencia de
carga final del receptor fue 1,30e−21 C y la de
J7 fue 1,75e−17 V frente al control del mismo
reloj. Los dos mantuvieron 448 iteraciones de
R59 por bloque. La mediana pareada del candidato
fue 1,851 ms, un 2,85 % por debajo del control.
El pico entre los tres lotes fue 2,351 ms.
[Proyección positiva](../evidence/rf_d_pilot_fast_r5959.json).

En negativo, la trayectoria y las cargas finales
coincidieron por bits, con 258 iteraciones en ambos
casos. Las medianas del candidato variaron de
1,420 a 2,357 ms entre lotes y el pico fue 9,756 ms.
El pase eléctrico permite ensayar el predictor,
y la dispersión deja sin confirmar el ahorro
negativo. Ambas ramas tuvieron cero asignaciones.
[Proyección negativa](../evidence/rf_d_pilot_fast_r5960.json).

La tangente completa R59/R60 mantuvo su salida
por bits y pasó el contraste con diferencias
centradas y Radau. El mayor error frente a Radau
fue 5,58e−9 V/V.
[Regresión de tangentes](../evidence/rf_d_pilot_receiver_handoff06.json).

El primer intento se detuvo al compilar el control
por un atributo condicional en una asignación.
La corrección envolvió la asignación en un bloque.
[Intento de compilación](../evidence/rf_d_pilot_fast_r5958.json).

### Productos agrupados con Q15 dinámico

El agrupado conservó por bits la trayectoria,
los diagnósticos y las 17 cargas finales del
control escalar. Ambas ramas pasaron Radau, los
cruces de CR6, la auditoría nodal y la partición
64/128, con cero asignaciones.

En positivo se usó la proyección de junturas en
control y candidato. La mediana pareada bajó un
15,47 % a 1,890 ms y el pico de los tres lotes
fue 2,177 ms, 1,63 veces el plazo.
[Agrupado positivo](../evidence/rf_d_pilot_fast_r5961.json).

En negativo se usó el predictor de feedback en
ambos binarios. La mediana pareada bajó un
17,49 % a 1,393 ms y el pico de los tres lotes
fue 1,941 ms, 1,46 veces el plazo.
[Agrupado negativo](../evidence/rf_d_pilot_fast_r5962.json).

El plazo de 1,333 ms a 128 frames sigue abierto
en el banco nativo. Las medidas corresponden al
receptor con Q15/CR6 y R59 cerrados, con C2, R60,
Q25 y CR8 impuestos.

La corrección impar agrupada se contrastó en
positivo con los productos agrupados en ambos
binarios. Conservó por bits la trayectoria y la
carga, con cero asignaciones. La mediana pareada
subió un 1,71 % y el pico llegó a 2,975 ms. Para
el candidato positivo se conservó el agrupado
de productos con la corrección impar original.
[Corrección impar con Q15](../evidence/rf_d_pilot_fast_r5963.json).

### Perfil de la rama positiva con Q15 dinámico

El ejecutable instrumentado reprodujo por bits la
trayectoria y las cargas. En 64 bloques midió 448
raíces de receptor por bloque y una media de 1149
evaluaciones de su residual. La raíz consumió
0,818 ms por bloque. La semilla de Q15 consumió
0,402 ms y el seguidor afín, 0,174 ms. El cierre
cargado del seguidor consumió 0,116 ms y su
respuesta, 0,057 ms.

El ejecutable ordinario tuvo una mediana pareada
de 1,847 ms y un pico de 2,231 ms en los tres lotes.
[Perfil positivo](../evidence/rf_d_pilot_fast_r5964.json).

### Evaluación AVX de las junturas del receptor

El ensayo de límites conservó por bits el resto
exponencial y la pendiente. Ambas ramas conservaron
por bits la trayectoria, las 17 cargas finales y
los diagnósticos, incluidos los hashes de los
pases agrupados previos. Pasaron Radau, los cruces
de CR6 y la auditoría de carga, con cero asignaciones.

En positivo, la mediana pareada bajó 4,32 % a
1,782 ms. La raíz instrumentada consumió 0,747 ms
por bloque, frente a 0,818 ms en el perfil escalar.
El pico ordinario fue 2,984 ms.
[Evaluación AVX positiva](../evidence/rf_d_pilot_fast_r5965.json).

En negativo, la mediana pareada bajó 6,13 % a
1,333 ms y el pico ordinario fue 2,218 ms. El
plazo de 1,333 ms sigue abierto en ambas ramas.
[Evaluación AVX negativa](../evidence/rf_d_pilot_fast_r5966.json).

Tras compartir los coeficientes de Horner, la voz
de 18 junturas pasó las tres escenas eléctricas,
la partición 64/128 y la regresión del hash de J7 f32.
[Regresión de la voz](../evidence/rf_d_pilot_returns20.json).

### Capacitancia terminal en la semilla de Q15

El primer ensayo entregó la semilla con la matriz
de carga congelada. Pasó la auditoría eléctrica y
la reserva del receptor. Los cierres completos del
bloque subieron de 259 a 509 en positivo y de 258
a 507 en negativo. Las medianas pareadas subieron
11,04 % y 24,44 %, respectivamente. El aumento de
reintentos motivó recuperar la carga exacta antes
de entregar la semilla al receptor.
[Primera semilla positiva](../evidence/rf_d_pilot_fast_r5967.json).
[Primera semilla negativa](../evidence/rf_d_pilot_fast_r5968.json).

Al restaurar la ley exacta antes de usar la semilla,
ambas ramas cerraron Q15 una vez por tick, 256 veces
por bloque. Las iteraciones de R59 bajaron de 448
a 445 en positivo y de 258 a 256 en negativo.
Frente al control del mismo reloj, la diferencia
máxima de carga de Q15 fue 1,16e−23 C y 1,51e−23 C.
Las diferencias de carga final del receptor fueron
9,39e−23 C y 0 C. Ambas ramas pasaron Radau, la
auditoría nodal, los cruces de CR6 y la partición.

En positivo, la mediana pareada fue 1,714 ms,
3,49 % por debajo del control. El pico fue
1,950 ms, 1,46 veces el plazo.
[Semilla verificada positiva](../evidence/rf_d_pilot_fast_r5969.json).

En negativo, la mediana pareada fue 1,314 ms,
1,44 % por debajo del control. El pico fue
1,582 ms, 1,19 veces el plazo. Hubo cero
asignaciones en ambas ramas. El límite de
1,333 ms sigue abierto en el banco nativo.
[Semilla verificada negativa](../evidence/rf_d_pilot_fast_r5970.json).

### Historia preparada de la carga exacta de Q15

El núcleo conservó los bits en ambos sentidos de
integración, en el empalme BE/BC y con voltajes
compensados. En el banco, ambas ramas coincidieron
por bits con el control y con los hashes de la
semilla verificada previa. Pasaron Radau, la
auditoría nodal, los cruces y la partición 64/128.
La biblioteca actual también pasó los 1280
vectores de depleción y el ensayo de 10.000
compañeros de carga con cero asignaciones.

En positivo, la mediana pareada bajó 10,68 % a
1,531 ms y el pico fue 1,855 ms. El perfil midió
0,222 ms para la semilla y 0,025 ms para preparar
la historia, frente a 0,375 ms para la semilla
anterior.
[Historia preparada positiva](../evidence/rf_d_pilot_fast_r5972.json).

En negativo, la mediana pareada bajó 16,50 % a
1,111 ms. Dos lotes dieron picos de 1,280 y
1,203 ms y el tercero alcanzó 1,538 ms. Hubo cero
asignaciones en ambas ramas.
[Historia preparada negativa](../evidence/rf_d_pilot_fast_r5973.json).

El primer intento se detuvo al compilar el
oráculo por una llave de cierre sobrante. La
corrección quedó aplicada antes de los pases.
[Intento de compilación](../evidence/rf_d_pilot_fast_r5971.json).

### Reúso de la carga y la conducción al cerrar Q15

El cálculo verificado de la semilla se reutilizó
en los 256 ticks de cada bloque y la conducción
incorporó la corriente y la pendiente de CR6 del
seguidor cerrado. El armado cargado instrumentado
consumió 7,5 µs por bloque en ambas ramas.

Se conservaron por bits la trayectoria y la carga
frente al control y al pase anterior. Pasaron Radau,
la auditoría nodal y la partición 64/128. Hubo
cero asignaciones.

En positivo, la mediana pareada bajó 0,97 % a
1,497 ms. El pico de los tres lotes fue 1,728 ms.
[Reúso positivo](../evidence/rf_d_pilot_fast_r5974.json).

En negativo, la mediana pareada bajó 3,36 % a
1,063 ms. Los picos fueron 1,275, 1,177 y
1,536 ms. El plazo de 1,333 ms sigue abierto
en el banco nativo.
[Reúso negativo](../evidence/rf_d_pilot_fast_r5975.json).

La ruta de Q15 con seguidor impuesto pasó la
auditoría en polarización directa, inversa y mixta.
La diferencia máxima de corriente fue 4,34e−19 A
y la de la matriz Schur, 5,20e−18 S. La carga y la
matriz de capacitancias coincidieron por bits.
[Auditoría del puerto Q15](../evidence/rf_d_pilot_q15_audit04.json).

### Proyección lineal de la historia en los reintentos de R59

En positivo se proyectaron 189 raíces por bloque.
La diferencia máxima frente al predictor directo
fue 1,11e−16 en la coordenada adimensional de
juntura. El mayor residual directo de las raíces
proyectadas fue 1,963e−13, dentro de 2e−13.

La trayectoria y las cargas coincidieron por bits
con el control. Pasaron Radau, la auditoría nodal,
los cruces y la partición 64/128. La mediana
pareada bajó 1,70 % a 1,465 ms y el pico fue
1,675 ms. Hubo cero asignaciones.
[Proyección de historia positiva](../evidence/rf_d_pilot_fast_r5976.json).

En negativo hubo un cierre por tick y cero raíces
proyectadas. El control y el candidato coincidieron
por bits. Las medianas del candidato variaron entre
1,086 y 1,405 ms. Para esta rama se conserva el
predictor directo en los pases siguientes.
[Proyección de historia negativa](../evidence/rf_d_pilot_fast_r5977.json).

### Cambio de la base del VCA en la semilla del seguidor

En positivo, la semilla eliminó 189 reintentos de
R59. El bloque pasó de 445 a 256 raíces y de
1146 a 957 evaluaciones del residual de junturas.
La diferencia de carga final del receptor fue
5,56e−21 C frente a la reserva de 1e−20 C.
Pasaron Radau, la auditoría nodal, los cruces y la
partición. La mediana pareada bajó 9,21 % a
1,387 ms y el pico fue 2,139 ms.
[Base del VCA positiva](../evidence/rf_d_pilot_fast_r5978.json).

En negativo se mantuvieron 256 raíces por bloque
y coincidieron la salida de audio y las cargas.
La mediana pareada subió 0,51 % y el pico fue
2,552 ms. Se conserva la semilla previa en esta
rama. Ambos pases registraron cero asignaciones.
[Base del VCA negativa](../evidence/rf_d_pilot_fast_r5979.json).

### Extrapolación de la realimentación de junturas

En positivo, con la predicción de base del VCA,
se conservaron 256 raíces por bloque. Las
evaluaciones del residual bajaron de 957 a 768.
La diferencia de carga final fue 1,07e−21 C
frente a la reserva de 1e−20 C. Pasaron Radau,
la auditoría nodal, los cruces y la partición.

En la primera tanda, la mediana pareada bajó
17,00 %. El máximo de los tres lotes del
candidato fue 35,356 ms y el control llegó a
40,554 ms en los lotes pareados.
[Primer contraste positivo](../evidence/rf_d_pilot_fast_r5980.json).

En negativo, las evaluaciones bajaron de 768 a
766, con 256 raíces en ambos casos. La diferencia
de carga final fue 3,31e−24 C. Pasaron las
comprobaciones eléctricas y la mediana pareada
subió 0,92 %. Para esta rama se conserva la
semilla previa.
[Contraste negativo](../evidence/rf_d_pilot_fast_r5981.json).

La repetición positiva reprodujo la trayectoria
y los diagnósticos del primer pase por bits.
La mediana pareada bajó 14,24 % a 1,143 ms.
Los picos de los tres lotes fueron 1,315, 1,342 y
1,702 ms. Hubo cero asignaciones. El máximo
sigue sobre 1,333 ms a 128 frames.
[Repetición positiva](../evidence/rf_d_pilot_fast_r5982.json).

### Límite de correcciones de la semilla afín

Una corrección redujo el coste de la semilla
instrumentada positiva de 0,176 a 0,067 ms.
Los cierres de R59 subieron de 256 a 407 por
bloque y la mediana pareada subió 3,80 %.
La diferencia de carga final fue 1,97e−20 C,
fuera de la reserva de 1e−20 C. Se rechazó este
candidato para la rama positiva.
[Una corrección positiva](../evidence/rf_d_pilot_fast_r5983.json).

En negativo se conservaron los 256 cierres por
bloque y coincidieron las cargas finales del
receptor. Pasaron Radau, la auditoría nodal,
los cruces y la partición. La mediana pareada
bajó 5,87 % a 1,011 ms. Los tres picos nativos
quedaron por debajo de 1,333 ms, con un máximo
de 1,160 ms y cero asignaciones.
[Una corrección negativa](../evidence/rf_d_pilot_fast_r5984.json).

Dos correcciones conservaron en positivo los
256 cierres, la trayectoria por bits y la carga
final. La semilla instrumentada bajó de 0,176 a
0,130 ms. La mediana pareada bajó 3,47 % a
1,099 ms. Los picos pareados fueron 1,274 y
1,155 ms. El lote inicial alcanzó 1,724 ms.
[Dos correcciones positivas](../evidence/rf_d_pilot_fast_r5985.json).

La repetición negativa con una corrección
reprodujo la trayectoria del primer pase por
bits y redujo la mediana pareada 6,26 % a
1,011 ms. El mayor pico fue 1,575 ms. En las
dos ramas sigue abierto el plazo conjunto.
[Repetición negativa](../evidence/rf_d_pilot_fast_r5986.json).

### Reúso de la evaluación de CR6 del seguidor

En positivo, la trayectoria y las cargas
coincidieron por bits con el control de dos
correcciones. Pasaron Radau y la auditoría nodal,
con cero asignaciones. Los tres picos nativos
fueron 1,161, 1,162 y 1,309 ms. La mediana
pareada fue 1,109 ms, un 2,04 % por encima del
control. La diferencia de picos entre ejecutables
no demuestra un ahorro atribuible al reúso.
[Reúso de CR6 positivo](../evidence/rf_d_pilot_fast_r5987.json).

En negativo, la trayectoria y las cargas
coincidieron por bits con el control de una
corrección. La mediana pareada fue 1,002 ms,
un 0,02 % por encima del control. El mayor
pico de los tres lotes fue 1,160 ms. Pasaron
Radau, la auditoría nodal y la partición con
cero asignaciones.
[Reúso de CR6 negativo](../evidence/rf_d_pilot_fast_r5988.json).

La auditoría independiente de Q15 con seguidor
impuesto reprodujo los hashes de las tres
polarizaciones del pase anterior.
[Auditoría Q15](../evidence/rf_d_pilot_q15_audit05.json).

La repetición positiva conservó los bits del
primer pase. Sus máximos por lote fueron 1,283,
1,146 y 1,316 ms. La mediana pareada bajó 0,62 %
a 1,088 ms. Los dos pases positivos cumplieron
el límite nativo de 1,333 ms. El cambio de
signo entre las medianas pareadas deja abierto
el ahorro atribuible al reúso.
[Repetición de CR6 positiva](../evidence/rf_d_pilot_fast_r5989.json).

La repetición negativa también conservó los bits.
La mediana pareada fue 1,008 ms y los picos
fueron 1,148, 1,342 y 1,420 ms. Falta confirmar
el plazo en un segundo pase negativo completo.
La integración y la medición en RackForge siguen
pendientes. Los pases nativos usaron señal, C2,
R60, Q25 y CR8 impuestos.
[Repetición de CR6 negativa](../evidence/rf_d_pilot_fast_r5990.json).

### Reproducción de las escenas Q15/R59 en RackForge

Las dos escenas cargaron como componentes
nativos en un slot del motor de RackForge.
J7 f32 coincidió por bits en ambos canales y
en todos los reinicios, sin fallos de slot.
Las entradas, el mapa y la trayectoria nativa
reprodujeron los hashes admitidos.

En positivo, las medianas calientes del host
fueron 1,088 y 1,075 ms. El peor arranque fue
1,521 ms y el peor bloque caliente, 1,571 ms.
Tres bloques calientes excedieron 1,333 ms.
[RackForge positivo](../evidence/rf_d_pilot_fast_r5992.json).

En negativo, las medianas calientes del host
fueron 0,996 y 0,998 ms. El peor arranque fue
1,713 ms y el peor bloque caliente, 1,782 ms.
Once bloques calientes excedieron 1,333 ms.
[RackForge negativo](../evidence/rf_d_pilot_fast_r5993.json).

El primer intento se detuvo al compilar el
probador del host. Se corrigieron el tipo de
frames y la referencia a la telemetría.
[Intento de compilación](../evidence/rf_d_pilot_fast_r5991.json).

### Contraste del nativo, la ABI y el slot

Se usó el mismo DLL en la ABI directa y en el
slot, con la misma salida J7 por bits en ambas
rutas y en todos los reinicios. No hubo fallos
de slot ni pérdidas del plazo completo de 2,667 ms.

En positivo, los dos lotes calientes de RackForge
cumplieron el margen de 1,333 ms. El mayor pico
caliente fue 1,178 ms y el de arranque, 1,390 ms.
En los lotes alternados, el nativo llegó a
1,586 ms y la ABI directa a 1,428 ms en caliente.
El slot añadió 6,85 y 28,45 µs a la mediana
caliente de la ABI directa.
[Contraste positivo de las tres rutas](../evidence/rf_d_pilot_fast_r5994.json).

En negativo, el peor bloque caliente del slot
fue 1,511 ms, con un bloque sobre el margen. La
ABI directa llegó a 1,521 ms. Las diferencias
de mediana entre slot y ABI directa fueron
19,95 y −6,95 µs. Las medidas corresponden al
motor con las entradas impuestas del recibo.
Queda pendiente el ensayo de la salida física.
[Contraste negativo de las tres rutas](../evidence/rf_d_pilot_fast_r5995.json).

### Escenas continuas de Q15/R59

Cada rama completó 16.384 frames continuos, con
las entradas reflejadas y la historia acumulada.
Los dos primeros bloques conservaron los bits
del recibo original. J7 y los 19 valores de
estado final comprobados coincidieron al
particionar el nativo en 64 o 128 frames.
El slot reprodujo todo J7 por bits, sin
fallos de slot ni pérdidas del plazo de
2,667 ms. Los picos de telemetría en el motor
fueron 1,643 ms en positivo y 1,135 ms en
negativo.
[Escena continua positiva](../evidence/rf_d_pilot_fast_r5996.json).
[Escena continua negativa](../evidence/rf_d_pilot_fast_r5997.json).

### Callback físico de la escena continua

El primer intento enumeró el par genérico
HD Audio y se detuvo antes de abrir un stream.
El perfil temporal del banco recuperó el par
NVIDIA y se retiró al terminar. Se verificó el
estado previo de los demás perfiles.
[Consulta inicial](../evidence/rf_d_pilot_fast_r5998.json).

En positivo, el control y ambos pases confirmaron
128 frames efectivos a 48 kHz y la salida NVIDIA.
El driver recibió silencio durante la medida.
El control llegó a 0,038 ms y registró un aviso
de reset. Los dos pases de 4.800 bloques tuvieron
medianas de 1,079 y 1,078 ms y picos de 1,704 y
3,895 ms. Hubo 22 y 68 bloques sobre 1,333 ms.
El segundo pase perdió seis plazos completos.
Ambos tuvieron cero asignaciones y fallos de slot.

Ningún ordinal superó el margen en ambos pases.
El peor bloque del segundo pase tomó 3,892 ms
dentro del render y 1,086 ms de pared en el
mismo ordinal del primer pase.
[Pases físicos positivos](../evidence/rf_d_pilot_fast_r5999.json).

En negativo, el control y ambos pases también
confirmaron la salida NVIDIA y 128 frames
efectivos. El control llegó a 0,037 ms y registró
un aviso de reset. Los pases tuvieron medianas
de 1,008 y 1,000 ms y picos de 1,494 y 1,556 ms,
con 5 y 20 bloques sobre el margen. Registraron
cero plazos perdidos, asignaciones y fallos de
slot. Los ordinales sobre margen fueron distintos
entre los dos pases. La selección temporal del
endpoint se restauró en ambas ramas.
[Pases físicos negativos](../evidence/rf_d_pilot_fast_r59100.json).
