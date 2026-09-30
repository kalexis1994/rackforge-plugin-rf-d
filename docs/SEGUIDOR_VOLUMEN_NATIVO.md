# Puerto nativo del seguidor de volumen

## Circuito, fuentes y límites

El [grafo de placa 2](CONTORNO_VOLUMEN_CIRCUITO.md) permite aislar Q3/Q2, R16 de placa `10 kΩ`, R15 `560 Ω`, R24 `6,8 kΩ`, R27 `16,9 kΩ` y CR6 `1N34A`. Fuente: **SVC-9 Fig. 9-7 PDF p. 9**, tabla 7-6 pp. 26–27; equivalente en SVC-204D Fig. 9-5 p. 65. La conexión de pin 7 a R59 `68 kΩ` y base Q18 de placa 4 se identifica en SVC-9 Figs. 9-17/9-11 pp. 19/13 y tabla 7-8 pp. 30–31.

Los cinco desconocidos son base Q3, emisor Q3/base Q2, colectores Q3/Q2, emisor Q2/salida y feedback R24/R27/CR6. **R15 carga los dos colectores**, no se sustituye por alimentación ideal. C2 y base Q15 son puertos de voltaje impuestos. Se puede añadir carga de salida `g·(Vout−Vref)`. En los escenarios cargados `g=1/68000 S`, `Vref=0,7 V`: referencia de laboratorio de base Q18, no su solución física. El puerto no guarda capacitores ni decide etapas del contorno.

[`loudness_follower.rs`](../crates/rf-d-circuit/src/loudness_follower.rs) utiliza matrices de tamaño fijo. Se mantienen Ebers–Moll con ambas junturas y CR6 Shockley, sin imponer caída `VBE=0,6 V` ni atenuación normalizada. Parámetros: `Is_BJT=10⁻¹⁴ A`, `βR=5`, `T=298,15 K`, `Is_CR6=10⁻⁸ A`, `n_CR6=1,5`; `βF=50/100/200` en las pruebas. **Son hipótesis no identificadas de semiconductores**, no tolerancias o distribución de piezas vintage. Se omiten capacitancias de juntura; la carga de C2 es corriente algebraica de base.

## KCL y signos de los puertos

Con `B`, `M`, `P`, `O`, `F` para los cinco nodos y `ID` positiva de feedback a base Q15:

```text
B: (B−Vc2)/10000 + IB3 = 0
M: −IE3 + IB2 = 0
P: (P−Vsupply)/560 + IC3 + IC2 = 0
O: −IE2 + (O−F)/6800 + g·(O−Vref) = 0
F: (F−O)/6800 + (F+10)/16900 + ID(F−Vreset) = 0
```

Unidades: V, Ω, S y A. La convención BJT `IE=IB+IC` es corriente saliente **del dispositivo** por emisor; las KCL de nodo suman corrientes salientes del nodo. Los tres puertos entregan corrientes positivas **hacia esta red**:

```text
I_C2    = (Vc2−B)/10000
I_RESET = −ID
I_REF   = g·(Vref−O)
```

`solve_port` devuelve `dI_i/dV_j`, matriz 3×3 en S, y `dO/dV_j` en V/V. Para calcularla resuelve `J·dx/dVj = −∂r/∂Vj` y añade las derivadas directas de cada corriente. La red activa no debe asumirse recíproca. Estas derivadas permiten cargar la futura KCL de C2, base Q15 y base Q18; encadenar voltajes unilateralmente omitiría las interacciones.

Se aceptan KCL <10 pA y corrección completa <10 nV. Presupuesto por defecto 16 iteraciones/16 divisiones; el API permite hasta 32/24 como límite numérico explícito. Los 60 casos fríos usan como máximo siete iteraciones. Una semilla se copia y un fallo no publica resultado. Ni la semilla fría ni los límites de Newton definen una ley de contorno.

## Oráculo y error de tangentes pequeñas

