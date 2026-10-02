# Forzamiento con reloj representable: variante declarada

El 2 de octubre de 2026 se conserva el primer
[experimento](BIESTABLE_FORZAMIENTO_PROTOCOLO.md) íntegro: 1.276 intervalos
finos válidos, dos detenciones de ataque por razón >2 y ocho recurrencias
bloqueadas por entregar RHS unidimensional al solver de columnas.

Esta variante cambia únicamente la planificación de subtiempos y el
formato de entrada/salida del solve. Mantiene leyes, memorias propias,
subdivisiones 2/4, ventanas de 64 pasos, extracción r/z, precisiones,
curvatura, gates, selección racional y alcance del protocolo anterior.
No se modifican sus productor, datos, recibos ni informe.

## Planificación declarada

Los tiempos de estas ventanas están en la misma binade binary64. Se
levanta exactamente su ULP y la distancia al destino a fracciones. El
total es un entero de ticks. Para cada intervalo, la parte más próxima
a ticks restantes / subpasos restantes se limita a floor(2*dt_previo/ULP).
El último consume los ticks restantes. Se exige en todos mínimo 1 ps,
razón <=2, representabilidad exacta y destino final idéntico al base.
Se rechaza otra binade o una partición imposible, conservando el estado.

Este ajuste es explícito y modifica algunos subintervalos respecto a la
división aritmética h/N. Se conserva dt - h/N en cada fila. No redondea
el destino original ni relaja el dominio. El solver sigue tomando su
propio último intervalo fino como historial adyacente.

Cada RHS de 94 componentes se convierte a columna 94x1 para el solver
existente y la solución se restaura a vector. Ambos errores hacia atrás
siguen obligados a <1e-10. No hay clipping, raíz nueva, fallback o reseed.

## Validación y alcance

Se verifican todos los estados/publicaciones y calendarios, replays
seleccionados y cada forzamiento/curvatura en Decimal80/100. Se guardan
resultados y fallos de ambos predictores, y auditorías racionales 0/31/63.
Los testigos racionales y RC del intento anterior verifican signos y
publicación por separado. El forzamiento extraído no es el defecto exacto
ni un estimador independiente utilizable sin la trayectoria fina.
El gate global desde DC de 1 mV, física, audio y deadline siguen abiertos.
