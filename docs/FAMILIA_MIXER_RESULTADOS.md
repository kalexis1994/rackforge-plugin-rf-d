# Acoplamiento condicional de familia, mezclador y C27

2026-10-24. [Protocolo previo](FAMILIA_MIXER_PROTOCOLO.md),
[banco completo](../evidence/family_mixer_complete01.json),
[continuaciones H128](../evidence/family_mixer_native128_01.json),
[raíces independientes](../evidence/family_mixer_steps01.json) y
[QA](../evidence/family_mixer_tests01.json).

## Dominio efectivamente contrastado

CA3046/SVC-204D y panel SVC-9 pp.5/19; C27 de entrada, Fig.9-11 p.13.
Tres CV de placa -2.6/-1.6/-.6 V y dos cargas: OSC1+EXT ON, o las cinco
ramas ON. Otras fuentes ideales a cero; potenciómetros .5; BASE_Q29
impuesto a 0 V. R45=33k una sola vez, C27=10 uF, mismos trims/temperatura
del bloque anterior. BUS libre conserva su carga. Estas ramas restantes
no representan otros osciladores autónomos o ruido real. No hay hardware.

El oráculo integra VCO completo, panel y capacitor durante 30 ms.
El reducido continúa los dos ciclos finales desde el mismo BUS/C27
observado en un reset real, con fase cero. No es arranque propio del
reducido ni historia independiente. CV y BASE siguen fijos; el pequeño
BUS resultante permite contrastar la aproximación cuasiestática sólo en
estas ventanas, no cargas variables arbitrarias o el filtro completo.

## Resultados y publicación de estado

Seis escenas, doce continuaciones 500/250 ns. Todas pasan:

| Máximo reducido/oráculo | Resultado | Gate |
|---|---:|---:|
| Frecuencia | 0.0853234 cent | 1 cent |
| BUS DC/norma armónica 1..8 | 5.68515 uV | 10 uV |
| Corrientes panel/otras/C27/KEYBOARD | 0.857629 nA | 2 nA |

Saw/tri/pulse pasan DC <=5 mV y vector armónico <=2%; IC1_SUM <=10 uV.
KEYBOARD se compara con i(VKEYBOARD) usando su signo de fuente; el API
de la familia conserva corriente entrando al circuito. Método y paso
del oráculo se contrastan por separado. No retirar DC, normalizar ganancia
o alinear más allá de los resets reales de cada historia.

Trapezoidal implícito de fase y carga C27, incrementos compensados HIGH/LOW;
residual <=1e-13 A y corrección <=1e-12 V. Todos los perfiles pasan balance
de carga, KCL y cero heap medido en los pasos. Tres rechazos por perfil
(presupuesto cero, CV no finito y carga inválida) dejan estado intacto;
el retry válido coincide por bits. Es control de publicación, no deadline RT.

[Auditoría](../evidence/family_mixer_steps01.json): 24 pasos aceptados
contrastados por bisección independiente, sin sembrarla con la raíz nativa;
BUS <=1e-12 V y fase <=1e-10 ciclos. Derivadas del residual y ley original
de C27 pasan. MNA independiente de las ramas del panel conserva R45 una
vez. Controles negativos de duplicar R45 e invertir corriente C27 son
detectados. Son raíces reducidas, no nuevas filas del VCO completo.

## Rechazos y correcciones conservados

1. El primer chequeo de KCL incluía t=0, donde .ic fuerza BUS mientras
   el OP asigna corriente cero al capacitor. El
   [diagnóstico](../evidence/family_mixer_start_diagnostic01.json) identifica
   ese punto; el mismo gate 1e-10 A pasa en la ventana tardía declarada.
   [Fallo/replay](../evidence/family_mixer_oracle01.json) guardados.
2. Gear125 completa tres escenas y aborta -1.6/L1 a 11.277 ms.
   [Gear62.5 y Trap125](../evidence/family_mixer_methods01.json) también
   abortan. No se admiten esos prefijos ni se altera C27 o el JFET por
   el mensaje de error. Los prefijos parciales se retiraron sin digest;
   sus estados no son reanalizables, aunque deck/log/fuente/replay sí están.
3. [Coordenada exacta](FAMILIA_MIXER_COORDENADA.md): z=(BUS-BASE)/.01,
   Cestado=1 nF y transferencia ideal recíproca de tensión/corriente.
   Se preservan carga física, energía y corriente original de C27.
   El [control](../evidence/family_mixer_scaled_control01.json) coincide
   con una escena directa que ya pasaba y completa la antes rechazada.
   Componentes activos, tolerancias y gates iguales. El banco final reusa
   tres casos directos y uno escalado; agrega dos CV altos y dos contrastes
   de método/paso, sin copiar sus ventanas. Una convergencia diferente
   no significa una física diferente.
4. [H64](../evidence/family_mixer_native01.json) pasa pasos, ondas y
   corrientes, pero rechaza BUS DC: 11.45 uV frente a 10 uV. Replay y
   estados conservados; ese candidato no queda admitido por el promedio
   de otras métricas. [H128](FAMILIA_MIXER_BANDA.md) deriva sólo de las
   mismas ocho ventanas entrenadas, con los primeros 65 coeficientes
   idénticos por bits. No reajusta con la reserva. El capacitor conserva
   área del reset que la representación H64 no reproduce suficientemente.

## Evidencia, límites y siguiente paso

Ventanas exactas float64 con contexto, streams completos por digest,
fuentes y búsquedas congeladas en recibos. Prefijos retirados sólo
regenerables; no archivo de todos los estados internos. Una sola área
temporal vacía al terminar, sin Cargo, nueva rlib, cache o WAV. Biblioteca
activa, datos H64 admitidos y escucha anterior permanecen por hash.
El QA hereda los 272 tests anteriores por identidad, sin reejecutarlos
ni sumar ensayos como unit tests. El bloque respeta 32 MiB sin QA.

Se admite el acoplamiento H128 condicional de estas seis escenas, con
memoria compartida al inicio. No la voz con filtro, una familia general de
CV temporal, el arranque reducido, RT o fidelidad audible a un vintage.
Siguiente: conectar BASE_Q29 a la entrada real del filtro y contrastar
la carga devuelta por la cadena. CV temporal conserva una admisión aparte.
