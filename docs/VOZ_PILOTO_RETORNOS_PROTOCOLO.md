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


## Tangentes de carga del receptor FOH

El trial copia el estado anterior y entrega un candidato,
los puertos y la matriz de derivadas de base del VCA y
TAIL respecto de las dos tensiones de fuente R59/R60.
La historia q, la entrada anterior y los defectos anteriores
se mantienen fijos durante la diferenciación. El llamador
puede confirmar el candidato después de cerrar sus vecinos.

Para z = ZH·base + ZU·u − P·n(z), se factoriza
J = I + P·diag(dn/dz), con las 34 leyes BE/BC completas.
Cada columna resuelve J·dz/du = ZH·U1 + ZU. La derivada
nodal es XQ·U1 + XU − XD·diag(dn/dz)·dz/du. Las dos
filas de salida corresponden a base del VCA y TAIL.
La entrada u está en voltios y la matriz se expresa en V/V.

Contrastar las cuatro entradas de la matriz durante
256 pasos internos desde un estado importado. Usar
perturbaciones centradas de 10 y 5 µV, copiando la
misma historia para ambos signos y cada fuente. Exigir
el mismo audio y cargas por bits al solicitar la tangente.
La primera matriz se compara además con el receptor
nodal original a 384/768 kHz. En ese contraste se interpola
la entrada dentro del intervalo FOH y se usa el mismo
snapshot inicial. El límite para cada derivada es
1e−6 V/V + 0,001·abs(derivada de referencia), tanto
para el contraste como para los refinamientos de paso
y perturbación. Los límites de audio y corriente previos
se conservan.

Medir aparte 64 bloques con consulta en cada paso y
64 bloques con una consulta al inicio del bloque.
Contar asignaciones y conservar los picos frente a
1,333333… ms. Estas mediciones observan el coste de
la interfaz. El cierre dinámico con los contornos debe
validar la frecuencia de actualización de la tangente.


## Cierre de R59 con el seguidor de volumen

El candidato une Q3/Q2, R15/R16/R24/R27 y CR6 al
receptor FOH por R59 de 68 kΩ. La fuente ideal en
el extremo de R59 se sustituye por la salida calculada
del seguidor. Se mantienen como entradas explícitas
la señal, C2, la base de reset y el colector de R60.
La base de reset se fija a 0 V como condición de este
banco. La alimentación del seguidor es 9,3 V según
el stamp nominal de board 2. El valor inicial de C2
se obtiene resolviendo el mismo circuito para reproducir
el punto de operación previo del receptor. Ese cálculo
prepara una condición del banco con las tarjetas nominales.

Cada trial del receptor parte de la misma historia
aceptada. Se cierra F = Vsalida_seguidor − Vfuente59
con dirección dV = F / (1 − dVsalida/dVbase · dVbase/dVfuente).
La tangente del audio se calcula en el primer paso del
bloque de 128 frames y se renueva si el residuo deja
de reducirse al menos a la mitad. El control calcula
una tangente nueva en cada paso. En ambos caminos se
acepta únicamente un desacuerdo de fuente de 1e−10 V
y de corriente R59 de 2 pA. El estado de audio y el
seguidor se publican juntos después de ese cierre.
El límite es ocho trials por paso.

La referencia une las 68 incógnitas de audio y cinco
del seguidor en las dos etapas de Radau. Reutiliza el
stamp nodal original y la linealización independiente
de loudness_follower. Los dos terminales de R59
aportan −1/68 kΩ en las columnas cruzadas. Comparar
384/768 kHz, J7 con los límites previos, ambos retornos
a 2 nA y las siete tensiones de carga/seguidor a 20 µV.
La entrada C2 recorre la misma excursión que usaba la
fuente anterior de volumen. Registrar la excursión
real obtenida en la salida del seguidor.

