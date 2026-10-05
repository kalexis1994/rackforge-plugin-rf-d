# VCO1, ladder y dos VCA: protocolo de integraciÃƒÂ³n

Fecha: 2026-10-05. Referencia previa del VCO: `f6429bf`.
Fuentes: SVC-9 Fig. 9-11 p. PDF 13 / SVC-204D p. 69, tabla 7-8
pp. PDF 30Ã¢â‚¬â€œ31; panel Fig. 9-17 p. 19. La hoja 9-11 se revisÃƒÂ³ visualmente
de nuevo para esta integraciÃƒÂ³n. [TranscripciÃƒÂ³n](../evidence/voice_board4_graph.json).

## Circuito y fronteras

Se elimina la fuente ideal del mixer del orÃƒÂ¡culo anterior. R45 panel,
C27, Q29/Q30 y sus cargas resuelven juntos el BUS. La red de 25 BJT de
placa 4 incluye Q26/Q28, las cuatro etapas ladder con capacitores 68 nF,
recuperaciÃƒÂ³n Q5Ã¢â‚¬â€œQ8, C10/R14/R73, Q16/Q15/Q18, Q14/Q13/Q21,
Q1/Q12/Q17, CR1/CR2, C2 y dos terminaciones impuestas.
R39, R49, R73 y los balances se representan elÃƒÂ©ctricamente; contactos
de resistencia cero son restricciones exactas. No se agrega un buffer
entre bloques ni se impone corriente de cola.

La tarjeta BJT es la misma hipÃƒÂ³tesis comÃƒÂºn del VCO, con carga finita;
no identifica TIS97/2N4058 vintage ni dispersiÃƒÂ³n o selecciÃƒÂ³n de pares.
CR1/CR2 usan una familia exploratoria ya documentada en
[DS-458](DIODOS_SALIDA_1N458A.md): n=2, 0.9 V a 100 mA, 25 grados C;
Is se deriva de Shockley. Se omiten carga, recuperaciÃƒÂ³n y resistencia
serie del diodo, sin afirmar identificaciÃƒÂ³n fÃƒÂ­sica.

R61 conserva candidatos 200/200000 ohm. El perfil funcional principal
usa **200 ohm del esquema**; el alternativo permanece separado. No se
resuelve la discrepancia del inventario por elegir una salida agradable.

Controles iniciales: cinco CV del VCO -2.1 V, teclado -2.1 V; R11/R8
calibrados en el laboratorio previo. SW9 ON, sierra, nivel elÃƒÂ©ctrico
0.5; los otros osciladores, ruido y preamp sin poblar. Filtro: R39=0.5,
R49=250 ohm, R73 inferior=500 ohm, EMPHASIS=50000 ohm; J2 a masa,
SW15 OFF, SW16/17 OFF. Contorno de loudness pin9=2 V, base Q21=2 V,
amount pin16=0 V impuestos. No son posiciones de perilla ni el circuito
normalizado del jack. Balances 12.5/50 ohm; ambas cargas 100 kohm.
Rieles ideales. No se incluye el amplificador de auriculares.

## Banco declarado antes de medir

- Arranque de 40 ms, observaciÃƒÂ³n despuÃƒÂ©s de 20 ms; pasos mÃƒÂ¡ximos
  500/250 ns Gear2 y 250 ns Trapezoidal2, opciones del VCO conservadas.
- Refinamiento y mÃƒÂ©todo: frecuencia dentro de 1 cent; extremos de BUS,
  recuperaciÃƒÂ³n y salida principal dentro de 5 mV; RMS AC dentro de
  1% mÃƒÂ¡s 10 microvolt. Balance integrado C2 frente a R75/R77 dentro
  de 0.1 nC. Estas son tolerancias de laboratorio, no especificaciones Moog.
- Controles reservados: cutoff elÃƒÂ©ctrico 0.2/0.8; contorno loudness
  0/1/4 V con base Q21 fija; base Q21 0 V con contorno fijo; emphasis
  5000/0 ohm; carga principal 10000 ohm; perfil R61=200000 ohm.
- Registrar finitud, periodo, amplitud, DC y corrientes de cola. La
  direcciÃƒÂ³n cutoff se observa en corriente Q28 y energÃƒÂ­a de armÃƒÂ³nicos,
  sin convertir la fracciÃƒÂ³n de perilla en Hz por una fÃƒÂ³rmula inventada.
  Comparar mute con escena nominal; no exigir monotonÃƒÂ­a de amplitud
  al cambiar resonancia. AutooscilaciÃƒÂ³n requiere un ensayo independiente.
- ConservaciÃƒÂ³n de netlist/log/export completos y hashes de fuentes
  antes/despuÃƒÂ©s, incluso ante rechazo. Una interpretaciÃƒÂ³n corregida
  reusa trazas; cualquier cambio elÃƒÂ©ctrico requiere un banco nuevo.

Una primera escucha de ciclos estacionarios es un adaptador explÃƒÂ­cito.
No demuestra Note On/Off ni una voz de duraciÃƒÂ³n completa. La integraciÃƒÂ³n
portable, envolventes y fidelidad fÃƒÂ­sica mantienen sus gates abiertos.

Primera corrida (56a222c): aborto en 2.277 ms en E402 durante reset,
con deck/log/export parcial conservados. El siguiente intento aumenta
sÃ³lo itl4 a 100 iteraciones de Newton; ecuaciones y tolerancias intactas.


## Resultado de la unión y banco independiente

La unión sigue rechazada: itl4=100, refinamiento/método, C4 alternativo
 y bypass=0 no completan el primer reset. Las cinco corridas, logs,
netlists y exports parciales se conservan. No se cambia el dispositivo
para forzar aceptación y no se promueve la voz acoplada.

El banco independiente de placa 4 usa una senoide de laboratorio a través
de 1 kohm, sin VCO ni buffer adjudicado al instrumento. Una exploración
preliminar de 440 Hz / 0.1 V completa 80 ms. Esta observación sirvió para
comprobar el harness, no para seleccionar tarjetas ni ajustar el circuito.

Banco siguiente: 80 ms, observación desde 40 ms, Gear2 2/1 microsegundo y
Trap2 1 microsegundo; tres nominales más los nueve controles reservados
anteriores, cuatro frecuencias 110/440/1760/7040 Hz a 1 mV y dos niveles
1/10 V a 440 Hz: **18 escenas**. Se conservan los gates de 5 mV,
1% + 10 microvolt y C2 0.1 nC. La frecuencia es ahora una entrada impuesta;
no se aplica el gate de frecuencia de un VCO autónomo. La transferencia
usa el fundamental observado en BUS, incluyendo su carga. No se extrae
una frecuencia de corte física de estos cuatro puntos.
