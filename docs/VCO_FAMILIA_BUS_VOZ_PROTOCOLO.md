# Ampliación de H128 para el BUS cargado de la voz

2026-11-07. El banco nominal monofónico observó de −0,942 a
−0,910 V y el circuito conjunto CA3046 observó de +0,891 a
+0,929 V. Son dos historias de arranque diferentes. Extender
la familia estacionaria al intervalo de −1 a +1 V sin
reinterpretar el signo ni forzar la carga de C27.
[Escena nominal](RECOVERY_ENGINE128_MONO_RESULTADOS.md),
[circuito conjunto](VOZ_DOS_CONTORNOS_RESULTADOS.md)

Mantener los ocho nodos de entrenamiento de la familia H128
original y añadir cuatro CV en cada extremo BUS ±1 V. Conservar
CA3046, selector, trims, temperatura, fuentes y red R6/R45 de
la familia. Usar la interpolación cúbica original en CV y
lineal por intervalos en BUS. Mantener los coeficientes
0–128 y la fase a partir del reset original. No extrapolar
ni recortar la entrada al dominio. Las derivadas en un nudo
BUS de cambio de tramo son unilaterales según el tramo elegido.
[Familia original](VCO_FAMILIA_PROTOCOLO.md)

Reservar seis combinaciones CV/BUS. Los CV −2,6/−1,6/−0,6 V
se cruzan con BUS −0,94/−0,91/−0,96 V y +0,89/+0,91/+0,94 V
respectivamente. En −1,6/−0,91 V añadir Trap125 y Gear62,5
como contraste del oráculo. Ventanas de 30 ms, ciclo denso
y gate anterior de periodicidad 1e−5 y balance 0,002.
Los puntos reservados quedan fuera del generador.

Mantener gates de 1 cent, DC de onda de 5 mV, armónicos
1–8 de onda al 2 %, IC1_SUM a 10 µV y corriente DC/armónica
de puertos a 2 nA. Conservar KCL del panel, disipación y
contraste de derivadas. Medir extremos y componentes 9–128
aparte. Un puerto estacionario aprobado no acredita la
trayectoria con BUS o CV variables.

En la unión con ambos contornos, conservar sus stamps,
el gatillo compartido, ambos voltajes de temporización,
las historias de juntura y los puertos de base VCA y
TAIL. El puerto del VCO aporta R6/R45 una sola vez al BUS.
Conservar C27 entre BUS y BASE_Q29. Contrastar las filas y
corrientes del acoplamiento con historias ya reservadas
antes de promover una trayectoria nueva. Las reservas
previas de recuperación, FIR y voz se conservan por identidad.

Los dos pases físicos con margen de 1,333 ms siguen sujetos
a la validación de una voz reducida completa. No usar un
banco de fuente impuesta como prueba de esa voz. Mantener un
área temporal y los rechazos con su replay. Sin WAV nuevo.

Para el puerto de audio, generar una tabla periódica Hermite
de 4096 fases a partir de H128. Contrastar la sierra con la
serie directa a 2 µV, la corriente a 2 nA, y las derivadas
de la tabla frente a diferencias centradas. Verificar KCL y
disipación con las resistencias originales. La tabla se
regenera fuera de audio y queda fuera de Git.

Acoplar el puerto al stamp de 118 nodos que ya carga ambos
contornos. Eliminar algebraicamente las dos fases Radau con
sus frecuencias dependientes del BUS de cada etapa. Verificar
las cuatro derivadas BUS/BUS resultantes con diferencias
centradas. Los términos cruzados que se entregan al solver
son coeficientes de Newton y dejan intacta la carga física.

Dos continuaciones condicionales de 128 muestras a 48 kHz.
Una parte del DC monofónico negativo, con KEY a 10 V en la
muestra 16 y vuelta a cero en la 96. La otra parte de la
historia positiva a 6 ms del circuito conjunto, en liberación.
Usar CV fijo de placa −1,6 V y fases declaradas. Conservar
HIGH/LOW de entrada. Comparar 32 y 64 subpasos por muestra
al mismo reloj y mantener el gate de estados de la voz
cargada de 20 µV + 2e−6·|V|. Contrastar C2, C5, BUS y
los retornos de ambos contornos, C27 y J7. Reensamblar
las filas de cada etapa reservada con el stamp anterior
de ambos contornos y con la red R6/R45 explícita. Exigir
20 pA en las filas físicas y el mismo Newton de 1 pA/2 nV.
Estas ramas conservan la historia de entrada y prueban
la discretización del candidato en una ventana. El arranque
propio y la comparación de nota completa quedan separados.

Si Newton rechaza un subpaso, conservar la historia y
repetir ese intervalo con bisección diádica, hasta tres
niveles. Registrar el rechazo y el replay previo. Mantener
el reloj común y los gates de raíz, carga y refinamiento.

Si la pareja 32/64 conserva la raíz pero falla el error
temporal, guardar su rechazo y refinar esa misma rama
con 128/256 subpasos por muestra. La historia, los
controles y los límites se mantienen. Comparar el
resultado a los mismos relojes de 48 kHz.

Si 128/256 queda fuera del gate durante la conmutación,
usar 512 y reutilizar el recorrido de 256 con los mismos
bytes de núcleo, tabla, compilador, biblioteca e historia.
Conservar el contraste anterior y comparar otra vez en los
129 relojes comunes.
