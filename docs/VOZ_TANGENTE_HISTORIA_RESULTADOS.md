# Tangente temporal respecto de la memoria anterior

2026-10-10. Model D clásico CA3046, misma escena de los ciclos corregidos.
[Protocolo original](VOZ_TANGENTE_HISTORIA_PROTOCOLO.md),
[perturbación menor](VOZ_TANGENTE_HISTORIA_FINA_PROTOCOLO.md),
[política escalada](VOZ_TANGENTE_HISTORIA_ESCALADA_PROTOCOLO.md),
[nativo admitido](../evidence/voice_history_tangent_native05.json),
[contraste independiente](../evidence/voice_history_tangent_reference01.json)
y [QA](../evidence/voice_history_tangent_tests01.json).

## Paso implementado

El helper de laboratorio forma Hx en coordenadas absolutas de etapa:
`Hx=−Σj Bij M(x)/h`. Resuelve `J·dY=−Hx·u` con el Jacobiano del paso.
En coordenadas incrementales se necesita `dδ=dY−u`; no se trata de
otra derivada del cierre estático. Se conservan cargas de junturas,
capacitores y memorias internas de corriente del macromodelo.
Estas últimas no identifican inductores físicos del instrumento.

Se compila solamente el caller. La biblioteca, sus leyes y Newton siguen
idénticos por hash. El solver de laboratorio copiado conserva por texto
la eliminación admitida del banco anterior; el contraste lineal usa
NumPy y Jacobianos independientes.

## Cobertura y resultados

48 pasos: dos memorias/dos resoluciones, primer paso, ambos resets y final,
cada uno con full/mid/end. Los pasos seleccionados abarcan
3.05175781e-11–1.5625e-08 s;
no representan todos los pasos aceptados de aquellas trayectorias.
Las 48 repeticiones de Newton reproducen ambos candidatos e incrementos
por bytes. 9600 columnas de historia/3.840.000 entradas analíticas,
7.680.000 entradas FD a dos tamaños; 432 direcciones de respuesta,
172.800 coordenadas de etapa y 1728 solves perturbados nuevos.

| Contraste | Peor ratio frente a gate 1 |
|---|---:|
| Hx: masa independiente | 0.00011213015 |
| Hx: diferencias centrales | 0.0252121399 |
| Respuesta: Jacobiano independiente | 0.00913367945 |
| Respuesta: solves perturbados | 0.00221362265 |

La fuga máxima de candidatos al variar historia/compensar incrementos es
1.97215226e-26 por ε,
gate 1e-18. Los 48 controles negativos de corriente algebraica 98 tienen
Hx y respuesta exactamente cero. Todas las filas y columnas se conservan,
incluidas las de corriente, con unidades de fila/columna.

El oráculo arma M desde las leyes Decimal100 del VCO y las incidencias
de carga de cadena, reduce BUS/índices y aplica Radau. Para las respuestas
arma el Jacobiano absoluto de ambas etapas y resuelve sus nueve RHS.
Las coordenadas de tensión y corriente usan gates distintos. Su evaluación
usa candidatos nativos; no produce nuevas raíces no lineales independientes.
El Jacobiano DC de cadena conserva la interfaz FD/binary64 heredada.

## Rechazos preservados y escala

Los intentos [01](../evidence/voice_history_tangent_native01.json) y
[02](../evidence/voice_history_tangent_native02.json) conservan errores de
compilación y replays: export privado del solver y declaraciones ajenas
copiadas con la función. Se usa finalmente la función de laboratorio
admitida, sin modificar ni recompilar la biblioteca.

[03](../evidence/voice_history_tangent_native03.json) y
[04](../evidence/voice_history_tangent_native04.json) conservan fuentes,
binarios parciales y replays: NoDecrease/IterationBudget al perturbar la
memoria L2 en pasos finales de 61/30,5 ps. No se atribuyen a fidelidad,
componentes físicos ni una causa universal del solver.

El intento 05 fija una selección de entrada antes del nuevo contraste:
limitar el cambio lineal previsto de ambas etapas a 10 µV/10 nA.
Para la dirección L2, ε queda entre 3.07773735e-16 y 1.470441e-13 A.
Su magnitud varía con el paso y se guarda en el codec RFJHIST2; el auditor
recalcula la política. Hx a etapas fijas conserva las perturbaciones
originales. Los gates de derivada/respuesta nunca se amplían. El tamaño
FD y su refinamiento no son una cota continua del error de trayectoria.

## Alcance y siguiente implementación

Se admite la respuesta local de estos pasos a h fijo. HIGH/LOW conserva
las evaluaciones de LOW a primer orden del kernel; este contraste finito
no deriva cada redondeo del codec. 248 tests Rust heredados, no reejecutados;
sin nuevos tests Rust, audio, SPICE, cambio de circuitos, fidelidad o RT.

Siguiente: propagar RHS de memoria por las etapas aceptadas usando una
factorización común; contrastar la propagación con historias perturbadas.
Separar primero el recorrido con calendario fijo del motor adaptativo.
La fase interpolada y el tiempo de retorno tienen su propia dependencia;
incluirla antes de formar el Jacobiano del mapa de retorno. No usar esta
respuesta local como corrección periódica ni afirmar asentamiento.

## Recursos

Intento admitido: 53.146269 s, compilación≤120 s/ejecución≤600 s,
900 s globales, stack 32 MiB. Reserva 1 GiB + 96 MiB estimados,
disco cada 250 ms, stop cooperativo. Preservar todos los outputs y
checkpoints anteriores; no se comprime ni borra evidencia en este bloque.
