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