Ejecutar 128 frames de calentamiento y contrastar
los 256 frames completos. Exigir replay por bytes,
partición 64/128 idéntica y acuerdo entre las tangentes
renovadas por bloque y por paso. Medir 64 repeticiones
del bloque posterior al calentamiento, incluyendo el
seguidor, todos los trials y las renovaciones de tangente,
con cero asignaciones y margen de 1,333333… ms. Quedan
pendientes las dinámicas propias de C2, C5 y el biestable.


En la continuación de trials del mismo paso, el receptor
puede arrancar desde las junturas de su trial anterior.
La nueva fuente se evalúa contra la misma historia q y
los mismos defectos aceptados del instante previo.
Cada trial verifica de nuevo el residuo de las leyes
completas con 2e−13. Si falla la semilla provisional,
se vuelve al predictor de la historia aceptada. La
semilla se descarta al terminar el paso y conserva
su función exclusivamente numérica. Contrastar otra
vez el circuito unido, la partición y el coste.


Preparar una sola vez por paso F·q_anterior y
N0·defecto_anterior del receptor. El objeto preparado
conserva también el estado anterior y sólo ofrece trials
que parten de esa misma historia. Cada nuevo extremo
de fuente se añade con el orden de operaciones previo.
El candidato se entrega después de resolver su raíz.

La factorización del seguidor calcula además el vector
dVnodo/dVbase resolviendo J·dV = e_salida/68 kΩ.
Ese vector predice los cinco voltajes cuando el trial
de audio entrega una nueva carga. La predicción se usa
sólo como semilla. Se comprueban de nuevo las cinco
filas no lineales, con 2e−15 A y 2e−12 V como antes.
Mantener los límites de cierre y el contraste nodal
unido en ambas ramas al medir el coste de estos reusos.


El ensayo opcional de exponencial compartida evalúa e^z
una vez para corriente y derivada en cada juntura del
seguidor. Para abs(z) ≥ 1/8 obtiene e^z−1 restando uno.
Dentro de esa banda conserva expm1(z) para evitar la
cancelación cerca de cero. La derivada usa siempre e^z,
incluida la polarización inversa. Se conservan tarjetas,
incidencias, temperatura y límites de solución.

La prueba numérica compara e^z−1 con expm1 en cero,
ambos lados del umbral y polarización inversa profunda.
Exige error relativo máximo de 16 épsilon de f64 y
los mismos bits de e^z para la pendiente. Se ejecuta
también el contraste existente de CR6 en directa y
la tangente de R59. El circuito unido debe pasar de
nuevo con los mismos gates antes de admitir el ensayo.


El producto agrupado del receptor conserva cuatro
filas por grupo y avanza sus columnas en el mismo
orden que el producto escalar. Rellena únicamente
los carriles fuera de las 17 cargas o 34 junturas,
y descarta esos carriles al devolver el resultado.
Cada acumulador arranca con el mismo cero negativo
del sumatorio previo. F, N0, N1, P y ZH conservan
sus coeficientes. La representación se prepara en
compilación y el audio usa arrays de tamaño fijo.

Compilar el control escalar y el candidato con los
mismos flags restantes y el mismo payload. Exigir
identidad completa por bytes, incluidos los diagnósticos
de cierre, además de los gates nodales anteriores.
Medir dos pares adicionales de 64 bloques, alternando
el orden de las variantes, y conservar todos los picos
al evaluar el margen de 1,333333… ms.


La misma representación puede reconstruir las seis
salidas con XQ, XU y XD. Calcular por separado los
productos de carga, fuente y defecto. Conservar después
el orden DC + carga + fuente − defecto del camino
escalar. Incluir esas seis salidas en la comprobación
por bytes y en el contraste de puertos del mismo banco.


Después del contraste de ambas ramas, el banco R59
selecciona el agrupado por defecto. Conserva
--no-packed-products para ejecutar sólo el camino
escalar. La opción de exponencial compartida sigue
siendo explícita e independiente.

