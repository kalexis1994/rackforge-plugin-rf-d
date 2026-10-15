# Padre sin DC del ladder: precisión conservada, costo aún rechazado

## Cambio ejecutado

El [generador](../tools/prepare_split_ladder.py) deriva un padre sin las
ocho resistencias/diez NPN del ladder DC. Conserva las 16 incidencias
dinámicas y la rama C10 originales, incluido bias 220 µF y acoplamientos
de entrada/salida. El [kernel](../crates/rf-d-circuit/src/split_ladder_kernel.rs)
retiene su stamp final para [transferirlo](../crates/rf-d-circuit/src/split_ladder_binding.rs)
una vez a las ecuaciones físicas. Las reacciones locales 9×9 se añaden
directamente al padre reducido; la congruencia local usa las incidencias
inmutables de T. No vuelve a evaluarse el ladder DC en el padre.

La [voz candidata](../crates/rf-d-circuit/src/split_ladder_voice.rs)
mantiene 111 coordenadas por etapa, 118 nodos físicos y el solver temporal
222 anterior. Conserva LOW, beta finita, fuentes, cargas y criterios de
convergencia/estimador originales. El [protocolo](SPLIT_LADDER_PROTOCOLO.md)
fijó gates y dominio nominal antes de ejecutar. No hay nueva calibración,
arranque, CV general, identificación física o admisión de RT.

El stamp pertenece al punto actual. La reconciliación de redondeo DD
calcula el offset compensado y aplica J·offset al DC, dentro del límite
128·epsilon²·max(1,abs(V)) V. Mayor offset, estado no canónico, sello no
finito o overflow rechazan antes de publicar cambios. Máximo observado:
2,465191e-32 V. Esto conserva la ley LOW analítica existente; no autoriza
reutilización entre estados o recetas. El padre rechaza corrientes o
enlaces DC nuevos en los interiores eliminados/diferenciales y conserva
enlaces legales nuevos entre coordenadas retenidas.

## Dos ensayos y un perfil

[Primer recibo](../evidence/split_ladder_native01.json): precisión pasa;
costo 31,802195 s frente a 16,526260 s del directo fresco, ratio 1,924343.
El padre usaba tipos propios y un adaptador de resultado físico. Rechazo
con fuentes/input/replay conservados antes de cambiarlo.

El [perfil](../evidence/split_ladder_profile01.json) del primero mide,
incluyendo replays: coordenadas 0,199328 s; kernel local 1,263518 s;
incremento físico 0,036839 s; llamada/retorno del padre 8,648849 s;
validación del padre 0,084135 s; proyección reducida 1,505038 s;
transferencia física 0,675065 s. 167.864 evaluaciones. Los timers terminan
antes del retorno de Stage: no cubren todas las copias/retornos ni son un
desglose exhaustivo. No permiten atribuir un tiempo a una copia concreta.
La trayectoria instrumentada coincide con el candidato; no es benchmark
de admisión y su costo no se usa para promoverlo.

El [segundo recibo](../evidence/split_ladder_native02.json) usa los tipos
State/Controls/Parts originales directamente en el padre y retira aquel
adaptador. Se repiten controles frescos y los mismos gates. Cambian el
conjunto y las condiciones temporales del ensayo; no se aísla causalmente
el efecto de cada modificación ni se infiere un comportamiento estadístico.

| Tiempo 32 µs por 60 ms de circuito, segundo ensayo | Resultado |
| --- | --- |
| Directo activo, control fresco | 17,017826 s |
| Unión reconstruida anterior, control fresco | 29,173873 s |
| Nuevo candidato separado | 26,787462 s |
| Ratio frente al directo / gate | **1,574082 / ≤0,90: rechazado** |
| Ratio frente a unión anterior | 0,918200; 8,18 % menos en este ensayo |

El menor costo frente a una unión anterior también rechazada no alcanza
para sustituir al directo activo: sigue costando 57,41 % más que éste.
Se conservan ambos rechazos y replays. No hay aceleración admitida.

## Precisión y controles ejecutados

[Probe de unión](../tools/split_ladder_local.rs),
[transferencia](../evidence/split_ladder_transfer01.json) y
[auditoría independiente](../evidence/split_ladder_audit01.json).

