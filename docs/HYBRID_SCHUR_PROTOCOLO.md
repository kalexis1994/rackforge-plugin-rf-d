# Condensación dinámica de la voz híbrida nominal

## Función y frontera, antes de medir

Continuar la [unión admitida](HYBRID_VOZ_RESULTADOS.md), CA3046/SVC-204D
nominal, 40–100 ms, panel fijo, KEY OFF a 75 ms. Mismo perfil periódico,
reloj, semilla HIGH/LOW, ecuaciones, tolerancias y estimador adaptativo.
No cambia el método Radau ni se elimina ninguna memoria física.

Las 118 incógnitas se separan en contornos `0..53`, audio `56..117`,
y puertos comunes `54=VCA_BASE`, `55=TAIL`. En el Jacobiano Radau de
236 filas, los dos bloques interiores tienen 108 y 124 incógnitas;
la frontera exterior tiene cuatro: ambos puertos en ambas etapas.
Incluye acoplamiento de cargas entre etapas; no condensa sólo DC.
Se verifica en cada matriz que no haya enlaces directos entre interiores.
Un enlace inesperado rechaza el solve, no se omite por una máscara.

Fuentes eléctricas heredadas: SVC-9 pp.9/13/19 (contornos, ladder/VCA
y panel), p.10 salida; parámetros y conflictos documentales permanecen
en el grafo admitido. La partición deriva de su conectividad. No añade
constantes audibles, cambia dispositivos o ajusta el sonido.

## Operación

Para cada bloque `A`, resolver `U=A^-1 b` y `W=A^-1 J_ip` por LU
con pivote escalado. Resolver el complemento de Schur de cuatro filas
`S=J_pp-sum(J_pi W)` con RHS `b_p-sum(J_pi U)`. Reconstruir
`d_i=U-W d_p`; comprobar las 236 ecuaciones originales del sistema
lineal. La historia anterior permanece fija en todos los trials.
Los factores se vuelven a calcular para cada Jacobiano; no se reutiliza
una linealización de otro estado o h. Workspace fijo, sin heap.

## Gates previos

- Backward por fila ≤1e-11, suma/productos compensados y escala
  `abs(b)+sum(abs(J)*(abs(d)+2 nV))`. Hasta tres refinamientos sobre
  el sistema completo; rechazo si no mejora o no satisface el gate.
- Newton original: ≤1 pA y ≤2 nV, mismo presupuesto y búsqueda de
  línea. Estimador y publicación atómica sin cambios.
- Dos trayectorias propias, techos full 64/32 µs. Comparar las 481
  observaciones y los estados finales contra el híbrido previo.
  Voltajes físicos: ≤20 µV+2e-6·abs(V); cargas R59/R60:
  ≤2 nA+2e-5·abs(I). J7 RMS ≤0,1 %, pico ≤0,3 %, media ≤1 µV.
- Conservar los gates anteriores contra el circuito completo de 250
  incógnitas: J7 RMS 3 %, pico 6 %, media 10 µV; C2/C5, BUS y cargas.
- 24 pares seleccionados, 5712 filas originales, Amount explícito:
  residual ≤20 pA/corrección ≤2 nV. Evaluación independiente de
  candidatos nativos, no otra trayectoria original nueva.
- Contraste local de correcciones en los 24 pares heredados, ocho RHS
  por par (residual real, VCA_BASE/TAIL/BUS por etapa y combinación
  reproducible). Backward y comparación con solve monolítico:
  ≤2 nV+1e-7·abs(d_ref) por incógnita. Sin RHS sólo de filas físicas.
- Verificar rechazo de un enlace interior no permitido en ambas
  orientaciones, RHS no finito y retry válido exacto.
- Heap cero durante integración. Medir una ejecución nueva del híbrido
  previo en el mismo banco y plataforma. Para admitir una aceleración,
  costo por ms simulado ≤90 % del control fresco; mismo tramo/techo.
  Un resultado correcto que no acelera se conserva como ensayo.

## Recursos y límites

Compiler y rlib congelados; sin Cargo/cache/biblioteca nueva. Un único
`tmp/lab-current`, exports compactos y recibos comprimidos con SHA.
Sin WAV ni carpetas permanentes de muestras. Fallo y replay inalterado
antes de reparar; no aflojar gates. Memoria de estado sigue completa:
se reduce el problema lineal exterior, no el número de cargas físicas.
El éxito no admite arranque, controles generales, parecido físico o RT.

## Reparación del contraste lineal

El ensayo local inicial rechaza una diferencia de corrección de 22,069
veces el gate. Se conserva con replay en `hybrid_schur_native01.json`.
Un diagnóstico sobre las mismas 192 matrices/RHS muestra que refinar
el solve monolítico tres veces con residual compensado reduce la fracción
máxima a 0,648, con el Schur sin cambios. El control lineal pasa a usar
esa referencia refinada y a comprobar también su backward ≤1e-11.
No cambia el híbrido monolítico usado en trayectorias o costo, ni los
gates, matrices o RHS del contraste. El diagnóstico y sus fuentes quedan
guardados. Una resta entre soluciones mal condicionadas no identifica
por sí sola cuál solve produce el error.

## Reparación del costo

El primer Schur que pasa el contraste eléctrico reconstruye los estados,
pero tarda 29,697 s frente a 28,597 s del control fresco: ratio 1,0385,
rechazado por el gate ≤0,90. `hybrid_schur_native02.json` conserva
fuentes, métricas y replay. El siguiente candidato almacena la frontera
triangular durante la LU y elimina las cuatro resoluciones auxiliares
de respuesta por bloque. Son las mismas ecuaciones y complemento de
Schur, con forward de RHS y reconstrucción por sustitución triangular.
No cambia las memorias, escena o gates. Ambos interiores y sus cuatro
puertos se reconstruyen antes de evaluar Newton y error temporal.

El candidato con frontera triangular pasa eléctricamente, pero sólo
reduce costo a 0,93493 del control y queda rechazado por el mismo gate
0,90 (`hybrid_schur_native03.json`, replay conservado). El siguiente
mantiene esa LU y evita armar la matriz Radau completa durante trials
que sólo necesitan residual. Las piezas eléctricas se evalúan iguales;
se arma Jacobiano para Newton y para el mérito de nodos débiles cuando
corresponde. La matriz se pasa prestada al solver, sin copia innecesaria.
No se cambia aceptación, búsqueda de línea, operaciones de residual o
reconstrucción; nuevo contraste con el control intacto y mismos gates.
