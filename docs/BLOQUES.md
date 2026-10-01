# Contrato por bloque de circuito

Para cada placa y ruta: designadores/nodos, referencias de esquema, alimentación, carga, unidades, ecuaciones, condiciones iniciales, ajustes, variación, solver, oráculo, perfil portable, vectores y comparación física. Usar la [plantilla RACE](https://github.com/kalexis1994/rackforge-race/blob/main/plantillas/BLOQUE_CIRCUITO.md) cuando empiece la derivación.

## Candidatos iniciales

1. **Teclado/control:** prioridad monofónica, gate/trigger, glide, tune y ruedas; documentar qué parte del MIDI de RackForge reproduce una señal original y cuál es una extensión.
2. **Osciladores:** tres cores y sus salidas, selección de forma, escalas, desafinación y oscilador 3 como fuente lenta/rápida. El [primer subgrafo VCO 1 CA3046](VCO1_CA3046.md) incluye C1, reset y referencia de eventos; el convertidor y los formadores aún no están resueltos. No reducir las formas a ondas matemáticas ideales sin derivar el punto de salida real.
3. **Ruido y mixer:** fuentes, cargas, ganancias, recorte y realimentación por entrada externa. Medir antes de atribuir toda saturación al filtro.
4. **Filtro ladder:** celdas, control de frecuencia, emphasis, seguimiento, contorno y no linealidad de entrada/retorno. Incluir autooscilación y comportamiento de graves bajo resonancia.
5. **Contornos y VCA:** curvas, tiempos por control, release/decay, retrigger, offset y transitorio de salida.
6. **Salida:** amplificación, carga, nivel y clipping final.

Este listado es un mapa de investigación. La topología exacta y sus componentes quedan sujetos a la revisión documental elegida y sus correcciones.

El [contorno cargado hasta J7](CONTORNO_CADENA_94_Y_ESTABILIDAD.md) reúne 94 nodos y 21 cargas. C2/reset son incógnitas. La [sonda ampliada del biestable](BIESTABLE_TRES_RAICES_Y_CARGA_RAPIDA.md) registra tres raíces y una inestabilidad rápida omitida; las cargas de diagnóstico no se incorporan a la voz ni eligen una rama.

El [inventario de junturas](CARGAS_JUNTURA_Y_DOMINIO_BIESTABLE.md) fija doce sesgos Q25/Q15 y verifica una primitiva de carga de dos terminales en 300 sondas sintéticas. Debe completarse identificación de parámetros, partición BJT, transporte y saturación antes de unir cargas físicas al biestable. Las [lecciones de conmutación para RACE](LECCIONES_RACE_CONMUTACION.md) conservan los gates reutilizables.

El [puerto C2/reset cargado](PUERTO_CONTORNO_CADENA_71.md) cuantifica corrientes y tangentes con los 71 nodos del circuito. El candidato temporal conserva la memoria entrante hasta la aceptación externa. La KCL del contorno deberá incorporar ambas corrientes; el biestable todavía no usa este puerto ni tiene conmutación admitida.

El [cierre conjunto de 71 nodos](SEGUIDOR_VCA_CADENA_71.md) incorpora la carga R59/base Q18 del primer VCA al seguidor de volumen. Devuelve corrientes a los puertos C2/reset y conserva los dieciocho capacitores de la cadena. C2 del contorno y la base reset todavía son fuentes impuestas; no hay conmutación física admitida.

Contornos: el [grafo de volumen y gatillo](CONTORNO_VOLUMEN_CIRCUITO.md) conserva los componentes y una ambigüedad de raíces del biestable. El [seguidor Q3/Q2 nativo](SEGUIDOR_VOLUMEN_NATIVO.md) cierra cinco nodos con CR6 y cargas impuestas, devolviendo corrientes/derivadas hacia C2, reset y futura base Q18. La conmutación y el contorno de filtro aún no están admitidos.

El [mapa de hallazgos](HALLAZGOS.md) enlaza cada bloque a la descripción y al esquema original; [REVISIONES.md](REVISIONES.md) registra qué variantes y correcciones pueden cambiar su derivación. En particular, la ruta de audio continúa después del ladder por recuperación de ganancia y **dos VCA** documentados en SVC-204D (PDF p. 12), y los contornos requieren representar el switch de final decay.
