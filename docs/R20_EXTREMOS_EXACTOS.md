# R20: extremos eléctricos exactos

## Fuente, dominio y reducción

SVC-9 Fig. 9-17, PDF p. 19 (SVC-204D p. 75), transcrito en [HI/LO](SALIDAS_PANEL_HI_LO.md) y [SW18 OFF](SW18_OFF_SALIDA.md): R20 es 5 kΩ, R75 es 1 kΩ, R57 es 33 kΩ y R58 es 1 kΩ. La posición se expresa como resistencia del cursor a masa, `L∈[0,5000] Ω`; no identifica la ley angular. Las cargas HI/LO son resistencias finitas positivas impuestas. No se añaden parámetros audibles ni contactos parásitos sin evidencia.

| Caso | Identificación exacta | Carga desde pin 21 | HI/LO |
| --- | --- | --- | --- |
| ON, L=0 | Cursor=masa | 5 kΩ | Ambos 0 V |
| ON, L=5 kΩ | Pin 21=cursor=HI | `5 kΩ∥Z_HI∥(33 kΩ+(1 kΩ∥Z_LO))` | LO conserva su divisor cargado |
| OFF, L=0 | Cursor=masa; jacks desconectados | 5 kΩ | Ambos 0 V |
| OFF, L=5 kΩ | Pin 21=cursor=masa | 0 Ω | Ambos 0 V |

El último caso sigue presentando **R75=1 kΩ** a C2_RIGHT. Por eso una carga equivalente nula en pin 21 es válida: se estampa `1/(R75+R_equivalente)`, nunca `1/0`. Para ON con L=0 se fija la resistencia paralela del cursor a cero exactamente; el segmento superior permanece 5 kΩ. Las fórmulas interiores conservan su aritmética previa. No se usa epsilon, saturación ni mute del circuito: J7 y su carga continúan conectados por R77/R21.

`output::main_load` amplía su dominio cerrado; valores negativos, mayores que 5 kΩ y no finitos siguen siendo inválidos. Las rutas que la usan heredan la reducción. La referencia Python de 66 nodos admite carga principal cero detrás de R75. La matriz explícita AC antigua de 51 nodos mantiene su dominio interior; sus ramas de resistencia cero exigirían identificar nodos antes de estampar.

## Contraste y resultados

[Generador](../tools/r20_endpoint_vectors.py): KCL de PIN21/HI/LO con identificación exacta de nodos en los shorts, independiente de las fórmulas de reducción. Se comprueban tres pares de cargas, cinco voltajes bipolares/DC y ambos extremos. La corriente por un segmento cortocircuitado se obtiene por KCL, no dividiendo cero entre cero.

[Vectores](../evidence/r20_endpoint_vectors.json): ocho escenas = dos R61 × dos extremos × dos estados SW18. Cada escena contiene cuatro pasos centrales, ocho en el extremo y cuatro de restauración a 48 kHz, BUS 100 Hz/20 mV, R14=25 kΩ. Python resuelve simultáneamente las 66 KCL por diferencias finitas; los historiales se integran desde su propio DC. La comprobación adicional de los jacks contra KCL explícita da máximo `3,38814e-21 V`.

Los gates previos se mantienen: nodos/jacks/capacitores <1 µV, corriente de cola <1 nA, KCL Python <100 pA y nativa <10 pA. Rust pasa **128 pasos**, máximo interno **0,279225 µV**, jacks **0,219476 nV**, auditoría de todas las KCL con el historial previo. También se comprueban los ocho arranques DC exactos. Pasan la suite Rust completa y heap cero; Python regenera exactamente estos vectores y los 128 vectores anteriores Q26/Q28→J7.

El [nuevo barrido](../evidence/circuit66_control_survey_r20.json) acepta 16384 muestras: los ocho casos R20 pasan sus 256 pasos y DC. Conserva seis fallos por cutoff máximo DC/Q21 a cero y cuatro rechazos de R21 exacto. El informe completo **sigue sin pasar**.

La [corrida de costo nominal](../evidence/circuit66_r20_deadline.json) da 2,3413 ms por bloque de 64, 128/128 fuera de 1,3333 ms y cero fallos de convergencia. Es una corrida de recursos, no una comparación causal de rendimiento ni un peor caso de extremos. No admite C7. C6 tampoco cambia.

```powershell
cargo test --workspace
python -m unittest discover -s tests -p test_r20_endpoints.py -v
python -m unittest discover -s tests -p test_cutoff_j7_vectors.py -v
cargo build --release -p rf-d-circuit --example circuit66_admission
./tools/run_circuit66_admission.ps1 -Mode controls -Output evidence/circuit66_control_survey_r20.json
```

La última orden termina con error y conserva el diagnóstico por las brechas restantes. RACE: un dominio abierto de API puede ser una limitación numérica; el extremo físico se deriva identificando nodos, no inventando una resistencia mínima.
