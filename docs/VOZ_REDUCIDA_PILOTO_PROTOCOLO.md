# Primer banco audible del motor reducido

Perfil documental CA3046 de RF-D. El solver acoplado queda
como referencia offline. El primer candidato ejecuta una
voz monofónica con sierra H128 y una reducción del tramo
R6/R45 → C27 → ladder → recuperación → ambos VCA → J7.
Conserva 18 voltajes de capacitor y las 12 leyes de
juntura del núcleo de recuperación.
[Modelo del tramo](RECOVERY_PORT_RESULTADOS.md)

## Alcance del primer motor

- Usar el mapa de cutoff 0,50, R61 de 200 Ω, R14 de 25 kΩ
  y polarización de ambos VCA a 2 V del banco de recuperación.
- Usar la sierra H128 preparada en CV −1,6 V y BUS 0 V. La
  fase se transpone con MIDI temperado 36–72 y conserva
  continuidad. El banco usa prioridad grave.
- Atenuar la excitación de laboratorio al máximo de 80 mV
  del ciclo para permanecer en el dominio del núcleo
  de entrada. El gate aplica una rampa lineal de 5 ms
  antes de R6/R45. Esta rampa es parte del estímulo
  del banco. La polarización de los VCA permanece fija.
- Contrastar el núcleo semilineal a 192 kHz con el de
  384 kHz, usando las familias FIR de J7 del proyecto
  y la misma latencia de 48 muestras. Las matrices
  exponenciales se preparan antes de renderizar.

La escena comprueba el tramo de audio con polarización
fija. La realimentación BUS→oscilador, el gatillo,
C2/C5 y los retornos R59/R60 quedan como requisitos
de la integración dinámica. Se mantendrán sus puertos
explícitos al sustituir las polarizaciones impuestas
por modelos reducidos. Las reservas de la voz completa
siguen perteneciendo al solver offline.

## Aceptación del banco

Comparar J7 en voltios, BUS, corriente R6/R45 y carga
de C27 al mismo reloj. Para el contraste musical,
exigir RMS relativo J7 ≤0,003, pico relativo ≤0,01,
media absoluta ≤1 µV. Para BUS y C27, exigir error
máximo ≤20 µV + 1 % de la excursión de referencia,
en voltios o voltios equivalentes de capacitor.
Para corriente de panel, ≤2 nA + 1 % de su excursión.
Probar legato, retorno a una nota retenida, rechazo
atómico y particiones de bloque. El objetivo nativo
es ≤1,333 ms por bloque de 128 muestras, cero
asignaciones durante el render. Medir el máximo
observado y contabilizar excedencias. La prueba no
abre el driver físico.

## Adaptador portable y escucha

Probar la misma voz a 192 kHz por la ABI wasm-v1 del
SDK de RackForge. Enviar la misma escena MIDI, confirmar
latencia y duplicación estéreo y comparar las muestras
de salida con el render nativo en el mismo reloj. Medir
los bloques de WebAssembly con la instancia calentada
y un arranque nuevo de la voz, en Node y fuera del host.

La audición usa una conversión fija de 125 µV por unidad
de escala completa, elegida tras el primer banco por el
nivel bajo de J7. Esta conversión sólo se aplica al
adaptador y al WAV. Las comparaciones eléctricas siguen
en voltios.