Cada intento de R59 resuelve el mismo residual de las
34 junturas del receptor con tolerancia de 2e−13 V.
Para cerrar el seguidor evalúa la base del VCA con la
fila 3 de DC + XQ·q + XU·u − XD·defecto. Al aceptar
el cierre aplica N1 a los defectos, reconstruye las
17 cargas y las seis salidas, y comprueba la corriente
de R59 con los puertos que entrega el paso.

Con `--compare-eager`, compilar el control que reconstruye
el estado completo en cada intento con los demás flags
idénticos. Comparar los bits de todas las salidas,
diagnósticos y 17 cargas finales. Aplicar la misma
comparación al control escalar y a la partición en
bloques de 64. Alternar el orden de cada pareja de
mediciones y evaluar el margen con todos los picos.

Con `--packed-odd`, aplicar la corrección impar de Newton
en grupos de cuatro filas independientes, como en el
motor WASM de recuperación. Para cada fila, restar desde
el residual los mismos productos P·pendiente·dirección
par, en el mismo orden y con dos multiplicaciones.
Conservar los pivotes pares, los límites del residual
y el fallback. Comparar ambas ramas con el control de
corrección impar original y las mismas matrices agrupadas,
con identidad de trayectoria, diagnósticos y cargas finales.

Con `--profile`, compilar una variante instrumentada aparte
con las mismas ecuaciones y el mismo estímulo. Atribuir el
coste del bloque al cierre inicial del seguidor, la historia
del receptor, su raíz, el cierre con carga, las dos tangentes
y la reconstrucción. Contar llamadas y nanosegundos por
etapa en 64 bloques después del calentamiento. Exigir los
mismos bits de trayectoria y cargas finales. El límite de
1,333 ms se aplica a la compilación sin instrumentación.

Con `--feedback-seed`, cada reintento usa como semilla
el predictor del nuevo voltaje de R59 menos P·defecto
del intento anterior. El residuo, los límites y el
predictor de respaldo se conservan. Comparar contra el
arranque anterior en las mismas ramas, con el contraste
de puertos y 1e−20 C de diferencia máxima en las cargas
finales, igual que el banco de entrega del receptor.
Contar además las evaluaciones de las raíces que llegan
a converger, tanto en el candidato como en su control.

Con `--reuse-law`, el reintento arranca en las mismas
junturas del intento previo y toma sus defectos,
pendientes y P·defecto ya evaluados. Recalcula el
predictor y todo el residual con la fuente nueva. Las
iteraciones posteriores vuelven a evaluar las leyes.
El respaldo sigue usando el predictor del último
estado aceptado. Exigir identidad por bits frente
al control que repite la evaluación y contar cuántas
evaluaciones se reutilizan en las raíces convergidas.

Con `--schur-follower`, eliminar la incógnita del reset
en cada paso de Newton del seguidor. En el Jacobiano,
la fila y columna del reset sólo acoplan con loudness
por −g24 = −1/R24. Para su diagonal s y residual r4,
restar g24²/s de la diagonal de loudness y sumar
g24·r4/s a su lado derecho. Reconstruir la corrección
del reset como (r4 + g24·d_loudness)/s. Usar el mismo
factor para la respuesta a R59 y conservar R15, Q3,
Q2 y la ley de CR6 con sus pendientes.

Comprobar las cinco corrientes originales con 2e−15 A
y las cinco correcciones con 2e−12 V. Ante fallo del
solve reducido, repetir con las cinco incógnitas desde
la semilla de entrada. Probar las reservas DC de CR6
y la respuesta a R59 contra el Jacobiano completo.
Contrastar los puertos con Radau en ambas ramas y
las cargas finales con el control de cinco incógnitas
con 1e−20 C de diferencia máxima. Medir a 128 frames
con la misma semilla del receptor en cada pareja.

Con `--predict-follower`, conservar del último cierre
aceptado las respuestas a C2 por R16 y a la base del
VCA por R59. Si el cátodo del reset sigue fijo,
avanzar la semilla del seguidor por ΔC2 antes de
resolver la primera raíz de audio. Usar la respuesta
a R59 del mismo punto para sembrar el seguidor cargado.
Las cinco corrientes y correcciones se comprueban al
resolver con la carga de cada intento de audio.

