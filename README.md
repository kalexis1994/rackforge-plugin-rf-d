# RF-D

Proyecto de recreación del **Minimoog Model D clásico** para RackForge. Su sonido se investigará mediante **RACE — RackForge Architecture for Circuit Emulation**: circuito documentado, leyes de control, calibración de servicio, comparación de audio y presupuesto de tiempo real. Este repositorio es independiente del host y de otros plugins RF.

## Estado

El [laboratorio de contorno y cadena de 94 nodos](docs/CONTORNO_CADENA_94_Y_ESTABILIDAD.md) calcula C2/reset dentro del circuito con 21 cargas. El refinamiento temporal conserva el rechazo cerca de 12,4 ms. Una [búsqueda de 102 semillas encuentra tres raíces](docs/BIESTABLE_TRES_RAICES_Y_CARGA_RAPIDA.md); cargas de juntura de diagnóstico revelan un modo creciente en la intermedia que el modelo instantáneo omitía. No se selecciona una rama ni se admite la conmutación física.

El [dominio de las junturas y sus cargas](docs/CARGAS_JUNTURA_Y_DOMINIO_BIESTABLE.md) registra doce puntos Q25/Q15 y verifica 300 sondas sintéticas de depleción/difusión con cuadratura independiente. Ninguno de esos puntos reproduce el sesgo de la medida Cob de las hojas adquiridas. Las primitivas conservan carga e historial; sus parámetros físicos y la partición BJT siguen abiertos. Las [lecciones para RACE](docs/LECCIONES_RACE_CONMUTACION.md) resumen los gates transferibles.

El [registro de fabricación 2N3392 y datos dinámicos](docs/FABRICACION_3392_Y_DATOS_DINAMICOS.md) incorpora GE/RCA 1987 y PN100A Process 10. Conserva la diferencia entre 2 pF típico y mínimo según fabricante y demuestra que los doce puntos del biestable quedan fuera del intervalo IC de su curva de conmutación. Ningún parámetro físico promovido.

El [BJT intrínseco con carga conservativa](docs/BJT_INTRINSECO_CARGA_CONSERVATIVA.md) tiene corrientes/cargas terminales, Jacobiano y memoria ligada a parámetros. Pasa 72 casos independientes contra ngspice 46, incluyendo matrices AC 3×3 a dos frecuencias. Es una hipótesis explícita de baja inyección con parámetros sintéticos; no se incorpora al motor ni admite todavía la conmutación del contorno.

El [BJT cargado en transitorios](docs/BJT_CARGADO_TRANSITORIOS.md) resuelve tres nodos y sus cargas en 252.000 pasos sin reset. Pasa refinamiento frente a ngspice: error propio máximo 1,35 mV, refinamiento independiente 127 µV. Conserva un aborto del oráculo y dos barridos que superaron los gates. La conmutación del biestable Model D sigue pendiente.

El [puerto conjunto C2/reset con carga de toda la cadena](docs/PUERTO_CONTORNO_CADENA_71.md) añade corrientes, matriz de admisión `2×2` y gradientes de los 71 nodos. Pasa 36 casos independientes DC/temporales con diferencia máxima de admisión **2,04 pS**, candidato temporal coherente y heap cero. En un escenario alto de C2, CR6 devuelve 0,495 mA a reset: esa carga deberá entrar en el biestable, cuya conmutación todavía requiere resolver la estabilidad.

El [cierre simultáneo de seguidor, R59 y cadena de 71 nodos](docs/SEGUIDOR_VCA_CADENA_71.md) calcula la base Q18 y la carga devuelta a C2/reset. Pasa veinte destinos DC y 256 pasos independientes, con error máximo de nodo **2,50 nV**, conservación de dieciocho cargas y heap cero. Los saltos se recuperan explícitamente con historial fijo; el costo de 16,12–16,96 ms por bloque todavía excede el plazo. El biestable y las fuentes reales del contorno siguen pendientes.

El [perfil de etapas VCA](docs/ETAPAS_VCA_Y_REPRODUCIBILIDAD.md) contrasta ocho etapas y reduce 38,46 % el costo de las escenas con saltos frente a 32: 9,708 ms de kernel acumulado por bloque, todavía fuera del plazo. Pasan 1152 pasos Rust con 8/16/32 etapas y heap cero. El banco con un estado temporal común reproduce exactamente los resultados entre workers y conserva aparte la variación del arranque DC.

