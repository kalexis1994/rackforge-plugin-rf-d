# Puerto de panel preparado para el VCO reducido

SVC-9 pp.5/19, OSC1 ON, selector de sierra. Se elimina exactamente
el cursor resistivo de R6; se mantienen tres corrientes y sus nueve
admitancias, incluido el retorno a masa y la carga del oscilador.
[Derivación y gates](VCO_PUERTO_PANEL_PROTOCOLO.md),
[recibo](../evidence/vco_panel_port01.json),
[QA](../evidence/lab_retention_tests01.json).

## Resultado

- R6=25 kΩ, R45=33 kΩ, α∈[0,1]; α=.5 da E=.5 Vsierra y R=39.25 kΩ.
- 70 estrellas originales con extremos/contactos y modos comunes pasan.
- 210 columnas FD ±1 µV, nueve admitancias por caso y disipación pasan.
- 1602 estados (DC y rejillas de ambas notas de 100 ms): cursor y corriente
  BUS coinciden con los nodos originales 39/12 y la sierra 46.
- Siete entradas inválidas se rechazan. Ninguna memoria física eliminada;
  red pasiva y suma de las tres corrientes dentro del gate de 2 fA.

Máximo uso de gates: corrientes 0.020785, cursor 0.000430,
Jacobiano 0.000640, FD 0.067313, potencia 0.000125. En la voz:
cursor 0.000125 y corriente BUS 0.000006560. Gates previos conservados.

La sierra procede todavía del VCO completo. La fórmula de Thévenin
mantiene su reacción a la corriente de BUS cuando se resuelve el generador
junto al puerto; no autoriza imponer una onda independiente de la carga.
Módulo de laboratorio, aún sin exportación de plugin. No se atribuye un
ahorro de tiempo de toda la voz a esta eliminación de un único nodo.

El ejecutable y exports nuevos se retiraron después del contraste;
`tmp/lab-current` queda vacío. No se generó audio nuevo ni una carpeta
permanente de muestras. La nota actual de 100 ms permanece disponible.

Siguiente: conectar un núcleo VCO reducido conservando este puerto y
medir forma, frecuencia, curvas CV y respuesta a cargas contra el original.
La cadena y ambos contornos siguen como referencia. Hardware/RT pendientes.
