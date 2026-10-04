# Cobertura real del soporte y conversión entre normas fijas

## Corte congelado

El [protocolo](BIESTABLE_COBERTURA_METRICAS_PROTOCOLO.md), helper y productor
se fijaron en `dff7032` antes de medir; datos, suite y validador en `54804a6`
antes de validar. No hay nuevos solves, inversas del circuito, candidatos P
o parámetros de sonido. Se conservan todos los informes y gates previos.

Se audita el linaje de **6.486 intervalos compensados desde DC** y **1.536
intervalos refinados** de las ocho referencias N2/N4. Cada entrada verifica
SHA del historial entrante, estado previo completo, clave, dt y cierre del
reloj publicado; cada final coincide con su archivo. Los cuatro anclajes
de ventana son idénticos a filas de la trayectoria completa por JSON canónico.
Es procedencia numérica, no una prueba de error físico del DC o del anclaje.

## Qué cubren exactamente los certificados

La muestra 31 aporta cuatro historiales para cada interpolante. El recinto
temporal de inversa y el análisis modal cubren **sólo el último subintervalo**
entre los dos tiempos más recientes, dividido en ocho celdas. Los otros
soportes, las 64 muestras y la duración completa de la ventana de laboratorio
no reciben por herencia una prueba de error continuo. La métrica cuadrática
es aceptada en seis casos; los dos de reset conservan su rechazo.

| Ventana | N | Inicio seleccionado (ms) | Fin seleccionado (ms) | Duración (ns) | Métrica P |
| --- | --- | --- | --- | --- | --- |
| prefix | 2 | 2,31972656250 | 2,31992187500 | 195,312500000 | aceptada |
| prefix | 4 | 2,31982421875 | 2,31992187500 | 97,6562499998 | aceptada |
| attack | 2 | 2,42310791016 | 2,42315673828 | 48,8281249999 | aceptada |
| attack | 4 | 2,42313232422 | 2,42315673828 | 24,4140624999 | aceptada |
| reset | 2 | 2,44206180573 | 2,44206199646 | 0,190734863233 | rechazada |
| reset | 4 | 2,44206190109 | 2,44206199646 | 0,0953674313998 | rechazada |
| tail | 2 | 2,50612621307 | 2,50622386932 | 97,6562499998 | aceptada |
| tail | 4 | 2,50617504120 | 2,50622386932 | 48,8281249999 | aceptada |

Los extremos binarios archivados se levantan a racionales exactos; la tabla
es redondeada. No se reemplaza el extremo binario de 3 ms por otra fracción
decimal, ni se reconstruye un reloj diferente sumando dt racionales.
N4 está contenido en N2 en las cuatro ventanas, con el mismo extremo final.

En el dominio completo de ~3 ms:

| Alcance seleccionado | Unión (µs) | Fracción del dominio (%) | Tramos | Huecos |
| --- | --- | --- | --- | --- |
| Inversa ideal y modos, N2 | 0,341987609863 | 0,0113995869954 | 4 | 5 |
| Inversa ideal y modos, N4 | 0,170993804931 | 0,00569979349770 | 4 | 5 |
| Inversa ideal y modos, unión N2/N4 | 0,341987609863 | 0,0113995869954 | 4 | 5 |
| Métricas aceptadas, unión N2/N4 | 0,341796875000 | 0,0113932291667 | 3 | 4 |
| Error real continuo certificado | 0 | 0 | 0 | sin recorrido certificado |

Se guardan todos los extremos de unión y complemento. No se suman dos veces
intervalos anidados. Quitar reset del conjunto de métricas aceptadas fusiona
el hueco que lo rodea; no demuestra que la región haya sido validada.

Los ocho extremos seleccionados comparten tiempo con una fila del reloj
completo, pero **ninguno comparte el historial completo** de esa fila.
El campo `selected_endpoint_matches_full_clock` se refiere a esa igualdad
de historial, no a igualdad de reloj. La suite contrasta ambos hechos por
separado. N2/N4 tienen historias propias y no son estados aceptados de la
trayectoria original; una conversión de norma no identifica sus errores.

## Las seis normas y sus conversiones

Para las seis P aceptadas se reconstruye G=diag(W_J)*P*diag(W_J)/(4*a²).
La norma es sqrt(e_Jᵀ*G*e_J), en las mismas cuatro coordenadas de error de
memoria de carga escaladas por S. G es simétrica positiva definida por LDLᵀ
racional. Los otros cinco bloques mantienen las mismas normas con W=1.

