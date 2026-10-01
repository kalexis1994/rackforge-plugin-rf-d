# Plan de investigación RACE para RF-D

No habrá acceso a una unidad física. El [protocolo sin hardware](VALIDACION_SIN_HARDWARE.md) define qué podemos comprobar y qué afirmaciones quedan fuera de alcance.

## Fase A — Perfil documental y circuito

1. El corpus de manuales, esquemas, boletines y datasheets está indexado en [FUENTES.md](FUENTES.md); resolver conflictos mediante [REVISIONES.md](REVISIONES.md).
2. Congelar la primera variante en la placa osciladora CA3046 Fig. 9-3 de SVC-204D. No fusionar Fig. 9-2, la primera placa discreta ni reediciones.
3. Transcribir cada placa a grafo de nodos, valores, conexiones y estados de control. Documentar calibración de fábrica, tolerancias y componentes no identificados.

**Salida:** perfil documental en [OBJETIVO.md](OBJETIVO.md), mapa de nodos reproducible y derivaciones por bloque. La falta de un serial físico no impide modelar el circuito nominal.

## Fase B — Solver y banco de pruebas

El [contorno cargado de 94 nodos](CONTORNO_CADENA_94_Y_ESTABILIDAD.md) conserva 21 cargas y deja C2/reset como incógnitas reales. El barrido temporal acepta 370 pasos antes de rechazos cercanos a la conmutación. La [búsqueda ampliada](BIESTABLE_TRES_RAICES_Y_CARGA_RAPIDA.md) encuentra tres raíces, y la auditoría de cargas rápidas muestra una inestabilidad omitida en la intermedia. Próximo corte: leyes de carga de juntura y dominio de los puntos de operación; no hay selección física de raíz admitida.

1. Crear un solver fuera de tiempo real para VCO, mixer, filtro, contornos, VCA y salida; derivar frecuencia, transferencia, puntos DC y transitorios.
2. Ejecutar las escenas de [CAPTURAS.md](CAPTURAS.md) como estímulos simulados, con controles y unidades reproducibles.
3. Contrastar las cifras con el manual, boletines y límites de datasheets. Reservar escenas para detectar sobreajuste de parámetros libres.

**Salida:** oráculo **numérico del circuito seleccionado**, con incertidumbre declarada. El oráculo no demuestra equivalencia con un ejemplar antiguo.

## Fase C — Referencias audibles públicas

1. Catalogar las grabaciones de autores/propietarios de Model D vintage candidatas en [VALIDACION_SIN_HARDWARE.md](VALIDACION_SIN_HARDWARE.md).
2. Clasificar escenas por identidad del instrumento, visibilidad de controles, formato y procesado. Las demos sin ajustes reconstruibles sirven para escucha musical, no para ajuste de constantes.
3. Comparar formas/rasgos y documentar coincidencias y fallas por fuente independiente; mantener aparte las reediciones.

**Salida:** informe de plausibilidad sonora por escena, sin reclamar proximidad cuantitativa a una unidad no medida.

## Fase D — Motor portable y plugin

La ruta global Q26/Q28→ladder→VCAs→J7 tiene Jacobiano analítico, optimizaciones contrastadas, [752384 muestras de estrés largo](ESTRES_LARGO_GLOBAL_66.md), [192 pasos independientes en ventanas de switches/tramos tardíos](VENTANAS_INDEPENDIENTES_ESTRES_GLOBAL.md), [refinamiento a 48/96/192 kHz](REFINAMIENTO_TEMPORAL_GLOBAL_66.md) y [observaciones de stack Win64](STACK_GLOBAL_66_WIN64.md). La media local aún excede el plazo de audio. El siguiente corte numérico debe completar extremos de controles y verificar recursos del host; VCO, mezclador cargado y contornos siguen pendientes para la voz completa.

1. Implementar contrato/estado, control, osciladores, mezcla, filtro, contornos/VCA, salida y adaptador RackForge.
2. Comparar cada bloque con el solver, incluyendo límites de controles y escenas reservadas.
3. Optimizar WebAssembly/tiempo real sólo después de medir errores; conservar ruta de referencia de precisión.

**Salida:** pruebas de circuito y audio, matriz por bloque, perfil de CPU y plugin `.rfplugin` sin material ajeno redistribuido.

## Fase E — Uso en vivo

