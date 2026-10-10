# Tangente de un paso respecto de su historia

2026-10-10. Model D clásico CA3046, escena y biblioteca de los
[ciclos corregidos](VOZ_CICLOS_CORREGIDOS_PROTOCOLO.md). No cambiar física,
solver, controles ni las 48 etapas seleccionadas de aquellos cuatro perfiles.

## Derivación y alcance

Con estados absolutos de etapa Yj y memoria x, el residuo es
`Ri=f(Yi)+Σj Bij [Q(Yj)-Q(x)]/h`. Su Jacobiano respecto de Y es el
Jacobiano ya usado por Newton. Con Y fijo, `Hx=−Σj Bij M(x)/h`;
las sumas de filas de B son +2 y −2. Para una dirección u, resolver
`J·dY=−Hx·u`. El endpoint es Y2. En coordenadas incrementales,
`dδ=dY−u`: omitir esa diferencia pierde la dependencia de historia.

M incluye los 18 capacitores de cadena, capacitores, cargas de junturas
y memorias de corriente del macromodelo del generador. Las últimas no son
componentes identificados del instrumento. Las fuentes quedan fijas.
HIGH/LOW del kernel evalúa componentes LOW a primer orden; contrastar ese
dominio finito y no declarar derivada exacta de todo el codec binario.

## Banco fijado antes de medir

48 pasos: full/mid/end de primer paso, reset 1, reset 2 y final, ambas
memorias y ambas resoluciones. Preservar old y los dos incrementos exactos.
Repetir el solve original y exigir ambos candidatos e incrementos bit exactos.

Contrastar las 200 columnas de Hx a perturbaciones centrales de historia:
10/5 µV en coordenadas V y 10/5 nA en coordenadas A (98..132). Compensar
los incrementos para conservar Y. Registrar la fuga de los candidatos;
gate de fuga por perturbación 1e-18. Todas las 400 filas a ambos tamaños.

Oráculo independiente: M(x) de las leyes Decimal100 del VCO y el inventario
de cargas de la cadena, luego la reducción de índices y los pesos Radau.
Gate Hx nativo: `2e-12+2e-9·|referencia|`, en unidad de fila/columna.
Gate FD Hx: `2e-9+1e-6·|referencia|`, misma unidad. Conservar también la
diferencia entre los dos tamaños, sin interpretarla como cota continua.

Nueve direcciones unitarias de historia: 43 (rampa), 5 (JFET), 12 (BUS),
139 (entrada C27), 199 (C10 izquierda), 194 (J7), 157 (cadena 24),
117 (corriente L2 del macromodelo IC1), 98 (corriente algebraica, control
negativo). Resolver dY de las dos etapas. Contrastar con Jacobiano de
etapa independiente y con cuatro solves perturbados por dirección.
Comparar cambios `ε·dY`: gate `1e-8 V/1e-11 A + 1e-4·|cambio|` por
coordenada de salida, conservando ambos tamaños y signos. Para 98 exigir
Hx y dY exactamente cero. Los nuevos solves usan los gates originales.

Este banco acredita solo respuestas de pasos a h fijo. No incluye la
elección adaptativa de paso, derivada del tiempo/fase del evento, propagación
de un periodo entero, Jacobiano periódico ni una nueva memoria corregida.

## Recursos y preservación

Solo caller contra biblioteca congelada: 120 s de compilación, 600 s de
ejecución/900 s globales, stack 32 MiB. Reserva 1 GiB + 96 MiB estimados,
control de disco cada 250 ms y stop cooperativo. Conservar fuente, outputs
parciales y replay antes de reparar. Proteger QA anterior, 2707 fuentes y
6940 archivos privados. Sin audio, SPICE, nuevos tests Rust, cambios de
circuito ni admisión de fidelidad física/RT.
