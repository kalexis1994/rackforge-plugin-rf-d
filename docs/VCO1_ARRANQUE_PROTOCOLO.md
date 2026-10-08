# VCO1: semilla propia y ciclos completos, protocolo previo

2026-10-08. Base3191073, CA3046 nominal, tarjetas y grafo congelados a 25°C.
No cambiar las ecuaciones de VCO1/741/BJT/JFET ni los gates del Newton.

## Semilla de circuito

La semilla no contiene estados SPICE, fixtures, una frecuencia, tabla de
notas o umbrales de reset. Usa KCL/KVL de SVC-9 p.5 y panel p.19; todas
las resistencias y constantes de semiconductores proceden de los grafos
anteriores. Estas aproximaciones sólo calculan el estado inicial de Newton;
ninguna sustituye las ecuaciones aceptadas o actúa en el integrador.

NEG4: divisor R166/R174 con carga exterior y base Q4. Corriente Q4 por
R48 y BJT BF/IS; juntura VT ln(1+I/IS). Fuente común E402 por dos canales
saturados y lambda, drenadores por R46/R5. Q8/Q9 por R45 y base común;
Q3 por R36 y corriente de base. Gate derecho cerca de C1=0 conduce a
DRIVE=R24*(10/R25-10/R4), sólo para la primera estimación DC.

Q2/Q6 incluyen saturación: resolver F/R de los dos transportes a partir
de corrientes terminales BF/BR, no suponer VCE=0.2V. Divisores y cargas
R3/R14/R29, Q1/R28/R23, panel R6/R45 y puente R30/R31 completan waveformers.
Q5/Q11 se estiman cortados en esta rama de arranque; el Newton completo
vuelve a evaluar todos los dispositivos. Los ocho ciclos escalares fijados
son un presupuesto de semilla, no pasos de tiempo.

IC1: KCL del sumador desde sus seis CV/R, R11/R37, R42 y R20. Trims R8
por pista total, Qa/Qb por ratio exponencial; Qc/R79 con corriente R42.
IC3 por R69/R78 y corriente de base. Las dos interiores 741 se inicializan
con su propio solver de puerto, sin tablas. Después se resuelven las 134
filas juntas con C1=0 y fuente de arranque explícita; Euler la retira.

Dominio del stamp y controles previo, con rechazo de semilla si una
aproximación no es válida. No se promete cobertura de todo ±40V o ±1A.
Primer banco: dos C4 nominales, ambos trims nominales y calibrados con
CV teclado -3.1/-2.1/-1.1/-0.1V, otros CV -2.1V. Toda semilla/control y
fallo queda ligado a source bytes. No ajustar constantes para coincidir
con un estado exportado; comparar sólo después de su convergencia.

## Gates

Startup: residual <=1e-13 A, restricciones <=1e-11 V y corrección
<=2e-9V/2e-12A, mismos gates del Newton. Nominales frente a los DC SPICE
condicionados anteriores: nodos <=2e-7V, corrientes <=2e-10A. Los otros
arranques se contrastan por las incidencias independientes, incluida
fuente C1=0 y masa; un fallo de SPICE anterior no se borra.

Ciclos completos: protocolo VCO1_NATIVO_PROTOCOLO sin relajar gates:
30ms, observar tras15ms, 500/250/125ns, C4 separadas. Exports completos,
resets/corrientes Qa/Q10, extremos de tres ondas/NEG4 y corriente al panel.
Frecuencia <=1cent y extremos <=5mV entre250/125ns; dispersión <=1e-5;
balance C1 <=0.002. Añadir contraste Euler independiente local en regiones
de rampa/reset y conservar los bancos Gear2/Trap2 como referencia externa.
Escenas reservadas y objetivos de calibración se admiten separadamente.

No audio/RT antes de comprobar la trayectoria para su alcance. Test aislado
sin heap para startup y pasos. Fuentes, comandos, modelos y exports con SHA;
fallos conservados y replay de la misma etapa antes de reparar.
