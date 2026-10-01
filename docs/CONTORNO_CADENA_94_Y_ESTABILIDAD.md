# Contorno cargado, 94 nodos y estabilidad local

## Qué cierra este laboratorio

El [puerto de C2/reset](PUERTO_CONTORNO_CADENA_71.md) permitió comprobar sus cargas. El nuevo oráculo une **todo el contorno de volumen y gatillo**, no sólo el seguidor, con la cadena de audio: `66+28=94` nodos interiores. **C2 y base Q15 de placa 2 dejan de ser fuentes impuestas.** Sus voltajes salen de la misma KCL que Q25/Q15, Q3/Q2, Q18 de placa 4, ladder, recuperación y salidas. Se mantienen las 18 cargas anteriores y las tres del contorno: 21 en total.

Fuentes: SVC-9 Fig. 9-7 PDF p. 9 y tabla 7-6 pp. 26–27 para contorno; Fig. 9-11 p. 13, Fig. 9-8 p. 10 y Fig. 9-17 p. 19 para cadena/cableado; SVC-204D §2.9/2.10 pp. 12–14. R59=68 kΩ une salida pin 7 de placa 2 y base Q18 de placa 4. Se conservan todos los conflictos e hipótesis de los [bloques anteriores](CONTORNO_VOLUMEN_CIRCUITO.md).

No se cambia el motor Rust. Es un laboratorio Python/NumPy fuera de tiempo real. Siguen impuestos BUS, alimentación de contorno de 9,3 V, base Q21 del segundo VCA a 2 V y fuentes de cutoff. No se cierran alimentación compartida Q26, carga del contorno de filtro, VCO/mixer, capacitancias de juntura ni almacenamiento de carga de BJTs. Controles interiores nominales: ataque 10 kΩ, decay 100 kΩ, sustain 2,5 kΩ; decay final ON; S-trigger abierto.

## KCL, estados y contraste

[`loudness_chain94_reference.py`](../tools/loudness_chain94_reference.py) usa las KCL de audio independientes y el grafo de contorno existente. Orienta todas las filas como corriente **saliente**, en A. Al combinar los subcircuitos se suman una vez las terminales faltantes:

```text
KCL(base Q18) añade −Vout_contorno/68000
KCL(salida contorno) añade −Vbase_Q18/68000
J[baseQ18,salida] = J[salida,baseQ18] = −1/68000 S
```

Los términos propios de R59 ya están en las diagonales de cada bloque. Se calculan juntos los 94 voltajes; no se pasa sólo un voltaje de envolvente a un VCA. La corriente de salida carga el seguidor y por su base a C2; CR6 carga reset dentro de la misma red.

Cada capacitor estampa `C/dt · (v−v_anterior)` con **un único dt**. La extensión del oráculo de 66 nodos acepta `dt_s` explícito; su valor predeterminado sigue siendo `1/48000 s`. C10 conserva su resistor serie de 25,5 kΩ y su historial separado. Un fallo no publica nodo ni carga. No se subdivide el tiempo dentro de una llamada fallida ni se prepara DC al encontrar un salto.

Hay dos rutas de Jacobiano: híbrida —66 columnas de audio por diferencias finitas y contorno analítico— y **94 columnas por FD centrales** de las KCL completas. Ambas usan matrices binary64 y `numpy.linalg.solve`; no comparten la derivada del contorno. Gates por raíz: KCL <10 pA y corrección completa <10 nV. El criterio de voltaje protege los nodos débiles del primer VCA en corte.

El [informe de primer rechazo](../evidence/loudness_chain94_fold.json) prepara DC cargado, aplica teclado +10 V desde t=10 ms y avanza con dt=1 ms. Ambos R61 aceptan doce pasos y rechazan el intervalo **12→13 ms** desde la raíz anterior. Dos semillas diagnósticas reproducen las raíces conocidas con error híbrido↔FD de **3,28 nV**. Son las dos encontradas por ese conjunto inicial de semillas, **no una enumeración exhaustiva**.

## Refinamiento temporal conserva el problema

