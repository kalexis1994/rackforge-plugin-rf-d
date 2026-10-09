# Ciclos propios de dos memorias corregidas

2026-10-09. [Protocolo](VOZ_CICLOS_CORREGIDOS_PROTOCOLO.md),
[raíces exactas](../evidence/voice_joint_corrected_cycles_inputs01.json),
[ejecución](../evidence/voice_joint_corrected_cycles_native01.json),
[contraste eléctrico](../evidence/voice_joint_corrected_cycles_reference01.json),
[comparación de derivas](../evidence/voice_joint_corrected_improvement01.json) y
[QA](../evidence/voice_joint_corrected_cycles_tests01.json).

## Trayectorias completas y refinamiento

Dos memorias corregidas, dos resoluciones: cuatro trayectorias propias
hasta 5,25 ms/2.752.512.000 ticks. El caller temporal es idéntico por bytes
al anterior; cambia el checkpoint inicial. Física y biblioteca congeladas.
La raíz guess=0 de cada cierre inicializa el motor, no el lift de Scene.

La escena conserva R61=200 Ω en el divisor de polarización, R30=830 Ω
y el retorno de énfasis cerrado con R14=25 kΩ: serie efectiva de 25,5 kΩ.
Ambas campañas usan estos mismos controles. R61 no es el control de énfasis.
Estas trayectorias no diagnostican por sí solas autooscilación; las derivas
se atribuyen a esta escena concreta, sin inferir su causa física.

| Memoria | Máxima media etapa | Intervalos | Frecuencia | ΔC27 por fase | ΔC10 por fase | ΔJ7 por fase |
|---|---|---:|---:|---:|---:|---:|
| 0 | 125 ns | 23854 | 410.801786893 Hz | +2.137917 µV | +65.282578 µV | -224.263235 µV |
| 0 | 62.5 ns | 44733 | 410.801784940 Hz | +2.137943 µV | +65.282578 µV | -224.263239 µV |
| 1 | 125 ns | 23853 | 410.801787134 Hz | +0.074162 µV | +59.915714 µV | -178.873515 µV |
| 1 | 62.5 ns | 44736 | 410.801785181 Hz | +0.074188 µV | +59.915714 µV | -178.873519 µV |

137176 intervalos/274352 medios endpoints. Cuatro prefijos de 2 µs
idénticos por bytes a las liberaciones corregidas previas; ocho restores
exactos a 250 µs/2,25 ms. 23 checkpoints por perfil: inicial, 2 µs y
21 anclas. 200 coordenadas a 22 relojes no iniciales por memoria,
peor ratio 0.0296681785. Frecuencia entre resoluciones: máximo
8.22922736e-06 cent; extremos 3.95639852e-07 V. Gates originales.

19200 ecuaciones nuevas en 96 puntos de etapa seleccionados, 96 corrientes
de terminales y 16 LTE independientes. No son nuevas raíces independientes.
Cada perfil tiene dos resets/un periodo observado: no son periodos
consecutivos asentados de una misma historia.

## Resultado de la predicción estática

Memoria 0: J7 -223.000778→-224.263239 µV por fase; 6/18 cargas reducen su deriva absoluta.
Memoria 1: J7 -199.636473→-178.873519 µV por fase; 5/18 cargas reducen su deriva absoluta.

Memoria 0: C27 reduce su deriva absoluta 105.271 veces; C10 la multiplica por 1.787637. La mayor deriva nueva corresponde al índice 9 (24→25, 3.3e-07 F): +1.850928→+3.859716 mV por fase.
Memoria 1: C27 reduce su deriva absoluta 78.541 veces; C10 la multiplica por 1.208284. La mayor deriva nueva corresponde al índice 9 (24→25, 3.3e-07 F): +2.611667→+3.720029 mV por fase.

El contraste refuta la hipótesis de mejora global para estas correcciones
estáticas. No se admite ninguna como memoria asentada de toda la cadena.

Todos los cambios se comparan con su memoria anterior a igual resolución
y fase interpolada rampa=-2 V. Las tablas conservan signos y empeoramientos.
Los ratios son |nuevo|/|anterior|; una base cero no admite división.

