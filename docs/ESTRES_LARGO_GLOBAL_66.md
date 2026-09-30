# Estrés largo del circuito global de 66 nodos

## Escena y alcance

El [solver global](SOLVER_GLOBAL_66_NODOS.md) usa la topología nominal de SVC-9 Fig. 9-11, 9-8 y 9-17. Esta escena valida convergencia e historial de sus 18 capacitores durante más tiempo que los vectores independientes de 128 pasos. Conserva Ebers–Moll, diodos, Euler implícito, rails, tolerancias de 10 pA y presupuesto Newton 16/16. Los semiconductores permanecen impuestos, no identificados físicamente.

Se ejecutan seis trazas: ambos R61 documentales, 200 Ω y 200 kΩ, a 44,1/48/96 kHz. Cada una dura dos segundos, redondeados hacia abajo a bloques completos de 64. La escena es reproducible en `stress_boundary` del benchmark:

| Frontera sintética | Ley / rango |
| --- | --- |
| BUS | 100 Hz/80 mV + 1600 Hz/15 mV + 4163 Hz/5 mV |
| Cutoff | fracción 0,5 + 0,04·sin(0,7 Hz) |
| Contorno impuesto pin 16 | 40 mV·sin(2 Hz) |
| RANGE | fracción 0,1 + 0,02·sin(0,3 Hz) |
| Teclado | 0,25·(1+sin(0,9 Hz)) V; fuente 1,2 kΩ; switches 1/3 y 2/3 |
| Modulación | 150 mV·sin(7 Hz); fuente 2 kΩ; switch ON/OFF |
| Control externo | 100 mV·sin(0,5 Hz), fuente 10 kΩ, conexión/desconexión |
| Loudness1 y Q21 | 1+sin(0,8 Hz) V / 1+sin(0,6 Hz) V |
| R21 inferior | 2 kΩ + 1,5 kΩ·sin(0,4 Hz) |
| EMPHASIS | R14=0/25/50 kΩ y abierto, alternados cada 250 ms |
| SW18 y J7 | switch alternado; cargas tip/ring de 32 Ω o abiertas |

Los switches, conexiones y cargas cambian al límite exacto de cada segmento de 250 ms, sin smoothing añadido. Las frecuencias y amplitudes son estímulos de laboratorio elegidos para combinar estados ya contrastados, no constantes del instrumento. No hay VCO, generador de contornos, ruido ni identificación de una unidad vintage en esta escena.

## Gates específicos

- Toda muestra aceptada satisface las 66 KCL <10 pA y conserva estado finito.
- Cada 64 muestras se vuelve a ensamblar KCL en el estado aceptado usando **el historial anterior**, no el recién publicado. Se contrasta la cota declarada por el solver.
- Mientras C10 está desconectado, su voltaje almacenado se conserva bit a bit; al reconectar, el solver recibe ese historial.
- Si falla DC o un paso, se registra fase, muestra, tiempo y error. Un paso rechazado debe conservar exactamente todo el estado. El proceso termina con error después de guardar el diagnóstico; no sustituye la falla por silencio ni amplía el presupuesto.
- Se registran histograma de iteraciones, evaluaciones máximas, reintentos, corriente de cola, pico J7 y estado final completo.

Esta auditoría usa el ensamblador Rust y detecta errores de convergencia/publicación; **no es un oráculo independiente** de las seis nuevas trazas. Los vectores Python, diferencias finitas y contraste con la partición siguen siendo los gates independientes de las escenas anteriores. No se extrapola identidad de trayectoria ni fidelidad sonora a partir de KCL.

## Resultado

Las [48 ventanas independientes posteriores](VENTANAS_INDEPENDIENTES_ESTRES_GLOBAL.md) añaden 192 pasos Python alrededor de siete transiciones y a 1,9 s por escenario. Usan el historial nativo capturado y después integran cuatro pasos propios; pasan todos los nodos y salidas con las cotas fijadas.

`evidence/circuit66_long_stress.json` conserva las seis corridas y metadatos de compilador, CPU, fuentes y ejecutable. Se aceptaron **752384 muestras**, con cero fallos y cero reintentos del predictor. Hubo **11756 auditorías de KCL** y **188084 comprobaciones de conservación de C10 abierto**. El máximo fue cinco iteraciones Newton y seis evaluaciones de residual por muestra, dentro del presupuesto.

Máximo KCL declarado: 9,999814 pA; máximo auditado: 9,998210 pA. La cola recorre 4,781–15,874 µA en la escena. Son resultados eléctricos condicionados, no mediciones de una placa.

| Tasa | Muestras por R61 | Duración por R61 |
| --- | --- | --- |
| 44,1 kHz | 88192 | 1,99982 s |
| 48 kHz | 96000 | 2 s |
| 96 kHz | 192000 | 2 s |

La escena no mide deadlines: las auditorías y serialización son tareas offline. La medición separada [de costo](EXPONENCIALES_GLOBAL_66.md) sigue por encima de 1,333 ms/bloque a 48 kHz. C7 permanece abierto. Faltan extremos completos del panel, poblaciones de semiconductores, sesiones de minutos/horas, refinamiento temporal, aliasing y host. C6 sigue sin evidencia de una unidad física.

```powershell
cargo build --release -p rf-d-circuit --example bench_ladder_recovery_output
./tools/run_circuit66_stress.ps1
```

## Otros ensayos de costo de este bloque

Se restituyeron dos variantes tras cinco pares y contraste de 8192 muestras:

| Variante | Media anterior | Media candidata | Cambio | Decisión |
| --- | --- | --- | --- | --- |
| Filas separadas con slices sin alias | 2,24904 ms | 2,24318 ms | −0,261 % | Mejora no distinguible de variación local |
| Recíprocos de escalas y diagonales, con división de respaldo | 2,24752 ms | 2,28062 ms | +1,473 % | Aumento de costo |

Parches y corridas: `evidence/circuit66_disjoint_rows_*` y `evidence/circuit66_reciprocals_*`. Ninguna variante está activa. No se admite una transformación por una ganancia insignificante de una media; se conserva la ruta ya contrastada.
