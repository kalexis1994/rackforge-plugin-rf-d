# Retornos explícitos del piloto de RF-D

Usar el piloto de 192 kHz como control. Abrir la
tensión de contorno que alimenta R59 de 68 kΩ y
la del pin 16 que entra a la base de Q26 por 47 kΩ.
Conservar R60 de 680 Ω entre TAIL y Q28, y C18
dentro del mapa dinámico del piloto. Leer las
corrientes con signo del contorno hacia Q18 por R59
y desde TAIL hacia Q28 por R60. Mantener C27, las
18 coordenadas de carga, las 12 leyes exponenciales
y el FIR de J7. Usar FOH en las tres entradas.
[Piloto](VOZ_REDUCIDA_PILOTO_PROTOCOLO.md),
[retornos de la voz de referencia](CONTORNOS_CADENA_PROTOCOLO.md)

El primer alcance es el punto nominal del piloto.
Admitir excursiones locales de ±15 mV respecto de
2 V en el retorno de volumen y ±1 mV respecto de
0 V en el pin 16. El audio mantiene ±80 mV. Estas
excursiones delimitan el banco, con tarjetas
nominales de laboratorio. Los contornos todavía
reciben sus tensiones de fuentes explícitas en
esta etapa. Validar el cierre de sus estados y la
conmutación del biestable como etapa separada.

Contrastar cada entrada por separado y juntas con
Radau no lineal de 68 nodos, a 384 y 768 kHz,
desde el mismo DC y con los mismos estímulos.
Conservar los límites del piloto en BUS, C27, J7
y panel, y aplicar 2 nA a cada retorno. Verificar
acuerdo con el piloto previo cuando los dos
controles son cero y partición 128/64 por bits.

Medir bloques completos de 128 muestras a
48 kHz, incluyendo sierra, control, plant y FIR.
Aplicar 1,333333… ms a cada bloque observado.
Separar el banco nativo, el motor de RackForge
y el callback físico.

El contraste inicial de R59 excedió el límite RMS
de J7 con las 12 leyes del piloto. Mantener también
los restos BE y BC de Q18 y el par de señal del
primer VCA, usando sus incidencias del stamp
circuit66 y la tarjeta nominal de 298,15 K,
Is de 10 fA, beta directa 100 e inversa 5.
No variar los estímulos ni los límites.
[Primer VCA](CASCADA_HASTA_SALIDA_DC.md)

## Paso por RackForge

Cargar el mismo piloto como paquete nativo
temporal en un slot a 48 kHz y 128 frames.
Comparar el control de dos entradas cero con
dos pases de la escena piloto con ambas
entradas activas. Son 376 bloques por pase.
Exigir identidad f32 con el banco nativo, sin
fallos del slot ni plazos perdidos, y máximo de
1,333333… ms. Usar un banco físico separado
para comprobar el periodo efectivo y la
variabilidad del callback.

## Rango alrededor del cruce positivo

Probar con el mismo mapa excursiones de ±120 mV
en R59 y ±12 mV en el pin 16, conservando los
límites de error de la primera etapa. La nueva
banda en R59 abarca las tensiones observadas en
torno al cruce positivo. El contraste conserva
la polarización de 2 V y separa esta banda
local de las excursiones completas del contorno.
Registrar el rango de corrientes y medir el
coste sobre una escena larga con ambos puertos
cerca de los nuevos límites.

El primer intento amplio conservó las corrientes
de retorno dentro del límite y excedió el error
RMS de J7 cuando sólo se excitó el filtro.
Mantener también BE/BC de Q26 PNP y Q28 NPN
en el mapa amplio, con las tarjetas nominales de
cutoff. Mantener C18 y los mismos límites.

Con Q26/Q28, las corrientes pasaron de nuevo y
el filtro aislado conservó un error RMS fuera
del límite a ±12 mV. Repetir el ensayo con una
banda de ±3 mV, sin mover el límite de 0,3 %.
Conservar ±120 mV en R59 y el mismo mapa con
22 leyes. Medir la banda resultante con la
misma campaña física a 128 frames efectivos.

Comparar la banda de ±3 mV con el mapa de
18 leyes y la tangente local de Q26/Q28. R60
y C18 conservan sus incidencias. Esta variante
debe repetir los tres estímulos, los límites
de corriente y J7, y la campaña de RackForge.


