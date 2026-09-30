# Seguidor de volumen, R59 y cadena simultánea de 71 nodos

## Alcance y trazabilidad

El [seguidor Q3/Q2](SEGUIDOR_VOLUMEN_NATIVO.md) y el [circuito de 66 nodos](SOLVER_GLOBAL_66_NODOS.md) se resuelven ahora juntos. La base Q18 de placa 4 deja de ser una carga de referencia de 0,7 V: su corriente y voltaje resultan del VCA unido al ladder, recuperación, segundo VCA, conversión y salidas HI/LO/J7.

Fuentes de conexión: **SVC-9 Fig. 9-7 PDF p. 9**, contorno de placa 2; **Figs. 9-11/9-17 pp. 13/19**, R59 y cableado; tablas **7-6 pp. 26–27 y 7-8 pp. 30–31**, valores. SVC-204D §2.9 p. 12 describe las etapas VCA y §2.10 pp. 13–14 los contornos. Se conservan las hipótesis de semiconductores y conflictos de revisión de los bloques anteriores. No se incorpora ninguna característica de una reedición.

El [código Rust](../crates/rf-d-circuit/src/circuit71.rs) añade cinco nodos a los 66 existentes: base Q3 (66), emisor Q3/base Q2 (67), colectores compartidos/R15 (68), salida de volumen (69) y feedback/CR6 (70). La base Q18 sigue siendo el nodo 32. La alimentación del seguidor permanece impuesta en 9,3 V; no se ha cerrado Q26/R62/R63 de placa 2.

**C2 de placa 2 y base Q15/reset siguen impuestos.** Se integran los dieciocho capacitores de la cadena anterior, incluidos C10 y C18 de cutoff. C2 del contorno no es uno de ellos. La entrada externa del segundo VCA continúa con base Q21 a 2 V, frontera de laboratorio pendiente de reconstruir. BUS tampoco procede todavía de VCO/mixer.

## Unión eléctrica y unidades

Con O=salida del seguidor y B18=base Q18:

```text
I59 = (O − B18) / 68000             [A, seguidor → Q18]
KCL(Q18 base) añade (B18 − O)/68000
KCL(seguidor O) añade (O − B18)/68000
J[32,69] = J[69,32] = −1/68000      [S]
```

Cada diagonal incluye la conductancia R59 una sola vez. No se duplica la resistencia al combinar los bloques, ni se fuerza una ganancia de VCA. Ambas junturas de Q18 siguen en Ebers–Moll. El oráculo Python ensambla la terminal faltante de R59 sobre su propia KCL de 66 nodos y obtiene el Jacobiano completo por diferencias finitas; no importa el Jacobiano Rust. Su fila 32 usa corriente entrante, mientras Rust usa saliente; el signo correspondiente se comprueba explícitamente.

La API devuelve además `I_C2=(Vc2−VbaseQ3)/10000` e `I_RESET=−I_CR6`, positivas hacia la red del seguidor. Son corrientes para el cierre posterior del contorno. Todavía no se insertan en su capacitor ni se decide con ellas la conmutación del biestable.

Las muestras de DC cubren C2 `0; 0,8469345758; 3,2; 6; 9,3 V`, bases reset `0,01/0,7 V` y ambos R61 `200 Ω/200 kΩ`. Resistencias nominales, βF=100, βR=5 y T=298,15 K son hipótesis condicionadas. El dominio validado es este conjunto y sus trayectorias; no todo voltaje finito aceptado por el API. En un caso con C2=0 resulta **O≈−1,132 V**; con C2=9,3 V, **O≈7,990 V**. Se mantienen esos voltajes eléctricos sin normalización `0..2` ni recorte. Esto tampoco define los extremos reales de C2.

## Preparación, rechazo y memoria

La preparación directa acepta una semilla completa de 71 nodos, abre los capacitores a DC y reconstruye sus voltajes tras converger. La preparación desde 66 nodos añade una semilla de seguidor en C2=3,2 V y 64 etapas DC hacia el destino. **3,2 V es un ancla numérica**, no un pico de envolvente medido. La semilla de audio debe estar cerca del ancla, con aproximadamente 2 V en R59. Una prueba conserva el rechazo `NoDecrease` al reconstruir ese arranque desde la raíz apagada: no se promete convergencia desde cualquier raíz. La semilla completa apagada, desplazada ±1 mV, sí reproduce el punto solicitado.

