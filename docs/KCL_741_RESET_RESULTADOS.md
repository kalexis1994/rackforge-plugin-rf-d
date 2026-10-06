# KCL del polo 741 y amplificación de residuales de corriente

2026-10-06. Continuación del [protocolo](KCL_741_RESET_PROTOCOLO.md), con
[resolución del pin externo](KCL_741_ALIAS_CORRECCION.md),
[presupuesto de ejecución](KCL_741_PRESUPUESTO_OBSERVACION.md) y
[reducción diagnóstica declarada](KCL_741_REDUCCION_DIAGNOSTICA.md).
La [auditoría](../evidence/voice_kcl_observation02.json) verifica fuentes,
artefactos y cálculos sin nuevos solves. La unión VCO/contorno sigue rechazada.

## Observación admitida y rechazos preservados

El inventario confirma R13/G4 en el nodo 16, L2/R13 en el 17 y una entrada
ideal de tensión de EOS en 16. Las fuentes MIF/POLY verifican que esa entrada
no agrega una corriente de carga. Se registraron conductancia R13=0.001 S
y transconductancia G4=3.1623e-8 S efectivamente estampadas, junto con los
voltajes anteriores/nuevos de siete nodos y la corriente de L2.

Se conservan tres dificultades de observación:

- La comprobación inicial del punto de inserción rechazó antes de aplicar
  parches, compilar o resolver. Se preservó la fuente y se verificó la copia
  íntegra antes de corregir esa comprobación.
- Cuatro solves conservaron sus trayectorias, pero no observaron el pin 1:
  `xic3.1` no existe porque XIC3 lo conecta a `QB_COLLECTOR`. Sus
  [registros incompletos](../evidence/voice_kcl_observation_rejection01.json)
  quedan rechazados. Otra copia cambia sólo el nombre buscado por la sonda.
- El control con el alias corregido agotó 120 s antes del export completo.
  Su [recibo](../evidence/voice_kcl_budget_rejection01.json) se conserva.
  Se repitió sólo esa escena con el mismo binario y límite de proceso 240 s;
  el runner derivado difiere en bytes únicamente en ese límite.

Son nueve solves en total: cuatro con observación incompleta, cuatro con
alias corregido y una repetición del control limitado por tiempo de ejecución.
Los [cuatro recibos admitidos](../evidence/voice_kcl_runs03.json) mantienen
los gates originales:

| Escena, sonda apagada/encendida | Identidad con baseline anterior | Resultado |
| --- | --- | --- |
| BUS cero | 219538 tiempos y seis vectores exactamente iguales | 40 ms completos |
| BUS variable | 7724 tiempos y seis vectores exactamente iguales | Mismo rechazo; último aceptado 2.277414365034117 ms |

El límite de proceso no altera paso mínimo, tolerancias o deadline de audio.
La trayectoria del ejecutable oficial continúa siendo diferente; las
conclusiones siguientes pertenecen a este build local.

## KCL pequeña y correcciones grandes coexistentes

En BUS variable se parearon 2897 solves; el último intento conserva 101.
Decimal de 80 dígitos reconstruye las dos KCL lineales completas de los nodos
16/17 y la ecuación de tensión EOS desde números binary64 observados.
No observa toda la KCL no lineal de la red ni una raíz independiente de ella.

| Magnitud | Máximo absoluto en el último intento |
| --- | ---: |
| KCL nodo 17 | 3.005020463e-22 A |
| KCL nodo 16 | 2.057978845e-21 A |
| Ecuación de tensión EOS | 1.101549407e-16 V |
| Corrección nodo 16 | 0.376550490 mV |
| Corrección nodo 17 | 0.376550490 mV |
| Corrección de la entrada de G4, v3−v49 | 6.892264537e-13 V |
| `req*gm*ulp(v3)` | 1.490008250 µV |

La iteración 101 cambia v16 unos 0.207585542 mV y la salida diferencial EOS
la misma cantidad, mientras v3−v49 cambia sólo 3.064215548e-14 V.
EOS conserva su ecuación y transmite el cambio de su control. Esto observa
el acoplamiento; no demuestra aún qué provoca todos los rechazos JFET.

## Reducción exacta con controles fijados

Se fijan para el diagnóstico v98, v3, v49 e historia estampada; se resuelven
algebraicamente sólo L2/R13/G4. Fraction verifica en **14353 registros**
(11456 del control y 2897 de BUS variable) la identidad exacta que descompone
la brecha v16−v16*. Sus entradas son los valores binary64 reales.

| Contribución | Máximo absoluto en BUS variable |
| --- | ---: |
| Brecha v16−v16* con controles fijados | 246.524676053 µV |
| `-(req+1/gR)*(iL+iG)` | 246.460274360 µV |
| Residual de la fila L2, con signo de la reducción | 2.442014444 µV |
| Residual KCL17 dividido por gR, con signo | 3.173152880e-16 V |

Cada máximo se evalúa por separado: no se suman máximos de iteraciones
distintas. La brecha máxima del control completo es 74.559225179 nV.
El gran coeficiente `req` amplifica el pequeño desajuste `iL+iG` en la
reducción. Una fila KCL muy pequeña en amperios no garantiza aquí una brecha
pequeña en voltios al mantener esos controles fijos.

La red completa puede modificar los controles y está realimentada por EOS.
La brecha diagnóstica **no es un error de la solución acoplada**, una cota
de convergencia o una causa demostrada del fallo oficial. L2 sigue siendo
un elemento artificial del macromodelo TI, sin identificación física vintage.

## Siguiente corte

Derivar y ensayar una representación de este subbloque que conserve su
transferencia, DC e historia sin amplificar del mismo modo el desajuste de
las ecuaciones de corriente. Antes de modificarlo: protocolo de equivalencia
algebraica y temporal, casos escalares independientes, control completo y
gates de forma/frecuencia/reset anteriores. Luego contraste entre builds
y cierre R45/contorno. La [hipótesis anterior del RHS variable](POLO_741_RESET_RESULTADOS.md)
permanece refutada; no se vuelve a seleccionar esa variante.

Pasan [41 regresiones enfocadas](../evidence/voice_kcl_tests02.json),
incluidas orientación, asociación, NaN, alias externo y reducción exacta.
Tarjeta, grafo, ejecutable oficial y WAV anterior conservan sus hashes.
No hay reformulación numérica medida, audio nuevo, admisión física o tiempo real.
