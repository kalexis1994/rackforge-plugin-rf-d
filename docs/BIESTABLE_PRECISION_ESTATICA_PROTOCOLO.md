# Precisión estática de la cadena de audio: protocolo previo

## Pregunta

El mapa mixto usa FD binary64 de los 66 nodos de audio. El contraste de
reset conserva 1,34857×10⁻⁶ en nodo 27/memoria 10 frente a gate 10⁻⁸.
El solve racional pasa, pero ninguno de cinco pasos FD cierra ese mapa.
Se contrasta una evaluación separada de corrientes y derivadas estáticas.

## Evaluador independiente

Transcribir las mismas ramas resistivas, Ebers-Moll y Shockley del oráculo
66 a un grafo de terminales con KCL saliente y sellos analíticos. Capacitores
abiertos: sin Newton, historial ni estado publicado en este evaluador.
Conservar las mismas constantes binary64 mediante `Decimal.from_float`,
incluidos Vt y equivalentes pasivos ya redondeados. Evaluar en Decimal80 y
Decimal100. No se recalibran parámetros ni se introduce una ley de dispositivo.

El grafo conserva las fronteras nominales usadas por el laboratorio:
R61=200 Ω, BUS=0 V, R21 inferior=2000 Ω, R20 ON, Q21 base=2 V,
fuente loudness=0 V antes de acoplarla al contorno. Q18/base32 recibe luego
la carga R59 acoplada que ya incluye el sistema de 94 nodos. El primer
VCA comparte su suministro/balances y corrientes de base con el segundo.
Las cargas de juntura Q25/Q15 conservan sus parámetros sintéticos.

## Casos y gates fijados

Reutilizar el primer intervalo de las cuatro ventanas guardadas E4G8:
prefijo, ataque, reset y cola. Reconstruir el mismo voltaje candidato con
`fsum` de sus incrementos; las memorias y clocks previos permanecen intactos.

1. Comparar las 66 corrientes estáticas Decimal80 con el oráculo binary64
   en cada punto: discrepancia máxima **<10 pA**. Una diferencia rechaza el
   contraste de ese punto y se guarda; no se corrige una topología en silencio.
2. Contrastar precisión Decimal80/100 y registrar identidad de valores y
   Jacobianos redondeados a binary64, sin tratar identidad como error exacto.
3. Derivar por FD central **Decimal80**, con nodos/perturbaciones levantados
   sin redondearlos de nuevo a binary64. Pasos previamente fijados:
   **10⁻⁴, 10⁻⁵, 10⁻⁶, 10⁻⁷ y 10⁻⁸ V**, 66 columnas por punto.
   Gate de derivada por componente: **10⁻³⁰ S + 10⁻⁸·|Janalítico|**.
   La escala absoluta registra derivadas pequeñas; se retienen todos los pasos
   y fallos, sin seleccionar un paso favorable.
4. Sustituir sólo el bloque estático 66×66 en una copia diagnóstica de J94,
   manteniendo el contorno, la carga R59 y sellos dinámicos existentes.
   Resolver los 25 RHS con eliminación racional sobre coeficientes binary64;
   gates hacia atrás binario/Decimal80 **10⁻¹⁰**, gate de mapa **10⁻⁸**.
   Contrastar el mapa analítico Decimal80 con los cinco mapas FD Decimal80,
   Decimal100 y los mapas mixto/FD previos. El último contraste conserva
   su fallo original aunque los nuevos mapas coincidieran entre sí.
5. Añadir inyecciones hipotéticas de **memorias 7, 10 y C2=18**, actual
   únicamente, a ±1 µV y ±0,5 µV: **48 solves de un intervalo**, cuatro
   ventanas. Comparar las respuestas centrales con el mapa diagnóstico
   y con el mixto anterior, bajo el gate ya fijado de **10 nV + 10⁻³|pred|**.
   Esa escala no admite una precisión de derivada de 10⁻⁸. Cada solve exige
   publicación KCL<10 pA, rama<10 fV y reloj/memorias intactos.

Se guarda el grafo completo, voltajes, matrices, comparaciones, todas las
inyecciones y fallos, fuentes/hashes antes/después y entorno. El protocolo
permanece congelado; los resultados van en otro documento. La transcripción
independiente contrasta cálculo, no identifica una pieza vintage.

No se modifica el integrador original, un motor de audio, los informes
anteriores ni la política adaptativa. No se admite error acumulado, transición
física, audio o tiempo real. Un fallo abre una revisión con intento conservado.

`python tools/loudness_latch_bdf_static_precision.py`
