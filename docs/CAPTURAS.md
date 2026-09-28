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

## Escenas dirigidas por el manual de servicio

- Dejar constancia del tiempo desde encendido y repetir afinación al inicio y tras **30 min**: SVC-204D PDF p. 29 pide ese calentamiento para la placa estabilizada.
- Probar osciladores con los tres selectores de rango en combinaciones distintas y registrar si existe buffer de octavas: SVC-204D pp. 53 y 57 describe interacción de selectores y kit correctivo.
- Medir el inicio de autooscilación con mixer apagado, contorno abierto y Emphasis barrido; el ajuste de servicio espera inicio entre **7 y 8** (SVC-204D p. 33). Repetir con distintas temperaturas/niveles antes de usar ese rango como objetivo DSP.
- Capturar legato con dos y tres teclas, pulsando y soltando en distinto orden, para distinguir prioridad de nota grave de retención de CV y orden pitch/trigger (SVC-204D p. 16).
- Si la placa 2 coincide con las tandas documentadas en SVC-204D §8.6–8.7, medir deriva del pitch sostenido y la respuesta del VCO 2 al trigger con ATTACK del contorno de filtro en cero y por encima de cero; anotar humedad y transistores instalados.
- Medir pulso de modulación con rueda al mínimo y, si hay residual, determinar si el control incorpora la modificación B-832 antes de decidir si es comportamiento nominal.
- Capturar release con final decay ON y OFF y ataques con retrigger breve; comparar la curva de cada contorno por separado (SVC-204D pp. 12–13).
- Capturar jack **HIGH** y **LOW MAIN OUTPUT** con la impedancia de entrada anotada. Los niveles de fábrica de SVC-204D p. 6 son típicos y dependen de la carga; no compararlos sin esa condición.

Repetir escenas, conservar datos fallidos y reservar configuraciones no usadas para ajuste. Alinear latencia de forma declarada; reportar nivel sin normalización y también comparación con ganancia igualada cuando ayude a aislar timbre. Evaluar diferencias por escena y peores casos. Una grabación de una sola unidad no representa todas las unidades fabricadas.

## Primer gate de audio

No se declarará similitud auditiva hasta tener una unidad identificada y capturas que cubran fuente, filtro, contornos y salida. Antes de esa etapa sólo se podrá afirmar topología o diseño nominal con alcance explícito.
