# Interfaz de carga de los dos contornos para la voz reducida

2026-11-08. Usar las historias nominales CA3046 del solver
cargado de 118 nodos. Conservar C18 en el contorno y
R59 de 68 kΩ y R60 de 680 Ω con sus terminales distintos.
La polarización del piloto audible tiene otro dominio.
[Topología y fuentes SVC-9](CONTORNOS_CADENA_PROTOCOLO.md),
[referencia H128](VCO_FAMILIA_BUS_VOZ_RESULTADOS.md)

Separar los 54 interiores de los contornos, los 62
interiores del tramo de audio y los dos terminales
compartidos VCA_BASE y TAIL. Exportar del mismo stamp
los residuos, conductancias y capacitancias de ambos
bloques. Comparar su recomposición con el stamp unido.
Mantener en audio la admitancia del puerto VCO al fijar
la fase del punto. R59/R60 quedan en el bloque de
contornos y el puerto se cierra sumando reacciones.

Derivar un mapa afín de puerto por bloque para las dos
etapas Radau, con el término de historia. Resolver la
interfaz de cuatro incógnitas y reconstruir la dirección.
Contrastar con un solve denso de 236 incógnitas. Usar
reservas antes y después de KEY y en ambos lados de la
inversión de volumen. Excitar por separado R59, R60 y
BUS, y perturbar la historia de cada bloque. Gates del
contraste lineal, 20 nV por coordenada, 2 nA por retorno
y residual backward componente a componente de 1e−10.
Probar rechazo de puerto singular y recuperación.

Para comprobar si basta un solo mapa afín, propagar
desde el estado fino de la muestra 77 hasta la 79.
Conservar las cargas en el avance y usar el ritmo de
fase y la tangente del puerto en el ancla. Comparar la
primera inversión de colectores contra su intervalo de
ocho ticks de la rejilla original y el nodo contra
20 µV + 2e−6·|V| en los relojes comunes. Informar por
separado si falla el calendario, la respuesta nodal o
las corrientes. El cierre lineal local y la trayectoria
tienen gates separados. La campaña de RackForge queda
supeditada a la validación de la trayectoria acoplada.

Contrastar también un híbrido local con el tramo de
audio afín en la muestra 77 y los dos contornos no
lineales activos. En cada etapa se evalúan sus
corrientes y los incrementos de carga desde el
último estado aceptado. Resolver su reacción junto
a la del tramo de audio en los mismos cuatro
terminales Radau, sin alimentar estados futuros.
Usar los mismos relojes, la misma prueba de inversión
y las mismas tolerancias que en el mapa congelado.

La prueba backward física normaliza cada fila con
`|A||x|+|b|+2 nV·sum(|A|)`, donde 2 nV es la
resolución de corrección del solver cargado. Mantener
también la medición sin piso y su escala en amperios
para identificar las filas sin excitación resoluble.

La segunda pasada del híbrido busca un descenso
del residual con hasta 24 mitades por corrección,
como el solver de referencia. Conserva 80
iteraciones máximas, la resolución de 2 nV y el
residual de 1 pA. Conservar el recibo de la
primera pasada, con Newton sin amortiguar.

La tercera pasada retira la tangente H128 del tramo
afín y evalúa su tabla original en las dos etapas.
Resolver dos incógnitas BUS adicionales, con la
fase eliminada mediante las ecuaciones Radau del
solver cargado. Conservar la búsqueda de descenso,
la memoria de carga y los mismos gates. Comparar
también el error de fase en los relojes comunes.

Al conservar H128, contrastar dos conjuntos de
junturas activas de audio. El primero conserva
los diez transistores del ladder. El segundo agrega
los cuatro de recuperación y cinco de señal de los
VCA. Usar las incidencias BE/BC de
[prepared_audio_stamp.rs](../crates/rf-d-circuit/src/prepared_audio_stamp.rs)
y la tarjeta nominal de 298,15 K, Is de 10 fA,
beta directa 100 e inversa 5. Reutilizar la ley de
resto exponencial del piloto. Eliminar el resto de
los nodos de audio y recalcular la reacción y su
tangente en los seis terminales. Comparar las dos
variantes con el mismo punto inicial y las mismas
tolerancias de tensión, corriente y calendario.

Sin ajustar los coeficientes a las ventanas, tomar
cada estado inicial de la malla fina y avanzar de
forma autónoma hasta el final. Probar 15–18 en la
rama negativa con la subida de KEY, 95–98 con su
bajada y 76–81 en la rama positiva para ampliar
la inversión y su recuperación. Usar los eventos
KEY de la referencia y el mismo criterio de
inicialización del nodo 22 de CR10 que el solver
cargado aplica en la entrada de gatillo. Usar los mismos
gates y conservar cada reserva por separado.

Precalcular el mapa de historia del tramo de audio
junto con sus reacciones afines. Probar luego cada
rama en un bloque autónomo de 128 muestras con una
sola linealización al inicio. Detener cada prueba
en la primera violación eléctrica para acotar el
dominio del mapa. Reservar para RackForge la voz
que supere una trayectoria continua con un reloj
viable para tiempo real.

## Junturas de placa 3

Conservar Q16 y Q11 PNP, Q10 NPN y CR1/CR2. El
mapa afín mantiene los resistores, las cargas en
J7 y la memoria de C15, C19 y C21. Agregar
solamente los restos exponenciales a partir de
sus tensiones de ancla. Los BJT nominales de esta
rama tienen beta directa 160, inversa 5 e Is de
10 fA. Q16 tiene el colector a −20 V. Los diodos
usan idealidad 1,5 e Is de 1,293303751274349 nA.
Todos usan 298,15 K. Son parámetros del oráculo
nominal, con la incertidumbre de dispositivo
descrita en el punto DC. [Topología de placa 3](TOPOLOGIA_AMP_AURICULARES.md),
[punto DC](PUNTO_DC_AMP_AURICULARES.md)

Aislar la contribución activa con cuatro
perturbaciones de 8 y 40 mV alrededor de las
muestras positivas 0 y 77. Contrastar el resto
de corriente y su Jacobiano con el stamp Rust
completo después de quitar su parte lineal. Los
límites son 0,2 pA y 2 pS. Repetir las reservas
de KEY y de conmutación y las dos trayectorias
continuas de 128 muestras, sin alimentar estados
del solver durante el avance. Se mantienen los
límites de tensión y de R59/R60 y el intervalo
de ocho ticks para el biestable.

## Conversión PNP antes de C2

La trayectoria con el amplificador de auriculares
activo alcanzó la muestra 65 y el mayor error
pasó al nodo de salida de C2. Conservar también
Q1/Q12/Q17 y los limitadores CR1/CR2 de placa 4.
Usar la tarjeta nominal a 298,15 K con beta
directa 100, inversa 5 e Is de 10 fA, y los
mismos parámetros de diodo del stamp para esa
placa. Mantener las cargas y los capacitores de
la conversión en el mapa de historia. Aplicar
cuatro perturbaciones adicionales y los mismos
límites de corriente y Jacobiano. [Conversión de salida](CONVERSION_SALIDA_DC.md)

Para la rama positiva completa, contrastar J7
además con los límites del banco de reloj
cargado. Usar RMS relativo de 0,1 %, pico
relativo de 0,3 % y error medio de 1 µV.
[Voz con reloj variable](VCO_FAMILIA_BUS_VOZ_RELOJ_PROTOCOLO.md)
