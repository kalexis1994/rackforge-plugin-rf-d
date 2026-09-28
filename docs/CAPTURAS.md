# Protocolo inicial de captura

El plan se cierra antes de medir. Capturas crudas en `captures/`, manifiesto de hashes y resultados derivados separados. No subir WAV, fotos internas ni archivos de referencia al repo.

## Identidad de sesión

Unidad/revisión, fecha, temperatura, tiempo de calentamiento, calibración, carga, salida, cables, interfaz, impedancia/ganancia, sample rate, profundidad, reloj, latencia, nivel de calibración y firmware/herramienta de secuenciación MIDI.

## Escenas

| Grupo | Contraste mínimo | Medida principal |
| --- | --- | --- |
| Osciladores | Fuente 1/2/3 sola; cada forma y rango; notas grave/media/aguda | Fundamental, espectro, nivel, deriva, arranque |
| Mixer | Una fuente a distintos niveles; pares; entrada externa | Ganancia, intermodulación, distorsión antes del filtro |
| Filtro | Cutoff y emphasis en extremos/intermedios, seguimiento, autooscilación | Respuesta, onset, nivel, grave, transitorio |
| Contornos | Gate corto/largo, retrigger, sustain, decay switch | Tiempo y curva, continuidad, cola |
| Performance | Glide, bend, mod wheel, notas repetidas, legato | CV/tono y respuesta temporal |
| Salida | Niveles de salida y cargas documentadas | Headroom, respuesta, ruido y recorte |

Repetir escenas, conservar datos fallidos y reservar configuraciones no usadas para ajuste. Alinear latencia de forma declarada; reportar nivel sin normalización y también comparación con ganancia igualada cuando ayude a aislar timbre. Evaluar diferencias por escena y peores casos. Una grabación de una sola unidad no representa todas las unidades fabricadas.

## Primer gate de audio

No se declarará similitud auditiva hasta tener una unidad identificada y capturas que cubran fuente, filtro, contornos y salida. Antes de esa etapa sólo se podrá afirmar topología o diseño nominal con alcance explícito.
