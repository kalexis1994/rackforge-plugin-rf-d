# Capacitores ideales: aproximación con resistencia serie decreciente

El cambio exacto de coordenadas pasó el contraste lineal de puerto pero
rechazó las cuatro uniones durante los primeros pasos. No se aplica al
modelo vigente. Se conservan fuente, benchmark y corridas rechazadas.

Se declara un aproximante independiente: añadir epsilon=1 miliohm en
serie con cada capacitor discreto >=10 microfarad de placa 4, conservando
todos sus valores, rieles, BJT, trims y tolerancias. No se identifica
epsilon con ESR vintage ni se calibra por sonido. El circuito ideal
epsilon=0 permanece como límite y conserva sus rechazos.

Este cambio **no es algebraicamente exacto**. Antes de admitir un oráculo
aproximado se deberá medir epsilon decreciente, el contraste contra las
escenas ideales completas y contra métodos/pasos. Ninguna aceptación
puede deducirse sólo de que converja. Se conservan 1 cent, 5 mV,
1% + 10 microvolt y balance C2 0.1 nC del protocolo de voz.

Primer ensayo: unión nominal, cutoff 0.2, contorno 0 V y base Q21 0 V,
10 ms Gear2 máximo 500 ns, KLU, epsilon=1 miliohm. La observación de C2
usa su tensión real descontando epsilon*I, no la tensión externa de la
rama RC. No se añade ruido, deriva, leak ni otros parámetros de pérdida.
