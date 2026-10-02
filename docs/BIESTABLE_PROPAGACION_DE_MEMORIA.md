# Propagación de memoria BDF2 en ventanas de circuito

## Pregunta y dominio

El [cúbico exacto](BIESTABLE_DEFECTO_Y_MEMORIA.md) muestra cómo el historial
compartido puede ocultar error. Este corte deriva una transferencia local
para el circuito sintético de 94 nodos y la contrasta con solves no lineales.
No usa la discrepancia completo/medios como defecto temporal exacto.

Se fijan cuatro límites de anclaje E4G8: **2,3 ms**, **2,4222 ms**,
**2,44205 ms** y **2,5 ms**. Cada ventana parte del último ensayo aceptado
no posterior al límite y conserva los **16 intervalos siguientes** del
[barrido desde DC](BIESTABLE_CRECIMIENTO_DESDE_DC.md), con ambos historiales,
fuentes y reloj originales. Se reproduce cada estado de referencia.

## Derivación en coordenadas de memoria

El vector m contiene 21 voltajes de capacitor y cuatro cargas QBE/QBC
divididas por **10⁻¹² C/V**, exclusivamente como escala de coordenadas.
Esa escala no es una capacitancia física añadida ni un parámetro de sonido.
Los potenciales nodales entrantes son semilla; se perturban aquí memorias
guardadas independientemente. La inyección hipotética **no representa un
estado pasado aceptado** ni una perturbación física calibrada.

Con los coeficientes BDF2, γ=a₂/a₀ y dt_eff=h/a₀:

`δm*= (1+γ)δm_current − γδm_previous`

El residuo nodal linealizado satisface `J δv = B δm*`. Para cada capacitor
lineal, B estampa su incidencia por `g=1/(dt_eff/C+R)`. Para QBE/QBC,
la incidencia B−E/B−C se multiplica por la escala de carga/dt_eff.

Después de resolver `X=J⁻¹B`, la publicación tiene
`δm_new = (P X + D)δm* = Tδm*`. Las ramas sin resistencia publican el
voltaje terminal. C10 conserva R=25,5 kΩ: su peso es
`β=dt_eff/(dt_eff+R C)`, con β por voltaje terminal y 1−β por memoria
virtual. Las cargas nuevas usan dQ/dV en las junturas del estado de destino.
La transferencia de dos historiales es `[(1+γ)T, −γT; I, 0]`.

J conserva el evaluador existente: audio estático por FD, contorno y carga
con sus derivadas existentes. El contraste completamente FD usa ±1 µV
en los 94 nodos; comparte el circuito y no es un oráculo físico independiente.

## Protocolo fijado antes de ejecutar

En cada anclaje se prueban cuatro direcciones:

- C2 actual: +1 µV en su memoria actual, cero en la precedente.
- C2 común: +1 µV en ambas memorias.
- C2 diferencial: +1 µV actual y −1 µV precedente.
- Diferencia de memorias fino−completo del ensayo aceptado del anclaje:
  sólo memoria actual; amplitud sin unidades. Se mantiene el intervalo
  precedente completo, sin sustituirlo por el historial medio.

Cada dirección usa signos ± y amplitudes **1 y 0,5**, para 16 continuaciones
por ventana, hasta **1024 intervalos no lineales nuevos** más 64 de referencia.
Se comparan respuestas centrales `(plus−minus)/2` con el tangente del mismo
signo/amplitud: gate nodal **10 nV + 10⁻³·|predicción|** en cada componente.
Es un gate local de linealización a estas amplitudes; no una cota temporal.

El solve matricial exige error hacia atrás componente a componente <10⁻¹⁰.
En el primer intervalo de cada ventana se contrasta X contra J completamente
FD con diferencia escalada `|X−Xfd|/(1+|X|)<10⁻⁸`. Se preserva un diagnóstico
FD fallido sin relajar esos gates. La magnitud del mapa depende de la escala
de coordenadas y no se presenta como una ganancia física universal.

Cada continuación comprueba KCL <10 pA, rama <10 fV, restauración exacta,
ratio ≤2, mínimo real 1 ps y memoria entrante intacta. No aplica el estimador
adaptativo al perturbar: el reloj está condicionado a la referencia, y estos
estados permanecen provisionales. Se guardan solves fallidos y cobertura.

