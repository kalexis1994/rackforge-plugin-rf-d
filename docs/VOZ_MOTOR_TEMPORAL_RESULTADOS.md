# Motor conjunto: error temporal y continuación corta

2026-10-08. [Protocolo previo](VOZ_MOTOR_TEMPORAL_PROTOCOLO.md).
[QA vigente](../evidence/voice_joint_engine_tests01.json).

## Qué se incorporó

`joint_engine` llama al circuito VCO1→BUS→cadena sin modificar sus leyes.
Mantiene200 coordenadas high/low, parámetros, ajustes, reloj y propuesta
en el checkpoint. Compara un paso completo con dos medios pasos desde la
misma historia y publica solamente el segundo endpoint admitido. No aplica
Richardson. Antes de publicar obtiene también las observaciones de ambos
medios pasos; C27 usa su derivada Radau y el BUS cierra sus corrientes.

El estado inicial es condicionado: arranque VCO con C1=0 más historia
anterior de cadena, levantando su BUS al del VCO. Desde allí, la historia
posterior la genera el solver conjunto. Los controles y las otras fuentes
son constantes. No se obtuvo todavía DC propio de toda la voz.

## Mediciones

[Tres tests nativos](../evidence/voice_joint_engine_native01.json) pasan:

| Objeto | Resultado |
|---|---|
| Cuatro perfiles | Otros puertos omitidos/impuestos ×medio máximo125/62,5 ns |
| Reloj final exacto | 1048576 ticks =2 µs en cada perfil |
| Intervalos admitidos | 17/23/17/23;80 en total,160 medios pasos publicados |
| Máxima fracción de puerta LTE local | 0,9287994255, puerta <=1 |
| Refinamiento al mismo reloj | Máxima fracción7,164493e-4 de2 µV/2 nA |
| BUS, incidencia R45/C27/otras fuentes | Peor balance2,033e-20 A; puerta1e-12 A |
| Restore y continuación | Cuatro replays exactos de estado, incrementos y observaciones |
| Rechazos | Dos objetivos inválidos, seis checkpoints inválidos y rollback por LTE |
| Heap | Cero asignaciones en una aceptación mínima y un rechazo por objetivo inválido |

Los80 intervalos excluyen las cuatro continuaciones de replay duplicadas.
Un intento con carga externa de−4 V de1 A, dominio de laboratorio heredado,
converge en Newton pero falla LTE con razón17397,1357 y presupuesto1.
El rechazo conserva estado, parámetros, propuesta y reloj. Esta escena
comprueba rechazo; no admite ese control extremo como perfil físico.

La primera aceptación requiere reducir la propuesta inicial. El conjunto
acepta un intervalo de7,8125 ns; no se fuerza a pasar con el máximo inicial.
El último intervalo se recorta al reloj objetivo. La prueba aislada de heap
acepta8 ticks =15,2587890625 ps, con medios de7,629 ps; no es una trayectoria
completa a ese paso mínimo.

El [oráculo nodal independiente](../evidence/voice_joint_engine_reference01.json)
comprueba las24 etapas seleccionadas de full/mid/end del comienzo y final
de los perfiles de máximo125 ns:4.800 ecuaciones. También reconstruye
en Decimal100 cuatro diferencias temporales y la historia compartida.
Evalúa puntos nativos; no cuenta como raíces independientes desde otra semilla.
Máxima fracción de puerta residual2,834e-6; corrección lineal máxima
1,316e-14 V/5,861e-18 A. Conserva las puertas del oráculo anterior.

Compilación y tests tardaron8,35 s en esta ejecución; tests3,87 s.
Stack de laboratorio32 MiB. No se extrapolan estos tiempos a deadlines
ni se convierte la medición parcial de heap en una garantía de todo el motor.
Todos los inputs y binarios quedan ligados por SHA256; no hubo fallos
en los dos procesos nuevos de validación ni nuevas ejecuciones SPICE.

## Límite y siguiente avance

El motor ya controla error temporal y memoria conjunta en una continuación
de2 µs. Esto no alcanza un periodo ni demuestra un reset completo bajo
carga, una nota musical, fidelidad vintage o tiempo real. No se produjo
nuevo audio. Siguiente: ampliar la trayectoria hasta el primer reset/ciclo
con carga activa, conservar trazas y contrastar checkpoints y refinamiento
antes de preparar una escucha de la cadena.
