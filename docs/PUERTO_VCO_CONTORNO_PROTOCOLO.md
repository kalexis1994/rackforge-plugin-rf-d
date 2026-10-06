# Separación numérica en R45: protocolo

El primer banco monolítico VCO/contorno rechaza las cuatro escenas durante
reset. Se conserva completo en `evidence/loudness_voice_screen01.json.gz`.
No se elimina una carga para declarar aceptada esa red.

Se ensaya relajación de ondas en el resistor físico R45 de 33 kohm del
[mezclador](MEZCLADOR_PANEL.md). Cada iteración resuelve desde DC las dos
historias completas: el VCO recibe BUS anterior; placa 4 recibe el cursor
R6 nuevo **a través de R45**. El BUS resultante vuelve al VCO siguiente.
Cada subproblema representa el mismo resistor; la red física ensamblada
tiene uno, no dos en serie. Ningún buffer, ESR o tarjeta nueva.

Las fronteras PWL son iterativas. Hasta cerrar tensión y corriente son
dos circuitos conducidos por fuentes; no una voz admitida. Las fuentes de
rieles son ideales e independientes como antes. No se modela su impedancia
compartida. Se mantienen `.ic v(RAMP_C1)=0` y el arranque del oráculo.
No se trasplanta ni reinicia un estado de carga durante una nota.

## Gates congelados antes del ensayo

- Horizonte 40 ms y máximo 500 ns para el primer control con contorno 2 V.
  Misma placa, tarjetas, trims y parámetros del nominal monolítico que
  completa; VCO con KLU/bypass=0/itl4=100, placa independiente Sparse.
- Semilla BUS=0 en todo el horizonte. Máximo diez iteraciones completas.
  Rechazo de un solve o agotamiento detiene el banco y conserva los recibos.
- Cada PWL simplifica la polilínea exportada con error máximo 1 microvolt.
  Se verifican **todos sus vértices**, extremos incluidos. El bound continuo
  corresponde a esas polilíneas, no a una solución física entre muestras.
- Cierre: máximo de tensión BUS <=10 microvolt y suma de corrientes de
  las dos fuentes de puerto <=1 nA en la unión de sus relojes completos.
  La corriente VCO además coincide con (R6-BUS)/R45 dentro de 1 nA.
  No se alinea fase ni se compara sólo una grilla que omita resets.
- El control cerrado debe contrastar BUS, recuperación y salida contra
  la traza monolítica nominal500: máximo <=5 mV en la unión de relojes,
  frecuencia <=1 cent por cruces de rampa -2 V ascendentes desde 2.01 ms.
- Sólo si ese control pasa se ensayan las cuatro escenas del
  [protocolo de unión](CONTORNO_VCO_UNION_PROTOCOLO.md) con contorno físico.
  Mismos tres contrastes, ventanas y balances acumulados de ambos C2.

No se extiende duración ni se renderiza audio de una pareja sin admisión.
El método es un laboratorio fuera de tiempo real. Un cierre muestreado no
prueba unicidad o estabilidad global de la relajación; los extremos, el
contorno de filtro, otros osciladores y hardware identificado siguen abiertos.
