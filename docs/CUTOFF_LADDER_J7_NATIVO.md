# Q26/Q28, ladder y salida acoplados

## Circuito y método

El módulo `cutoff_ladder_output` une [Q26/Q28/C18](CUTOFF_NATIVO_Q26_Q28.md), el ladder de 16 nodos, recuperación Q5–Q8, ambos VCAs, conversión, panel y placa 3 hasta J7. Conserva el perfil documental SVC-9 Fig. 9-11 (PDF p. 13), Fig. 9-8 (p. 10), Fig. 9-17 (p. 19) y Table 7-8 (pp. 30–31). No incorpora características de reediciones.

La nueva API recibe cutoff eléctrico, RANGE, contorno, teclado, modulación y jack; **no recibe una corriente de cola**. En cada ensayo Newton sustituye la frontera fija por la corriente de R60/Q28 y añade `dI_TAIL/dV_TAIL` al Jacobiano del nodo TAIL. Es una eliminación local de los cuatro nodos de control, equivalente al complemento de Schur del sistema conjunto. Is/β/T permanecen explícitos. BUS sigue siendo una fuente impuesta, igual que las leyes de volumen y las señales de control aguas arriba.

La condición DC resuelve simultáneamente Q26/Q28 y el ladder con capacitores abiertos. El paso temporal conserva el mismo historial C18 durante todos los ensayos y durante el reintento desde el estado anterior. Sólo al converger publica Q26/Q28, ladder y toda la salida. El lazo opcional C10/R14/R73 mantiene las ecuaciones de [EMPHASIS nativo](EMPHASIS_NATIVO_C10.md), en Ω eléctricos, con C10 de 10 µF. La ruta anterior con corriente fija conserva su alcance de laboratorio.

El dominio y las incertidumbres de cada bloque se heredan sin ampliarlos: rails ideales, Ebers–Moll simple, fuentes externas declaradas, posiciones eléctricas y R61=200 Ω o 200 kΩ como escenarios documentales separados. La tolerancia exterior es 100 pA y la del puerto Q26/Q28 10 pA; Newton/búsqueda siguen acotados a 16/16, con fallo atómico. Euler implícito condiciona la transferencia temporal; no es una medición de un Model D.

## Oráculo independiente de 66 nodos

`tools/cutoff_j7_vectors.py` primero cierra 20 nodos DC mediante diferencias finitas. Después `headphone_coupled_transient_reference.py` resuelve las 66 incógnitas temporales en una sola matriz: 62 nodos de señal y cuatro de control. Diferencia todas sus columnas; no llama al solver ni a las tangentes Rust. La ruta anterior de 62 nodos conserva sus vectores exactamente.

`evidence/cutoff_j7_vectors.json` contiene 64 pasos a 48 kHz por cada R61, 128 en total. BUS es una senoide de 440 Hz y 20 mV; cambian cutoff, contorno, SW16/SW17, SW15, J2, RANGE, R14 y SW18. Cada paso congela los 66 voltajes, C18, C10, corriente de cola y salidas. Las fuentes de control son escenarios, no interpretaciones musicales del panel.

El test Rust compara todos los nodos (incluido pin 22 reconstruido por KCL), historial de capacitores, corriente y salidas. Reevalúa el puerto aceptado con C18 anterior y exige igualdad exacta del estado publicado. También comprueba datos inválidos, presupuesto agotado y un predictor rechazado. El test global confirma cero asignaciones de heap en inicialización y pasos, tanto con C10 abierto como cerrado.

| Resultado de 128 pasos | Máximo / criterio |
| --- | --- |
| Error interno de 66 nodos | 1,374 µV / <2 µV |
| Error J7 | 22,40 nV / <1 µV |
| Error de corriente de cola | 1,260 pA / <1 nA |
| Relación señal/error numérica | 91,4 dB / >90 dB |
| KCL exterior y control | <100 pA y <10 pA |

La comparación anterior examinaba los primeros 24 nodos y J7; aquí se amplía a los 66. Las tolerancias se declaran por magnitud: el criterio interno de 2 µV cubre la acumulación de las tolerancias locales de la partición. No se modificaron los criterios ni los vectores anteriores.

## Costo y gates

`cargo run --release -p rf-d-circuit --example bench_ladder_recovery_output -- --cutoff --emphasis` mide 8192 muestras de calentamiento y 8192 medidas, bloques de 64 a 48 kHz, Windows / Ryzen 5 5600X. Incluye BUS 100 Hz/100 mV, R14=25 kΩ y contorno sintético de 2 Hz/20 mV. El escenario de costo difiere del de vectores; no es una comparación de aceleración entre ellos.

Una ejecución dio media **25,737 ms**, p99 **29,701 ms**, máximo **29,875 ms** frente al plazo **1,333 ms**. Los 128 bloques excedieron el plazo. Hubo cero fallos y cero reintentos de predictor, KCL ladder máximo 1,455 pA y control 0,0003514 pA. La cola respondió entre 6,825 y 7,019 µA. Registro en `evidence/cutoff_ladder_native_deadline.json`.

Se amplía C5 (discretización/oráculo) en RACE. C6 (audio vintage) permanece abierto y C7 (plazo nativo) **no pasa**. No hay plugin instalable ni afirmación de fidelidad sonora. El próximo trabajo debe atacar la anidación del solver y completar fuentes de control/mezcla, conservando el oráculo y las medidas de error.
