# Desarrollo y validación sin acceso a un Minimoog

**Restricción del proyecto:** no habrá una unidad física disponible para RF-D. El trabajo no queda bloqueado por esa ausencia. El primer blanco es un **perfil documental de circuito**, no el audio de un ejemplar identificado.

## Blanco implementable

La primera ruta modelará la placa osciladora **CA3046** descrita por SVC-204D, PDF pp. 14–16 y Fig. 9-3 (PDF p. 61), junto con las placas de control, filtro y salida de la misma documentación. La placa posterior **μA726** (Fig. 9-2, PDF p. 60) se conserva como variante explícita para una segunda ruta. La placa totalmente discreta de las primeras unidades es una tercera variante cuya fuente de esquema aún debe verificarse. El límite de número de serie y los kits descritos en [REVISIONES.md](REVISIONES.md) no se convierten en una mezcla implícita de componentes.

Esta selección prioriza una revisión clásica documentada, con esquema, descripción funcional y procedimiento de calibración. [Un propietario que midió placas CA3046 y μA726](https://forum.moogmusic.com/t/minimoog-model-d-differences/14878) describe diferencias de sierra y pulso; sus imágenes originales ya no están disponibles, por lo que se registra como observación de campo y no como medida numérica. **No supone** que esta revisión representa todos los Model D clásicos ni que una demo pública use esa misma placa. Las constantes proceden de circuito, BOM, datasheets y condiciones de servicio; las que dependan de una unidad concreta se registran como intervalo o incógnita.

## Tres contrastes independientes

1. **Coherencia eléctrica.** Derivar nodos, puntos DC, relaciones de frecuencia, cargas, RC, no linealidades y condiciones de calibración del manual. Verificar límites y extremos con un solver de referencia fuera de tiempo real. Anotar toda hipótesis de transistor, potenciómetro o ajuste que el papel no resuelva.
2. **Implementación numérica.** Comparar la versión portable con el solver de referencia usando entradas idénticas: notas, controles, barridos y niveles. Fijar tolerancias antes de optimizar. Esto comprueba que el plugin sigue el circuito elegido, no que suene idéntico a un ejemplar histórico.
3. **Plausibilidad sonora.** Usar varias grabaciones realizadas por sus autores con Model D vintage, si permiten identificar instrumento y escenas. Comparar rasgos robustos (familia de ondas, carácter de resonancia, articulación, respuesta a sobrecarga) y registrar desacuerdos. Una grabación pública sin ajustes y cadena conocidos no identifica ganancias, curvas de perilla ni parámetros individuales.

El [corpus de investigación numérica](FUENTES.md#investigación-de-métodos-numéricos) incluye dos derivaciones del ladder para contrastar ecuaciones y métodos de integración. La literatura sobre la sierra de Moog localizada hasta ahora usa un **Voyager** como señal medida: aporta técnicas de antialias, pero no una plantilla espectral del Model D clásico.

## Fuentes de audio candidatas y límite de cada una

| ID | Fuente primaria de la grabación | Uso admisible | Falta para comparación estricta |
| --- | --- | --- | --- |
| AUD-YORK | [Radek Rudnicki, *Immortal Waves*](https://radek-rudnicki.net/immortal-waves/): informa que grabó un Model D vintage de la Universidad de York, primero las ondas crudas de sus tres osciladores. | Contraste de **forma de ciclo** y armonía de osciladores. | El paquete fue editado a ciclos únicos para Elektron; no conserva ataque, deriva, fase continua ni ganancia absoluta. No se informa revisión de placa ni cadena completa. |
| AUD-WHITMORE | [Andy Whitmore, demo de su Model D de 1978](https://www.andywhitmore.com/news/links-to-tour-of-greystoke-studio-demos-of-synths-how-to-make-a-dance-track/) ([video](https://youtu.be/ub4kyQRAApk)). | Escucha de gestos musicales y posiciones visibles del panel cuando la toma lo permita. | Audio de video, cadena y calibración no declaradas; ninguna métrica espectral fina ni nivel absoluto. |
| AUD-BMF-8903 | [Bob Moog Foundation, Model D vintage serial 8903](https://moogfoundation.org/2021-minimoog-raffle-win-a-vintage-minimoog-model-d-in-gorgeous-custom-cabinet/), con videos en la página. | Segunda unidad histórica independiente para comparar rasgos de performance. | Unidad restaurada; no hay inventario público completo de placas, ajustes ni captura seca controlada. |
| AUD-MOOG-2016 | [Moog Music, barridos de filtro grabados directos](https://soundcloud.com/moogmusicinc/3-filter-sweeps?in=moogmusicinc%2Fsets%2Fminimoog-model-d-sound-samples), sin EQ, compresión ni efectos según la descripción. | Contraste **auxiliar** de material publicado durante la reedición 2016; no fija valores del clásico. | Confirmar identidad exacta de la unidad; posiciones, niveles y carga no están especificados con precisión. |
| AUD-RHEA-SYNTHMANIA | [SynthMania, interpretación de las fichas de Tom Rhea](https://www.youtube.com/watch?v=S_FKXtwqJoQ), publicada en 2015. | [Tres escenas con fichas verificadas y ajustes iniciales de RF-D](PATCHES_REFERENCIA_MODEL_D.md). | Transcribir los gestos de cada tramo. Número de serie, revisión de placa y cadena de grabación pendientes. |

Estas fuentes son **candidatas**, no un conjunto de datos aprobado. Antes de analizar audio se comprobarán disponibilidad, identidad, formato y derechos. Sólo se conservarán archivos localmente cuando el propietario los ofrezca para descarga en condiciones compatibles; Git y el plugin guardarán únicamente enlaces, metadatos y resultados propios.

## Escalera de afirmaciones

| Evidencia lograda | Afirmación permitida |
| --- | --- |
| Esquema, BOM y ecuaciones contrastadas | “Modela la topología y la calibración nominales de la revisión documentada.” |
| Solver y plugin concuerdan en escenas reservadas | “La implementación portable reproduce el modelo de referencia dentro de los límites declarados.” |
| Comparación con varias demos vintage de procedencia conocida | “Comparte estos rasgos audibles observados”, con escenas y límites específicos. |
| Capturas controladas de un instrumento identificado | Sólo entonces se podría afirmar proximidad cuantitativa a esa unidad y condición. Esta etapa no está prevista para RF-D. |

Se puede publicar un instrumento musical útil y una recreación de circuito sin superar el último escalón. Las afirmaciones de fidelidad deben corresponder exactamente a la evidencia disponible.

En RACE, los gates de grafo, control, modelo, variación, discretización y tiempo real pueden avanzar con sus límites declarados. El gate **C6 de comparación con instrumento** quedará abierto. Su ausencia no se reemplaza por una buena puntuación frente al solver ni por semejanza con una grabación comprimida.

## Primeras tareas ejecutables

1. Transcribir Fig. 9-3 a un grafo de nodos con valores, controles, conexiones, cargas y dudas visibles; documentar cada derivación en [BLOQUES.md](BLOQUES.md).
2. Derivar VCO 1 aislado y un solver de alta precisión; comprobar frecuencia, forma y límites de servicio, con escenarios fuera del ajuste.
3. Construir la ruta mixer → filtro → recuperación → VCA 1/2 → salida y el teclado/contornos. Mantener perfiles de revisión separados.
4. Preparar un banco de escucha con fragmentos identificables de **al menos dos** unidades vintage y escenas propias equivalentes donde el panel sea reconstruible. Las escenas no reconstruibles sirven para escucha general.
5. Registrar en [MATRIZ_DE_FIDELIDAD.md](MATRIZ_DE_FIDELIDAD.md) qué se sabe del circuito, qué pasa pruebas numéricas y qué queda abierto en audio físico.