Se calculan **36 pares ordenados**, seis identidades exactas y 30 puentes
no triviales, con **990 consultas racionales**. Alpha*Gsource-Gdest positiva
definida certifica kappa²; una raíz exterior de 256 bits da kappa. Se guardan
seeds Rayleigh/norma, 32 bisecciones, pivotes y factores. Son superiores
certificados, sin afirmar optimalidad de su redondeo o búsqueda.

La tabla presenta el superior de junturas kappa: filas origen, columnas
destino. La conversión del máximo de los seis bloques es **max(1,kappa)**.

| Origen → destino | prefix N2 | prefix N4 | attack N2 | attack N4 | tail N2 | tail N4 |
| --- | --- | --- | --- | --- | --- | --- |
| prefix N2 | 1 | 1,00000466936 | 0,314590341319 | 0,314612159560 | 79,2398799828 | 79,2392709326 |
| prefix N4 | 1,00004016683 | 1 | 0,314589790589 | 0,314611609352 | 79,2413207539 | 79,2407116920 |
| attack N2 | 30,5484459063 | 30,5478660308 | 1 | 1,00010708952 | 639,606397934 | 639,600054726 |
| attack N4 | 30,5520192362 | 30,5514392959 | 1,00015059935 | 1 | 639,655118304 | 639,648774088 |
| tail N2 | 445,533029260 | 445,524178735 | 39,5062347984 | 39,5056949385 | 1 | 1,00010014846 |
| tail N4 | 445,535594559 | 445,526743983 | 39,5064656515 | 39,5059257883 | 1,00010369953 | 1 |

Algunos límites de conversión son grandes; deben pagarse al cambiar norma.
El mapa compara normas de **un mismo vector físico de error**, no transporta
estados a través de tiempo. Todos los certificados conservan
`actual_interface_verified=false` y `missing_region_propagation_proven=false`.
No se multiplica un puente por una cota local para saltar un hueco.

## Reset y trabajo que queda

Reset conserva inversa ideal certificada y ocho celdas por nivel con una
raíz real positiva del bloque interno congelado. Esto no equivale a probar
inestabilidad de toda la trayectoria no lineal acoplada. No se elimina el
rechazo de P ni se atribuye inexistencia de toda métrica a un candidato.
Para cubrir reset se necesita una norma y comparación **no contractivas**
declaradas, con crecimiento y entradas acotados; contracción no es requisito
para una cota finita en un intervalo finito.

El siguiente [plan de cobertura](BIESTABLE_COBERTURA_DESDE_DC_PLAN.md)
empieza por DC y consistencia del salto KEY 0→10 V, inventaría el error
entrante y exige regiones contiguas antes de interfaces entre métricas.
Los objetivos de anclaje previos siguen condicionados al tangente ideal.
**1 mV global sigue abierto**, junto con el resto no lineal, física, voz y deadline.

## Evidencia y regresiones

[Datos](../evidence/loudness_latch_bdf_static_precision_coverage_bridge.json.gz):
**961030 bytes**, SHA comprimido
`9c940504683b2a173c247118e11838976986437f577d2f0749de2dc7362b408a`,
SHA canónico `1a9e18a0c2f0151f4975a7bba657fefe1603c1ff94e813c5445c131c7a72de23`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_coverage_bridge_summary.json).
La [suite](../tests/test_loudness_latch_coverage_bridge.py) pasa **6/6 al primer
intento**, 19.8116313 s. Comprueba unión/complemento exactos, contacto y
solapamiento, conservación de longitud y rechazo de dominios inválidos.
Audita historiales y tampering, todas las trayectorias y soportes, rechazo
de reset y diferencia de reloj frente a identidad de estado.

Normas diagonales con ratio conocido prueban identidad y max(1,kappa).
Se reconstruyen las seis matrices G, sus inversas, los 36 puentes y las
990 consultas, con desigualdades cuadráticas en vectores racionales
independientes, guards, unidades, fuentes, bytes y destinos.
El [recibo](../evidence/loudness_latch_bdf_static_precision_coverage_bridge_validation.json)
conserva SHA antes/después idénticos. El [corpus](BIESTABLE_COBERTURA_METRICAS_ENTRADAS.md)
recupera dependencias y versiones históricas.

```powershell
python tools/loudness_latch_bdf_static_precision_coverage_bridge.py
python tools/validate_bdf_static_precision_coverage_bridge.py
```