Sin semilla, con cambio de cátodo o ante un rechazo
del paso, usar el cierre inicial completo desde el
último estado aceptado. Medir cuántos cierres
iniciales se ejecutan, los reintentos completos
y el coste de renovar las dos respuestas. Contrastar
J7, ambos retornos y las cargas finales con el
control de cierre inicial y con Radau.

Con `--predict-cathode`, añadir la respuesta al
cátodo del último cierre aceptado. La derivada
de la fila de reset respecto del cátodo es −g_CR6.
Resolver J·dV = e_reset·g_CR6 con el mismo factor
del seguidor y sumar dV·Δcátodo a la semilla.
La corriente y la pendiente de CR6 usan la misma
ley y la misma temperatura. Contrastar las cinco
componentes de la tangente por diferencia centrada
en los dos puntos DC en directa ya admitidos.

Con `--vary-cathode`, centrar el cátodo 0,45 V por
debajo del divisor R24/R27 sin corriente de CR6.
Volver a equilibrar C2 en la referencia conjunta y
modular el cátodo a 263 Hz con amplitud de un cuarto
del semirango de R59. Reducir a la mitad la excursión
de C2 para reservar margen en ese puerto. Exigir CR6
en directa, el dominio de R59 y los mismos límites
de Radau en ambas ramas. Comparar contra el predictor
de C2/R59 que vuelve al cierre inicial cuando cambia
el cátodo. El estímulo sigue siendo una entrada del banco.

Con `--tight-follower`, exigir una corrección máxima
de 2e−14 V en el seguidor tanto para el candidato
como para todos sus controles. Se conservan el
residual de 2e−15 A, el cierre de R59 y el límite de
1e−20 C entre cargas finales. Repetir la misma
modulación tras el rechazo de la reserva positiva
para medir la sensibilidad al criterio de convergencia.

Con `--cross-cathode`, centrar el cátodo en el
divisor R24/R27 a corriente nula de CR6. Aplicar
una senoide de 263 Hz y 0,15 V de amplitud con
la misma excursión reducida de C2. Resolver el
equilibrio inicial de C2 en Radau. Este estímulo
reserva el cambio de polaridad local alrededor
del cero de CR6.

En cada rama exigir al menos dos cambios de signo
de la tensión de CR6 y uno durante el bloque medido.
Comparar los índices de cruce a 96 kHz del candidato,
los controles y las referencias 384/768 kHz. Obtener
la corriente de CR6 de la tensión de cada trayectoria
con la ley de germanio del seguidor y exigir el
límite de retornos de 2 nA. Conservar el dominio
de R59, la reserva de carga final de 1e−20 C y los
demás límites del banco.

Con `--reset-port`, exportar la corriente que entra
en Q15 por CR6 y sus dos derivadas respecto de C2
y la base de Q15. Mantener fija la historia de audio,
la señal y la fuente de R60 al diferenciar.
Sea a la tangente de la base del VCA respecto de
la fuente R59 en el receptor, s_b la respuesta de
loudness a la base del VCA y s_p su respuesta al
puerto p. Con R59 cerrado, la respuesta de la base
del VCA al puerto es a·s_p/(1−a·s_b). Sumar ese
efecto a la derivada de la tensión de reset y aplicar
g_CR6·(dV_reset/dp−1) para el cátodo. Para C2 el
término directo del cátodo vale cero.

Contrastar ambas columnas en todos los ticks con
diferencias centradas de 10 y 5 µV desde el mismo
estado previo. Exigir 20 pS de error y refinamiento,
2 nA de error de corriente contra Radau y coincidencia
por bits de la trayectoria y las cargas del banco.
La consulta de la tangente usa un ejecutable aparte.

Con `--dynamic-q15`, resolver en cada paso de 96 kHz
la base y el colector de Q15 junto con el puerto
CR6/R59. Para cada intento, usar la base provisional
como cátodo y resolver R59 desde la misma historia
de audio. Restar la corriente de CR6 de la fila de
base y su tangente del Jacobiano. Conservar las
leyes y las cargas BE/BC del banco Q15 anterior.

