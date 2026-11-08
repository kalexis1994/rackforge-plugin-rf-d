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
