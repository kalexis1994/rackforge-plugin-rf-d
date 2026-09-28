# Contrato por bloque de circuito

Para cada placa y ruta: designadores/nodos, referencias de esquema, alimentación, carga, unidades, ecuaciones, condiciones iniciales, ajustes, variación, solver, oráculo, perfil portable, vectores y comparación física. Usar la [plantilla RACE](https://github.com/kalexis1994/rackforge-race/blob/main/plantillas/BLOQUE_CIRCUITO.md) cuando empiece la derivación.

## Candidatos iniciales

1. **Teclado/control:** prioridad monofónica, gate/trigger, glide, tune y ruedas; documentar qué parte del MIDI de RackForge reproduce una señal original y cuál es una extensión.
2. **Osciladores:** tres cores y sus salidas, selección de forma, escalas, desafinación y oscilador 3 como fuente lenta/rápida. No reducir las formas a ondas matemáticas ideales sin medir el punto de salida real.
3. **Ruido y mixer:** fuentes, cargas, ganancias, recorte y realimentación por entrada externa. Medir antes de atribuir toda saturación al filtro.
4. **Filtro ladder:** celdas, control de frecuencia, emphasis, seguimiento, contorno y no linealidad de entrada/retorno. Incluir autooscilación y comportamiento de graves bajo resonancia.
5. **Contornos y VCA:** curvas, tiempos por control, release/decay, retrigger, offset y transitorio de salida.
6. **Salida:** amplificación, carga, nivel y clipping final.

Este listado es un mapa de investigación. La topología exacta y sus componentes quedan sujetos a la revisión física elegida.

El [mapa de hallazgos](HALLAZGOS.md) enlaza cada bloque a la descripción y al esquema original; [REVISIONES.md](REVISIONES.md) registra qué variantes y correcciones pueden cambiar su derivación. En particular, la ruta de audio continúa después del ladder por recuperación de ganancia y **dos VCA** documentados en SVC-204D (PDF p. 12), y los contornos requieren representar el switch de final decay.
