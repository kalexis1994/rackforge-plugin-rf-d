# Recuperación y par de entrada mediante puertos no lineales

2026-11-06. Resultado experimental, SVC-9 Fig.9-11 p.13, R61=200/L1,
R14=25k, cutoff fijo .49/.50/.51, loudness1/2=2 V. Entrada de laboratorio
U=a*(sin(2*pi*137*t)+.3*sin(2*pi*1103*t)),4 ms desde DC. No H128,
contornos, cambio dinámico de cutoff o unidad física. [Adopción CA-72](CA72_ADOPCION.md).

## Qué cambió

La recuperación Q8/Q6/Q7/Q5 y después Q29/Q30 usan las mismas curvas
Ebers–Moll que el circuito completo. Se resuelven12 uniones, manteniendo
los18 voltajes de capacitor y todos los puertos; el resto de dispositivos
conserva G local. Las matrices se calculan fuera del procesamiento.
SDIRK2 conserva dos etapas implícitas. El estado lleva también historia y
defectos derivados para lectura/predicción; no son capacitores nuevos.

Se reutilizaron las reservas ya existentes, sin ajuste de parámetros ni
nuevas campañas de muestras. El corpus conserva todos los puertos sobre
la rejilla y estados completos dispersos: la aceptación nodal aquí cubre
esas filas, no los estados de68 nodos ya retirados entre ellas.

| Ensayo | Resultado |
| --- | --- |
| Recuperación sola,8 uniones | .01 V pasa; .1 V rechaza en TAIL, ~2.32 uV;1 V rechaza |
| Recuperación + entrada,12 uniones,250 ns | .01 y.1 V pasan en los tres cutoff;1 V sigue rechazado |
| Implementación384 kHz, a=.1 V | Máximo nodal conservado .878/.924/.968 uV; RMS relativo J7 ~.0000620/.0000641/.0000655 |
| Identidad nativa de leyes y Jacobiano |64 perturbaciones por variante; coincidencia dentro de gates originales |
| Solve compacto frente a Newton68 híbrido |48 etapas por variante; gates1 nV,1 pA y10 pV de carga pasan |
| Rust frente a Python completo |4611 pasos por variante; nodos<=1e-10 V, puertos<=1e-14 A, cargas<=1e-11 V |

Las lecturas a250 ns desde Rust384 kHz usan una integración parcial desde
su propia carga y entrada interpolada, sin sembrar estados del oráculo ni
interpolar nodos rápidos. Constituyen auditoría del método, no admisión
adicional de FIR o audio continuo. El gate nodal1 uV y los gates anteriores
de corriente/audio no cambiaron.1 V, cutoff dinámico y controles generales
permanecen fuera de admisión.

## Coste y corrección acotada

Se mantuvieron ambas mediciones1200 bloques de1024 pasos384 kHz más FIR
para128 muestras48 kHz, primer bloque incluido. Primer bloque produce80
frames por la latencia384 del FIR; los siguientes producen128. Ninguna
reserva de coste excluye ese arranque. Entrada y cronómetro fuera del DSP.

| Solve | Mediana/bloque | P99 | Máximo | Deadlines >2.667 ms |
| --- | --- | --- | --- | --- |
| Newton12 completo |3.5792 ms |3.8306 ms |4.8839 ms |1200/1200 |
| Newton modificado, bloque6 |1.8720 ms |2.7926 ms |2.9515 ms |29/1200 |

La segunda versión utiliza seis derivadas BE como precondicionador, pero
evalúa las doce leyes BE/BC y exige el mismo residual2e-13. No elimina la
corriente inversa. Ambas variantes pasan igualdad de implementación,
puertos por bits, cero heap y24 rechazos/retry atómicos ensayados cada una,
incluido agotamiento del presupuesto. El coste mejora ~48%, pero NO pasa
el objetivo50% ni todos los deadlines. La voz completa sigue sin admisión RT.

Se conservan un fallo del adaptador Python (dimensión de perturbación),
su replay sin cambios; un fallo del parser de frames80/128, su banco
repetido sin cambios; y un error de compilación del buffer6, repetido antes
de corregirlo. El análisis del coste original usa su PRIMER banco, no el
replay más rápido. Los recibos conservan versiones de fuente por bytes.

## Evidencia y siguiente decisión

Protocolos previos: [recuperación](RECOVERY_PORT_PROTOCOLO.md),
[entrada](RECOVERY_PORT_INPUT_PROTOCOLO.md), [coste](RECOVERY_PORT_COSTE_PROTOCOLO.md).
Recibos: [8 uniones](../evidence/recovery_port_model01.json),
[12 uniones](../evidence/recovery_port_input_model02.json),
[Rust original](../evidence/recovery_port_native01.json),
[auditoría original](../evidence/recovery_port_analysis01.json),
[Rust compacto](../evidence/recovery_port_fast_native03.json),
[auditoría compacta](../evidence/recovery_port_fast_analysis01.json),
[QA](../evidence/recovery_port_tests01.json).

El próximo bloque debe reducir el trabajo de integración/solve con estas
leyes como control y mantener las reservas. La extensión física siguiente
son los pares restantes del ladder y el convertidor, antes de1 V/cutoff
general. No se modifica el motor de escucha ni se genera otro WAV. El
corpus previo,8769 inputs y fuentes originales se conservan; no hay nuevo
árbol Cargo, SPICE o carpetas de muestras. Binarios temporales retirados.

La QA también conservó un rechazo de comparación literal de tracebacks: el
replay tenía otro lugar de llamada, pero la misma excepción del fixture.
La corrección compara la excepción final y conserva ambas trazas completas.
