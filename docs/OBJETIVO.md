# Objetivo de referencia

## Blanco

- **Instrumento:** Moog Minimoog Model D de producción clásica, monofónico.
- **Revisión de placas:** pendiente. Registrar número de serie, designadores y revisiones de las placas de osciladores, contornos, fuente/ruido, filtro, salida y rectificador de una unidad física antes de congelar el blanco. El manual 204D separa oscilador antiguo y estabilizado en el umbral documental 10175, pero el estabilizado también podía instalarse como reemplazo; ver [REVISIONES.md](REVISIONES.md).
- **Estado de calibración:** pendiente. Una unidad desajustada no define automáticamente el diseño nominal.
- **Reediciones:** 2016 y 2022 son referencias comparativas, no se fusionan con la revisión clásica elegida. Moog documenta diferencias funcionales entre ambas [aquí](https://moogmusic-help.freshdesk.com/en/support/solutions/articles/69000840518-moog-minimoog-model-d-what-are-the-differences-between-the-2022-and-the-2016-minimoog-model-d-).
- **Unidad(es) físicas y captura:** pendientes. Identificar sin datos personales, documentando temperatura, calentamiento, carga y cadena de grabación.

## Sonido y comportamiento que se estudiarán

| Bloque | Alcance inicial | Pregunta que puede afectar al sonido |
| --- | --- | --- |
| Teclado, glide y ruedas | Nota monofónica, prioridades y control continuo | ¿Cómo cambia el CV en Note On/Off, legato y glide? |
| Osciladores 1–3 | Rangos, formas de onda, afinación, mezcla y oscilador 3 como modulación | ¿Qué forman las ondas y cómo afectan el nivel/carga y la deriva? |
| Ruido y modulación | Blanco/rosa, mezcla de modulación y destinos | ¿Qué espectro y profundidad llegan a osciladores y filtro? |
| Mezclador y entrada externa | Ganancia por fuente y saturación anterior al filtro | ¿Qué nivel produce sobrecarga y cómo se realimenta la salida? |
| Filtro | Ladder, cutoff, emphasis, seguimiento de teclado y contorno | ¿Cómo varían resonancia, pérdida de graves y saturación con nivel? |
| Contornos y VCA | Ataque, decay, sustain, release con switches/trigger originales | ¿Qué tiempos, curvas y transitorios corresponden al circuito? |
| Salida | Amplificación final, nivel y carga | ¿Qué respuesta y recorte aporta la ruta completa? |

Las etapas son candidatas de investigación, no una declaración de que ya estén modeladas o medidas.

## Contrato de producto

- Voz mono como comportamiento por defecto; sin polifonía ni capas añadidas dentro del motor que se presenten como originales.
- Presets, MIDI y automatización de RackForge como adaptadores de performance. Separar claramente control virtual del circuito histórico.
- El panel y los documentos de programa guardarán valores reproducibles; una extensión moderna se marcará como tal.
- Windows, WebAssembly y otras plataformas RackForge compartirán un motor portable. Sample rates y presupuesto se fijarán tras el primer oráculo y perfil.
- No se usará un filtro ladder genérico como sustituto de la ruta completa.

## Decisión pendiente para iniciar el modelado

Identificar una unidad de referencia y contrastar sus placas con el manual de servicio correspondiente. Hasta entonces, la topología es una hipótesis de familia y no se fijan parámetros sonoros de producción.
