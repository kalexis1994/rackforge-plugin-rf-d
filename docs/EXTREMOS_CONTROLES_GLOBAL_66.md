# Barrido de extremos del circuito global

## Alcance y criterio

Banco offline `circuit66_admission --controls`: 34 escenarios por cada hipótesis de R61 (200 Ω y 200 kΩ), a 48 kHz. Se cambia un control, trim o fuente por vez desde el centro, se mantiene 128 muestras y se restaura otras 128. BUS es una senoide de 100 Hz y 20 mV. Semiconductores, temperatura, alimentaciones y cargas son los supuestos nominales del banco; no identifican una población vintage.

Además se intenta un arranque DC en frío con el inicializador anidado histórico. Los capacitores quedan abiertos en DC. Un caso admitido exige DC y todos sus pasos, KCL global menor que 10 pA, estado finito y publicación atómica. Un fallo conserva exactamente nodos, predictor y cargas de capacitores, y queda registrado. El ejecutable y el wrapper devuelven error cuando falla cualquier caso soportado; terminar el barrido no significa aprobarlo.

Los límites resistivos provienen de SVC-9, Fig. 9-11 (PDF p. 13), Fig. 9-8 (p. 10) y Fig. 9-17 (p. 19); las derivaciones están en las fichas de cada bloque. Los ±0,2 V de contorno, modulación y fuente externa son sondas sintéticas, no límites demostrados del instrumento. Los 1 mΩ de R21 son puntos interiores para estudiar acondicionamiento, no sustituyen sus cortocircuitos exactos. La ley angular de los controles sigue pendiente.

## Resultado previo a correcciones

[Informe](../evidence/circuit66_control_survey.json), esquema `rf-d/circuit66-control-survey/v1`: **no pasa**, 14336 muestras aceptadas, seis fallos de casos soportados y ocho rechazos de extremos todavía fuera del dominio de las API.

| Frontera, en ambos R61 | DC en frío | Salto y restauración | Lectura |
| --- | --- | --- | --- |
| Cutoff máximo | `IterationBudget` | 256 pasos aceptados | Dependencia de la inicialización; no falla la transición ensayada |
| Segundo control de volumen a 0 V | `IterationBudget` | Falla la primera muestra | Presupuesto insuficiente con las semillas actuales |
| Ambos controles de volumen a 0 V | `IterationBudget` | Falla la primera muestra | Mismo límite, no se reemplaza por un mute digital |
| Otros 27 casos soportados por R61 | Aceptado | 256 pasos aceptados | Alcance de un control por vez |
| R20/R21 exactamente 0 o 5 kΩ | `InvalidInput` | Rechazo atómico | Dominio abierto de las API actuales; faltan los casos eléctricos exactos |

El [primer informe](../evidence/circuit66_control_survey_initial.json) contaba R20 como fallo inesperado. La inspección de `main_load` mostró que también estaba fuera de dominio; se conserva el registro original y se corrige la clasificación, sin convertir ese rechazo en soporte eléctrico.

## Trabajo siguiente

1. Resolver R20 en sus límites mediante reducción exacta de cortocircuitos, contrastada con una referencia independiente; no introducir una resistencia mínima artificial.
2. Separar la semilla DC completa de la obligación de resolver primero la cadena anidada. Comparar los puntos DC resultantes y conservar el presupuesto 16/16 y KCL.
3. Investigar Q21 cerca de apagado con su ley Ebers–Moll completa. Registrar si falla una semilla, un salto, o el acondicionamiento; no elevar silenciosamente el presupuesto ni cambiar la fuente de contorno por smoothing arbitrario.
4. Resolver los extremos exactos de R21 y los productos de controles críticos. El barrido actual no cubre combinaciones ni prueba la voz completa.

RACE C5 permanece abierto para estos extremos. C6 (audio vintage) y C7 (deadline/host) siguen abiertos.
