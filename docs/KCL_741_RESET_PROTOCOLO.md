# KCL 16/17 y acoplamiento G4/EOS durante reset

2026-10-06. Tras [refutar el RHS variable](POLO_741_RESET_RESULTADOS.md),
observar el acoplamiento antes de cambiar la representación numérica.
Preservar íntegramente los builds anteriores; copiar `newton-build02` en
`newton-build03`. Mantener decks, circuito, modelos, tolerancias y método.

## Inventario y ecuaciones

Macromodelo TI LM741 con SHA256
`f58370983c8bd22bf6a59ddd05a1dd492f1a0ea60f673ffd460a356da5e693dc`.
El nodo 17 conecta L2 y R13; el 16 conecta R13, G4 y la entrada ideal de EOS.
Verificar ese inventario y el puerto de entrada de XSPICE; una conexión de
control no implica una corriente de carga. L2 sigue siendo artificial.

Registrar los coeficientes **efectivamente estampados** de R13 y G4,
los voltajes anteriores/nuevos 98, 17, 16, 3, 49, 7, 1 y la corriente L2.
Con las orientaciones de la netlist, definir:

- `iR = gR*(v17-v16)`, hacia 17→16.
- `iG = gm*(v3-v49)`, hacia 98→16.
- `r17 = iR-iL`, corriente saliente del nodo 17.
- `r16 = -iR-iG`, corriente saliente del nodo 16.
- `rEOS = (v7-v1)-(1e-3+v16-v49)`, ecuación de tensión de EOS.

Reconstruir con Decimal de 80 dígitos desde los valores binary64 observados.
Comparar ecuaciones anteriores/nuevas, correcciones nodales, cambios de
corriente y fuente de control. Reutilizar la asociación estricta de L2 y
exigir coincidencia con los registros nuevos de cada solve; rechazar NaN,
ausencia, duplicados o coeficientes incorrectos.

Conservar por separado la fila L2, las dos KCL lineales completas de esos
nodos y la ecuación EOS. No llamar a ese conjunto KCL no lineal completa
de la red. Cuantificar `req*ulp(iL)` y `req*gm*ulp(v3)` como escalas de
representación, sin convertirlas en una cota del solve acoplado.

## Gates y decisión posterior

Ventana y escenarios anteriores: 2.2773–2.2775 ms, BUS cero/variable.
Medir sonda apagada/encendida en ambos: todos los tiempos y seis vectores
deben ser exactamente iguales al build anterior. BUS cero debe completar
40 ms y BUS variable conservar el mismo rechazo. Auditar fuentes, módulo,
inicialización, runtime, exportaciones y ejecutable antes/después.

Este corte sólo observa. Cualquier eliminación de estado, escalado o
coordenada alternativa requiere otro protocolo: derivación algebraica,
historia, DC, precisión, control completo y gates de forma/frecuencia/eventos
anteriores. Una KCL pequeña puede coexistir con correcciones grandes;
no identifica la causa del fallo por sí sola ni se transfiere al oficial.

Fuentes ngspice 46 fijadas en `ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6`:
[R13/RESload](https://raw.githubusercontent.com/imr/ngspice/ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6/src/spicelib/devices/res/resload.c),
[G4/VCCSload](https://raw.githubusercontent.com/imr/ngspice/ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6/src/spicelib/devices/vccs/vccsload.c),
[puertos POLY](https://raw.githubusercontent.com/imr/ngspice/ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6/src/xspice/icm/spice2poly/icm_spice2poly/ifspec.ifs)
y [evaluación POLY](https://raw.githubusercontent.com/imr/ngspice/ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6/src/xspice/icm/spice2poly/icm_spice2poly/cfunc.mod).