El primer ensayo usó trapecio con el residual
I_n + I_anterior + 2·ΔQ/h. Para reducir el error
de arranque, usar Euler implícito en el primer
paso y BDF2 a reloj fijo a partir del segundo.
El residual es I_n + (3·ΔQ_n−ΔQ_anterior)/(2h).
Conservar el historial aceptado al probar cada
punto y comprobar 2e−15 A y 2e−12 V antes de
publicar ambos estados.
El equilibrio inicial usa el divisor R24/R27 sin
corriente de CR6. Ajustar la fuente impuesta de
R56 para ese equilibrio. Modularla 0,15 V a 263 Hz
para ejercer ambos sentidos de CR6. Q25 y CR8
son fronteras de laboratorio alrededor de ese punto.

Comparar contra Radau conjunto de 75 nodos por
etapa a 384 y 768 kHz con el stamp completo de la
placa y las mismas leyes de carga. Exigir los
límites de audio y de 20 µV y 2 nA para los puertos.
Registrar el error temporal de carga y su contraste
con 2e−20 C del primer ensayo. Aplicar la reserva
de 2e−20 C al balance discreto con la misma historia
y el mismo integrador, como en el banco Q15 previo.
Rearmar las cinco filas del seguidor y las dos de
Q15 desde cada punto publicado con el stamp completo.
Reconstruir ΔQ y el residual de Euler/BDF2 a partir
de los voltajes aceptados y exigir 2e−15 A en las
siete filas. Verificar también los índices de cruce,
el dominio de R59, la suma de incrementos de carga
y la partición 64/128 por bits. Medir el
coste y las asignaciones a 128 frames después del
calentamiento. C2 y el colector de R60 se imponen.

Con `--cached-q15-gain`, usar en la dirección de
Newton de Q15 la tangente del receptor que ya
mantiene el cierre R59. Recalcular la corriente
de CR6 y el residual completo en todos los intentos.
Comparar al mismo reloj contra la tangente exacta
en cada intento. Exigir la auditoría nodal de
ambos, los mismos cruces y diferencias máximas
de 2e−20 C en Q15 y 1e−20 C en las cargas finales
del receptor. Medir dos parejas en orden alternado
y aplicar el plazo a todos los picos del candidato.

Con `--predict-q15`, proyectar la tensión de reset
desde el último punto aceptado usando las respuestas
a C2 y a la base de Q15 con R59 cerrado. Aplicar la
ley completa de CR6 sobre esa tensión provisional y
resolver la semilla con el mismo residual Euler/BDF2
de Q15. Verificar después el cierre completo del
receptor y Q15. Si falta la tangente, falla la semilla
o se rechaza el cierre, volver al punto anterior
aceptado con el mismo historial.

Comparar con el arranque anterior, con la misma
política de tangente del receptor. Contar todas las
evaluaciones del cierre de audio, incluidas las de
reintento. Conservar la auditoría nodal, Radau, los
cruces y las reservas de carga al mismo reloj.

Con `--q15-retry`, sembrar cada propuesta de Q15
desde el cierre provisional anterior de R59. Proyectar
el seguidor con la nueva base de Q15, aplicar la
respuesta local de la base del VCA con R59 cerrado
y usar la raíz de junturas previa como semilla.
Cada propuesta usa las cargas originales del paso.
Si el cierre provisional falla, repetir desde la
historia aceptada. Conservar la verificación de
las filas y la corrección de Q15, y la auditoría de
los puertos del seguidor. Contar los intentos y las
iteraciones de R59 de los cierres que retornaron.
Contrastar con la misma semilla de Q15 y la misma
política de tangente con el arranque anterior de R59.

