# Familia CV/BUS acoplada al puerto mezclador/C27

Protocolo previo, 2026-10-24. SVC-9 pp.5/19, Fig.9-17, y p.13,
Fig.9-11: CA3046/SVC-204D con trims y datos exactos de VCO_FAMILIA.
Conservar las ocho curvas entrenadas, sin ajuste nuevo o extrapolación.

## Frontera y alcance

El BUS pasa a ser incógnita, con R6=.5/R45=33k una sola vez. Añadir las
otras ramas ON originales del panel y C27=10 uF hasta BASE_Q29 impuesto
a 0 V. Esa frontera permite aislar el puerto; no es el filtro completo.
Fuentes restantes impuestas a 0 V, potenciómetros .5, sin red OFF:

- L0: OSC1 y EXT ON; EXT por R46=33k.
- L1: las cinco ramas ON; OSC2/3 por 25k/33k, NOISE por 25k/11k,
  EXT por 33k. Resistencias originales; no modelar estas fuentes como
  otros osciladores activos o ruido físico.

KEYBOARD [-2.6,-1.6,-.6] V; otras cinco entradas -2.1 V. Seis escenas.
R8=.2613404652606161, R11=521.3126579373712 ohm, C4=10 pF,
SW6=3/10, 25 C, rails originales y NEG4_REF libre con carga extra 0 A.
La familia se usa como hipótesis cuasiestática ante el pequeño BUS libre;
el contraste sólo puede admitir las ventanas/escenas realmente ensayadas.
No implica CV temporal, cargas arbitrarias, otra topología, RT o vintage.

## Oráculo y continuación compartida

Seis transitorios completos del VCO de circuito más panel/C27, Gear2,
30 ms, máximo 125 ns. Trap2/125 ns y Gear2/62.5 ns en -1.6/L1.
Sólo sustituir Vmixer por las ramas explícitas y C27/BASE. El VCO conserva
su arranque C1=0. Inicializar BUS con el DC medio estimado por la familia;
es condición inicial de carga, no semilla de una raíz VCO o dato de ajuste.

Retener los últimos dos ciclos con contexto desde el tercer último reset
ramp=-2 V después de 15 ms. Inicializar la continuación reducida desde
ese reset real con fase=0 y exactamente BUS del oráculo interpolado allí.
Esto comparte memoria terminal, no demuestra arranque propio del reducido
ni independencia de dos historias. Integrar hasta dos vueltas de fase,
máximos 500/250 ns, trapezoidal implícito de fase y carga C27.

Ecuaciones: C27*dBUS/dt + Ipanel_BUS + Iotras=0;
dphase/dt=f(CV,BUS). Resolver el incremento de BUS, sin restar dos cargas
grandes; fase/carga HIGH/LOW con TwoSum. Candidato provisional hasta
residual <=1e-13 A y corrección <=1e-12 V. Máximo 32 iteraciones,
dominio BUS [-.125,.125] V y CV original; rechazo sin publicar estado.
Iotras=BUS*sum(1/Rthevenin), fuentes cero; Rthevenin=39250/17250/33000 ohm
según rama. Derivada incluye el efecto de BUS sobre frecuencia y fase.

## Gates previos

- Dominio íntegro en cada ventana, fin completo y reloj creciente.
- Comparaciones entre métodos/pasos y reducido/oráculo, sin quitar DC,
  cambiar ganancia o realinear: fase entre resets reales de cada historia.
  Frecuencia <=1 cent; saw/tri/pulse DC <=5 mV y vector armónicos 1..8
  <=2 %. Picos y armónicos altos son diagnósticos de la serie finita.
- BUS DC y norma armónica 1..8 <=10 uV. Panel BUS, otras ramas y
  corriente de C27: DC/norma armónica <=2 nA. IC1_SUM <=10 uV absoluto,
  corriente KEYBOARD <=2 nA. No atribuirle medición de las otras CV.
- KCL original del oráculo con corriente independiente i(VBASE) <=1e-10 A.
  Balance integrado C27 relativo <=.002, o absoluto <=1e-14 C cuando
  el throughput es pequeño. No confundirlo con un balance global de energía.
- Rust: KCL <=1e-18 A, residual/corrección Newton <=1; balance de carga
  trapezoidal <=1e-16 C +1e-8 de throughput. Derivadas del residual contra
  diferencias centradas relativas 1e-5 más 1e-10 absoluto. Contrastar MNA
  independiente del panel sin duplicar OSC1; medir cero heap en pasos.
- Entradas inválidas o Newton sin presupuesto: estado intacto y retry
  válido igual por bits. Controles negativos: doble R45 y signo C27
  invertido deben ser detectados por el contraste eléctrico.

## Evidencia y recursos

Un tmp/lab-current, vacío al inicio/final. Compiler/ngspice/macromodelo
congelados por QA previo. Sin Cargo, rlib, cache, audio o nuevos inputs
privados. Export binario con lector ya contrastado; guardar digest/tamaño
antes de retirar, deck/log y ventanas float64 exactas en pack sin pérdida.
Fuentes y fallos/replays antes de corregir; JSON canónico o estados
tipados en restauración. Prefijos retirados sólo regenerables.

Nuevo bloque <=32 MiB de evidencia sin QA; cada export <=256 MiB,
reserva >=1 GiB; SPICE <=180 s, compile <=120 s y reducido <=240 s/proceso.
Reusar biblioteca sólo si fuera necesaria, sin reconstruirla. Pruebas
anteriores heredadas por identidad. No reejecutar campañas largas ajenas.