Los [saltos VCA con historial fijo](docs/SALTOS_VCA_HISTORIAL_FIJO.md) pasan 384 muestras independientes, incluyendo apagado y restauración: error interno máximo 7,15 nV. La API rescata 16 rechazos sin subpasos físicos ni borrar cargas. Es una ruta experimental explícita, todavía demasiado costosa; el banco de stack conserva una diferencia de 1,30 pV frente a su gate de identidad de 1 pV.

La [inicialización DC por continuación VCA](docs/DC_VCA_CONTINUACION.md) añade una ruta explícita de preparación para uno o ambos controles en cero. Pasa 18 semillas frente a raíces independientes (1,57 nV), reconstruye las 18 cargas y acepta 1152 pasos posteriores de reposo. Conserva los gates por etapa y heap cero. El salto abrupto durante audio sigue pendiente.

Los [topes exactos de R21](docs/R21_EXTREMOS_EXACTOS.md) ya identifican cursor→masa y PIN22→cursor en el solver global. Pasan 128 pasos de integración Python independiente (máximo de nodo 0,22 nV), Jacobianos, corrientes de los cortos, heap cero y stack con cambios entre topes. El barrido acepta 17408 muestras y conserva los seis fallos previos.

La [dirección Newton reutilizada](docs/DIRECCION_NEWTON_REUTILIZADA.md) conserva en bits los 23224 valores de las capturas de apagado y reduce 23,18 % el costo de la política precisa: **2,953 ms/bloque**. Mantiene heap cero y los gates de voltaje. Todavía excede el deadline de 1,333 ms.

El [criterio temporal de voltaje](docs/CRITERIO_VOLTAJE_TRANSITORIO_GLOBAL.md) corrige las 96 sondas de apagado (máximo interno 0,150 nV frente a las raíces independientes). Pasa de nuevo el estrés de 752384 muestras y heap cero. Su primera implementación costó 3,939 ms/bloque, luego reducido reutilizando direcciones; aún no cumple tiempo real. Los saltos abruptos y el contorno real siguen pendientes.

El [apagado sintético de VCAs](docs/APAGADO_VCA_GLOBAL_66.md) registró 20/96 sondas con error interno >1 µV en la política anterior, hasta 1,318 mV. El criterio de voltaje corrige esa brecha; los saltos de una muestra siguen fallando. Estos estímulos no modelan el contorno.

La [inicialización DC global con semilla completa](docs/DC_GLOBAL_SEMILLA_COMPLETA.md) resuelve cutoff máximo y contrasta 14 puntos independientes con error máximo 2,25 nV. Añade criterio de corrección de voltaje para nodos débiles. Conserva dos rechazos exploratorios de semillas desplazadas; apagado de Q21 sigue pendiente.

El [barrido de extremos global](docs/EXTREMOS_CONTROLES_GLOBAL_66.md) detectó fallos de arranque con cutoff máximo y de transición al apagar Q21. [R20 admite sus extremos exactos](docs/R20_EXTREMOS_EXACTOS.md), con 128 pasos independientes y SW18 ON/OFF; R21 exacto está cerrado en el solver global. El barrido actualizado mantiene seis casos fallidos de arranque/apagado.

El [banco de stack Win64](docs/STACK_GLOBAL_66_WIN64.md) pasa hilos de 512 KiB. La compilación DC observaba 324 KiB; con [topes R21](docs/R21_EXTREMOS_EXACTOS.md) se observan 328 KiB comprometidos durante procesamiento/reintentos. La observación por páginas deja pendiente el pico exacto y la admisión en RackForge.

El [refinamiento temporal global](docs/REFINAMIENTO_TEMPORAL_GLOBAL_66.md) añade 26880 pasos a 48/96/192 kHz, con dos señales y ambos R61. Las diferencias entre pasos se reducen con cocientes de 1,98–1,99; las diferencias de discretización siguen siendo medibles a tasas de audio.

El [ensamblado global ordenado](docs/ENSAMBLADO_GLOBAL_ORDENADO.md) y las [exponenciales compartidas](docs/EXPONENCIALES_GLOBAL_66.md) reducen el costo medio a 2,233 ms/bloque, con los gates independientes y heap cero. El [estrés largo](docs/ESTRES_LARGO_GLOBAL_66.md) añade 752384 muestras a 44,1/48/96 kHz con ambos R61, sin fallos y con cambios de controles, EMPHASIS y cargas. El deadline de 1,333 ms sigue excedido.