En transitorio se exige KCL <10 pA y corrección Newton completa <10 nV; no basta una corriente pequeña en nodos débiles. Presupuesto 16 iteraciones/16 divisiones por solve. Predictor y reintento usan la misma memoria. Si ambos fallan, `step` no modifica ningún nodo, historial ni fuente anterior.

`step_continued` es una recuperación **explícita de laboratorio**: entre 1 y 64 etapas de las fuentes C2/reset, con BUS, dt, panel, alimentaciones y los dieciocho historiales originales fijos. Sólo el último resultado publica estado. No hay subpasos físicos, descarga artificial ni reconstrucción DC durante audio. Los contadores incluyen el trabajo de reintentos dentro de una llamada exitosa; los clocks también incluyen la llamada primaria rechazada antes de la continuación.

R21 conserva sus topes exactos de 0/5000 Ω. En ellos la fila 49 expresa una igualdad de voltaje; las demás son corrientes. Se informa por separado del error de esa igualdad y de la corriente del corto. Se comprueba su conservación tras unir el seguidor.

## Contraste y recursos

Los [vectores independientes](../evidence/circuit71_loudness_vectors.json) resuelven cuatro escenarios, veinte destinos DC y 256 pasos a 48 kHz, BUS senoidal de 20 mV/100 Hz y saltos entre C2=3,2/6/0,8469/0 V. Cada oráculo mantiene su propia trayectoria y cargas. Se congelaron antes del contraste gates de 1 µV en nodos/capacitores/jacks, 1 nA en corrientes y los criterios Newton anteriores.

El [informe nativo](../evidence/circuit71_native.json) registra:

| Magnitud | Máximo absoluto |
| --- | --- |
| Nodo Rust↔FD | **2,4963 nV** |
| Capacitor Rust↔FD | **19,7034 pV** |
| HI/LO/J7 Rust↔FD | **5,1979 pV** |
| Corriente de puerto/cola Rust↔FD | **3,3104 fA** |
| KCL nativa | **9,4491 pA** |
| Corrección Newton nativa | **1,8727 nV** |

El FD registra cuatro rechazos directos en total; Rust registra doce llamadas primarias rechazadas y las rescata con 32 etapas. Son políticas numéricas diferentes; todos sus resultados finales satisfacen los mismos gates. Se guardan los motivos y muestras en ambos informes. Las 71 columnas analíticas se comprueban por FD en dieciséis puntos temporales, además de errores de presupuesto, NaN, topes R21 y publicación atómica. La regresión de heap incorpora preparación y saltos de esta ruta y mantiene **cero asignaciones**. Pasan **50 tests Rust** del workspace y nueve tests Python de contorno/seguidor/unión.

Ryzen 5 5600X, Win64, Rust 1.97: cuatro bloques calentados de 64 pasos cuestan **16,12–16,96 ms** de kernel, frente a **1,333 ms** disponibles. Son cuatro observaciones, no una distribución de deadlines. La nueva factorización de 71 nodos usa orden natural; no se ha admitido una optimización ni stack específico para esta ruta. Este cierre **no cumple tiempo real** ni demuestra fidelidad sonora. El wrapper guarda CPU, compilador, revisión anterior al commit y hashes exactos de fuentes/oráculo/ejecutable.

```powershell
python tools/circuit71_loudness_vectors.py
python -m unittest discover -s tests -p test_circuit71_loudness.py -v
cargo test --workspace
cargo build --release --example circuit71_admission
./tools/run_circuit71_admission.ps1
```

## Próximo cierre

Obtener la admisión conjunta vista desde C2 y reset, con toda la carga R59/Q18, y reintegrarla en el contorno. La [ambigüedad de raíces del biestable](CONTORNO_VOLUMEN_CIRCUITO.md) sigue abierta; no se elegirá una rama por conveniencia sonora. RACE C5 se cierra únicamente para las fronteras y escenas anteriores; conmutación física, parámetros de una unidad, voz completa, audio externo y deadline siguen pendientes.