| Memoria a 62,5 ns | Capacitor | Δv anterior (µV) | Δv nuevo (µV) | Ratio absoluto | Observación |
|---|---|---:|---:|---:|---|
| 0 | índice 0 | +335.467892291 | +422.605607463 | 1.25974979 | aumenta |
| 0 | índice 1 | +932.912785180 | +975.599947477 | 1.04575686 | aumenta |
| 0 | índice 2 | +994.071372278 | +886.711107171 | 0.89199944 | reduce |
| 0 | índice 3 | +472.063686962 | +237.921373715 | 0.504002702 | reduce |
| 0 | índice 4 | -10.375491334 | +1.677404610 | 0.161669896 | reduce |
| 0 | C27 | +225.063565987 | +2.137943161 | 0.00949928591 | reduce |
| 0 | índice 6 | +62.047680476 | +118.709449964 | 1.91319722 | aumenta |
| 0 | índice 7 | -64.479567053 | -121.365078503 | 1.88222539 | aumenta |
| 0 | índice 8 | +205.571275815 | +673.634158714 | 3.27688854 | aumenta |
| 0 | índice 9 | +1850.927725312 | +3859.715657200 | 2.08528707 | aumenta |
| 0 | índice 10 | +2.568527727 | +5.698740658 | 2.21867983 | aumenta |
| 0 | índice 11 | +0.110545424 | +0.066795026 | 0.604231483 | reduce |
| 0 | índice 12 | +401.803776537 | +922.366131419 | 2.29556362 | aumenta |
| 0 | índice 13 | +181.131412138 | +503.801870616 | 2.78141635 | aumenta |
| 0 | índice 14 | -2813.083806970 | -2776.089765183 | 0.986849293 | reduce |
| 0 | índice 15 | +26.126860822 | +76.219415449 | 2.9172818 | aumenta |
| 0 | índice 16 | +0.000000000 | +0.000000000 | base cero | igual |
| 0 | C10 | +36.518916736 | +65.282577643 | 1.7876373 | aumenta |
| 1 | índice 0 | +338.804641349 | +422.517120234 | 1.24708185 | aumenta |
| 1 | índice 1 | +850.792238697 | +888.561016467 | 1.04439248 | aumenta |
| 1 | índice 2 | +832.213202955 | +733.115188185 | 0.880922323 | reduce |
| 1 | índice 3 | +311.250128839 | +113.676666769 | 0.365226087 | reduce |
| 1 | índice 4 | -0.818763733 | +2.478238995 | 3.02680602 | aumenta |
| 1 | C27 | +5.826858900 | +0.074188302 | 0.0127321261 | reduce |
| 1 | índice 6 | +85.530256525 | +111.930696417 | 1.30866784 | aumenta |
| 1 | índice 7 | -89.675028191 | -113.117574057 | 1.26141665 | aumenta |
| 1 | índice 8 | +343.272209627 | +720.485045025 | 2.09887379 | aumenta |
| 1 | índice 9 | +2611.666903705 | +3720.028959526 | 1.42438875 | aumenta |
| 1 | índice 10 | +3.677087604 | +5.586928595 | 1.51938958 | aumenta |
| 1 | índice 11 | +0.128199196 | +0.018419690 | 0.143680232 | reduce |
| 1 | índice 12 | +580.253465069 | +912.322707999 | 1.57228308 | aumenta |
| 1 | índice 13 | +277.027159033 | +520.945105473 | 1.88048387 | aumenta |
| 1 | índice 14 | -2501.152908555 | -2195.596489361 | 0.877833771 | reduce |
| 1 | índice 15 | +40.589854340 | +79.555365402 | 1.95998154 | aumenta |
| 1 | índice 16 | +0.000000000 | +0.000000000 | base cero | igual |
| 1 | C10 | +49.587427805 | +59.915713703 | 1.20828436 | aumenta |

El reporte conserva ambas resoluciones, J7, medias Radau del panel,
corrientes inferidas por cambios de fase y desviación de la predicción
lineal. La diferencia entre pasos observada no es una cota continua.
No aplicar gates temporales a la diferencia entre condiciones iniciales.
Una mejora parcial no convierte la matriz estática en Jacobiano periódico.
Las cargas que aumenten o sigan derivando delimitan la siguiente decisión;
no elegir la memoria por amplitud de salida ni ajustar componentes.

## Balance y alcance

Las integrales Radau son propias de cada nueva historia: saw/BUS/entrada 6,
corriente cursor→BUS y desbalance. C1 de terminales completos Qa/Q10/Q7
entre endpoints reales: peor balance relativo 1.41579898e-15. Ocho balances
C27, periodo/recorrido por perfil: peor error 1.27072433e-24 C, gate 1e-12 A
por duración. Identidad media de panel: 4.07634606e-18 V, gate 1e-9 V.
No se transplanta una integral desde otra memoria. El ledger nativo no
es una segunda cuadratura independiente de todas las etapas.

Se admiten estos ciclos y su comparación; no periodicidad asentada,
encendido físico, fidelidad vintage, nuevo audio, SPICE o RT.
248 tests Rust heredados por identidad sin reejecutarlos. El siguiente
bloque debe evaluar las cargas restantes y medir periodos consecutivos
de una historia antes de declarar asentamiento.

## Decisión para el siguiente bloque

La respuesta estática ya no se usa como sustituto de la respuesta durante
el periodo. Formular el residuo de retorno de las cargas en una fase
declarada: diferencia entre fases sucesivas de la misma historia, con
duración y brackets conservados. Incluir la salida y las memorias del
generador que no pertenecen a estas 18 cargas; separar la neutralidad de
fase de las derivas físicas. Las ramas con mayor deriva orientan el
diagnóstico, sin eliminarlas del circuito ni de las observaciones.

Antes de admitir otra corrección, contrastar la respuesta del recorrido
completo y su coste. Si se diferencia un integrador, incluir dependencia
de la historia, cargas de junturas, eventos y elección de paso; comprobar
su derivada con perturbaciones de trayectorias propias. El resultado de
este banco refuta una sustitución estática, pero no admite ese futuro
mapa ni sus derivadas. No extrapolar a un encendido físico o fijar un
warmup para ocultar el residuo.

## Recursos y preparación

Campaña serial 4039.043554 s; cuatro perfiles dentro de 1800 s cada
uno/7200 s globales y 32000/48000 intervalos. Reserva 1 GiB, preflight
con 64 MiB estimados, control de disco cada 250 ms. Stack 32 MiB; solo
compilación del caller, biblioteca de física admitida sin recompilar.

Se conserva el [fallo del generador y replay](../evidence/voice_joint_corrected_cycles_prepare_failure01.json):
la derivación pedía sustituir una referencia que ya había retirado al
eliminar la errata histórica del nuevo auditor. La reparación retira esa
sustitución sin modificar gates y reanuda desde el manifiesto previo,
verificado por JSON canónico, sin sobrescribirlo. Todas las historias y
bytes anteriores permanecen protegidos. No se comprimen ni borran nuevos
registros durante esta campaña.