Las [48 ventanas contrastadas con Python](docs/VENTANAS_INDEPENDIENTES_ESTRES_GLOBAL.md) añaden 192 pasos alrededor de switches y en tramos tardíos, con historiales eléctricos compartidos: máximo interno 0,205 µV y J7 0,398 nV. Amplían el contraste numérico de la escena.

**Corpus documental reunido.** Hay manual de servicio completo (82 páginas), esquemas, manual de operación temprano, boletines de fábrica, patente y hojas de componentes; sus hashes y límites están en el [registro de fuentes](docs/FUENTES.md). El proyecto [avanza sin acceso físico](docs/VALIDACION_SIN_HARDWARE.md): la primera ruta tiene como blanco la placa osciladora **CA3046** documentada. Ya existe un [subgrafo de VCO 1](docs/VCO1_CA3046.md), referencias ejecutables de sus primeras etapas, un [bus de mezcla de cinco fuentes](docs/MEZCLADOR_PANEL.md) y un [punto DC condicionado del ladder completo](docs/LADDER_EBERS_MOLL_DC.md) con [recuperación y EMPHASIS temporales](docs/TRANSITORIO_FILTRO_ACOPLADO.md). Faltan la identificación de parámetros de una placa real, el motor de audio y el plugin instalable. No hay afirmación de fidelidad sonora. El nombre RF-D designa el proyecto; no implica afiliación con Moog Music.

## Objetivo musical

La [columna resistiva del ladder en DC](docs/COLUMNA_RESISTIVA_LADDER_DC.md), las [dos pilas activas](docs/PILAS_ACTIVAS_LADDER_DC.md), el [cierre Ebers–Moll de 16 nodos](docs/LADDER_EBERS_MOLL_DC.md), su [núcleo de pequeña señal](docs/LADDER_PEQUENA_SENAL.md), la [recuperación activa Q5–Q8](docs/RECUPERACION_ACTIVA_FILTRO.md), el [lazo de EMPHASIS en pequeña señal](docs/LAZO_EMPHASIS_PEQUENA_SENAL.md) y el [transitorio no lineal acoplado](docs/TRANSITORIO_FILTRO_ACOPLADO.md) con [Jacobiano analítico](docs/JACOBIAN_ANALITICO_FILTRO.md) tienen referencias ejecutables. La [carga pasiva del primer VCA](docs/CARGA_VCA1_FILTRO.md) ya está unida a la red AC y al [transitorio de 27 nodos](docs/TRANSITORIO_CARGA_VCA1.md). El [barrido de supuestos](docs/BARRIDO_SESGO_LADDER_DC.md) y la [malla de sensibilidad de EMPHASIS](docs/SENSIBILIDAD_EMPHASIS.md) delimitan escenarios; faltan parámetros de una placa real y motor de audio.

Recrear la voz **monofónica** de un Model D para bajos, leads y articulación en vivo: tres osciladores, ruido, mezclador, filtro ladder, contornos de filtro y volumen, glide, ruedas y ruta de salida. Los presets y el cambio de sonidos en RackForge serán funciones del host/plugin; no se presentarán como memoria del instrumento histórico.

El [objetivo técnico](docs/OBJETIVO.md) define qué queda dentro de la emulación y qué exige una decisión de revisión. No se mezclan características de los Model D originales con las reediciones de 2016/2022 sin evidencia y una decisión explícita.

## Cómo empezar

