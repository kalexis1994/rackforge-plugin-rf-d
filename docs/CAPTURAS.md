# Escenas de prueba y comparación

RF-D no tendrá capturas propias de un Minimoog. Este documento define **estímulos del circuito simulado** y los mínimos de metadatos para aprovechar grabaciones públicas. Los WAV ajenos, si están ofrecidos para descarga, permanecen en `references-local/` y fuera del paquete. Los resultados derivados guardan enlace, fecha, hash cuando exista, escena y limitaciones.

## Identidad de una referencia externa

Autor y enlace original; declaración sobre vintage/reedición; serial o año sólo si el autor lo aporta; controles visibles o descritos; salida, efectos, carga, interfaz, formato y compresión cuando se conozcan. Cada campo desconocido permanece **desconocido**. Una foto externa no identifica la placa instalada.

## Escenas reproducibles del solver

| Grupo | Estímulo mínimo | Medida del modelo | Comparación externa posible |
| --- | --- | --- | --- |
| Osciladores | Fuente 1/2/3 aislada; cada forma, rango y nota grave/media/aguda | Fundamental, ciclo, armónicos, nivel interno y final, arranque | Ciclos publicados sólo para forma/armónicos; video sólo rasgos amplios. |
| Mixer | Una fuente a varios niveles, pares y entrada externa | Ganancia e intermodulación por etapa | Escucha de saturación cuando controles/ganancia sean visibles. |
| Filtro | Cutoff/emphasis extremos e intermedios, tracking y autooscilación | Respuesta, onset, atenuación grave, transitorios | Barridos visibles con identidad de equipo; sin nivel absoluto si la cadena es desconocida. |
| Contornos | Gate corto/largo, retrigger, sustain y final decay | Curva, tiempos, continuidad y cola | Comparación de articulación cuando la nota y el panel se observen. |
| Performance | Glide, bend, mod wheel, legato y orden de notas | CV/tono y transiciones | Escucha de gesto en demos de performance, sin inferir constantes exactas. |
| Salida | Salidas HIGH/LOW, cargas declaradas y niveles | Headroom, respuesta y recorte simulado | Sin umbral externo si carga, ganancia o normalización son desconocidas. |

## Controles de fábrica que sí se pueden probar sin equipo

- El solver debe reproducir condiciones de alimentación y las relaciones de ajuste de SVC-204D §5; no tratar ±10,000 V como medición de una unidad concreta.
- La placa μA726 tiene un procedimiento tras 30 min de calentamiento (SVC-204D PDF p. 29). Se conserva como contraste de revisión, sin aplicar ese ajuste a la ruta CA3046. Modelar temperatura sólo con mecanismos y parámetros documentados; el warmup real queda sin validar.
- El procedimiento de servicio espera inicio de regeneración entre 7 y 8 en Emphasis (SVC-204D PDF p. 33). Esta condición de calibración sirve como objetivo nominal de control, con tolerancia visible y sin prometer que toda unidad se comporta igual.
- Probar prioridad de nota grave, orden pitch/trigger y final decay de acuerdo con SVC-204D PDF pp. 12–16. Las pruebas del plugin verifican su implementación, no la latencia exacta de contactos de una unidad antigua.
- Conservar los efectos de kits y defectos de [REVISIONES.md](REVISIONES.md) fuera del perfil base, salvo evidencia de que pertenecen a él.

## Gate de audio

Se permite informar **plausibilidad** cuando varias referencias vintage independientes comparten un rasgo audible en escenas identificables y RF-D lo reproduce de forma repetible. Un video con compresión o un ciclo único no permite calibrar deriva, amplitud absoluta, tiempo de contorno o distorsión de una etapa concreta. El contraste riguroso con hardware identificado queda como brecha explícita en la [matriz](MATRIZ_DE_FIDELIDAD.md).