Con `--predict-q15-audio`, calcular una lectura
provisional de la base del VCA con la historia FOH
aceptada, la señal y R60 del paso nuevo, y la fuente
anterior de R59. Evaluar la ley una vez sobre el
predictor de junturas con el feedback anterior.
Proyectar la diferencia de la base al reset con la
respuesta del seguidor y el denominador de R59
cerrado. Usar este término sólo para la semilla
Euler/BDF2. Resolver y auditar los estados con las
mismas ecuaciones y límites completos.

Comparar con la misma política de reintentos y
tangente sin esa lectura provisional. Contar los
intentos y las iteraciones de R59 después de la
semilla y medir el coste total de ambos caminos.

Con `--predict-q15-cr6`, conservar la ley no lineal
de CR6 en la semilla. Si s es la respuesta de reset
al cátodo en el estado aceptado con R59 cerrado y
g es la pendiente de CR6, la conductancia del resto
del circuito vista desde reset es g/s−g. Congelarla
durante la predicción y aplicar la excursión de C2
como una corriente equivalente con la conductancia
total g/s. Resolver la fila de reset junto con las
dos filas de Q15. Eliminar la corrección de reset
al resolver y reconstruirla antes de verificar las
tres filas y correcciones de la semilla.

Si la conductancia equivalente es inválida o falla
la semilla, queda disponible el arranque desde el
estado aceptado. El cierre final conserva el stamp
completo. Comparar contra la proyección lineal con
las mismas políticas de R59 y Q15.

Con `--predict-r59-affine`, resolver un seguidor
provisional con la base del VCA aproximada por
Vbase_anterior + a·(loudness−loudness_anterior).
La derivada de la corriente por R59 respecto de
loudness en esta semilla es (1−a)/R59. Conservar
las cinco filas del seguidor y CR6. Empezar el
cierre real en los voltajes provisionales y
comprobar la base del VCA, el residual y R59 con
el receptor completo. Ante rechazo de la semilla
conservar el arranque previo. Comparar ambas ramas
con la misma semilla no lineal de Q15.

Con `--tight-r59`, exigir 2e−13 V de acuerdo en
la fuente de R59 para candidato y control. Mantener
la reserva de carga del receptor en 1e−20 C y
verificar ambos cierres. Repetir el contraste afín
tras los rechazos de la carga positiva a 1e−10 V y
2e−12 V para comprobar el efecto de la convergencia.

Con `--predict-r59-junctions`, resolver la columna
de R59 de la tangente existente del receptor.
Resolver (I+P·diag(pendiente))·dz/dV_R59 =
ZH·U1[:,R59]+ZU[:,R59] y guardar la dirección en
V/V junto con la ganancia de base del VCA. Cuando
un reintento comparte la historia FOH, la señal y
R60 de la raíz provisional, iniciar en esa raíz
más la dirección por el cambio de tensión en R59.
Evaluar la ley en las junturas proyectadas y
comprobar el residual completo de 2e−13 V. Ante
fallo del predictor, conservar el arranque desde
la historia aceptada. Comparar con el mismo cierre
de R59, la misma reserva de carga y los mismos
reintentos de Q15.

Con Q15 dinámico, contrastar `--packed-products`
contra la misma configuración escalar, incluyendo
el mismo predictor de R59 y el cierre de Q15/CR6.
El agrupado comparte cada entrada entre cuatro
filas y conserva el orden de suma por fila.
Exigir igualdad por bits en la trayectoria, los
diagnósticos y las 17 cargas finales, además de
Radau, la auditoría de carga y el plazo nativo.
Si se añade `--packed-odd`, el control también usa
los productos agrupados y el contraste aísla la
corrección impar de Newton.

Con Q15 dinámico, `--profile` mide los cierres de
R59, incluida la ruta de reintento de Q15, y las
semillas de Q15 y del seguidor afín por separado.
Verificar igualdad por bits del resultado completo
con el ejecutable sin instrumentar. Excluir el
calentamiento de los contadores y usar sólo el
ejecutable sin instrumentación para el plazo.

