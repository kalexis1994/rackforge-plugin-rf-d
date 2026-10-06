# JFET de reset: representación equivalente

Se mantiene la tarjeta exploratoria E402 de 25 C, LEVEL=1, B=1, RD=RS=0.
Los ensayos previos que movían sólo sus cargas conservan su rechazo.
Este ensayo separa **canal y ambas junturas cargadas**, sin modificar los
valores de corriente o capacitancia del [modelo registrado](../evidence/vco1_laboratory_devices.json).

## Derivación y alcance

Para VDS>=0: U=max(VGS-VTO,0), Z=min(U,VDS),
ID=BETA*(1+LAMBDA*VDS)*Z*(2U-Z). Para VDS<0 se intercambian drain/source
y se invierte el signo. Con B=1 el término adicional de Sydney University
es cero. Un B-source representa el canal; dos diodos representan la
conducción gate/source y gate/drain y sus cargas. IS y gmin son los mismos;
N=1, CJO=CGS/CGD, VJ=PB, M=.5, FC=.5, TT=0, TNOM=25.

La carga de juntura Q=2*PB*C0*(1-sqrt(1-V/PB)) antes de FC*PB y su
continuación cuadrática coinciden con LEVEL=1. No se omite una carga ni
se asigna un tiempo de almacenamiento nuevo. El cambio de representación
no hereda la admisión de la primitiva ni identifica un E402 vintage.

Fuentes primarias congeladas en revisión ngspice
`ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6`:
[carga/canal JFET](https://raw.githubusercontent.com/imr/ngspice/ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6/src/spicelib/devices/jfet/jfetload.c),
[Bfac y temperatura](https://raw.githubusercontent.com/imr/ngspice/ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6/src/spicelib/devices/jfet/jfettemp.c),
[conducción/carga de diodo](https://raw.githubusercontent.com/imr/ngspice/ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6/src/spicelib/devices/dio/dioload.c).
La igualdad se restringe a esta tarjeta y temperatura; RD/RS, B distinto
de uno y otras temperaturas requieren nuevas derivaciones y pruebas.

## Orden y gates previos al ensayo

1. Banco independiente de tres terminales: referencia JFET intacta y
   candidato, fuentes idénticas PWL/sinusoidal, inversión VDS y juntura
   directa hasta .65 V. Duración 20 microsegundos, máximo 5 ns, Gear2.
   Error de corriente <=1 nA +1e-6 relativo en todos los instantes;
   diferencia integrada por terminal <=1e-14 C. Son los gates anteriores.
2. Control positivo: mismo deck y BUS=0 de la primera iteración aceptada,
   sólo se cambia la representación JFET. Duración 40 ms / 500 ns.
   Voltajes <=5 mV en grilla común 5 microsegundos, frecuencia <=1 cent,
   igual número de cruces de rampa -2 V y diferencia de sus tiempos <=10 ns.
   Sin alinear fases. Preservar identidad del deck y export originales.
3. Reproducción del VCO fallido de la tercera iteración con BUS variable,
   mismo deck salvo representación y destino del export. Completar 40 ms
   con sus tolerancias originales antes de volver al cierre de R45.

El banco termina en el primer rechazo y conserva deck, log, export y
recibo. Ningún resultado local admite automáticamente la unión con
contorno, su refinamiento, audio de una nota larga o ejecución en tiempo real.
