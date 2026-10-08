# Radau cargado: los dos pisos recuperados y siguiente reset atravesado

2026-10-08, base99dd80a. [Protocolo de etapas/cargas](VCO1_RADAU_PROTOCOLO.md), [extensión acotada](VCO1_RADAU_CONTINUACION_PROTOCOLO.md) y [reconstrucción del puerto](VCO1_RADAU_PUERTO_PROTOCOLO.md). CA3046 nominal, 25 °C, C4=10 pF, controles y carga de mixer impuestos. Kernel Rust privado y oracle Decimal100 propios; tarjetas físicas y crate de producción intactos. No nuevo SPICE/audio.

## Etapas acopladas

Radau IIA(3) resuelve ambas etapas con 268 ecuaciones, F_i+Σ B_ij·ΔQ_j/h=0. A⁻¹=B tiene coeficientes binary64 exactos 1,5/0,5/−4,5/2,5. Conserva las cargas no lineales, cuatro flujos inductivos, hi/lo y restricciones individuales sin forzar filas algebraicas. Historia fija durante todos los trials; sólo etapa2 es endpoint. Stage order2 y condiciones de orden3 verificadas con fracciones exactas; no garantizan ese orden global para esta DAE. [Fuente/derivación](../evidence/voice_vco1_radau_method01.json): PDF primario guardado privado por hash, no copiado al repo. Jacobiano cuasi-Newton y corrección de primer orden en lo heredados y declarados. Newton/masa/corrección mantienen gates anteriores.

El [banco01](../evidence/voice_vco1_radau_probe01.json) pasa ocho tríos desde los dos últimos estados rechazados por SDIRK, half7,62939/15,2588/30,5176/61,0352 ps. **48 raíces internas** contrastadas, error nodal máximo2,58608e−11 V, gates2e−7 V/2e−10 A. Los ocho errores locales pasan en todas las 134 incógnitas, sin Richardson o división por7. En los dos mínimos, ratios0,02116424684 y0,01440660269, frente a rechazos SDIRK superiores a1. Los máximos de esos dos tríos son otros nodos internos de IC1; no se omite XIC3.7 del control.

## Continuaciones con reloj real

Cumplido el requisito previo, **1 µs adicional** desde la segunda historia completa con1830 endpoints, min15,2588 ps, max15,625 ns y LTE máximo0,999926144. Las cuatro observaciones fijadas aportan ocho raíces independientes admitidas. No es una trayectoria independiente completa o una nota musical.

La [extensión serial01](../evidence/voice_vco1_radau_continuation01.json) empieza desde el mismo endpoint anterior en ambos perfiles y completa3 ms adicionales:

| Máximo de medio paso aceptado | Endpoints | Mínimo efectivo | LTE máximo | Cruce ascendente C1 por−2 V |
|---|---:|---:|---:|---:|
| 500 ns | 9078 | 15,2588 ps | 0,999449637 | 2,433210983918841 ms |
| 250 ns | 15006 | 15,2588 ps | 0,999449931 | 2,433210983918851 ms |

Cada perfil exporta ambas etapas y memorias completas: 542 columnas, 9079/15007 filas incluyendo historia inicial, reloj exacto y todos los gates. RAMP_C1 cubre aproximadamente−3,99021..−0,000636231 V; el cruce prefijado confirma que atraviesa el siguiente reset. Ocho intervalos reales (cuatro por perfil) añaden16 raíces contrastadas. Cero abortos o replays de estas campañas; preflight y reserva de disco pasan. El cruce cercano entre perfiles no sustituye el banco de periodicidad, refinamiento de frecuencia, carga/corrientes de ciclo y arranque propio.

## Puerto y aporte derivativo conservados

La [auditoría](../evidence/voice_vco1_radau_ports01.json) reevalúa **72 etapas seleccionadas** (48 banco, ocho continuación1 µs, dieciséis perfiles3 ms), correcciones independientes de las268 filas y retorno al suelo. Reconstruye **144 identidades** de base Q2/memoria L2 (dos tarjetas por etapa). Ambos estados internos participan en la derivada Radau; no reemplazar el término por una ganancia o una diferencia Euler. Las seis comprobaciones racionales de R(z) coinciden con (1+z/3)/(1−2z/3+z²/6). Etapas/locales/retornos admitidos no acreditan todas las muestras contra una trayectoria independiente.

La condensación exacta del bloque anterior mantiene sus propios resultados y rechazos Euler/SDIRK. Esta discretización distinta recupera los dos pisos y cruza otro reset con el mismo modelo/gates. No atribuir toda la mejora a un único polo o declarar identidad física de un 741 vintage. Pila8 MiB y CLI con archivos/Vec son de laboratorio; heap y deadlines del método nuevo no están medidos.

## Identidad del recibo y siguiente puerta

El recibo inicial reutiliza el literal de schema legado `charge-sdirk-local-probe/v1` del adaptador anterior. Sus fuentes/compilación, B, raíces y exports identifican inequívocamente Radau; el recibo se conserva por bytes exactos. Antes de publicación se guarda la versión medida del helper en el snapshot y se corrige sólo ese literal y su comprobación de mínimo4 ticks (antes8, todos los endpoints medidos usan≥8). Sin rerun físico o reinterpretar resultados; QA verifica los dos reemplazos exactos. El snapshot también conserva las portadas y política LF anteriores.

Siguiente: arranque propio con Radau, varios períodos completos y banco temporal/corrientes/refinamiento bajo gates existentes, después carga activa con R6/R45 transferidos una sola vez. Estas continuaciones parten de historia heredada de Euler/SDIRK, perfil10 pF único; no admiten DC libre, osciladores2/3, frecuencia calibrada, fidelidad física, voz completa o un WAV nuevo. La [QA](../evidence/voice_vco1_radau_tests01.json) hereda235 tests por identidad; cero nuevos tests unitarios o ejecuciones heredadas, y no cuenta las72 etapas o sus reevaluaciones como tests Rust.
