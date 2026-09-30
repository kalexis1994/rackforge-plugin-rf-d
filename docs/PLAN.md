# Plan de investigación RACE para RF-D

No habrá acceso a una unidad física. El [protocolo sin hardware](VALIDACION_SIN_HARDWARE.md) define qué podemos comprobar y qué afirmaciones quedan fuera de alcance.

## Fase A — Perfil documental y circuito

1. El corpus de manuales, esquemas, boletines y datasheets está indexado en [FUENTES.md](FUENTES.md); resolver conflictos mediante [REVISIONES.md](REVISIONES.md).
2. Congelar la primera variante en la placa osciladora CA3046 Fig. 9-3 de SVC-204D. No fusionar Fig. 9-2, la primera placa discreta ni reediciones.
3. Transcribir cada placa a grafo de nodos, valores, conexiones y estados de control. Documentar calibración de fábrica, tolerancias y componentes no identificados.

**Salida:** perfil documental en [OBJETIVO.md](OBJETIVO.md), mapa de nodos reproducible y derivaciones por bloque. La falta de un serial físico no impide modelar el circuito nominal.

## Fase B — Solver y banco de pruebas

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

El [apagado con rampas de laboratorio](APAGADO_VCA_GLOBAL_66.md) localizó 20/96 sondas >1 µV. El [criterio temporal de voltaje](CRITERIO_VOLTAJE_TRANSITORIO_GLOBAL.md) las corrige y pasa el estrés largo. La [reutilización de direcciones](DIRECCION_NEWTON_REUTILIZADA.md) reduce el costo posterior sin cambiar bits. [R21 exacto](R21_EXTREMOS_EXACTOS.md) pasa integración independiente y recursos con ambos topes. Próximos cortes: semillas de apagado, recursos/host y circuito real de contorno; los saltos abruptos siguen agotando Newton.

El [barrido global de extremos](EXTREMOS_CONTROLES_GLOBAL_66.md) encontró dependencias de semilla DC con cutoff máximo, fallo al llevar Q21 a cero y extremos R20/R21 rechazados. [R20 exacto](R20_EXTREMOS_EXACTOS.md) y [R21 exacto global](R21_EXTREMOS_EXACTOS.md) ya pasan; la [semilla DC completa](DC_GLOBAL_SEMILLA_COMPLETA.md) resuelve cutoff máximo y añade un criterio de voltaje para nodos débiles. Próximos cortes: apagado de Q21, dependencia de semillas y recursos del host; conservar los informes fallidos.

Probar Note On/Off, retrigger, legato, glide, ruedas, cambios de preset y recuperación de estado. Mantener la voz mono y describir las comodidades de RackForge como extensiones. Validar transiciones sin discontinuidades accidentales ni asignaciones en el hilo de audio.

## Primer corte de implementación

Empezar por **VCO 1 aislado → mezclador → filtro abierto → VCA/salida**, con un grafo de circuito y un solver simple que admita barridos de notas y niveles. Luego filtro autooscilante y contornos. Cada etapa debe poder avanzar sin una captura privada.

**Corte 0 en curso:** [VCO 1 CA3046](VCO1_CA3046.md) ya tiene subgrafo funcional, resistencias de IC1 cotejadas con tabla 7-5, pinout de IC2, tramo de netlist de C1/bases/IC3 con alimentaciones, R11/R37, [inventario de conexiones de la referencia −4 V](REFERENCIA_MENOS4V.md), ramal resistivo de Schmitt/Q10, [topología parcial de Q7/Q8/Q9/Q4/Q3](VCO1_AMPLIFICADOR_FET.md), [Q2/Q1 y 21B](VCO1_TRIANGULO.md), [Q11/Q12 y 20B](VCO1_PULSO.md) y [cargas internas corregidas de la sierra 9B](VCO1_SALIDA_SIERRA.md). Hay referencias incrementales de voltaje, [razón exponencial ideal de corriente](VCO1_CONVERTIDOR_IDEAL.md), [explorador de carga DC ideal](VCO1_CARGA_DC_IDEAL.md), [polarización condicional de Q5](../tools/vco1_schmitt_bias_reference.py), [puerta FET condicionada](../tools/vco1_fet_gate_reference.py), [pesos pasivos del pulso](../tools/vco1_pulse_passive_reference.py), [selector SW6, puente 9B–21B y dos puertos R6/R45](VCO1_CABLEADO_PANEL.md) y referencia de eventos para C1. La relación de frecuencia es **normalizada y condicional**; la etiqueta −4 V y el divisor sin carga dan corrientes de Qb distintas y ninguno fija la corriente real. La [KCL del bus de mezcla](MEZCLADOR_PANEL.md) ya incorpora las cinco rutas ON con cargas de potenciómetro condicionadas. El siguiente corte es encontrar parámetros primarios para Qc y cerrar corrientes de carga de −4 V, además de resolver el conflicto 10/100 pF de C4, el comportamiento de los FET/BJT, R78 dinámica, la solución acoplada de 9B/21B/20B/22B, la entrada real del bus de mezcla y el mapa de posiciones del panel. Sólo entonces se podrá producir la sierra cargada para el mixer.
