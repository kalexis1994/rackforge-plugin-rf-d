# Evaluación eléctrica preparada para la voz híbrida

## Función fijada antes de medir

Continuar la [voz condensada](HYBRID_SCHUR_RESULTADOS.md), CA3046/SVC-204D
nominal, 40–100 ms, KEY OFF a 75 ms, con el mismo perfil VCO, reloj,
semilla HIGH/LOW, cargas, Newton, Schur y estimador temporal. Se optimiza
la evaluación de las ecuaciones; no se ajustan parámetros audibles.

La cadena heredada vuelve a validar tarjetas y reducir panel/cargas en
cada trial, calcula Q26/Q28 y R59 de una frontera antigua y después
los descarta/sustrae al unir los contornos reales. El candidato:

- valida y prepara metadatos inmutables al construir Parameters;
- conserva las validaciones de estado/h/controles durante cada trial;
- omite el cutoff y R59 antiguos en el stamp de audio, ya presentes en
  el contorno compartido; C18 se cuenta sólo en éste;
- omite sumas de entradas exactamente cero al trasladar matrices,
  inspeccionando todas las entradas reales, sin máscara de sparsity;
- conserva leyes BJT/diodo, compensación HIGH/LOW y las cargas de cadena.

Fuentes: SVC-9 pp.9/13/19 y p.10, mismas tarjetas e hipótesis del
grafo admitido. Derivación reproducible desde los fuentes originales
de circuit66, chain_charge y dual_voice_chain, sin alterar esos archivos.
No se almacena un Jacobiano de otro estado o h. Parameters preparado
pertenece a su configuración; no es una cache global mutable.

## Gates previos

- 48 etapas de los 24 pares heredados: DC/dQ ≤20 pA + 1e-7·abs(ref),
  Jacobiano/masa ≤2e-9 S + 2e-7·abs(ref), estados reconstruidos exactos.
- 118 columnas de diferencia finita en cuatro etapas seleccionadas,
  ±1 µV, incluidos BUS, VCA_BASE y TAIL: ≤2e-9 S + 2e-5·abs(FD).
- Dos trayectorias propias, techos full 64/32 µs, 481 observaciones
  cada una y los 118 estados finales, frente al Schur previo:
  voltajes ≤20 µV + 2e-6·abs(V), cargas ≤2 nA + 2e-5·abs(I),
  J7 RMS ≤0,1 %, pico ≤0,3 %, media ≤1 µV.
- Mantener gates contra la voz completa: J7 RMS 3 %, pico 6 %, media
  10 µV, además de C2/C5, BUS y R59/R60 del protocolo de unión.
- Auditoría original de 24 pares/5712 filas, Amount explícito:
  residual ≤20 pA y corrección ≤2 nV. Candidatos nativos auditados,
  sin afirmar una segunda trayectoria original independiente.
- Newton 1 pA/2 nV, backward Schur ≤1e-11 y estimador sin cambios.
  Rechazos de paso y retries exactos; heap cero en integración medida.
- Control fresco de Schur previo con mismo tramo/techo, flags y equipo.
  Admitir ahorro de costo sólo si ratio candidato/control ≤0,90.
  Si no pasa costo, conservar como ensayo aunque sea correcto.

## Recursos y alcance

Compiler/rlib congelados, sin Cargo o biblioteca nueva. Un solo
`tmp/lab-current`, retirando ejecutables/exports al guardar métricas.
Sin WAV ni carpetas de muestras. Fallos con fuentes, entrada acotada
y replay sin cambios antes de reparar. Mantener todos los inputs
admitidos y los gates. Dominio nominal heredado; sin arranque, CV
general, fidelidad física, antialias de producción o tiempo real.

## Ajuste de implementación tras el rechazo de costo

El primer candidato pasa etapas, FD y trayectorias, pero cuesta 1,03873
del control fresco: rechazo por el mismo gate 0,90, guardado con replay
en `hybrid_stamp_native02.json`. El siguiente usa coordenadas naturales
al estampar (mismo orden de acumulación por celda), sin permutación
densa posterior. Además comprueba finitud de cada entrada copiada o
suma no nula en el ensamblado de 118 nodos, en vez de recorrer después
las matrices completas otra vez. Las celdas restantes se inicializan
a cero y todas las entradas de las piezas se inspeccionan.

