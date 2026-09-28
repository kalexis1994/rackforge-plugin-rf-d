# RF-D

Proyecto de recreación del **Minimoog Model D clásico** para RackForge. Su sonido se investigará mediante **RACE — RackForge Architecture for Circuit Emulation**: circuito documentado, leyes de control, calibración física, comparación de audio y presupuesto de tiempo real. Este repositorio es independiente del host y de otros plugins RF.

## Estado

**Corpus documental reunido.** Hay manual de servicio completo (82 páginas), esquemas, manual de operación temprano, boletines de fábrica, patente y hojas de componentes; sus hashes y límites están en el [registro de fuentes](docs/FUENTES.md). Todavía no hay motor de audio, plugin instalable ni afirmación de fidelidad. La revisión de placas y la unidad de referencia siguen pendientes de identificación. El nombre RF-D designa el proyecto; no implica afiliación con Moog Music.

## Objetivo musical

Recrear la voz **monofónica** de un Model D para bajos, leads y articulación en vivo: tres osciladores, ruido, mezclador, filtro ladder, contornos de filtro y volumen, glide, ruedas y ruta de salida. Los presets y el cambio de sonidos en RackForge serán funciones del host/plugin; no se presentarán como memoria del instrumento histórico.

El [objetivo técnico](docs/OBJETIVO.md) define qué queda dentro de la emulación y qué exige una decisión de revisión. No se mezclan características de los Model D originales con las reediciones de 2016/2022 sin evidencia y una decisión explícita.

## Cómo empezar

1. Revisar el [mapa de revisiones](docs/REVISIONES.md) y el [plan de investigación](docs/PLAN.md); cerrar la placa/unidad de referencia antes de fijar constantes DSP.
2. Usar el [registro de fuentes](docs/FUENTES.md) para localizar la página exacta y los [hallazgos técnicos](docs/HALLAZGOS.md) para definir cada contraste.
3. Derivar cada [bloque de circuito](docs/BLOQUES.md) en unidades eléctricas y registrar incertidumbres en la [matriz de fidelidad](docs/MATRIZ_DE_FIDELIDAD.md).
4. Ejecutar el [protocolo de capturas](docs/CAPTURAS.md) con escenas y límites definidos antes de comparar el audio.
5. Aplicar los [gates de RACE](https://github.com/kalexis1994/rackforge-race/blob/main/docs/06-circuitos.md) y el [contrato de plugins RackForge](https://github.com/kalexis1994/rackforge/blob/main/docs/PLUGIN_DEVELOPMENT.md) al implementar y publicar.

## Límites de recursos

Manuales descargados, esquemas, fotos internas, mediciones y WAV de referencia pertenecen a `references-local/` o `captures/`, fuera de Git. El repo guarda identificadores, hashes, derivaciones, pruebas y resultados. Ningún paquete `.rfplugin` incluirá material original que no se pueda distribuir.
