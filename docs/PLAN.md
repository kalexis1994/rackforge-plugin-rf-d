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

1. Implementar contrato/estado, control, osciladores, mezcla, filtro, contornos/VCA, salida y adaptador RackForge.
2. Comparar cada bloque con el solver, incluyendo límites de controles y escenas reservadas.
3. Optimizar WebAssembly/tiempo real sólo después de medir errores; conservar ruta de referencia de precisión.

**Salida:** pruebas de circuito y audio, matriz por bloque, perfil de CPU y plugin `.rfplugin` sin material ajeno redistribuido.

## Fase E — Uso en vivo

Probar Note On/Off, retrigger, legato, glide, ruedas, cambios de preset y recuperación de estado. Mantener la voz mono y describir las comodidades de RackForge como extensiones. Validar transiciones sin discontinuidades accidentales ni asignaciones en el hilo de audio.

## Primer corte de implementación

Empezar por **VCO 1 aislado → mezclador → filtro abierto → VCA/salida**, con un grafo de circuito y un solver simple que admita barridos de notas y niveles. Luego filtro autooscilante y contornos. Cada etapa debe poder avanzar sin una captura privada.

**Corte 0 en curso:** [VCO 1 CA3046](VCO1_CA3046.md) ya tiene subgrafo funcional, resistencias de IC1 cotejadas con tabla 7-5, pinout de IC2, tramo de netlist de C1/bases/IC3, R11/R37, [inventario de conexiones de la referencia −4 V](REFERENCIA_MENOS4V.md) y reset parcial, referencias incrementales de voltaje, [razón exponencial ideal de corriente](VCO1_CONVERTIDOR_IDEAL.md), [explorador de carga DC ideal](VCO1_CARGA_DC_IDEAL.md) y referencia de eventos para C1. La relación de frecuencia es **normalizada y condicional**; la etiqueta −4 V y el divisor sin carga dan corrientes de Qb distintas y ninguno fija la corriente real. El siguiente corte es cerrar la polarización de Qc/IC3 y las corrientes de carga de −4 V, además de completar Schmitt/Q10 con R78 dinámica. Sólo entonces se podrá producir la sierra cargada para el mixer.