El stamp audio de 66 nodos conserva su comprobación completa de finitud.
La envoltura de 68 conserva chequeos de estado/h, DC y dQ; sus matrices
se verifican al transferirlas al sistema de 118. Los capacitores lineales
tienen constantes finitas y h≥MIN_DT_S; las cuatro filas omitidas son
los antiguos nodos de cutoff, ahora vacíos. Las entradas copiadas de
contorno se verifican explícitamente. Toda suma de matriz puede rechazar
un resultado no finito. No se elimina la protección por overflow de las
leyes no lineales ni se impone una máscara de coeficientes permitidos.

El candidato anterior también queda rechazado por costo (ratio 1,03550,
`hybrid_stamp_native03.json`, con replay). Se añade una ruta de residual
para trials fuera del gate Newton: evita construir matrices de audio y
su transferencia. Conserva corrección HIGH/LOW mediante J·LOW analítico
por dispositivo; no redondea el estado ni omite LOW. Se contrasta en las
mismas 48 etapas con gate DC/dQ 20 pA + 1e-7·abs(ref). Cerca del gate
de Newton se reevalúan residual/Jacobiano completos para el mérito de
nodos débiles. Newton, solución publicada y estimador siempre usan la
ruta completa. Todos los gates exteriores y de costo permanecen iguales.

Esa ruta reduce costo a 0,901787 del control, todavía por encima del
gate: `hybrid_stamp_native04.json` se conserva como rechazo con replay.
El siguiente candidato fuerza inline en las envolturas de ensamblado
preparado y en el evaluador de audio. Permite eliminar materialización
de matrices temporales no utilizadas por el modo residual. No cambia
leyes, validaciones o flags del compiler; se vuelve a medir contra el
control fresco y con el mismo gate. No atribuir una mejora posterior
únicamente a preparar metadatos o quitar las ramas duplicadas.

El inline inicial no cumple costo (0,922739, recibo/replay
`hybrid_stamp_native05.json`). Se acota la interfaz de trials a retornar
sólo DC/dQ y se ensamblan ambas etapas con accesos directos, conservando
el orden de operaciones por fila. La envoltura de Parts también se
expande para eliminar matrices temporales no usadas. La ruta completa
y el mérito cerca de Newton se conservan. Se repiten los mismos
contrastes eléctricos y de costo; un gate casi aprobado sigue rechazado.

Ese candidato también falla costo (0,913501, `hybrid_stamp_native06.json`,
con replay). Se extiende la ruta de residual a volumen/filtro, incluidos
sus puertos compartidos: J·LOW se calcula por dispositivo y por puerto,
sin omitir las componentes LOW de C5, reset, VCA_BASE o TAIL. Las cargas
no lineales de las seis parejas de latch siguen evaluándose con la ley
original compensada, aunque no se materialice su matriz en un trial.
La ruta completa conserva DC/Jacobiano/masa y vuelve a contrastarse en
las mismas 48 etapas, FD, trayectorias y gates originales. Se eliminan
trabajos no consumidos en trials; no se aproximan los contornos.

El candidato queda apenas fuera del gate de costo (0,900573,
`hybrid_stamp_native07.json`, con replay), sin redondearlo a aprobado.
El siguiente calcula HIGH/LOW provisional una sola vez en la frontera
de 118 nodos y proyecta ese mismo candidato a contornos/audio. Antes de
proyectar valida old/delta/candidato y su representación canónica, en
ambos modos. Los helpers internos reciben estado prevalidado y mantienen
los chequeos de h, controles y finitud de leyes/ensamblado. No recalculan
la misma suma compensada ni vuelven a validar las proyecciones parciales.
La historia anterior y los incrementos de carga permanecen separados y
sin cambios. El dominio nominal exige voltajes absolutos menores que
40 V, ya heredado de State; no se extiende a extremos del API genérico.
Se vuelven a medir los mismos gates de etapas, FD, voz, memoria y costo.

El candidato de estado compartido también falla costo (0,918001,
`hybrid_stamp_native08.json`, con replay). Se cambia la acumulación de
J·LOW en el modo completo: usar las mismas derivadas por dispositivo
y por puerto que en el modo residual, evitando productos densos con
entradas nulas. Se conservan LOW, Jacobiano completo y cargas. Es una
reordenación de sumas f64, no una aproximación de la compensación.
Incluye R14/C10 y BUS explícitamente; no duplica corrección en las
interfases. Los mismos gates de etapas, FD, voz, memoria y costo se
mantienen, incluida auditoría original con su acumulación independiente.
