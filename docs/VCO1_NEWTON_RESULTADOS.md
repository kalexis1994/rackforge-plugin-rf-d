# VCO1: solve conjunto y continuación nativa corta

2026-10-07. Pasó el [protocolo](VCO1_NEWTON_PROTOCOLO.md).
El [Newton](../crates/rf-d-circuit/src/vco1_newton.rs) resuelve las 134
filas del [ensamblaje completo](VCO1_STAMP_RESULTADOS.md), conservando
BJT/JFET, ambos 741, sus memorias y cargas. No modifica algoritmos anteriores.

## Fronteras y estado

DC condicionado de arranque C1=0 explícito, con corriente reconstruida
Istartup=-KCLoriginal. La restricción sólo puede existir en Mode::Dc.
Los pasos Euler libres conservan todas las KCL y no imponen rampa,
frecuencia, reset o timer. La memoria entrante queda fija durante todos
los trials. Sólo un solve aceptado devuelve el estado completo candidato.
Presupuesto64/24, Armijo1e-4 sobre corrección, gates finales de residual
y corrección separados. Eliminación existente con pivotes escalados:
sólo salta coeficientes exactamente cero.

## Banco y resultados

[Referencia independiente](../evidence/voice_vco1_newton_reference01.json):
dos raíces DC desde referencias SPICE anteriores perturbadas 10 uV/1 nA,
seguidas por C4 10/100 pF × dt125/250/500 ns durante **8 us**. 64/32/16
pasos por perfil: **224 pasos**, seis historias completas separadas.
Referencias por incidencias Decimal100 y pivotes absolutos; las primitivas
conservan su interfaz binary64. No se afirma precisión Decimal100 de
todo el estado después de esa interfaz ni se usa Rust como oráculo.

[Producción](../evidence/voice_vco1_newton_native01.json) inicia cada
perfil desde su propio DC resuelto y transporta únicamente sus candidatos
aceptados. Todos los voltajes/corrientes se comparan a igual dt y paso.

| Medición | Máximo |
|---|---:|
| Diferencia de voltajes frente a referencia | 1,9539925233e-14 V |
| Diferencia de corrientes de ramas | 6,9388939039e-18 A |
| Iteraciones en DC/pasos del banco | 3 |
| Trials por solve | 2 |

Pasaron gates1e-13 A/1e-11 V y corrección2e-9 V/2e-12 A en cada
candidato, balance de KCL/masa y corriente de arranque. También repetición
pura, presupuesto mínimo rechazado, retry desde la misma entrada y
rechazos de estado/control/dt/frontera sin mutación o candidato parcial.
Test aislado: **128 solves encadenados, cero asignaciones**. Compilación
O2 y compiler/binarios/comandos por hash; no benchmark de deadline.

Tres tests nuevos pasan al primer intento, sin fallos nuevos ni SPICE
nuevo. La referencia corta parte de semillas SPICE de laboratorio:
**no admite semilla propia, arranque desde cero o DC libre**. Los 8 us
no cubren un periodo/reset. No admiten frecuencia estacionaria, formas
periódicas, refinamiento temporal, calibración o una nueva escucha.

## Admisión y siguiente bloque

[QA de publicación](../evidence/voice_vco1_newton_tests01.json):
**220 controles, tres nuevos y 217 heredados por identidad**. Reconstruye
los 224 pasos y ambas raíces independientes, conserva fuentes medidas,
verifica snapshots y entradas públicas/privadas. No reejecuta tests heredados.

Admite solve conjunto y continuación corta en la frontera declarada.
Sigue semilla/arranque propio robusto y trayectoria de ciclos completos,
con refinamiento y controles reservados. Después transferir R6/R45 al
mixer activo. DC libre y arranque calibrado rechazados siguen pendientes,
la nota larga anterior sigue rechazada, física/RT/producto siguen abiertos.
