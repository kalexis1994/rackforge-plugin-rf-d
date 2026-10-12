# Primera dirección de corrección dinámica de memoria

2026-10-12. Model D clásico CA3046, memoria 0/calendario original 125 ns,
misma escena R61=200 Ω y biblioteca. [Contrato previo](VOZ_CORRECCION_DINAMICA_PROTOCOLO.md),
[inputs/propuesta](../evidence/voice_dynamic_direction_inputs01.json),
[nativo](../evidence/voice_dynamic_direction_native01.json),
[oráculo](../evidence/voice_dynamic_direction_reference01.json),
[QA](../evidence/voice_dynamic_direction_tests01.json).

## Hipótesis de una dirección

La [matriz anterior](VOZ_RETORNO_CONDICIONADO_RESULTADOS.md) se usa para
formular una combinación de objetivos. Sólo C27 tenía FD completa; las
demás columnas no se admiten individualmente por esta nueva campaña.
A es la derivada de las 18 derivas de tensión de rama respecto de los
objetivos condicionados. La fila 16 es nula en esta frontera; se fija
delta_v16=0 y se calcula una solución de norma mínima en las otras 17
filas/columnas, con SVD truncada a s>1e−8·s_max. Rango observado 16.
El menor modo 7.88442811e-18 contrasta con el menor retenido
0.00497736192; no invertir ese modo ni declarar solución única.

La dirección d cambia como máximo 0.00423628083068 V;
no requiere reducir el límite de confianza de 0,1 V. v(a)=v0+a·d,
a adimensional. En cada a se resuelve la raíz de 218 filas manteniendo
x43=0 y restaurando los nodos algebraicos. Se modifica el estado inicial,
no los componentes, trims, controles o leyes del circuito.

Decimal100 resuelve el sistema proyectado de 16 incógnitas. Se verifican
reconstrucción SVD, ortogonalidad, ecuaciones normales y norma mínima.
Error independiente de dirección 2.992398e-17 V.
La deriva prevista fuera del rango se conserva en el recibo; no se oculta
el residuo ni se presenta la predicción como periodicidad medida.

## Historias propias y contraste

Cuatro FD completas, ±epsilon_a y ±epsilon_a/2; epsilon_a=7.99241275035e-05.
La cota usa sum(gain_k·|d_k|) de los máximos nativos anteriores e incluye
la respuesta inicial. Puede sobreestimar una dirección que cancela.
Los cambios escalados tienen unidades V/A y los tiempos s; las respuestas
sin escalar son por a, no por V de un único objetivo.

Una quinta historia propia a=1 prueba el candidato. Son 212720 solves
nuevos, seis raíces/1308 ecuaciones y 100 candidatos independientes de
400 filas (40000 ecuaciones). Cada historia recorre desde su propia raíz
los 42544 medios pasos del calendario guardado. Se observan siete nodos
en todo el recorrido y se auditan los veinte puntos preseleccionados.
La contracción B·d y las respuestas de etapa/evento reutilizan las matrices
guardadas de la base, con sumas Decimal100. No hay nueva propagación
independiente de todos los pasos ni nueva admisión de A completa.

Se detectan ambos cruces crecientes x43=−2 en cada historia. Cada bracket
conserva índices, ticks, h y estados HIGH/LOW. El candidato cruza en
índices [20189, 42543]; la base usaba 20189 y 42543. Los tiempos
incluyen el reloj de cada bracket, además de alpha. Así se admite cambiar
de bracket sin confundir una diferencia de alpha con una diferencia de tiempo.

| Contraste | Peor ratio frente a gate 1 |
|---|---:|
| Raíz direccional | 2.9977023e-10 |
| Estado antiguo | 0.000123770491 |
| Etapas | 0.0001237344 |
| Estado en fase | 3.72597845e-06 |
| Tiempo de cada reset | 0.00274355689 |
| Periodo | 0.00240599698 |
| Deriva | 5.84755434e-06 |
| Deriva de ramas | 1.62028764e-08 |

Gates: cambios 1e−8 V/1e−11 A +1e−4 relativo; tiempo 1e−17 s
+1e−4 relativo; ramas 2e−8 V +1e−4 relativo. Raíces y observador
mantienen los gates heredados. Se contrastan raíz, estado antiguo,
ambas etapas, estados en fase, ambos tiempos, periodo y deriva.

| Tamaño relativo | Efecto de periodo/piso | Efecto J7/piso |
|---|---:|---:|
| 1.0 | 11.890627 | 1.79958311 |
| 0.5 | 5.94531351 | 0.899791557 |

Los recibos incluyen cambios observados y predichos. Un efecto inferior
al piso absoluto no queda resuelto relativamente por pasar el gate.

## Resultado del candidato

