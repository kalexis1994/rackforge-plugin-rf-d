# Controles cero y selección finita de pequeña señal

[Protocolo](BIESTABLE_PEQUENA_SENAL_PROTOCOLO.md) y productor fijados
antes de medir en `afc8144`, el 2 de octubre de 2026. Bloque separado
del [contraste anterior](BIESTABLE_DIRECCIONES_EXTREMAS_RESULTADOS.md),
con gates y seis direcciones de ataque intactos.

## Reproducción de la base

Las cuatro continuaciones sin inyección completan **256 pasos nuevos**.
Sus historias publicadas son **canónicamente idénticas** a las 256 historias
de referencia. Diferencia nodal y de memoria: **cero**. El mismo mecanismo
de perturbación/continuación no introduce deriva en este control.
Esto no prueba una causa exclusiva de la respuesta par anterior, pero
descarta deriva de reproducción observable en esos controles.

## Nuevas amplitudes de ataque

Las **48 continuaciones de ataque** completan **3.072 pasos nuevos**,
sumando **3.328 solves no lineales nuevos** con los controles. Todos los
gates de solve y publicación pasan; máximo KCL 2,58272 pA. No se resetea,
retima ni ejecuta el estimador adaptativo local. Cero solves nuevos de mapas.

Pasan **24/24 contrastes centrales** y **13/24 comparaciones de ambos
signos**. Los otros **11 fallos individuales** permanecen en el informe.
En todos ellos falla el gate nodal; memoria conserva sus gates.

| Norma doble de inyección | Direcciones con ambos signos aprobados | Mayor error nodal individual normalizado |
| --- | --- | --- |
| 0,125 uV | **0/6** | 2,51728 |
| 0,0625 uV | **1/6**, sólo C7 común | 1,20034 |
| 0,03125 uV | **6/6** | 0,550189 |
| 0,015625 uV | **6/6** | 0,237015 |

Gate por coordenada/intervalo: 10 nV + 1e-3 |predicción|. La norma doble
usa ambas memorias y Q/(1 pF) para las cargas, escala exclusivamente
numérica. No se recomienda una amplitud de integración a partir de esta tabla.

En la dirección de máximo nodal, la respuesta par máxima pasa de
0,571526 uV a 0,142882 / 0,0357203 / 0,00893017 uV en los cuatro niveles.
Se conserva la evolución sin afirmar un orden asintótico ni ajustar un
coeficiente cuadrático con esos datos. El contraste central sigue cancelando
la parte par; por eso se mantienen los gates individuales.

Estos pases pertenecen a seis direcciones/amplitudes de una ventana,
sin admitir una bola no lineal en 50 coordenadas ni un límite musical.
Los **18 fallos de ataque anteriores** a 1/0,5/0,25 uV no se resuelven
retroactivamente. No se cambia tolerancia, circuito ni referencia.

El siguiente trabajo útil es derivar la curvatura direccional del residual
y de la memoria publicada desde las leyes de circuito, con sus dos
historiales. Un predictor de segundo orden debe contrastarse con datos
reservados y gates declarados, conservando los fallos del predictor lineal;
ajustarlo y probarlo sobre estas mismas respuestas no sería validación.

No se deriva aquí el defecto temporal ni una cota global. El gate de
**1 mV desde DC** sigue abierto, junto con física vintage, audio y deadline.

## Evidencia y pruebas

[Datos](../evidence/loudness_latch_bdf_static_precision_memory_small_signal.json.gz):
20.531.061 bytes; SHA comprimido
`82aba2ee663917b51e25d44a624738fb0b26d40f854d405458ab02f210b40fcd`;
SHA canónico
`8ab824a6ee4eaa41ba24620058f75e54071d1fef2fec11a80d8c92cf2cce9089`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_memory_small_signal_summary.json):
145 entradas, controles, todos los niveles y fallos.

El [recibo](../evidence/loudness_latch_bdf_static_precision_memory_small_signal_validation.json)
conserva **4/4 pruebas**, un intento exitoso de 32,246 s, entradas
idénticas antes/después. Verifica controles cero, selección congelada y
los 18 fallos anteriores; las 52 inyecciones y todos los pasos con
linaje/publicación/diferencias/predicción; métricas centrales/individuales;
104 replays nuevos seleccionados, presupuestos inmutables, almacenamiento
y alcance. No se repite la suite histórica.

```
python tools/loudness_latch_bdf_static_precision_memory_small_signal.py
python tools/validate_bdf_static_precision_memory_small_signal.py
```