El [puerto cargado C2/reset](PUERTO_CONTORNO_CADENA_71.md) añade admisión `2×2` y gradientes `71×2` desde raíces completas, veinte DC y dieciséis temporales. Mantiene la memoria entrante durante todos los ensayos y devuelve un candidato provisional. Próximo corte: estudiar estabilidad y dinámica del biestable incorporando su carga real, sin seleccionar una raíz por conveniencia.

El [cierre de 71 nodos](SEGUIDOR_VCA_CADENA_71.md) une Q3/Q2 con R59/base Q18 y la cadena hasta J7: veinte destinos DC, 256 pasos independientes, corrientes de C2/reset, memoria atómica y heap cero. Preparación y continuación son explícitas; se conserva un rechazo de semilla DC apagada. El costo todavía excede el plazo. El próximo corte obtiene las tangentes conjuntas y resuelve la ambigüedad del biestable antes de reintegrar el capacitor C2.

El [apagado con rampas de laboratorio](APAGADO_VCA_GLOBAL_66.md) localizó 20/96 sondas >1 µV. El [criterio temporal de voltaje](CRITERIO_VOLTAJE_TRANSITORIO_GLOBAL.md) las corrige y pasa el estrés largo. La [reutilización de direcciones](DIRECCION_NEWTON_REUTILIZADA.md) reduce el costo posterior sin cambiar bits. [R21 exacto](R21_EXTREMOS_EXACTOS.md) pasa integración independiente y recursos con ambos topes. La [continuación DC VCA](DC_VCA_CONTINUACION.md) resuelve 18 arranques de fuentes en cero mediante una API de preparación. Próximos cortes: resolver saltos conservando los historiales, recursos/host y circuito real de contorno; los saltos abruptos siguen agotando Newton.

El [barrido global de extremos](EXTREMOS_CONTROLES_GLOBAL_66.md) encontró dependencias de semilla DC con cutoff máximo, fallo al llevar Q21 a cero y extremos R20/R21 rechazados. [R20 exacto](R20_EXTREMOS_EXACTOS.md) y [R21 exacto global](R21_EXTREMOS_EXACTOS.md) ya pasan; la [semilla DC completa](DC_GLOBAL_SEMILLA_COMPLETA.md) resuelve cutoff máximo. La [continuación temporal VCA](SALTOS_VCA_HISTORIAL_FIJO.md) rescata saltos con historial fijo y el [perfil de ocho etapas](ETAPAS_VCA_Y_REPRODUCIBILIDAD.md) reduce 38,46 % el costo de esas escenas. Con estado temporal común se reproduce el render entre workers; permanece la sensibilidad del arranque. Próximos cortes: costo normal/peores muestras, contorno físico, dependencia de semillas y recursos del host; conservar los informes fallidos.

Probar Note On/Off, retrigger, legato, glide, ruedas, cambios de preset y recuperación de estado. Mantener la voz mono y describir las comodidades de RackForge como extensiones. Validar transiciones sin discontinuidades accidentales ni asignaciones en el hilo de audio.

## Contorno de volumen: avance y gate pendiente

El [grafo eléctrico y oráculo de placa 2](CONTORNO_VOLUMEN_CIRCUITO.md) reconstruye diez BJTs, gatillo, tres memorias capacitivas, panel y decay final. El biestable presenta dos raíces diferentes para el mismo paso; quedan registradas sin selección. El [puerto nativo Q3/Q2/CR6](SEGUIDOR_VOLUMEN_NATIVO.md) reproduce 60 casos y entrega tres corrientes/tangentes con heap cero. Siguiente cierre: R59/base Q18 real; después estabilidad de conmutación y cargas compartidas antes de unir contorno completo/VCA o afirmar Note On/Off físico. Los intervalos físicos nuevos no se recortan al `0..2 V` del laboratorio anterior.

## Primer corte de implementación

El [segundo integrador BDF2](BIESTABLE_BDF2_CARGA.md) ya verifica coeficientes, dos memorias aceptadas y conservación en C10/junturas. Próximo gate: barrido A3/B3 0..3 ms, diferencias al mismo tiempo y observación de tiempos, conservando los fallos de Euler.

Los [tiempos observados](BIESTABLE_TIEMPOS_DE_TRANSICION.md) separan la subida ATTACK_OUT de la caída final de Q25. Siguiente gate: error acumulado antes de ambas regiones con refinamiento adicional y otra integración, sin retimar las trazas para aprobar el contraste original.

