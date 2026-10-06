# La fila equivalente falla el control completo

2026-10-06. Se ejecutó el [protocolo congelado](741_FILA_REDUCIDA_PROTOCOLO.md).
Los [tres recibos](../evidence/voice_741_row_runs01.json) y la
[auditoría](../evidence/voice_741_row_validation01.json) conservan fuentes,
ejecutable, runtime, decks y exportaciones. La auditoría reproduce los gates
sin nuevos solves. **La variante queda rechazada; BUS variable activo no se mide.**

## Qué cambió

Sólo se reemplaza la fila de rama de `l.xic3.l2` mediante una combinación
invertible de las KCL de 16/17, dividida por la escala declarada:
`v98-v16+(req+1/gR)*gm*(v3-v49)=veq`.
Se mantienen L2, R13, G4, EOS y las contribuciones terminales de corriente.
gR/gm se obtienen de los dispositivos reales; conexiones y activación se
comprueban en setup. Los nuevos elementos dispersos sólo existen al habilitar.

Cuatro archivos C/header del dispositivo inductor cambian en una copia
separada. Se recompila el módulo completo por el cambio de estructura privada.
El prefijo de INDload que calcula/publica flujo y llama a NIintegrate conserva
exactamente su texto; su hash está en la auditoría. La historia, arranque,
truncamiento y recuperación permanecen en el código original. La operación
de fila cambia la representación numérica, sin afirmar identidad binary64.

Cinco pruebas racionales verifican filas arbitrarias, raíz DC, estados Gear
1/2 con historial real compartido, escala y signos. Cuatro pruebas de control
rechazan voltajes/DC fuera de gate y relojes parciales. Esas comprobaciones
no sustituyen la trayectoria completa del VCO.

## Resultado y parada

| Ejecución | Filas / último tiempo aceptado | Gate |
| --- | --- | --- |
| Variante desactivada, BUS cero | 219538 / 40 ms | Exacta al baseline anterior |
| Variante desactivada, BUS variable | 7724 / 2.277414365034117 ms | Mismo prefijo/rechazo, exactamente igual |
| Variante activa, BUS cero | 7733 / 2.2774109959695487 ms | Rechazada: control de 40 ms incompleto |

El control activo informa `Timestep too small` y señala `jq7_left`, con
paso final reportado de 6.25e-19 s. El proceso devuelve exit code 0, pero
el runner registra aborto, reloj parcial y `trajectory_complete=false`.
El primer punto de los cinco voltajes y la corriente de puerto es idéntico
al control; ese punto no admite los 40 ms posteriores.

No se calculan los gates de forma/frecuencia/eventos de un control completo
ni se mide BUS variable activo. No se ajusta escala, tolerancia o componente
para rescatar este resultado. Se preservan los tres runs y ambos builds.

## Alcance y siguiente contraste

La equivalencia exacta de filas y la conservación del código de memoria son
necesarias, pero esta variante empeora la cobertura temporal del control.
El experimento no demuestra por sí solo la causa: cambia coeficientes,
escalado y estructura dispersa dentro de un sistema no lineal realimentado.
La [amplificación diagnosticada anteriormente](KCL_741_RESET_RESULTADOS.md)
sigue siendo una observación local; no admitía esta transformación.

El siguiente [protocolo de matriz completa](NEWTON_MATRIZ_COMPLETA_PROTOCOLO.md)
capturará A, RHS y soluciones del build original y contrastará el sistema
lineal observado con mayor precisión antes de otro cambio de representación.
Separará error del solve lineal, evaluación de dispositivos y convergencia
no lineal. El ejecutable oficial conserva otra trayectoria.

Pasan [50 regresiones enfocadas](../evidence/voice_741_row_tests02.json).
Los inputs físicos anteriores, ejecutable oficial y WAV conservan sus hashes.
No hay tarjeta promovida, unión VCO/contorno admitida, audio nuevo o tiempo real.
