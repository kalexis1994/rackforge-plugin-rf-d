# RF-D

Proyecto de recreación del **Minimoog Model D clásico** para RackForge. Su sonido se investigará mediante **RACE — RackForge Architecture for Circuit Emulation**: circuito documentado, leyes de control, calibración de servicio, comparación de audio y presupuesto de tiempo real. Este repositorio es independiente del host y de otros plugins RF.

## Estado

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

La [derivación parcial de VCO 1](docs/VCO1_CA3046.md) explica los límites de la referencia ejecutable. Puede comprobarse con `python -m unittest discover -s tests -v`; no necesita instalar dependencias.

La ruta experimental BUS→J7 dispone de [vectores de admisión numérica](docs/VECTORES_PORTABILIDAD_AURICULARES.md). Ya existen un [puerto Rust de la placa 3](docs/PUERTO_NATIVO_PLACA3_AURICULARES.md), la [frontera R77/R21](docs/PUERTO_NATIVO_PANEL_AURICULARES.md), la [salida desde C2 hasta J7](docs/PUERTO_NATIVO_C2_SALIDAS.md), la [conversión Q1/Q12/Q17 con C4](docs/PUERTO_NATIVO_C4_CONVERSION_SALIDA.md), el [segundo VCA unido hasta J7](docs/VCA2_SALIDA_NATIVA.md), el [primer VCA con R2/C6/C15 hasta J7](docs/VCA1_SALIDA_NATIVA.md), la [recuperación Q5–Q8](docs/RECUPERACION_SALIDA_NATIVA.md), el [ladder nativo](docs/LADDER_SALIDA_NATIVA.md) y el [lazo C10/EMPHASIS](docs/EMPHASIS_NATIVO_C10.md). Los bloques tienen oráculos independientes: el nuevo cierre BUS→J7 coincide con un modelo monolítico Python de 62 nodos en ambos R61 y en una traza de 192 muestras con cambios de R14/SW18 (error máximo J7 25,6 nV, relación señal/error **numérica** 115 dB). El [perfil de costo](docs/PERFIL_COSTO_CADENA_NATIVA.md) localiza la anidación de solves; [compartir la factorización de tangentes](docs/OPTIMIZACION_TANGENTES_MULTI_RHS.md) redujo el costo parcial. El cierre C10 tarda ~22,6 ms por bloque de 64 frente a 1,33 ms disponibles. La corriente de Q28 y las leyes de volumen siguen siendo límites impuestos. Aún no es una voz ni cumple el presupuesto de tiempo real; equivalencia numérica no implica fidelidad sonora. Puede comprobarse con `cargo test --workspace`.

## Límites de recursos

Manuales descargados, esquemas, fotos internas, mediciones y WAV de referencia pertenecen a `references-local/` o `captures/`, fuera de Git. El repo guarda identificadores, hashes, derivaciones, pruebas y resultados. Ningún paquete `.rfplugin` incluirá material original que no se pueda distribuir.
