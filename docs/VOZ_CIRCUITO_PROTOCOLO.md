# VCO1, ladder y dos VCA: protocolo de integración

Fecha: 2026-10-05. Referencia previa del VCO: `f6429bf`.
Fuentes: SVC-9 Fig. 9-11 p. PDF 13 / SVC-204D p. 69, tabla 7-8
pp. PDF 30–31; panel Fig. 9-17 p. 19. La hoja 9-11 se revisó visualmente
de nuevo para esta integración. [Transcripción](../evidence/voice_board4_graph.json).

## Circuito y fronteras

Se elimina la fuente ideal del mixer del oráculo anterior. R45 panel,
C27, Q29/Q30 y sus cargas resuelven juntos el BUS. La red de 25 BJT de
placa 4 incluye Q26/Q28, las cuatro etapas ladder con capacitores 68 nF,
recuperación Q5–Q8, C10/R14/R73, Q16/Q15/Q18, Q14/Q13/Q21,
Q1/Q12/Q17, CR1/CR2, C2 y dos terminaciones impuestas.
R39, R49, R73 y los balances se representan eléctricamente; contactos
de resistencia cero son restricciones exactas. No se agrega un buffer
entre bloques ni se impone corriente de cola.

La tarjeta BJT es la misma hipótesis común del VCO, con carga finita;
no identifica TIS97/2N4058 vintage ni dispersión o selección de pares.
CR1/CR2 usan una familia exploratoria ya documentada en
[DS-458](DIODOS_SALIDA_1N458A.md): n=2, 0.9 V a 100 mA, 25 grados C;
Is se deriva de Shockley. Se omiten carga, recuperación y resistencia
serie del diodo, sin afirmar identificación física.

R61 conserva candidatos 200/200000 ohm. El perfil funcional principal
usa **200 ohm del esquema**; el alternativo permanece separado. No se
resuelve la discrepancia del inventario por elegir una salida agradable.

Controles iniciales: cinco CV del VCO -2.1 V, teclado -2.1 V; R11/R8
calibrados en el laboratorio previo. SW9 ON, sierra, nivel eléctrico
0.5; los otros osciladores, ruido y preamp sin poblar. Filtro: R39=0.5,
R49=250 ohm, R73 inferior=500 ohm, EMPHASIS=50000 ohm; J2 a masa,
SW15 OFF, SW16/17 OFF. Contorno de loudness pin9=2 V, base Q21=2 V,
amount pin16=0 V impuestos. No son posiciones de perilla ni el circuito
normalizado del jack. Balances 12.5/50 ohm; ambas cargas 100 kohm.
Rieles ideales. No se incluye el amplificador de auriculares.

## Banco declarado antes de medir

- Arranque de 40 ms, observación después de 20 ms; pasos máximos
  500/250 ns Gear2 y 250 ns Trapezoidal2, opciones del VCO conservadas.
- Refinamiento y método: frecuencia dentro de 1 cent; extremos de BUS,
  recuperación y salida principal dentro de 5 mV; RMS AC dentro de
  1% más 10 microvolt. Balance integrado C2 frente a R75/R77 dentro
  de 0.1 nC. Estas son tolerancias de laboratorio, no especificaciones Moog.
- Controles reservados: cutoff eléctrico 0.2/0.8; contorno loudness
  0/1/4 V con base Q21 fija; base Q21 0 V con contorno fijo; emphasis
  5000/0 ohm; carga principal 10000 ohm; perfil R61=200000 ohm.
- Registrar finitud, periodo, amplitud, DC y corrientes de cola. La
  dirección cutoff se observa en corriente Q28 y energía de armónicos,
  sin convertir la fracción de perilla en Hz por una fórmula inventada.
  Comparar mute con escena nominal; no exigir monotonía de amplitud
  al cambiar resonancia. Autooscilación requiere un ensayo independiente.
- Conservación de netlist/log/export completos y hashes de fuentes
  antes/después, incluso ante rechazo. Una interpretación corregida
  reusa trazas; cualquier cambio eléctrico requiere un banco nuevo.

Una primera escucha de ciclos estacionarios es un adaptador explícito.
No demuestra Note On/Off ni una voz de duración completa. La integración
portable, envolventes y fidelidad física mantienen sus gates abiertos.
