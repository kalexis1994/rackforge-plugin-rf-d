# Tasa dirigida por congruencia: misma métrica y mismas conversiones

## Prueba fijada

El [protocolo](BIESTABLE_JUNTURAS_DIRIGIDA_PROTOCOLO.md), helper y productor
se fijaron en `ca5b8da` antes de medir. Se reutilizan exactamente las seis
métricas aceptadas y los dos rechazos de reset. No cambian P, W, escala
rho, normalización del anclaje, norma, conversiones, forzamiento o mapas
nodales. No se resuelven inversas del circuito ni nuevos candidatos.

Desde la LDLᵀ racional de P=L*D*Lᵀ se reconstruye R=L^-1 y se verifica
R*P*Rᵀ=D. El certificado usa T=R*S*Rᵀ, donde
S=(P*B/rho+(B/rho)ᵀ*P)/2. Se compila una única aparición de cada
B[k,q] antes de aplicar intervalos: conserva cancelaciones de los dos
productos firmados sin multiplicar recintos intermedios independientes.
La base de prueba es interna; la norma publicada sigue siendo la misma.

Centro C y radio Q de T dan T<=C+diag(r), r_i=sum_j Qij. Esta
majorización dirigida se deriva de 2|xi*xj|<=xi²+xj²; todos los radios
permanecen, sin reemplazarlos por un máximo isotrópico. Se prueba
alpha*D-C-diag(r) positiva definida por LDLᵀ racional y 32 bisecciones.
Se conservan seeds, factores y consultas. Hay **48 certificados y
1.584 consultas de tasa**. El inferior del bracket corresponde al
problema auxiliar; no demuestra una tasa real positiva de la familia.

La intersección con el superior isotrópico anterior se declara antes de
medir y se hace sólo en la misma P, norma, escala y anclaje. Se guardan
bruto, anterior y final, y cuál aporta el superior. **40/48** tasas
finales son estrictamente menores; las ocho restantes conservan la anterior.
Sólo M_JJ cambia en la comparación de seis bloques. Todo lo demás se
reutiliza por índice y SHA desde la evidencia inmutable.

## Comparación completa

Los dos casos de reset siguen rechazados y no reciben propagación nueva.
Las seis cotas nodales calculadas no empeoran respecto a la variante
cuadrática isotrópica anterior. La tabla muestra términos forzados con
anclaje cero **hipotético**, y el coeficiente del anclaje ponderado común.
Son cotas del tangente ideal variable; no errores observados del DAE.

| Ventana | N | Mayor tasa superior dirigida (1/s) | Forzado cuadrático anterior (V) | Forzado dirigido (V) | Coeficiente de anclaje dirigido |
| --- | --- | --- | --- | --- | --- |
| prefix | 2 | -1,98006911325e7 | 6,41872359122e-6 | 6,41857983995e-6 | 1758,21341958 |
| prefix | 4 | -1,98138588773e7 | 5,78532726688e-6 | 5,78532726688e-6 | 589,543782934 |
| attack | 2 | 1,91859252724e9 | 8,27052383020e609 | 9,16353967054e9 | 6,08734098821e18 |
| attack | 4 | 7,66374405748e7 | 3,67801677017e70 | 5,21848261270e-6 | 2130,28961476 |
| reset | 2 | candidato previo rechazado | sin propagación cuadrática | sin nueva propagación | sin coeficiente nuevo |
| reset | 4 | candidato previo rechazado | sin propagación cuadrática | sin nueva propagación | sin coeficiente nuevo |
| tail | 2 | -5,26286918326e6 | 5,33902713709e-6 | 5,33902712938e-6 | 589,543782955 |
| tail | 4 | -5,27203318180e6 | 9,92152208337e-6 | 9,92152208336e-6 | 341,381585581 |

**Ataque N4 baja a ~5,22 µV** desde ~3,68e70 V. Su término espectral
RMS previo, de otra norma, era ~1,27e52 V: la comparación nodal puede
presentarse con el mismo anclaje físico, pero no se intersectan sus tasas.
Ataque N2 mejora mucho y todavía da ~9,16e9 V, una cota enorme.
Las tasas de ataque mantienen superiores positivos; no son prueba de
crecimiento real en P ni de inestabilidad modal. La contracción interna
variable certificada continúa en las **32 celdas de prefijo y cola**.

Prefijo N4 y cola cambian muy poco: los datos conservan fracciones exactas
para que la igualdad aparente de una tabla redondeada no sustituya la
comparación. Mantener las ocho filas y los dos niveles no demuestra
convergencia temporal: las consultas seleccionadas y sus dominios tienen
alcance condicionado y no forman una trayectoria continua desde DC.

No se cierra 1 mV global. El coeficiente de anclaje N4 de ataque es
~2130,29 y su error entrante sigue desconocido; faltan restos no lineales,
recorrido completo y conversiones entre intervalos con P distintas.
No se cambia circuito, cálculo nativo, audio o deadline.

## Evidencia y regresiones

[Datos](../evidence/loudness_latch_bdf_static_precision_junction_directed.json.gz):
**2698314 bytes**, SHA comprimido
`5ff69abfab387a26728ef6a2f85c298ec3aae1d43219af0036717cd5f7e824da`,
SHA canónico `67b7add450271b56071e00707c83ba44e85f3adce5356686676d3949e1275ca0`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_junction_directed_summary.json).
Cada caso referencia la métrica anterior por SHA y conserva base exacta;
cada celda guarda centro, radio, diagonal dirigida, seeds, consultas,
factores, superiores bruto/anterior/final y comparación nueva. Forzamiento,
conversiones y salida se reconstruyen desde sus referencias anteriores.

La [suite](../tests/test_loudness_latch_junction_directed.py) pasa **6/6 al primer intento**,
11.818152 s. Verifica congruencia y norma, cancelación de un coeficiente,
productos puntuales independientes, y positividad semidefinida del
majorante en las **1.024 matrices vértice** de una caja simétrica 4×4,
con todos sus menores principales. Contrasta familias intervalares y
unidades, reconstruye los 48 certificados y **1.584 consultas**, y exige
que todas las componentes salvo M_JJ sean idénticas. Reproduce las seis
propagaciones, rechazo de reset, fuentes, bytes canónicos y destinos.
El [recibo](../evidence/loudness_latch_bdf_static_precision_junction_directed_validation.json)
conserva SHA antes/después idénticos. El [corpus ampliado](BIESTABLE_JUNTURAS_DIRIGIDA_ENTRADAS.md)
identifica todas las dependencias y versiones históricas.

Próximo bloque: balancear la majorización del radio en la base diagonal D
con regla fija, manteniendo P y todas sus conversiones. No ajustar por
sonido ni por resultado, y conservar ataque N2 y los rechazos explícitos.
**Anclaje, restos, 1 mV global, física, audio y deadline siguen abiertos.**

```powershell
python tools/loudness_latch_bdf_static_precision_junction_directed.py
python tools/validate_bdf_static_precision_junction_directed.py
```
