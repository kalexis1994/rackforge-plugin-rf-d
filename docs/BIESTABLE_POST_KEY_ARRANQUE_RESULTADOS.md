# Publicación del evento y arranque propio desde t=0+

## Protocolo y adapter congelados

Helper, productor y [protocolo](BIESTABLE_POST_KEY_ARRANQUE_PROTOCOLO.md)
se fijaron en `d5a7b18` antes de ejecutar. Reutilizan exactamente el
[evento racional certificado](BIESTABLE_POST_KEY_RESULTADOS.md), el recinto
primario robusto y el DC publicado previo. No se resuelve otro DC/evento,
se modifica una ley ni se cambia el integrador histórico.

El adapter publica 94 potenciales y 25 tasas auxiliares mediante pares
high+low y mide exactamente su error racional. Conserva los **21 pares de
memoria y cuatro cargas de juntura** previos. Reconstruye todos los nodos,
aliases y rails duplicados del contorno con los high nuevos, manteniendo
los mirrors de condensadores y firma de circuito. No recalcula cargas
desde los high redondeados, porque rompería la conservación del evento.

`rf-d/post-key-bdf-origin/v1` conserva identidades de evento e historial
previo, fuente 0→10 V y clock cero. Su historia tipada tiene KEY=10,
previous=None y ningún previous_dt/key. La clase histórica History admite
esa estructura aunque el texto de un guard diga DC; el esquema externo
identifica explícitamente el límite derecho, no un DC KEY=0. Las tasas
auxiliares no se convierten en historial BDF2 ni se usan en lugar de un paso.

## Error de publicación y anclaje inicial

La restauración JSON canónica conserva todo el estado y sus memorias.
El chequeo racional exterior evalúa las leyes ideales directamente sobre
los pares restaurados; Decimal100 da un contraste independiente.

| Magnitud | Máximo observado/certificado | Gate / alcance |
| --- | --- | --- |
| Error exacto de pares nodales frente al centro racional | 7,38237137523e-32 V | añadido a la cota del evento |
| Error exacto de pares de tasa | 1,51866674157e-30 V/s | añadido a la cota de tasa |
| KCL exterior del evento publicado | 7,41000669489e-33 A | <10 pA |
| Restricciones de carga exteriores | 4,16255178801e-31 V de coordenada | <10 fV |
| Exponente máximo del evento | 27,4053573773 | <=45, sin clamp |

La suma exacta entre recinto del evento y error de pares certifica el estado
nodal publicado a **~37,51 nV por nodo**, con cota auxiliar de tasa
**~37,51 V/s**. Se conserva la caja inicial de memoria DC, por identidad
de sus 25 valores: **~147,95 pV ponderados**, pesos lineales uno y pesos
de juntura 1/8, 1/4, 1/256, 1/512. Su conversión a una norma temporal
todavía debe probarse explícitamente.

El anclaje local publicado queda conocido. El rechazo backward de la
inversa H119 binary64 anterior permanece intacto; no se admite esa inversa
en audio ni se convierte este resultado en una prueba del plugin nativo.

## Trayectoria propia: 512 intervalos, mismo reloj

Se usan los primeros 512 intervalos del reloj completo compensado, sin
control adaptativo ni retiming. El origen cambia de DC KEY=0 al estado
post-KEY publicado. **Primer paso backward Euler y 511 pasos BDF2**;
cada BDF2 usa estados realmente aceptados, sin fallback ni reinicio.
Todos los estados entrantes/salientes, coeficientes, SHA y diagnósticos
quedan en el informe. La primera resolución requiere una iteración y el
prefijo acumula 1.085 iteraciones declaradas por el solver histórico.

Los **512/512** pasos pasan publicación, restauración canónica, reloj,
inmutabilidad y contraste discreto Decimal100. El prefijo llega a
**0,0023318359374999834 s (~2,332 ms)**, sin rechazos ni stop.

| Contraste | Máximo | Gate |
| --- | --- | --- |
| KCL publicada por el chequeo histórico | 9,86377471401e-12 A | <10 pA |
| KCL discreta independiente Decimal100 | 9,86377437002e-12 A | <10 pA |
| Restricciones lineales publicadas / Decimal100 | 3,63547941816e-27 V | <10 fV |
| Diferencia nodal frente al arranque histórico, endpoints iguales | 3,59445624926e-12 V (~3,59 pV) | <10 nV, 0 fallos |
| Diferencia de coordenada de memoria frente al histórico | 1,08244337971e-13 V (~0,108 pV) | <10 nV, 0 fallos |

El residual independiente usa KCL estática ideal y derivadas BDF de las
cargas almacenadas, con coeficientes binarios levantados exactamente.
La consistencia de juntura publicada presenta desajuste máximo
**5,38173878392e-14 V en Q/S**: queda como diagnóstico, separado del gate
de restricciones lineales. No se inventa un gate universal ni se oculta.
Todas las diferencias por nodo y memoria se conservan, no sólo los máximos.

Que ambas trayectorias coincidan en endpoints no prueba su error frente al
DAE ideal. El prefijo posee procedencia propia; ningún interpolante anterior
que cruzaba el salto queda reutilizado como reconstrucción suave de t=0+.

## Evidencia y validación

[Datos](../evidence/loudness_latch_bdf_static_precision_post_key_startup.json.gz):
**2318164 bytes**, SHA comprimido
`a076bbc6886b2824c15fa7dbff25599078058813a137bb2744b6d9f96c2bd786`,
canónico `c2f0f574742f59733819b6c8fce9ccffa56b86cc926880588ec86da482b65bfc`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_post_key_startup_summary.json).

Datos, ocho regresiones y validador se congelaron en `0430b10`.
**Ocho pruebas pasan al primer intento, 10,1142039 s**: pares y error exacto,
25 cargas conservadas, mirrors completos, guards, recintos del evento,
cotas iniciales, orden BE/BDF, linaje completo, 512 chequeos independientes
de corrientes salientes, comparación por coordenada, bytes, fuentes y scope.
Las entradas son idénticas antes/después de validar. El recibo aceptado
se fija en `19aaf47` antes de ampliar el [corpus](BIESTABLE_POST_KEY_ARRANQUE_ENTRADAS.md).

## Alcance y siguiente corte

`post_key_published_initial_error_known=True` identifica el anclaje local
del integrador offline. **Duración de error continuo realmente certificado:
cero.** `actual_dae_error_bound`, `full_path_coverage` e `initial_error_known`
global siguen falsos. Global 1 mV, resto temporal, hardware, voz audible y
deadline conservan sus gates. No hay cambios en el motor nativo.

El [plan de primer soporte continuo](BIESTABLE_PRIMER_SOPORTE_CONTINUO_PLAN.md)
aborda reconstrucción desde el límite derecho, conversión de memoria,
defecto integrado y recinto autosuficiente antes de propagar más tiempo.