El [corte de incrementos compensados](BIESTABLE_INCREMENTOS_COMPENSADOS.md) ya cierra el intervalo rechazado con ambos Jacobianos y conserva sus 21 memorias durante 32 pasos posteriores. El [barrido A2/B2](BIESTABLE_BARRIDO_COMPENSADO.md) completa 0..3 ms y verifica 4152 medios intervalos; falla el gate temporal de 1 mV con 5,147 V máximos. Próximo bloque: medir por separado ATTACK_OUT/Q25, sensibilidad acumulada y otra integración. Se conserva el barrido v1 fallido.

El trabajo de conmutación actual tiene un [inventario de doce sesgos y primitivas de carga verificadas](CARGAS_JUNTURA_Y_DOMINIO_BIESTABLE.md), un [BJT intrínseco conservativo contrastado contra ngspice](BJT_INTRINSECO_CARGA_CONSERVATIVA.md), [transitorios cargados con historial y refinamiento](BJT_CARGADO_TRANSITORIOS.md) y una [sonda Q25/Q15 no lineal de 94 nodos](BIESTABLE_CARGA_NO_LINEAL.md). La sonda conserva 25 memorias escalares y reproduce tres soluciones a 1 ms. El [primer barrido adaptativo desde DC](BIESTABLE_TRAYECTORIA_ADAPTATIVA.md) publica 2982 intervalos; la política estricta se detiene y ambas trazas difieren hasta 5,006 V. El [diagnóstico del rechazo](BIESTABLE_RECHAZO_Y_ORIGEN_CARGA.md) reproduce un límite representable en C2 y demuestra sensibilidad del estimador al cero convencional de Q. El [corte de incrementos compensados](BIESTABLE_INCREMENTOS_COMPENSADOS.md) ya verifica esa corrección; el siguiente gate es repetir el refinamiento completo con la métrica v2. La carga condicionada no identifica una pieza vintage ni admite una transición Note On/Off. Las [lecciones para RACE](LECCIONES_RACE_CONMUTACION.md) mantienen ese orden de gates.

Empezar por **VCO 1 aislado → mezclador → filtro abierto → VCA/salida**, con un grafo de circuito y un solver simple que admita barridos de notas y niveles. Luego filtro autooscilante y contornos. Cada etapa debe poder avanzar sin una captura privada.

**Corte 0 en curso:** [VCO 1 CA3046](VCO1_CA3046.md) ya tiene subgrafo funcional, resistencias de IC1 cotejadas con tabla 7-5, pinout de IC2, tramo de netlist de C1/bases/IC3 con alimentaciones, R11/R37, [inventario de conexiones de la referencia −4 V](REFERENCIA_MENOS4V.md), ramal resistivo de Schmitt/Q10, [topología parcial de Q7/Q8/Q9/Q4/Q3](VCO1_AMPLIFICADOR_FET.md), [Q2/Q1 y 21B](VCO1_TRIANGULO.md), [Q11/Q12 y 20B](VCO1_PULSO.md) y [cargas internas corregidas de la sierra 9B](VCO1_SALIDA_SIERRA.md). Hay referencias incrementales de voltaje, [razón exponencial ideal de corriente](VCO1_CONVERTIDOR_IDEAL.md), [explorador de carga DC ideal](VCO1_CARGA_DC_IDEAL.md), [polarización condicional de Q5](../tools/vco1_schmitt_bias_reference.py), [puerta FET condicionada](../tools/vco1_fet_gate_reference.py), [pesos pasivos del pulso](../tools/vco1_pulse_passive_reference.py), [selector SW6, puente 9B–21B y dos puertos R6/R45](VCO1_CABLEADO_PANEL.md) y referencia de eventos para C1. La relación de frecuencia es **normalizada y condicional**; la etiqueta −4 V y el divisor sin carga dan corrientes de Qb distintas y ninguno fija la corriente real. La [KCL del bus de mezcla](MEZCLADOR_PANEL.md) ya incorpora las cinco rutas ON con cargas de potenciómetro condicionadas. El siguiente corte es encontrar parámetros primarios para Qc y cerrar corrientes de carga de −4 V, además de resolver el conflicto 10/100 pF de C4, el comportamiento de los FET/BJT, R78 dinámica, la solución acoplada de 9B/21B/20B/22B, la entrada real del bus de mezcla y el mapa de posiciones del panel. Sólo entonces se podrá producir la sierra cargada para el mixer.
