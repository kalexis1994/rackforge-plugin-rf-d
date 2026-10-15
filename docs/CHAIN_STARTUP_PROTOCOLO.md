# DC propio, memoria inicial y ataque de la cadena nominal

## Alcance y condiciones iniciales

Motor seleccionado por [incidencias](INCIDENCE_VOICE_RESULTADOS.md),
CA3046/SVC-204D nominal. Misma escena, leyes y cargas SVC-9 pp.9/19/13/10;
un solo VCO periódico de fase, sierra fija, mismas resistencias R6/R45.
Este arranque es de la cadena, no del circuito físico del VCO ni de la
alimentación del instrumento. No prueba parecido con un Moog físico.

Resolver DC a t=0, KEY=0, S abierto, fuente periódica congelada en su valor
en t=0. Capacitores abiertos en DC; sus tensiones iniciales salen de los
terminales convergidos. No imponer todas las cargas cero ni copiar un
estado de 40 ms de otra trayectoria. Se admite un origen de fase arbitrario
como condición del generador periódico ya existente, sin reajustarlo.

Dos aproximaciones de Newton: heurística publicada de nodos de volumen,
filtro/timer y DC parcial de la cadena audio del mismo modelo. La segunda
perturba esos voltajes numéricos. Son ayudas de convergencia en voltios,
no parámetros sonoros, raíces copiadas o trayectorias de preparación.
El resultado es una raíz conjunta propia de 118 incógnitas con HIGH/LOW.
No afirmar unicidad global del sistema con latches por usar dos semillas.

DC nativo: residual ≤1 pA y corrección completa ≤2 nV, máximo 100 Newton
y 28 backtracks, mismos límites eléctricos. Rechazo de semilla/control de
tiempo/budget inválidos, sin publicación parcial. Auditoría independiente
de 119 filas originales con Amount: ≤20 pA/2 nV; comparar ambas raíces
por nodo ≤1 µV. El DC congela la fuente; al liberar tiempo sus memorias
parten exactamente de ese resultado, sin hacer otro DC.

## Campaña temporal y gates

Reloj entero existente. KEY 0 hasta 1 ms, 10 V hasta 75 ms, después 0 V;
eventos exactos y estado continuo al cambiar KEY. Primera meta: observar
arranque/ataque y después completar 0–100 ms en dos perfiles 64/32 µs.
No declarar nota completa si sólo pasa un prefijo. Misma raíz inicial
para ambos, grilla común 125 µs. Motor temporal/estimador intactos:
Newton 1 pA/2 nV, error 500 µV+1e-4·abs(V), refinamiento J7 0,5 % RMS,
1,5 % pico, media 5 µV; C2/C5, BUS y corrientes según el contrato híbrido.

Conservar controles, todas las memorias, replays exactos, rechazo atómico
y heap cero. Auditar etapas seleccionadas de arranque, ambos lados de
KEY ON/OFF y final con las ecuaciones originales, 20 pA/2 nV. Contrastar
también el directo histórico sobre este estado inicial cuando la campaña
candidata pase. No comparar el ataque con la antigua rama que partía de
otra historia a 40 ms, ni tratarlo como validación física nueva.

Fijar semilla/publicación, entradas y fuentes antes de medir. Fallos con
replay sin cambios antes de corregir. Compiler/rlib congelados, un solo
tmp/lab-current vacío al terminar. Recibos ≤8 MiB sin QA, sin WAV, Cargo,
biblioteca, cache o muestras nuevas. Heredar tests anteriores por identidad,
declarando los bancos efectivamente ejecutados. Sin nueva admisión RT.