Con `--pack-receiver-law`, evaluar en cuatro lanes
AVX el resto exponencial y su pendiente cuando
todas las junturas del grupo cumplen |z| < 0,125,
con z adimensional referido al punto de trabajo.
Compartir los coeficientes desde 1/2! hasta 1/12!
y el orden de Horner con la evaluación escalar.
Los grupos mixtos y la cola conservan la evaluación
escalar y el dominio |z| ≤ 40. El control usa el
mismo modelo y el mismo agrupado de matrices.
Exigir igualdad por bits tanto en el ensayo de los
límites del kernel como en el banco de Q15/R59,
además de las reservas y el contraste con Radau.

Con `--predict-q15-charge`, guardar la matriz de
capacitancias terminales de Q15 del paso aceptado,
en faradios. En la semilla, estimar el incremento
BE/BC con esa matriz por el cambio de tensión
de base y colector. Conservar la corriente no
lineal de CR6 y el historial de carga aceptado.
El primer paso usa la ley completa en la semilla.
En pasos posteriores, al converger con la matriz
congelada, recuperar el incremento y la tangente
exactos y verificar nuevamente las filas de la
semilla. Si no se obtiene convergencia dentro del
presupuesto de la semilla, usar el arranque desde
el estado aceptado. El cierre cargado también evalúa
la ley exacta y sólo publica su propia carga.
Comparar con la misma semilla no lineal de CR6,
la integración Euler/BDF2, el contraste nodal y
las reservas de carga del mismo reloj.

Con `--prepare-q15-terminal`, preparar una vez por
tick el extremo anterior aceptado de las integrales
de depleción BE y BC de Q15. Guardar la capacitancia
en F y el factor de depleción adimensional. Reusar
también el término de difusión anterior y conservar
la diferencia BC compensada en dos partes.
Para dos extremos bajo el empalme, usar la misma
integral con `log1p` y `expm1`, su signo y los
mismos límites. Si un extremo llega al empalme,
usar la integral por tramos original. La semilla
verificada, los reintentos y el cierre cargado
comparten la historia aceptada del tick. Exigir
igualdad por bits en el núcleo de carga, en toda
la trayectoria y en las cargas finales frente
al control con el mismo predictor.

Con `--reuse-q15-endpoint`, conservar en la semilla
verificada el incremento exacto BE/BC, su tangente
en F y las filas de conducción previas a CR6.
La primera evaluación cargada recibe el mismo par
de voltajes y las mismas fuentes Q25/CR8 del tick.
Aplicar la corriente y la pendiente de CR6 del
seguidor cerrado y comprobar las filas completas.
Descartar el cálculo provisional si se reintenta
con otros voltajes o desde la historia aceptada.
El perfil cuenta los usos y el tiempo de armar
las filas cargadas. Exigir igualdad por bits y
conservar las reservas del control.

Con `--project-r59-history`, conservar el predictor
lineal de junturas del primer intento calculado
directamente. Cuando se repite el cierre con la
misma historia FOH, señal y R60, sumar al predictor
original (ZH·U1[:,R59]+ZU[:,R59])·ΔV_R59. Mantener
el ancla original entre reintentos. Calcular las
cargas y las lecturas con la expresión original
de FOH. El perfil recalcula el predictor directo
y verifica el límite de residual de 2e−13 en cada
raíz proyectada del bloque. Exigir también las
reservas del mismo reloj y la igualdad entre
las compilaciones instrumentada y ordinaria.

Con `--predict-r59-base-drift`, guardar al aceptar
el paso el cambio de la base del VCA menos la
respuesta afín debida al cambio de fuente R59.
Sumar ese cambio en V al intercepto de la semilla
del paso siguiente. La pendiente de R59 y la
estimación de este cambio se usan sólo para
sembrar el seguidor. La raíz del receptor y el
cierre cargado conservan sus ecuaciones completas.
Comparar contra el mismo cierre afín, medir
cuántos intentos de R59 quedan y exigir la
reserva de cargas del mismo reloj.