| Comprobación | Resultado |
| --- | --- |
| 48 etapas frente al grafo físico completo | DC/J: error 0 A / 0 S; ΔQ/masa iguales |
| 591.408 coeficientes del Jacobiano reducido frente a unión anterior | Error 0 S |
| FULL frente a residual | DC/ΔQ bit a bit en 48 etapas |
| Kernel desde 96 semillas perturbadas | Error reconstruido frente al anterior 0 V |
| Congruencia por incidencias | 2048 entradas finitas con cancelación; no nulas bit a bit, ceros numéricos iguales |
| Perímetro del padre/transferencia | 48 rechazos y 38 recuperaciones exactas; diez recuperaciones después de dos rechazos FULL/residual |
| Metadatos de transferencia adicionales | 30 rechazos atómicos con 30 retries exactos, incluidos dos overflows finitos y otro punto LOW |
| Enlace legal nuevo del padre | Se conserva y se retira en el retry siguiente |
| Gates de la unión reejecutados | 222 columnas FD, 144 direcciones y 36 rechazos del wrapper pasan |
| Trayectorias 64/32 µs de ambos candidatos | Prefijo completo antes de FINAL idéntico a la unión anterior: GRID/ROOT/SOLVER; estados finales iguales |
| Auditoría independiente del segundo | 5712 filas originales; residual ≤0,998264 pA, corrección ≤1,678588 nV |
| Newton / backward en las trayectorias finales | ≤0,999932 pA / 1,996897 nV; backward ≤9,997113e-12 |
| Publicación / heap del candidato final | Ocho replays y diez rechazos atómicos; cero asignaciones en integración |

Los márgenes anteriores de dirección/reconstrucción y corrección Newton
siguen siendo pequeños. Se conservan todos los gates. La auditoría evalúa
los endpoints nativos en las ecuaciones originales de 119 nodos, incluido
Amount; no genera otra trayectoria de referencia independiente.

El [cierre QA](../evidence/split_ladder_tests01.json) diferencia precisión y
costo: separación verificada, candidato no promovido. Directo de
`7c0524273048099f3fd246562c9b87d7cadffb61` activo. Los 255 tests Rust y
las 83 guardas del solver 222 anterior se conservan por identidad; no se
reejecutan esas suites. Los probes y trayectorias de esta tabla sí son
nuevos. Sin WAV, rlib, Cargo o inputs privados de sonido nuevos; binarios
y semillas retirados del área temporal única.

El primer cierre QA excedió el presupuesto previo de 8 MiB por duplicar
las mismas fuentes en los dos rechazos. Se conserva el
[fallo y replay](../evidence/split_ladder_qa_failed01.json). La
[compactación](../tools/compact_split_sources.py) comparte 33 imágenes de
fuentes y guarda cuatro reemplazos; el recibo 02 pasa de 6.239.059 a
1.544.171 bytes. La [prueba](../evidence/split_ladder_compaction01.json)
reconstruye exactamente los bytes originales y su SHA, que sigue ligado
a la auditoría previa. Los recibos quedan dentro de los mismos 8 MiB,
sin cambiar gates, fuentes medidas o resultados numéricos. Para leer las
fuentes de 02, usar `compact_split_sources.images` y para sus bytes medidos
`expanded_bytes`; el codec compartido referencia el recibo 01 por SHA.
La prueba registra Python/zlib y el nivel gzip del recompressor empleado.
Si otro runtime produce bytes gzip diferentes, falla el SHA del sobre;
las imágenes de fuentes siguen siendo legibles sin recomprimir. Reproducir
los bytes originales del sobre requiere aquel runtime registrado.

## Continuación concreta

El código aún resuelve el sistema reducido y, para comprobar convergencia,
factoriza además el sistema físico completo. El siguiente bloque debe
preparar el Newton actual una sola vez y reconstruir su corrección física
mediante Schur, incluyendo el residual algebraico remanente. Contrastar
esa corrección contra el solve original; conservar su gate y el estimador
físico. Perfilar ambos solves antes de atribuirles costo y volver a las
trayectorias/auditoría/costo fresco. Evitar más cambios de adaptadores sin
reducir ese trabajo algorítmico, manteniendo el directo activo mientras
no pase el gate de promoción.
