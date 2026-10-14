# Paso temporal controlado por señales y cargas

Variante experimental del circuito nominal SVC-9 pp.5/9/13/19, sin
hardware. Base: `35bf843`, referencia estricta de 24 ms en
[QA anterior](../evidence/voice_cost_tests01.json).
Se conservan las 250 ecuaciones, memorias HIGH/LOW, Newton, cargas,
puertos y solver. Se aproxima únicamente la resolución temporal.

## Hipótesis y dominio

Los estados internos del macromodelo LM741 contienen escalas mucho más
cortas que las señales útiles. Controlar todos esos estados a 2 µV cuesta
demasiado para escuchar una nota. Una comparación coarse/fine de los
56 nodos físicos del VCO y los 118 de la cadena puede permitir pasos mayores.
No se afirma una cota matemática del error global.

Estimador previo a medición: VCO `200 µV + 1e-4 |V|`; también diferencias
entre terminales de C2/C3/C4/C6. Cadena y ambos contornos:
`500 µV + 1e-4 |V|`. Son presupuestos numéricos de laboratorio;
no tolerancias de componentes ni del hardware. No son divisores Richardson.
El candidato publicado sigue siendo dos medios Radau con historia propia.
Los interiores 741 y corrientes ideales permanecen en cada solve;
se excluyen del estimador temporal de esta variante.

Primer banco: misma inicialización condicionada, KEY 0→10 V a 1 ms,
10→0 a 6 ms, fin 24 ms, rejilla 125 µs. Máximos de paso completo
64/32 µs. Sin alineación de fase, ajuste de nivel o normalización.

## Gates fijados antes del banco

- Frente a la referencia estricta al mismo reloj: 56 nodos VCO
  `20 mV + .002 |V|`, 118 cadena `2 mV + .001 |V|`.
- R59/R60: `20 nA + .002 |I|`; J7 error RMS ≤1 % del RMS original,
  error máximo ≤3 % del máximo absoluto original, DC medio ≤5 µV.
- Refinamiento 64/32 µs: mismos gates, con RMS J7 ≤0.5 %, máximo ≤1.5 %.
- Newton y BUS conservan los gates nativos anteriores. Rechazo atómico
  ante intervalo inválido, KEY inválido y dominio eléctrico inválido.
- Medir costo total de la trayectoria, duración y cantidad de solves.
  Un ahorro temporal no admite automáticamente tiempo real.

Si pasa, continuar una escena de KEY sostenido durante 300 ms y liberación
hasta 500 ms con dos resoluciones. Esa escena nueva sólo tiene contraste
entre resoluciones; no hereda una referencia estricta de 500 ms.
Publicar audio de J7 con duración real, banda y ganancia fijas declaradas.
Conservar cualquier fallo y replay sin cambios antes de reparar.

## Segunda hipótesis — señal y carga

Tras admitir el primer banco, una segunda política conserva los gates
externos y observa BUS, R6, C1, sierra/triángulo/pulso y NEG4. Controla
diferencias de tensión de los seis capacitores VCO, los 17 de cadena y
los siete de ambos contornos, con `500 µV + 1e-4 |Vcap|` y un piso de
**2 pC** para capacitores pequeños (`max(presupuesto V, 2 pC / C)`).
C1 y señales VCO conservan además 200 µV. El piso es un presupuesto
numérico experimental, sin interpretación como tolerancia física.
Las cargas BE/BC y memorias 741 siguen resueltas en todas las etapas;
no forman parte del estimador. Esta selección no descarta ecuaciones.
Gates de contraste y refinamiento permanecen iguales. No se admiten
las tensiones internas excluidas como trayectorias temporalmente precisas.