Productores: `tools/loudness_latch_bdf_memory_transfer.py` y
`tools/loudness_latch_bdf_memory_windows.py`.

`python tools/loudness_latch_bdf_memory_windows.py`

Fuentes y E4G8 se identifican por SHA antes/después. El archivo canónico
gzip y su resumen conservan todos los estados, matrices y rechazos propios;
los informes anteriores permanecen intactos. No hay promoción de un
controlador, refinamiento global, error exacto, hardware ni audio.

## Primer intento y solve equilibrado

El productor declarado en `4f958b1` falla en el primer mapa de prefijo:
error componente a componente **0,99999547**, frente a gate 10⁻¹⁰.
El número de condición de J es ≈1,983×10¹⁶; el componente que dispara
el rechazo tiene denominador ≈9,985×10⁻²⁸. El intento conserva su matriz,
estado inicial, paso de referencia, fuentes originales completas, SHA y
fallo en `evidence/loudness_latch_bdf_memory_windows_attempt1.json.gz`.

La segunda revisión usa escalado de filas/columnas y hasta **ocho**
correcciones de refinamiento, con el residuo de los mismos J/B evaluado
en Decimal80. Se exige el **mismo 10⁻¹⁰** tanto al residuo binario anterior
como al residuo Decimal80. No se cambia J, B, topología, gate de Newton
o una memoria de referencia, ni se recortan coeficientes pequeños.

La sonda del primer mapa necesita una corrección y da ≈4,15×10⁻¹³ en
ambas medidas. Eso habilita repetir el experimento completo; no sustituye
sus contrastes no lineales ni el diagnóstico completamente FD.

## Suplemento FD declarado después del barrido de ventanas

La segunda revisión completa las 1024 etapas y pasa sus 32 contrastes
centrales. Sus 64 mapas con el evaluador mixto pasan el solve equilibrado.
El mapa completamente FD de la cola pasa; los tres primeros conservan
fallos algebraicos después de ocho correcciones. Sus informes permanecen
intactos, con ese gate abierto.

Se declara otro contraste antes de ejecutarlo: levantar cada entrada
binary64 de **los mismos Jfd/B** a una fracción exacta y resolver por
eliminación racional con pivoteo. Se verifica `Jfd·X=B` exactamente antes
de redondear X a binary64. Luego se repiten ambos gates de error hacia
atrás 10⁻¹⁰ y el gate escalado mixto/FD 10⁻⁸. Una matriz exactamente
singular se registra como fallo; no se cambia el paso FD, J, B o el gate.

El suplemento prueba los primeros intervalos de las cuatro ventanas, no
reintegra ni reescribe las 1024 etapas. Su precisión es algebraica sobre
coeficientes ya redondeados; no convierte FD en derivación exacta del
circuito ni amplía la cobertura de direcciones/tiempo.

`python tools/loudness_latch_bdf_fd_transfer_audit.py`

## Resultado de las cuatro ventanas

Las 64 continuaciones hipotéticas completan **1024 intervalos nuevos**, más
64 de replay de referencia, sin alterar el reloj ni las memorias entrantes.
Los **32/32 contrastes centrales** pasan el gate declarado. El mayor error
normalizado es 0,00019610 (reset, C2 diferencial, amplitud 1; límite 1).
Los 64 mapas mixtos pasan ambos gates algebraicos; su máximo es
7,97201×10⁻¹¹ en ataque, bajo el límite 10⁻¹⁰.

| Ventana | Máxima KCL publicada (A) | Respuesta C2 actual (µV) | C2 común (µV) | C2 diferencial (µV) | Memoria fino−completo (nV) |
| --- | --- | --- | --- | --- | --- |
| Prefijo | 1,64609×10⁻¹² | 1,49999 | 0,999999 | 1,99998 | 3,39891 |
| Ataque | 1,32962×10⁻¹³ | 1,58052 | 1,13723 | 2,02382 | 15,6358 |
| Reset | 3,67139×10⁻¹⁵ | 1,50000 | 1,00000 | 2,00000 | 4,35447 |
| Cola | 6,83719×10⁻¹⁴ | 1,49997 | 0,999999 | 1,99995 | 11,0384 |