Con `--predict-receiver-feedback`, guardar al
aceptar el paso la diferencia de P·defecto frente
al estado anterior, en coordenadas de juntura.
En el primer intento del receptor, extrapolar
P·defecto una diferencia más y usarlo sólo en
la semilla. El cierre calcula todas las leyes y
el residual completo. Ante error, reintentar
con la semilla original y la misma historia.
Comparar el número de evaluaciones del residual,
el tiempo y la reserva del mismo reloj.

Con `--predict-r59-one-correction`, formar las cinco
filas del seguidor afín provisional y aplicar como
máximo una corrección de Newton. Usar el mismo
complemento de Schur y la misma pendiente de R59
del cierre afín de control. Pasar el voltaje
provisional al receptor y conservar la iteración
completa del seguidor y el cierre de R59. Medir
cuántos intentos se desplazan al cierre completo,
el coste total y la reserva de carga del mismo reloj.

Con `--predict-r59-two-corrections`, permitir una
segunda corrección con la tangente recalculada en
los voltajes provisionales. Conservar la salida
temprana si pasan las tolerancias y usar como
semilla el último voltaje provisional. Aplicar
el mismo contraste y las mismas reservas.

Con `--reuse-follower-cr6`, conservar la corriente
de CR6 en A y su pendiente en S calculadas en
el punto de convergencia del seguidor. Usarlas
para la columna del cátodo, el puerto de reset
y el extremo anterior de la semilla de Q15.
Si se usa el factor completo, evaluar CR6 una
vez en los voltajes convergidos. Los intentos con
voltajes nuevos siguen evaluando la ley completa.
Exigir igualdad por bits y las reservas eléctricas.

Con `--rack-replay` y un recibo nativo admitido,
reconstruir el mapa y las entradas exactas de esa
rama. Exigir los hashes originales de mapa, entrada
y trayectoria. Empaquetar temporalmente el componente
nativo y renderizarlo en un slot de RackForge a 48 kHz,
128 frames y estéreo. Cada frame del ensayo toma el
segundo extremo J7 de 96 kHz, convertido a f32 en
ambos canales. Medir dos lotes de 64 pares de bloques,
reiniciando el estado fuera del reloj entre pares.
Comparar por bits ambos bloques y todos los reinicios.
Alternar el orden nativo/host y registrar el arranque,
el bloque caliente, los fallos y los plazos del host.
Este ensayo usa las fuentes impuestas del recibo y
un render directo del motor de RackForge.

Medir también el mismo DLL a través de
`PluginInstance::process_wide`, con la misma
activación, reinicios y salida estéreo, fuera
del mezclador. Intercalar esta prueba entre
el nativo y el slot, en ambos órdenes. Exigir
la misma salida J7 por bits en las tres rutas.
Registrar por separado las diferencias de mediana
entre el nativo, la ABI y el slot.

Con `--rack-continuous`, recorrer las entradas
admitidas hacia adelante y hacia atrás, sin
duplicar los extremos. Cada cambio de dirección
conserva la separación de un tick entre entradas.
Mantener la historia de Q15/R59 y las cargas del
receptor durante todo el recorrido. Comparar
16.384 frames de J7 entre el nativo y el slot,
y comparar la trayectoria y el estado final al
particionar el nativo en bloques de 64 y 128.
Los dos primeros bloques deben reproducir el
recibo original.

Con `--rack-physical`, usar el componente continuo
en el callback del banco ASIO de RackForge. El
banco entrega silencio a los buffers físicos
mientras ejecuta el circuito y mide el callback.
Verificar el endpoint NVIDIA, el avance efectivo
de 128 frames y la restauración del perfil ASIO.
Si falta el perfil del banco, seleccionar el
monitor NVIDIA presente sólo en ese perfil
temporal y verificar su eliminación al terminar.
Registrar un control silente y dos pases de 4.800
bloques de cada rama con el mismo criterio de
1,333 ms, asignaciones y fallos. Conservar los
pases rechazados y distinguir el plazo del
callback de la comparación de J7 en el motor.
