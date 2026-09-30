# Puerto C2/reset con carga completa de R59/Q18

## Circuito y alcance

El [cierre de 71 nodos](SEGUIDOR_VCA_CADENA_71.md) expone ahora un puerto de dos terminales: voltaje del capacitor C2 de placa 2 y base Q15 del biestable. Se incluyen Q3/Q2/CR6, la resistencia R59, Q18 y toda la cadena ladder→J7. La base Q18 se calcula internamente; no es una tercera fuente impuesta.

Fuentes: **SVC-9 Fig. 9-7 PDF p. 9**, R16 de placa `10 kΩ`, Q3/Q2 y CR6; **Figs. 9-11/9-17 pp. 13/19**, R59 `68 kΩ` y cableado; **tablas 7-6/7-8 pp. 26–27/30–31**. Se mantienen las hipótesis eléctricas, R61 alternativo y límites documentados del cierre anterior. Las capacitancias de juntura están omitidas. No se añade ningún ajuste audible nuevo.

`circuit71::solve_port` devuelve un candidato provisional con todos los nodos, dieciocho cargas y salidas, las dos corrientes y sus derivadas. El estado de entrada se recibe por referencia inmutable. Con `previous=None`, los capacitores se abren a DC y se preparan sus voltajes después de la raíz. Con `Some`, se calcula un único paso Euler implícito con los dieciocho historiales entrantes fijos. No existe continuación automática dentro de este puerto.

## Derivación de corrientes y tangentes

Las corrientes positivas desde cada terminal **hacia la red cargada** son:

```text
I_C2    = (Vc2 − B3)/10000                          [A]
I_RESET = −Is_CR6 · expm1((F − Vreset)/(n·VT))        [A]
VT      = k·T/q                                     [V]
gD      = Is_CR6 · exp((F − Vreset)/(n·VT))/(n·VT)    [S]
```

B3 es el nodo 66, F el 70. Para el Jacobiano completo `J` de 71 nodos, las únicas dependencias directas de estas dos fuentes son:

```text
J · dX/dVc2    = e66 / 10000
J · dX/dVreset = e70 · gD

dI_C2/dVj    = (δj,C2 − dB3/dVj)/10000
dI_RESET/dVj = −gD · (dF/dVj − δj,RESET)
```

Ambos segundos miembros se resuelven con **una factorización**, mediante el helper multicolumna existente. La derivada entrega `2×2` en S y `71×2` en V/V. Es una derivada local del paso discretizado a dt fijo y carga anterior fija, no una respuesta AC espectral. La red activa no se fuerza recíproca, positiva o diagonal. Los coeficientes minúsculos en corte tampoco se sustituyen por cero para facilitar el solve.

Para unir este puerto al resto del contorno, su KCL sumará `I_C2` al nodo C2 e `I_RESET` a la base Q15. Las cuatro derivadas entrarán con esos mismos signos en el Jacobiano externo. Todos los ensayos de ese Newton deberán reutilizar el mismo estado entrante. **Sólo la raíz aceptada del circuito completo podrá publicar el candidato**; publicar cada evaluación del puerto integraría varias veces las mismas cargas. Esta API prepara esa conexión, pero todavía no la ejecuta ni resuelve la [ambigüedad del biestable](CONTORNO_VOLUMEN_CIRCUITO.md).

## Oráculo independiente y precisión

[`circuit71_port_vectors.py`](../tools/circuit71_port_vectors.py) usa las KCL Python de la red completa y perturbaciones centrales de cada fuente. Sus [36 casos](../evidence/circuit71_port_vectors.json) contienen veinte puntos DC y dieciséis pasos alrededor de saltos, ambos R61 y reset `0,01/0,7 V`. Las variantes temporales mantienen las cargas del paso anterior, sin recalcularlas al perturbar C2 o reset.

El oráculo exige **KCL <0,1 pA y corrección <1 pV**, frente a los 10 pA/10 nV de admisión nativa. Ese margen evita derivadas falsas en puertos débiles. Se usan perturbaciones de 10 µV y se repite con 20 µV: variación máxima **0,2575 pS** en admisión y **8,7597×10⁻⁹ V/V** en gradientes. La posibilidad de configurar gates del oráculo no cambia sus valores predeterminados ni los vectores de transitorio del bloque previo.

Gates congelados: nodos `1 µV`, corrientes `1 nA`, admisión `1 nS`, gradientes de nodo `2×10⁻⁵ V/V`; esos dos últimos se aplican también al refinamiento FD. El [informe Rust](../evidence/circuit71_port_native.json) usa semillas completas desplazadas 1 mV y registra:

| Magnitud | Máximo absoluto |
| --- | --- |
| Nodo frente a FD | **0,4277 pV** |
| Corriente frente a FD | **1,03×10⁻¹⁷ A** |
| Admisión frente a FD | **2,0428 pS** |
| Gradiente de nodo frente a FD | **5,6739×10⁻⁷ V/V** |
| Candidato de puerto frente a `step`/continuación | **1,8727 nV** |

La última comparación incluye todos los nodos, dieciocho voltajes capacitivos y J7 en los dieciséis casos temporales. La API conserva los gates de su raíz y retorna errores sin modificar el estado entrante. Hay regresiones de presupuesto insuficiente y NaN, reproducción fresca de perturbaciones DC/temporales y heap cero, incluyendo ambos segundos miembros. Pasan **52 tests Rust** del workspace y **once tests Python** de contorno, seguidor y unión.

## Carga de reset observada

Con C2=9,3 V y base reset=0,01 V, **escenario impuesto de laboratorio**, CR6 conduce hacia el reset:

```text
I_C2    =   8,16785 µA
I_RESET = −495,35735 µA

                 fuente C2       fuente RESET
dI_C2/dVj          73,2924 µS       −5,4340 µS
dI_RESET/dVj      −12,5894 µS      192,6614 µS
```

Los términos cruzados diferentes expresan la actividad de la red. Esa corriente no puede omitirse al cerrar Q15: una base reset ideal podría absorberla sin moverse y ocultaría el acoplamiento. Estos números no identifican el pico real de C2 ni constituyen una medición vintage.

## Recursos y reproducción

Ryzen 5 5600X/Win64/Rust 1.97: después de una preparación por caso se miden ocho repeticiones desde la misma semilla perturbada y el mismo historial, **288 llamadas**. El kernel de raíz más dos tangentes cuesta **147,59 µs de media y 268,7 µs máximo por llamada**, observados en esta ejecución sin aislamiento del sistema operativo. JSON, comparación y los solves de contraste con `step` quedan fuera del clock. Es costo de este puerto condicionado, no de una muestra de voz: un Newton externo lo evaluaría varias veces. El deadline global y stack específico siguen sin admitir; no se extrapola una voz en tiempo real a partir de este perfil.

```powershell
python tools/circuit71_port_vectors.py
python -m unittest discover -s tests -p 'test_circuit71*.py' -v
cargo test --workspace
cargo build --release --example circuit71_port_admission
./tools/run_circuit71_port_admission.ps1
```

El wrapper conserva revisión, CPU, compilador y hashes. RACE C5 queda contrastado para este puerto y escenas; C6/audio, la conmutación física, parámetros reales, integración completa del contorno y C7/deadline permanecen abiertos. El próximo trabajo es estudiar estabilidad y dinámica omitida del biestable con esta carga antes de seleccionar una rama.