## Cargas del receptor positivo reducido

El receptor FOH de 17 cargas y 34 junturas devuelve la
base del VCA y TAIL junto a las corrientes R59/R60.
Se usan las mismas reconstrucciones nodales que generan
esas corrientes al aceptar el estado del receptor.
Contrastar ambas tensiones a reloj común contra Radau
a 768 kHz, con límite absoluto de 20 µV. El refinamiento
384/768 kHz debe pasar los límites de audio y retornos
previos. Exigir identidad de los seis canales anteriores
al leer también las dos cargas y repetir los bytes.

Comprobar el signo de ambos puertos mediante las identidades
I59 = (Vfuente59 − Vbase) / 68 kΩ e
I60 = (Vtail − Vfuente60) / 680 Ω, con desacuerdo máximo
de 2 pA. Las fuentes recorren 1,91 ± 0,015 V y
1,33 ± 0,010 V, junto al estímulo de BUS ya definido.

Medir 64 repeticiones del receptor a 96 kHz, cada una
con 256 pasos internos que corresponden a 128 frames
de host a 48 kHz. Incluir el arranque desde DC y
consumir todas las salidas. Contar las asignaciones
dentro del intervalo medido. Registrar mediana, p99
y máximo frente al margen de 1,333333… ms. Esta
medición cubre el receptor con señal y tensiones de
contorno impuestas. La integración incluye después
el coste de los generadores, contornos, FIR y host.


El ensayo `--receiver-only --block-roots` divide la dirección
inicial del receptor de 34 junturas en grupos de 4/2/3/8
pares BE/BC. Conserva el orden de las leyes del piloto y
añade las ocho junturas BE del ladder superior al final.
Durante las dos primeras iteraciones usa estos grupos
como precondicionador. Un fallo de factorización devuelve
la dirección completa y desde la tercera iteración se
usa la dirección completa. Cada aceptación exige el
residuo de las 34 leyes con el mismo límite de 2e−13.
Los límites de puertos, J7 y temporales anteriores se
aplican también a este ensayo.


## Continuidad desde un estado eléctrico cargado

La transferencia del receptor positivo usa un estado del
circuito de 68 nodos con sus partes alta y baja, el valor
de señal y las dos tensiones de fuente del instante anterior.
El mapa conserva las 17 coordenadas de capacitor retenidas,
incluida C27. Calcula q = A·δV y los restos exponenciales
desde E·δV con las mismas incidencias y tarjetas del
receptor. Guarda también la entrada previa y reconstruye
la realimentación del precondicionador. Las referencias
de tensión se restan antes de sumar las partes alta y baja.
Las coordenadas q están en voltios y C·q expresa la carga
en coulombs relativa al anclaje. El mapa y el snapshot
comparten topología, unidades y punto de operación.

Arrancar la referencia desde el reposo positivo admitido,
avanzar 128 frames con las fuentes existentes e importar
su estado final. Continuar otros 128 frames a 96 kHz.
Contrastar cada carga conservada con un máximo de 1e−20 C,
y J7, R59/R60 y los voltajes de carga con los límites
anteriores. La referencia usa Radau a 384/768 kHz y
el refinamiento debe pasar en el tramo continuado.
Exigir replay idéntico, importación de DC idéntica por
bits a la ruta previa y contraste con la trayectoria
ininterrumpida del receptor. Un control que reinicia
la memoria debe exceder los límites del mismo tramo.

Rechazar nodos o señal no finitos, fuentes fuera del
dominio y junturas fuera del dominio exponencial.
Medir 64 continuaciones del receptor desde el estado
importado, con cero asignaciones y el mismo margen
de 1,333333… ms. La transferencia inicial se prepara
antes del intervalo cronometrado. Las fuentes de señal
y contorno siguen impuestas en este contraste.


El mismo contraste se aplica a la rama negativa con
fuentes −0,28 ± 0,005 V y 1,45 ± 0,001 V. El anclaje
usa el estado negativo de la referencia admitida y el
procedimiento directo ya contrastado. La proyección
normaliza cada defecto por su corriente de polarización,
conservando las mismas incidencias y 34 junturas. La
importación reconstruye el resto adimensional que usa
ese mapa y todas las 17 memorias retenidas. Se aplican
los mismos límites de carga, audio, retornos y tiempo,
incluido el control que detecta un reinicio de memoria.
