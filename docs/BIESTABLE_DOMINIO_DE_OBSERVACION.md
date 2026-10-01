# Consulta al mismo reloj dentro del dominio temporal

## Motivo y política previa

La [rejilla B3/C3 original](BIESTABLE_OBSERVACION_ENTRE_MUESTRAS.md) conserva
139 consultas fallidas y tres consultas válidas con un resto temporal menor
que 1 ps. La nueva versión fija **h mínimo de observación=1 ps**, igual al
mínimo declarado de ambas trayectorias, antes de repetir esos puntos.
Conserva los 386 instantes originales, sus etiquetas y el gate de 1 mV;
no aproxima el tiempo pedido al extremo almacenado.

Si el destino es un extremo aceptado o el resto es ≥1 ps, reutiliza la
consulta original. Si el resto es positivo y menor que 1 ps, retrocede
exactamente un estado aceptado, restaura sus dos historiales reales y
resuelve dos medios intervalos BDF2 hasta el tiempo solicitado. El segundo
usa la memoria provisional del primero. Ambos deben tener h≥1 ps,
crecimiento respecto del historial anterior ≤2, KCL <10 pA y error de rama
<10 fV. No hay reinicio, elección de otra raíz ni publicación de esas memorias
en la trayectoria principal. Un fallo queda registrado y no activa otra ruta.

Esta política no redefine el tiempo real de las trayectorias: declara un
camino numérico de consulta diferente cuando el anclaje más cercano queda
fuera del dominio. Por ello ambas memorias intermedias y cada diagnóstico
se conservan. Tampoco aplica aceptación local por predictor BE/BDF2 a
las observaciones; continúan siendo provisionales.

## Resultado

| Medida | Resultado |
| --- | ---: |
| Tiempos observados | 386/386 |
| Consultas válidas | 772/772 |
| Consultas originales reutilizadas | 630 |
| Consultas desde anclaje anterior | 142 |
| Intervalos provisionales nuevos | 284 |
| Intervalo provisional mínimo | 12,207031 ns |
| KCL máxima de intervalos provisionales | 9,86447 pA |
| Puntos del prefijo hasta 2,3 ms | 99/99 |
| Discrepancia máxima del prefijo muestreado | 59,0099 µV, trigger, 0,95 ms |
| Discrepancia máxima de toda la rejilla | 0,126367839 V, nodo 66 |

El **gate diagnóstico del prefijo muestreado pasa**: 99 puntos completos
con diferencia <1 mV. No demuestra una cota continua antes de 2,3 ms.
El máximo completo permanece a 2,442491150 ms y **falla el gate de 1 mV**.
Se conservan sin cambios el prefijo interpolado original fallido, el informe
de consultas incompletas y la comparación B3/C3 completa.

## Evidencia y regresión

Productor: `tools/loudness_latch_bdf_observation_domain.py`.

Datos: `evidence/loudness_latch_bdf_observation_domain.json.gz`.

Resumen: `evidence/loudness_latch_bdf_observation_domain_summary.json`.

`python tools/loudness_latch_bdf_observation_domain.py`

`python -m unittest discover -s tests -p test_loudness_latch_bdf_observation_domain.py -v`

Cinco pruebas verifican todas las memorias intermedias, publicación directa
con Decimal80, residuos del solver, conservación de ambos estados ante
consulta, dominio de los intervalos y destino exacto. Comprueban que sólo
los restos menores que 1 ps usan el anclaje anterior, que los datos originales
reutilizados permanecen idénticos, y repiten las consultas primera, central
y final de esa ruta en cada política, también con Jacobiano totalmente FD
(diferencia <10 nV y KCL <10 pA). Los hashes incluyen los informes
previos; el JSON canónico comprimido se restaura sin pérdidas.

## Continuación

La mejora del observador no disminuye el pico de la transición entre
trayectorias. El siguiente experimento debe separar la memoria acumulada
antes de la regeneración del error introducido dentro de la región rápida:
continuaciones diagnósticas desde dos historiales aceptados comunes, junto
al contraste original desde DC. La inicialización compartida debe declararse
y no puede validar retroactivamente el prefijo, el circuito vintage ni audio.