1. Revisar el [mapa de revisiones](docs/REVISIONES.md), el [plan de investigación](docs/PLAN.md) y el [protocolo sin hardware](docs/VALIDACION_SIN_HARDWARE.md); fijar la revisión documental antes de derivar constantes DSP.
2. Usar el [registro de fuentes](docs/FUENTES.md) para localizar la página exacta y los [hallazgos técnicos](docs/HALLAZGOS.md) para definir cada contraste.
3. Derivar cada [bloque de circuito](docs/BLOQUES.md) en unidades eléctricas y registrar incertidumbres en la [matriz de fidelidad](docs/MATRIZ_DE_FIDELIDAD.md).
4. Preparar las escenas de [CAPTURAS.md](docs/CAPTURAS.md) como pruebas simuladas y usar audio público sólo en los contrastes permitidos por su procedencia.
5. Aplicar los [gates de RACE](https://github.com/kalexis1994/rackforge-race/blob/main/docs/06-circuitos.md) y el [contrato de plugins RackForge](https://github.com/kalexis1994/rackforge/blob/main/docs/PLUGIN_DEVELOPMENT.md) al implementar y publicar.

La [derivación parcial de VCO 1](docs/VCO1_CA3046.md) explica los límites de la referencia ejecutable. Las referencias básicas usan la biblioteca estándar; el nuevo laboratorio de 94 nodos/modos requiere NumPy, registrado en `requirements-lab.txt`. Tras instalar esa dependencia puede ejecutarse `python -m unittest discover -s tests -v`.

La ruta experimental BUS→J7 dispone de [vectores de admisión numérica](docs/VECTORES_PORTABILIDAD_AURICULARES.md). Ya existen un [puerto Rust de la placa 3](docs/PUERTO_NATIVO_PLACA3_AURICULARES.md), la [frontera R77/R21](docs/PUERTO_NATIVO_PANEL_AURICULARES.md), la [salida desde C2 hasta J7](docs/PUERTO_NATIVO_C2_SALIDAS.md), la [conversión Q1/Q12/Q17 con C4](docs/PUERTO_NATIVO_C4_CONVERSION_SALIDA.md), el [segundo VCA unido hasta J7](docs/VCA2_SALIDA_NATIVA.md), el [primer VCA con R2/C6/C15 hasta J7](docs/VCA1_SALIDA_NATIVA.md), la [recuperación Q5–Q8](docs/RECUPERACION_SALIDA_NATIVA.md), el [ladder nativo](docs/LADDER_SALIDA_NATIVA.md) y el [lazo C10/EMPHASIS](docs/EMPHASIS_NATIVO_C10.md). Los bloques tienen oráculos independientes: el nuevo cierre BUS→J7 coincide con un modelo monolítico Python de 62 nodos en ambos R61 y en una traza de 192 muestras con cambios de R14/SW18 (error máximo J7 25,6 nV, relación señal/error **numérica** 115 dB). El [perfil de costo](docs/PERFIL_COSTO_CADENA_NATIVA.md) localiza la anidación de solves; [compartir la factorización de tangentes](docs/OPTIMIZACION_TANGENTES_MULTI_RHS.md) redujo el costo parcial. El cierre C10 tarda ~22,6 ms por bloque de 64 frente a 1,33 ms disponibles. La corriente de Q28 y las leyes de volumen siguen siendo límites impuestos. Aún no es una voz ni cumple el presupuesto de tiempo real; equivalencia numérica no implica fidelidad sonora. Puede comprobarse con `cargo test --workspace`.

El [control Q26/Q28 nativo](docs/CUTOFF_NATIVO_Q26_Q28.md) incluye C18, ambas junturas BJT y las ramas de cutoff, contorno, teclado, modulación y jack. La [cadena integrada hasta J7](docs/CUTOFF_LADDER_J7_NATIVO.md) calcula la cola desde el circuito y coincide con un oráculo monolítico de 66 nodos en 128 pasos (error J7 22,4 nV). Tarda ~25,7 ms por bloque de 64 frente a 1,33 ms disponibles. BUS y las fuentes de contorno/teclado/modulación siguen impuestos; falta una voz completa y el gate de tiempo real.

El [solver global analítico experimental de 66 nodos](docs/SOLVER_GLOBAL_66_NODOS.md) conserva el mismo circuito y evita los solves anidados. Se contrastó contra Python, por diferencias finitas de todo el Jacobiano y en 8192 muestras contra la ruta por puertos. Cinco comparaciones alternadas dieron **9,39 veces menos costo medio**: **2,559 ms** por bloque frente a **24,037 ms**. Conserva los criterios de error y cero heap; todavía excede los **1,333 ms** disponibles y no se admite como motor del plugin.

## Límites de recursos

El [contorno de volumen de placa 2](docs/CONTORNO_VOLUMEN_CIRCUITO.md) tiene grafo y oráculo de transistores, gatillo y cargas capacitivas. Las primeras semillas detectaron dos raíces; el cierre cargado y la búsqueda ampliada registran tres, sin elegir una. El [puerto nativo del seguidor Q3/Q2](docs/SEGUIDOR_VOLUMEN_NATIVO.md) pasa 60 casos independientes con error máximo de nodo 7,63 nV y entrega corrientes/tangentes para el acoplamiento posterior. No equivale todavía a una envolvente física validada ni a una voz completa.

Manuales descargados, esquemas, fotos internas, mediciones y WAV de referencia pertenecen a `references-local/` o `captures/`, fuera de Git. El repo guarda identificadores, hashes, derivaciones, pruebas y resultados. Ningún paquete `.rfplugin` incluirá material original que no se pueda distribuir.
