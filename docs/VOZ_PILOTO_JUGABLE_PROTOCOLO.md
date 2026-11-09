# Base jugable de RF-D con el criterio de RF-5

Separar el solver acoplado nominal CA3046 como referencia
offline y el camino audible de producción por bloques.
Empezar con el piloto ya contrastado a 192/384 kHz.
Mantener la misma sierra H128, el ladder, los VCA, J7,
el FIR y la conversión fija de 125 µV por escala completa.
La base tiene una sola sierra, cutoff y polarización fijos
y una rampa de laboratorio. La entrada MIDI selecciona
una nota monofónica grave en el rango 36–72.
[Derivación y contraste del piloto](VOZ_REDUCIDA_PILOTO_RESULTADOS.md).

Empaquetar el adaptador portable con una entrada MIDI y
una salida estéreo. Instalar el paquete en un almacén
temporal y enviar la partitura de ocho eventos por el
enrutador real de RackForge. Confirmar el hash de las
48.128 muestras estéreo contra el piloto archivado.
Medir dos instancias nuevas a 48 kHz con 128 frames,
cero eventos descartados, cero fallos de slot y un máximo
de 1,333 ms por bloque. Conservar fallos y repeticiones.
Publicar un único paquete local de audición al pasar
el contraste y el presupuesto offline.

Las incorporaciones siguientes deben conservar un
contrato de circuito por bloque. El primer acople usa
el piloto de retornos como referencia de puertos.
Los estados de C2/C5, las corrientes R59/R60 y el
evento del biestable se contrastan con el solver
antes de integrar sus modelos de tiempo real.
[Retornos](VOZ_PILOTO_RETORNOS_PROTOCOLO.md),
[gatillo y biestable](VOZ_PILOTO_GATILLO_PROTOCOLO.md).

## Puertos de retorno en el paquete

Integrar las 18 leyes ya contrastadas en el piloto
FOH a 192 kHz, con C27, C18, el ladder, ambos VCA,
R59 de 68 kΩ y R60 de 680 Ω. Exponer dos entradas de
laboratorio automatizables, en mV. R59 recibe el
offset alrededor de 2 V dentro de ±15 mV. El pin 16
del filtro recibe ±1 mV alrededor de 0 V y actúa
sobre la rama de R60 a través de Q26/Q28.
La escena nominal arranca con ambos offsets a cero.

Antes de empacar, verificar la misma planta contra
Radau a 384/768 kHz con las tres escenas de retornos.
Aplicar el contrato previo de J7 y 2 nA por retorno.
Para el banco del paquete, dirigir CC20/21 a los
extremos de los offsets desde el host y comparar
las 48.128 muestras estéreo por bits con la misma
secuencia aplicada al ABI portable. Comparar también
con controles neutros para demostrar su efecto.
Mantener los dos pases de 128 frames, 48 kHz y el
presupuesto de 1,333 ms. Los estímulos de frontera
siguen siendo explícitos hasta integrar C2/C5.
[Contrato eléctrico](VOZ_PILOTO_RETORNOS_PROTOCOLO.md).

Emparejar filas independientes de las matrices de
carga y realimentación en carriles SIMD. Conservar
el orden de suma por fila y el residuo de las 18
leyes. Empaquetar con Binaryen 132 y exigir salida
idéntica al componente escalar para la misma escena.
El banco reutiliza el ejecutable de RF-5 o el indicado
por la variable `RF_D_WASM_OPT`.

## Panel de audición 0.3.0

El paquete declara una superficie web de PLAY y usa
`plugin.parameters`, `plugin.set_parameter` y la
telemetría canónica `parameter_changed` de RackForge.
El panel y el motor comparten seis índices públicos.
El preset Pilot Saw restablece los valores de fábrica.
El estado `RFD1` guarda los seis valores como f64 LE,
con validación antes de publicar un restore.

| Control | Intervalo | Inicial | Acción en el piloto |
| --- | --- | --- | --- |
| Saw mix | 0–100 % | 100 % | Escala la sierra antes del mixer/capacitor de entrada dentro de su límite de 80 mV |
| Output | 0–100 % | 100 % | Escala la salida de audición después de J7; un recorrido completo tarda 64 frames |
| Attack | 1–100 ms | 5 ms | Duración nominal de la rampa de audición ascendente |
| Release | 1–200 ms | 5 ms | Duración nominal de la rampa de audición descendente |
| Filter trim | ±1 mV | 0 mV | Entrada del pin 16 de la planta FOH |
| Volume bias | ±15 mV | 0 mV | Desplazamiento del extremo de R59 alrededor de 2 V |

Los porcentajes y los tiempos de rampa son decisiones
de audición. Los límites de los trims provienen del
[contraste eléctrico admitido](VOZ_PILOTO_RETORNOS_RESULTADOS.md).
La planta conserva una sierra monofónica. El acople
de C2/C5 y el biestable sigue en el banco offline.

El banco automatiza los seis índices en el ABI y en
el enrutador MIDI de RackForge. Con el preset de
fábrica y con la automatización previa de R59/pin 16,
exige coincidencia por bits con 0.2.0. Prueba cada
control por separado, incluido el silencio del fader
de salida, y un restore válido y otro rechazado.
Con todos los controles activos compara el escalar,
el SIMD y RackForge por bits y aplica 1,333 ms de
máximo a dos pases offline de 128 frames efectivos.
