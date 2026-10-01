# Biestable: trayectoria propia desde DC

## Alcance

Continúa la [sonda de carga no lineal Q25/Q15](BIESTABLE_CARGA_NO_LINEAL.md). Ahora se prepara el circuito completo de 94 nodos en DC con KEY=0 V, conserva sus 21 cargas anteriores y calcula las cuatro cargas nuevas desde ese mismo punto. Las cargas no aportan corriente en DC; sí quedan preparadas para el primer intervalo. No se reutiliza el prefijo temporal anterior para afirmar una trayectoria del circuito ampliado.

Escena de laboratorio: R61=200 Ω, parámetros sintéticos del perfil TF/TR=1/3 ns, alimentación y controles del circuito anterior; en t=0 la fuente KEY pasa de 0 a 10 V y permanece allí. Duración solicitada 3 ms. No es una medición ni una recreación certificada de Note On. Las dinámicas omitidas siguen enumeradas en el bloque anterior.

## Integración y publicación

En cada intento de duración h se resuelven tres candidatos:

1. Un paso completo h desde el último estado aceptado.
2. Un medio paso h/2 desde ese mismo estado.
3. Otro medio paso h/2 desde el candidato intermedio.

Se compara el paso completo con el destino de los dos medios pasos. Sólo se publican los **dos intervalos físicos h/2**, con todos sus voltajes y cargas, después de aceptar el intento completo. No se promedian estados ni se aplica extrapolación de Richardson. Si un solve o un criterio falla, ninguno de sus candidatos sustituye el historial anterior.

Newton conserva KCL<10⁻¹¹ A y corrección<10⁻⁸ V en los tres solves. La semilla de la juntura algebraica del teclado se adapta a la fuente nueva; ninguna carga se edita para acomodar el salto. La estimación temporal no introduce un ADSR ni selecciona una de las raíces anteriores.

Las diferencias se escalan por `absoluto + relativo·max(abs(completo),abs(fino))`. Se comparan los 94 voltajes y las cuatro cargas orientadas. También se limita el incremento BE/BC de cada medio intervalo y se revisa la tasa positiva del descriptor congelado en el estado anterior y los dos destinos.

## Políticas declaradas antes de ejecutar

| Criterio | Política A | Política B |
| --- | ---: | ---: |
| Voltaje absoluto / relativo | 100 µV / 10⁻⁴ | 25 µV / 2,5×10⁻⁵ |
| Carga absoluta / relativa | 10⁻¹⁸ C / 10⁻³ | 2,5×10⁻¹⁹ C / 2,5×10⁻⁴ |
| Incremento BE/BC por medio intervalo | 50 mV | 25 mV |
| Producto (h/2)·λ positiva congelada | ≤0,1 | ≤0,05 |
| h máximo / mínimo | 100 µs / 1 ps | 100 µs / 1 ps |
| Presupuesto total de intentos | 2000 | 2000 |

Si un criterio falla, h se divide por dos. Si los cocientes de error son <0,25 y los otros criterios están por debajo de la mitad del límite, h puede duplicarse hasta el máximo. Estos números son **políticas numéricas del experimento**, no parámetros del instrumento. El mínimo corresponde al intento completo; los intervalos publicados son h/2.

El descriptor conserva el nodo serie de C10, rango dinámico 25 y las puertas anteriores de transformación/residuo. La tasa inicial se evalúa en el límite izquierdo KEY=0; después se usan puntos con KEY=10. Una tasa positiva congelada es un diagnóstico local. Fuera de equilibrio, no incluye la variación de C a lo largo del movimiento y no prueba estabilidad de la trayectoria.

## Evidencia y límites

Generador: `tools/loudness_latch_time_probes.py`; contrato de intento: `tools/loudness_latch_time_reference.py`; [informe](../evidence/loudness_latch_time_probes.json). Guarda cada medio intervalo publicado, las métricas de los candidatos, los intentos rechazados, sus hashes del estado previo, el estado final y cualquier presupuesto agotado. Verifica que las fuentes no cambien durante la ejecución.

`accepted_step_quality_passed` admite sólo la calidad declarada de los pasos guardados. Cada escena informa por separado si llega a 3 ms. Un prefijo aceptado no equivale a completar la escena ni a demostrar una transición física.

### Resultado del primer barrido

| Resultado | Política A | Política B |
| --- | ---: | ---: |
| Intentos aceptados | 723 | 768 |
| Intervalos Euler publicados | 1446 | 1536 |
| Intentos rechazados | 33 | 39 |
| Tiempo final | 3 ms | **2,444484901 ms** |
| Menor intento aceptado h | 190,735 ps | 95,3674 ps |
| Máximo KCL de los tres candidatos aceptados | 9,914×10⁻¹² A | 9,978×10⁻¹² A |
| Escena completa | Sí | **No: paso mínimo** |

La política B conserva 32 rechazos de error/incremento y siete rechazos de line search desde el mismo último estado. El siguiente intento habría sido de 0,745058 ps, inferior al mínimo declarado de 1 ps. No se eleva el mínimo, relaja KCL, reinicia carga ni sustituye una raíz para completar la escena. Q25 permanece con colector de 0,673368 V en ese último estado.

En el intervalo común, desde 25 µs hasta 2,444484901 ms, las trazas difieren hasta **5,00592 V en ATTACK_OUT**, a t≈2,424609375 ms. Son 2059 instantes de comparación interpolada; no se alinean las transiciones ni se normalizan las amplitudes. **El refinamiento todavía no admite esta transición.** La calidad local de pasos aceptados y completar una de las escenas son resultados distintos de la convergencia entre políticas.

Siguiente diagnóstico concreto: reproducir el último rechazo con historial fijo y estudiar tanto el residuo del solve como la escala de error relativa a cargas cuyo origen Q(0)=0 es convencional. Este informe conserva sus criterios y el fallo original.

La comparación entre políticas utiliza la unión de sus tiempos aceptados y una interpolación lineal en ambas trazas. Empieza después del primer destino intermedio de ambas rutas: interpolar el salto algebraico entre t=0 y ese primer punto fabricaría una diferencia. Se registra el intervalo excluido y el máximo observado por nodo/instante. No es una cota entre muestras ni un error frente a tiempo continuo.

La estimación por duplicación de paso **no es un oráculo independiente del circuito**. Dos políticas tampoco establecen el orden de convergencia ni eliminan la incertidumbre de los componentes. El informe conserva `independent_trajectory_oracle=false`, `temporal_error_bound_admitted=false`, `physical_switching_admitted=false` y `audio_admitted=false`.

Seis regresiones reconstruyen el DC, KCL y todas las memorias en cada medio intervalo; repiten candidatos a lo largo de la transición; verifican los modos en puntos guardados, hashes de rechazo, políticas y presupuestos; y regeneran la comparación entre trazas. No necesitan repetir todo el barrido para revisar sus datos.

```powershell
python tools/loudness_latch_time_probes.py
python -m unittest discover -s tests -p test_loudness_latch_time.py -v
```

Siguientes cierres: comparar con otra integración del circuito completo, refinar observaciones alrededor de la transición, revisar transporte y cargas omitidas, y medir el costo de una futura reducción. Una escucha parcial de filtro/VCA/salida puede preceder a la voz completa; este laboratorio no convierte todavía RF-D en un sintetizador tocable.
