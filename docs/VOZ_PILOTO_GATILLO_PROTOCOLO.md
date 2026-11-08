# Gatillo compartido con biestable de volumen y carga de filtro

Cerrar Q20/Q12, C7, el biestable Q25/Q15 y los
excitadores Q16–Q18 en las mismas etapas Radau.
Usar las tarjetas nominales y panel CA3046 de
la referencia acoplada. Conservar C7 de 100 nF
y C4 de 10 nF entre sus dos placas, junto con
las cargas BE/BC de Q12, Q20, Q25 y Q15.
Conservar R28 y las dos ramas equivalentes de
R36/CR8, las resistencias de carga de filtro
y los dos caminos de sustain por CR9.
[Contrato del gatillo](VOZ_GATILLO_CARGADO_PROTOCOLO.md),
[referencia cargada](CONTORNOS_CADENA_PROTOCOLO.md)

Las fronteras son la realimentación del seguidor
x4, el temporizador C2 x5, sustain x14 y x48,
y el lado filtro de sus cargas de reset x41/x52.
Sus corrientes de reacción conservan el signo
de KCL. KEY fija el estímulo y S-trigger queda
abierto en las reservas archivadas. No se imponen
los colectores de Q20, Q12, Q25 o Q15.

Comparar contra el solver acoplado en la ventana
positiva 76–81 y en los dos flancos negativos
de KEY. En cada ventana se usa un único estado
inicial. Para la admisión a ocho ticks, exigir
0,2 pA y 2e−20 C en los stamps, 20 µV de error
máximo nodal y los mismos intervalos y sentidos
de los cruces. Mantener la banda de corriente y
audio de R59/R60 para cualquier futura unión con
el motor del piloto.

Conservar las leyes y el paso de 8 ticks al
interpolar los seis puertos externos desde
192 kHz. Si el paso fino pasa, contrastar además
intervalos locales de 64 y 1024 ticks a igual
interpolación. Una malla más gruesa sólo se admite
si mantiene los límites, incluido el intervalo
archivado del cruce. No usar las fronteras de
reserva para alimentar un callback del motor.

En el cruce positivo, barrer todas las combinaciones
de fronteras finas e interpoladas, con el paso
local de ocho ticks y los mismos gates. Registrar
las fronteras mínimas necesarias. Para recuperar
una raíz cerca del cruce se permiten subpasos
como semilla. El paso original vuelve a resolver
sus propias dos etapas y conserva sus límites de
residuo (1 pA) y de corrección (2 nV).
