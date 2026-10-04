# Próximo corte: publicar el evento y arrancar una trayectoria propia

La [consistencia post-KEY](BIESTABLE_POST_KEY_RESULTADOS.md) demuestra raíz
local uniforme para las cargas del DC, con cota nodal ~37,51 nV. El centro
es racional de laboratorio; el estado del integrador todavía no está publicado.
Este plan no congela tiempos, seeds o radios para nuevas mediciones.

## Estado tipado y memoria

Inspeccionar todos los campos de IncrementState, estado joint, latch y
serialización antes de sustituir potenciales. No dejar caches o duplicados
de voltaje incongruentes. Convertir el centro racional a pares high+low con
regla fija; registrar el error de cada componente frente al racional.
Conservar exactamente las 21 memorias lineales y cuatro cargas de juntura
publicadas antes del evento, con sus escalas. Las tasas del evento son un
artefacto auxiliar de consistencia, no una historia previa BDF2.

Volver a evaluar KCL y restricciones del evento sobre el high+low restaurado,
con gates 10 pA, 10 fV y dominio <=45. Añadir error de publicación al recinto
del evento sin cambiar el modelo, ni regenerar el DC o los certificados
congelados. Validar JSON mediante estado tipado/canonical, unidades, reloj,
identidad del estado anterior y fuente KEY=10. Mantener separado el rechazo
de la inversa binary64 y la prueba ideal de la raíz.

## Arranque y comparación

Crear una historia nueva en t=0, previous=None, previous_dt=None y KEY=10,
identificada explícitamente como posterior al evento, no como DC KEY=0.
Declarar primer paso backward Euler y posteriores BDF2 sólo tras disponer
de dos estados reales. Congelar tiempos y política de aceptación antes de
avanzar; preservar todos los pasos, rechazos y estados de entrada/salida.

Comparar con el arranque histórico sólo en relojes coincidentes, distinguiendo
diferencia de trayectoria y error frente al modelo ideal. Conservar ambos
linajes completos. No reutilizar interpolantes que cruzan el salto algebraico
como reconstrucción suave a la derecha de KEY.

## Primer soporte continuo

Definir reconstrucción y método para el tramo inicial con menos de cuatro
historiales, su consistencia de carga, residual integrado y resto no lineal.
La memoria inicial conserva la caja DC previa; convertir explícitamente
sus pesos a la norma del primer tramo. El recinto nodal post-KEY no reemplaza
esa conversión ni autoriza atravesar huecos temporales.

Avanzar por soporte contiguo desde cero con prueba autosuficiente de recinto,
propagación y publicación. Mantener cobertura real en cero hasta que ese
certificado exista. Global 1 mV, física, voz audible y deadline siguen abiertos.