Son máximos centrales entre los 94 nodos y 16 intervalos, a amplitud 1.
La última columna usa la diferencia de memorias del anclaje guardado;
no representa un error exacto ni explica por sí sola el máximo desde DC.
Las respuestas a amplitud 0,5 se contrastan por separado.

## Resultado del suplemento racional

Las cuatro matrices Jfd/B tienen residuo racional exactamente cero antes
de redondear X. Después del redondeo, los errores hacia atrás binarios y
Decimal80 quedan por debajo de 1,329×10⁻¹⁶ y 9,741×10⁻¹⁷ respectivamente.
Eso cierra el contraste algebraico del suplemento, con los coeficientes
originales intactos. El contraste de mapas pasa **3/4**:

| Ventana | Diferencia escalada mixta/FD | Gate 10⁻⁸ |
| --- | --- | --- |
| Prefijo | 8,66717×10⁻¹⁰ | Pasa |
| Ataque | 1,74284×10⁻⁹ | Pasa |
| Reset | **1,34857×10⁻⁶** | **Falla** |
| Cola | 1,06786×10⁻⁹ | Pasa |

En reset, el máximo corresponde a fila nodal 27, columna de memoria 10:
X mixto=0,9951210990927287 frente a Xfd=0,99511840853223. Esta localización
es una inspección posterior de las matrices archivadas, sin nueva admisión.
Las cuatro direcciones no lineales verificadas no cubren las 25 columnas
independientes: su éxito no cierra el gate de la matriz completa.

Se preservan los tres fallos algebraicos originales del solve FD iterativo,
el primer intento sin equilibrar y el fallo de mapa en reset. El suplemento
no reescribe ninguno ni cambia el paso FD de ±1 µV.

## Evidencia y regresiones

- [Ventanas completas](../evidence/loudness_latch_bdf_memory_windows.json.gz):
  7.719.625 bytes, SHA256 comprimido
  `ca71f1e36ad995719e31155b478cee5ad1824deef248005a04bee137359d359c`.
- [Resumen de ventanas](../evidence/loudness_latch_bdf_memory_windows_summary.json).
- [Suplemento FD](../evidence/loudness_latch_bdf_memory_fd_audit.json.gz):
  111.879 bytes, SHA256 comprimido
  `12a88c2146e6bb7f2b658a96b67f59e975463457d2e8beb6f1dfd37cbb7e0d94`.
- [Resumen FD](../evidence/loudness_latch_bdf_memory_fd_audit_summary.json).
- [Recibo de validación](../evidence/loudness_latch_bdf_memory_windows_validation.json):
  **3+7=10 pruebas**, un intento exitoso, comandos/exit codes/salida y
  hashes de entradas sin cambios. Comprueba el fallo original, los sellos,
  todas las publicaciones, 32 contrastes, replay de 64 intervalos no lineales
  seleccionados y las cuatro eliminaciones racionales.

`python tools/validate_bdf_memory_windows.py`

El HEAD contextual de las ventanas es `910c6e2`; el del suplemento y de las
regresiones es `a22d2f1`. Los SHA identifican los bytes reales de entrada;
el commit que archiva sus resultados puede ser posterior.

## Siguiente gate

Auditar la sensibilidad del contraste FD de reset a su paso y al cálculo
separado de las contribuciones estáticas/dinámicas, conservando el fallo
original de ±1 µV. Declarar esa auditoría antes de ejecutar y retener todos
sus resultados, sin escoger un paso por el resultado favorable. Después,
contrastar más direcciones de memoria y ventanas más largas antes de usar
los mapas para estimar error acumulado. Los gates global de 1 mV, físico,
audio y deadline permanecen abiertos.

La [sensibilidad FD posterior](BIESTABLE_RESULTADOS_SENSIBILIDAD_FD.md)
completa ese primer diagnóstico con 40 matrices y conserva reset fallido.
La [auditoría de entradas históricas](REPRODUCIBILIDAD_DE_ENTRADAS_HISTORICAS.md)
archiva los tres JSON CRLF usados en Windows y prueba reconstrucción de
sus SHA desde los blobs Git, sin reescribir este experimento.