Admitida la mejora del candidato en esta escena y calendario.
El criterio previo exige L2 y máximo de deriva≤0,5 de la base,
además de |deriva J7|≤la base. Todos se calculan sobre el resultado
no lineal propio, no sobre la predicción. No se aplica aún como estado
predeterminado de producto ni se extrapola a otras escenas.

| Magnitud | Resultado |
|---|---:|
| Ratio L2 de 18 derivas | 0.0021867055731 |
| Ratio del máximo de 18 derivas | 0.00199744081258 |
| Deriva J7 base V | -0.000224263234611 |
| Deriva J7 candidato V | -6.30277290208e-07 |
| Predicción J7 V | 8.98199169848e-07 |
| Periodo base s | 0.00243426399764324 |
| Periodo candidato s | 0.00243426399615554 |

| Rama | Deriva base V | Deriva medida V | Predicción V | Cambio de objetivo V |
|---|---:|---:|---:|---:|
| 0 | 0.000422605576071 | 1.24147346011e-06 | -4.15453554805e-12 | 0.00423628083068 |
| 1 | 0.000975599923424 | 1.45319087459e-06 | -1.63311838662e-10 | 0.000650314373402 |
| 2 | 0.000886711084763 | -4.46108348662e-07 | -6.7231170815e-10 | -0.000596384699693 |
| 3 | 0.000237921356059 | -4.93506709029e-07 | 8.77081891021e-07 | -0.0006752143514 |
| 4 | 1.67740575858e-06 | 7.81084503589e-09 | 2.22656667043e-09 | -1.67327702844e-05 |
| 5 | 2.13791727091e-06 | 6.17969877732e-11 | 3.73700323815e-11 | 0.000338985311032 |
| 6 | 0.000118709450916 | 5.58735195308e-07 | 8.87693435339e-07 | 9.52605954101e-05 |
| 7 | -0.000121365079546 | -1.34763555027e-06 | -8.79258854824e-07 | -9.23965863844e-05 |
| 8 | 0.000673634167496 | 1.23145000106e-06 | -1.30833064667e-08 | 0.000514341458061 |
| 9 | 0.00385971569042 | 7.292822793e-06 | 1.31922150677e-08 | 0.00307035124068 |
| 10 | 5.69874070914e-06 | 2.52506694523e-08 | 1.47112755068e-08 | 2.57614301577e-06 |
| 11 | 6.67950250271e-08 | 2.27848495473e-07 | 2.27643186466e-07 | -2.49940016285e-06 |
| 12 | 0.000922366139793 | 1.84402973022e-06 | 4.4002542186e-08 | 0.000667834974522 |
| 13 | 0.000503801875802 | 1.10692985469e-06 | 1.63603628611e-07 | 0.000352063064695 |
| 14 | -0.00277608970747 | -7.709553645e-06 | 2.10406842941e-07 | -1.35737443962e-10 |
| 15 | 7.62194162565e-05 | 3.17690184805e-07 | 1.7576701718e-08 | 4.7969934377e-05 |
| 16 | 0 | 0 | 2.31123252907e-32 | 0 |
| 17 | 6.52825781258e-05 | 1.28806537688e-07 | -2.36469716963e-11 | 9.53979757495e-05 |

Ramas que empeoran por más del piso de 2e−8 V: [11].
El recibo también informa el máximo cambio al mismo reloj de rampa,
saw, tri, pulse, BUS, cursor y J7. Mejorar deriva por fase no significa
reproducir las mismas tensiones al mismo reloj ni identificar el sonido físico.

## Organización del laboratorio y límites

Cuatro workers con parámetros/calendario inmutables, estados y archivos
propios. Worker 0 recorre luego el candidato. Cinco prefijos seriales
de 64 pasos coinciden con los workers en los cinco estados HIGH/LOW:
640000 coordenadas por bits, 320 solves seriales adicionales. Se almacenan
81 puntos por historia (prefijo más selección), con auditor independiente
en los veinte puntos originales. Los kernels no cambian. Esto no mide
plazo ni optimización del procesamiento de audio.

Nativo 1440.090037 s; oráculo 32.979117 s; salidas 28806481 bytes.
Disco reservado 1 GiB, estimación 64 MiB; RAM inicial≥1 GiB, cuatro stacks
de 32 MiB, vigilancia 250 ms. Compile≤120 s, run≤3400 s, éxito≤3560 s,
administrativo≤7200 s, auditor≤300 s. 248 tests Rust heredados por identidad.
Sin nueva biblioteca, audio, SPICE, fidelidad física o RT.

Se admite la dirección contrastada y se registra la decisión del candidato.
Falta contrastar ciclos posteriores, calendario adaptativo y otro perfil
antes de usarlo como inicialización estable. No acredita mapa de Poincaré,
periodicidad asentada ni las 18 columnas individuales por FD completa.