[`loudness_follower_vectors.py`](../tools/loudness_follower_vectors.py) formula las cinco KCL por separado y obtiene todos los Jacobianos por diferencias finitas centrales. Los [60 vectores](../evidence/loudness_follower_vectors.json) cubren cinco voltajes C2 (`0`, `0,8469345758`, `3`, `6`, `9,3 V`), dos bases reset (`0,01/0,7 V`), carga abierta/R59 y tres βF. Las resistencias/temperatura restantes están fijas; esto no acredita el resto del dominio finito aceptado por el API.

La primera comprobación de tangentes falló: el oráculo con corrección <10 nV podía detenerse en la misma raíz al perturbar un puerto débil. Eso daba una derivada cero falsa. Reducir sólo el incremento FD no lo resolvió. El oráculo ahora exige **KCL <0,1 pA y corrección <1 pV**; incremento de Jacobiano `1 µV` y de puertos `10 µV`. Se mantuvieron los gates previos de comparación: nodos `1 µV`, corrientes `100 pA`, tangentes `1 nS`, ganancia `10⁻⁶ V/V`.

El [informe nativo](../evidence/loudness_follower_native.json), Ryzen 5 5600X/Win64/Rust 1.97, registra:

| Magnitud | Máximo absoluto |
| --- | --- |
| Diferencia de nodo Rust↔oráculo | **7,630492 nV** |
| Diferencia de corriente de puerto | **6,295139 pA** |
| Diferencia de tangente de corriente | **13,797793 pS** |
| Diferencia de ganancia de salida | **9,551203×10⁻⁸ V/V** |
| KCL nativa | **8,373889 pA** |
| Corrección Newton nativa | **7,630492 nV** |

Las cinco columnas del Jacobiano se contrastan por diferencias finitas en cada caso. También se prueban semillas ±1 mV, límites de presupuesto, entradas inválidas, reproducción de las muestras y coincidencia del seguidor aislado con el reposo del contorno completo bajo **las mismas fronteras**. Cargar la salida reduce su voltaje y aumenta la corriente tomada de C2: no se cancela esa corriente para facilitar la convergencia.

## Recursos y reproducción

La prueba de heap existente incluye diez solves fríos del puerto con sus tres tangentes y conserva **cero asignaciones**, junto a toda la ruta anterior. Pasan **46 tests Rust** del workspace y seis tests Python de los nuevos bloques. La observación de costo del ejemplo mide 64 bloques tras ocho calentamientos: **271,94 µs de media y 288,4 µs máximo por 64 solves algebraicos fríos**. Clocks excluyen carga de JSON/comparación/serialización. No hay historial C2, gatillo, ladder ni audio en ese perfil: **no es el costo de la voz ni un gate del host**. No modifica el incumplimiento del plazo de la cadena de 66 nodos.

```powershell
python tools/loudness_follower_vectors.py
python -m unittest discover -s tests -p 'test_loudness_*.py' -v
cargo test --workspace
cargo build --release --example loudness_follower_admission
./tools/run_loudness_follower_admission.ps1
```

El wrapper guarda revisión, CPU, compilador y hashes de ejecutable, código y oráculo, incluso ante fallo. RACE C5 se cierra sólo para este puerto condicionado y los escenarios descritos. C6/audio, conmutación del biestable, parámetros físicos y deadline completo siguen abiertos.

## Siguiente cierre

El [cierre de 71 nodos](SEGUIDOR_VCA_CADENA_71.md) ya une el seguidor con R59 y base Q18 calculada, conservando toda la cadena hasta J7. El siguiente pendiente es la admisión conjunta desde C2/reset y el regreso al biestable; el bloque aislado anterior mantiene su alcance y evidencia propios.

Unir R59/base Q18 y el seguidor simultáneamente para cuantificar la carga real de la salida. Después reintegrar la corriente de entrada en C2 y el feedback en Q15, resolviendo primero la [ambigüedad del biestable](CONTORNO_VOLUMEN_CIRCUITO.md). Los voltajes de este circuito no están restringidos al intervalo `0..2 V` usado en las continuaciones VCA de laboratorio: **no normalizar ni recortar la fuente física para entrar en ese API**. Ampliar y comprobar el solver correspondiente antes del acoplamiento.
