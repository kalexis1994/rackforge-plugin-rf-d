# Memoria acumulada: cuatro ventanas de 64 intervalos

El [protocolo](BIESTABLE_MEMORIA_LARGA_PROTOCOLO.md) y productor quedaron
fijados antes de ejecutar en `08e2663`, el 2 de octubre de 2026. Conservan
residual, circuito, Newton y publicación; amplían longitud y direcciones
del contraste de memoria con el Jacobiano compensado.

## Cobertura y gates

Las **128 continuaciones** completan sus 64 pasos: **8.192 solves no
lineales nuevos**, 256 intervalos de referencia heredados y 256 mapas
equilibrados. No se recalcula DC, retima ni resetea la historia.
Pasan **64/64 contrastes centrales** de los 94 nodos y 25 memorias bajo
10 nV + 1e-3 |predicción|. Las inyecciones son hipotéticas; no constituyen
historias físicas aceptadas ni ejecutan el estimador adaptativo local.

| Ventana | Ancla → fin (ms) | Intervalos nuevos | Máx. KCL publicado | Error central nodal máximo |
| --- | --- | --- | --- | --- |
| prefix | 2,300000 → 2,330859375 | 2.048 | 2,03203 pA | 0,726845 pV |
| attack | 2,422198486 → 2,426281738 | 2.048 | 2,55441 pA | 18,1481 pV |
| reset | 2,442049789 → 2,442074203 | 2.048 | 0,00734096 pA | 0,742162 pV |
| tail | 2,499973869 → 2,512473869 | 2.048 | 0,104614 pA | 0,737433 pV |

Máximo error central de memoria: 0,115990 pV de coordenada. Máximo
error normalizado del contraste nodal: 0,000669073; memoria: 0,0000108314,
ambos menores de 1. Gates de KCL, rama, round trip y corrección Newton
permanecen intactos. Los 256 solves de mapa pasan ambos errores hacia
atrás: máximo **7,85666e-11**, frente a 1e-10.

Las **12 auditorías seleccionadas** (0,31,63 en cada ventana) pasan
álgebra racional y comparación de mapas con el grafo estático
Decimal80/100. Máximo |X-Xref|/(1+|Xref|): **4,65766e-14**;
para T: **2,56892e-15**. Los Jacobianos estáticos redondeados coinciden
en ambas precisiones. No se auditaron independientemente los otros 244
mapas ni todo el circuito espacial: contorno y dinámica siguen compartidos.

## Qué aporta la ampliación

Se contrastan C2 actual/común/diferencial, las cuatro cargas de juntura
actuales por separado y la diferencia cruda sombra/full original. Las
cargas usan Q/(1 pF); la inyección de 1 uV equivale a 1e-18 C.
Esa escala no identifica capacitancia física ni produce un gain universal.

En ataque, Q25 BC actual produce **17,1243** veces la amplitud de entrada
en la respuesta nodal máxima observada; Q25 BE produce 15,8740.
Las otras regiones responden de forma distinta. C2 común también conserva
una respuesta: su máximo nodal en ataque es 1,13723 veces la entrada.
Son cocientes observados en direcciones/amplitudes declaradas, no normas
inducidas sobre todo el estado doble ni evidencia de una causa exclusiva
de los fallos temporales.

La diferencia sombra/full se usa como dirección hipotética del experimento
original sobre la nueva base compensada. **No es un defecto exacto**,
corrección de trayectoria ni cota de error global. Aunque pasan las 64
respuestas, no se cubren todas las direcciones independientes de las 50
coordenadas de historia doble. El siguiente diagnóstico debe contrastar
los productos acumulados sobre esa base completa y su redondeo, conservando
la separación entre mapa lineal, respuesta finita y error temporal.

El [contraste desde DC](BIESTABLE_CONTROLADOR_COMPENSADO_RESULTADOS.md)
sigue fallando el gate temporal de **1 mV**. Este corte no lo recalcula
ni lo cierra; tampoco admite conmutación vintage, audio o deadline.

## Reproducción

[Datos](../evidence/loudness_latch_bdf_static_precision_memory_long.json.gz):
55.648.976 bytes; SHA comprimido
`956c78ef84b02ef18e464b848101eace9dfae0c45226db0080cd518b556a8ecf`;
SHA canónico
`1b2c7c751d8fb37a7544941dfd2d591d3dc4be04d77834c768b04fde880f8381`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_memory_long_summary.json):
136 entradas, tiempos, conteos, gains, máximos y alcance.

El [recibo](../evidence/loudness_latch_bdf_static_precision_memory_long_validation.json)
conserva **5/5 pruebas**, un intento exitoso de 94,125 s y entradas
idénticas antes/después. Verifica anclas/reloj/direcciones; los 256 errores
algebraicos y 12 replays equilibrados; cuatro replays racionales;
publicación, linaje, diferencias y recurrencia de los 8.192 pasos;
64 contrastes centrales; 64 replays no lineales seleccionados;
presupuesto fallido inmutable y almacenamiento. No se repite la suite histórica.

```
python tools/loudness_latch_bdf_static_precision_memory_long.py
python tools/validate_bdf_static_precision_memory_long.py
```
