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
