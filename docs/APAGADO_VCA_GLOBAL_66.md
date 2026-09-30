# Apagado sintético de los VCAs: convergencia y voltaje interno

## Fronteras ensayadas

SVC-9 Fig. 9-11, PDF p. 13: Q18 controla el primer VCA y Q21 el segundo, con sus pares diferenciales completos. Se conservan los componentes, Ebers–Moll, temperatura nominal y ambos candidatos de R61. El banco impone fuentes lineales **2→0→2 V** a Q21, o simultáneamente a ambos controles. No identifica sus niveles reales ni genera el contorno del instrumento. No se introduce smoothing en DSP.

Veintiocho escenas = dos R61 × segundo/ambos controles × rampas de 1, 8, 16, 32, 64, 128 o 256 muestras, a 48 kHz; BUS 100 Hz/20 mV, R14=25 kΩ. Cada rampa descendente llega exactamente a cero, mantiene 64 muestras, sube con la misma duración y mantiene otras 64. Las duraciones son 0,020833–5,33333 ms. Son puntos de ensayo, no una frontera universal de estabilidad.

## Barrido nativo

[Captura](../evidence/circuit66_vca_release_survey.json): **no pasa**. Las cuatro escenas de un solo salto fallan en su primera muestra (`IterationBudget`), preservando exactamente nodos, predictor y capacitores. Las otras 24 aceptan **7104 muestras**, máximo 11 iteraciones y cero reintentos. No se elevó el presupuesto 16/16 ni se aplicaron subpasos.

Converger esas rampas tampoco basta para cerrar C5: se registraron 96 sondas al llegar a cero, al final de la espera, al comenzar la subida y al acabar la restauración. Cada sonda conserva su historial entrante completo y su frontera. No se afirma integración independiente de todo el tramo anterior.

## Contraste de voltaje condicionado

[Referencia independiente](../tools/circuit66_vca_release_probes.py): ensambla KCL DC desde los módulos Python de circuito, añade los 18 capacitores por Euler y mantiene el historial capturado. Diferencia las 66 columnas y refina desde el candidato nativo hasta **KCL <10 pA y corrección Newton <10 nV**, con presupuesto offline 40/32. Ninguna factorización o coeficiente proviene de Rust. Las leyes de semiconductores siguen siendo supuestos, igual que en el nativo.

[Resultado](../evidence/circuit66_vca_release_probe_vectors.json): **20/96 sondas fallan** el gate interno de 1 µV. Máximo **1,317790 mV**, nodo 34 (emisores comunes del segundo par Q14/Q13), al primer paso de subida de la rampa de 256 muestras/R61=200 kΩ. El candidato nativo tenía KCL máximo 3,10466 pA y una corrección estimada de 1,28459 mV. Las corrientes pequeñas de apagado permiten cumplir el criterio de corriente antes de resolver bien ese voltaje.

En las 96 sondas: error máximo de jacks **0,020253 nV**, capacitores **0,024610 nV** y corriente de cola `3,26536e-19 A`. Esos gates pasan; el de nodos internos permanece fallido y no se compensa con el pequeño error de salida. Estos números describen una equivalencia numérica condicionada, no ruido medido ni fidelidad vintage.

Los puntos refinados tienen KCL <10 pA tanto en Python como al evaluarlos con `circuit66::linearize` de Rust y el mismo historial. La regresión Rust comprueba los 96 puntos contra las ecuaciones nativas (máximo 4,50672 pA); Python regenera exactamente la captura derivada, incluidos sus 20 fallos. Esa regresión valida el diagnóstico y las raíces de referencia; no convierte los 20 errores nativos en admisión.

## Próximo corte

Contrastar un criterio de corrección de voltaje para pasos temporales, con costo, stack y heap medidos. Después estudiar la semilla para saltos abruptos y derivar el contorno físico. Mantener los presupuestos y fallos atómicos; no usar las rampas de laboratorio como sustituto del circuito de contorno. C5 de apagado, C6 y C7 quedan abiertos.

```powershell
cargo build --release -p rf-d-circuit --example circuit66_admission
./tools/run_circuit66_admission.ps1 -Mode vca-release -Output evidence/circuit66_vca_release_survey.json
python tools/circuit66_vca_release_probes.py
python -m unittest discover -s tests -p test_circuit66_vca_release_probes.py -v
cargo test -p rf-d-circuit --test cutoff_ladder_output independently_refined -- --nocapture
```

El wrapper y el generador devuelven error después de guardar sus informes fallidos. La suite de diagnósticos pasa al reproducir esos resultados históricos, sin esconder la brecha.
