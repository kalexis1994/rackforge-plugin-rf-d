# Seguidor de volumen en la voz con VCO real

Contrato previo, 2026-10-12. Model D CA3046. Conectar Q3/Q2/CR6 de
placa 2 y R59=68 kΩ al conjunto VCO1→BUS→ladder→VCAs→J7. Fuentes:
SVC-9 Fig.9-7 p.9, Figs.9-11/9-17 pp.13/19 y tablas7-6/7-8
pp.26–27/30–31; leyes e hipótesis del
[puerto anterior](PUERTO_CONTORNO_CADENA_71.md).

205 incógnitas, dos etapas Radau. Los cinco nodos del seguidor son
algebraicos; no añadir capacitancias artificiales. Sustituir la fuente
de volumen de2 V por el nodo de salida resuelto: KCL Q18 añade
−Vout/68000, KCL del seguidor añade (Vout−VbaseQ18)/68000.
El Jacobiano contiene ambos términos cruzados −1/68000 S.
Evaluar componentes low mediante el mismo Taylor de primer orden ya
declarado en la voz. No omitir la corriente CR6 del puerto de reset.

Usar exactamente las400 coordenadas high/low del checkpoint abierto
de62,5 ns a5,25 ms. Preparar únicamente cinco incógnitas algebraicas
con la carga Q18 entrante; no recalcular las cargas de VCO/cadena.
C2 impuesto en0,8469345758149237/3,2/6 V, reset impuesto0,01/0,7 V,
alimentación9,3 V. Son escenarios heredados de laboratorio, no fases,
umbrales ni ajuste de un contorno identificado. Las corrientes positivas
hacia el circuito son I_C2=(Vc2−B3)/10000 A e
I_reset=−Is·expm1((F−Vreset)/(n·VT)) A.

Doce trayectorias de2 µs desde esa misma memoria, pasos fijos Radau
h=125/62,5 ns (16/32 pasos). No controlador adaptativo ni prueba de
conmutación causal del biestable. Cada solve recibe historial inmutable;
publicar sólo su candidato aceptado. Repetir el primer solve por bits.
Archivar primer/último par completo y finales high/low. Refinamiento de
todo el estado:2 µV, corrientes desconocidas2 nA. Contrastar cada etapa
seleccionada con Decimal100 VCO y KCL Python/FD de la cadena/seguidor,
gates previos2e−11 A /2e−10 V y corrección1 µV /1 nA.
Contrastar también las dos corrientes expuestas y R59 a1 nA.

Compilar sólo llamador/módulo de laboratorio contra la biblioteca congelada;
248 tests Rust heredados por identidad, cero nuevos tests de biblioteca.
Presupuestos: compilación120 s, ejecución300 s, oráculo300 s, reserva
de disco1 GiB con salida estimada16 MiB y stack32 MiB. Conservar fallos,
fuente exacta y replay antes de cualquier reparación. No cambiar gates.
Sin nuevo audio, ADSR completo, identificación física ni admisión RT.