El [barrido temporal](../evidence/loudness_chain94_time_survey.json) mantiene teclado ON desde el mismo t=10 ms y rehace cada trayectoria con sus propias 21 cargas. No busca una raíz alternativa cuando la ruta habitual falla.

| dt | Pasos aceptados por R61 | Inicio del intervalo rechazado |
| --- | ---: | ---: |
| 1 ms | 12 | 12,000 ms |
| 0,5 ms | 25 | 12,500 ms |
| 0,25 ms | 49 | 12,250 ms |
| 0,125 ms | 99 | 12,375 ms |

Son **370 pasos aceptados** entre ambos R61, más ocho rechazos conservados. El último estado válido permanece intacto. Esto sitúa el problema cerca de la conmutación; **no determina un instante físico de switching** ni demuestra que una integración suficientemente fina lo resolverá sin completar la dinámica.

## Descriptor con masa singular

Para estudiar modos locales se usa el Jacobiano estático `G` del circuito congelado en cada candidato, y la matriz capacitiva `C`:

```text
C · dδx/dt + G · δx = 0
(G + λC) · v = 0
```

No se invierte C ni se añaden capacitores epsilon a todos los nodos. Los 21 voltajes capacitivos son coordenadas independientes; el resto permanece algebraico. El helper construye `x=T·[v_cap;z]`, con `BᵀT=[I,0]`, donde B es la incidencia capacitiva. La transformación conserva `C_cap=diag(Ci)` y elimina z por Schur:

```text
K = Gdd − Gda · Gaa⁻¹ · Gad
A = −diag(Ci)⁻¹ · K
λ = eigenvalues(A)
```

**C10 requiere un nodo adicional** en este análisis: su midpoint, conectado a base Q30 por 25,5 kΩ. La red descriptor tiene 95 voltajes, 21 coordenadas dinámicas y 74 algebraicas. Colocar C10 directamente entre nodos 22/7 cambiaría el circuito y sus polos. Una regresión verifica el polo analítico `−1/((Ra+Rs)·C)` de un capacitor con resistencia serie.

El [descriptor base](../evidence/loudness_descriptor_stability.json) contrasta las dos raíces conocidas del contorno aislado y cargado, seis casos. Sus modos locales son decrecientes. La condición de `Gaa` alcanza aproximadamente **7,62×10¹¹**: se conserva el dato y se comprueba también el residuo del pencil completo, no sólo el eigenproblema reducido. Máximo residuo relativo en esos casos: **2,90×10⁻¹¹**, frente al gate de 10⁻⁹. Los polos se emparejan uno a uno, conservando multiplicidad; gate relativo de contraste FD 0,005.

Estos son **Jacobianos congelados en puntos de un transitorio**, no pruebas de equilibrio ni de estabilidad global. Que sus modos salgan decrecientes no decide qué raíz corresponde al historial físico. La [búsqueda ampliada y auditoría de cargas rápidas](BIESTABLE_TRES_RAICES_Y_CARGA_RAPIDA.md) encuentra una tercera raíz y muestra una inestabilidad omitida por la masa original.

## Pruebas y reproducción

Se contrastan las 94 columnas en las raíces del primer rechazo, preparación desde semilla desplazada, prefix independiente, R59, 21 historiales, rechazo atómico, entradas no finitas y dt inválido. También se verifica C10 serie, rango dinámico 21/25, modos crecientes en una red de resultado conocido y emparejamiento de polos repetidos. Se preservan todos los fallos del barrido temporal.

```powershell
python -m pip install -r requirements-lab.txt
python tools/loudness_chain94_probes.py
python tools/loudness_descriptor_stability.py
python tools/loudness_chain94_root_survey.py
python tools/loudness_fast_charge_audit.py
python tools/loudness_chain94_time_survey.py
python -m unittest discover -s tests -p test_loudness_chain94.py -v
```

Los informes registran Python **3.12.10**, NumPy **2.5.2**, sistema, revisión previa al commit y hashes. No se mide ni se admite un deadline del plugin para estos oráculos. RACE: cálculo y reproducción condicionados; estabilidad física, conmutación causal, parámetros reales, audio y tiempo real todavía abiertos. No hay selector ADSR ni elección automática de una raíz.
