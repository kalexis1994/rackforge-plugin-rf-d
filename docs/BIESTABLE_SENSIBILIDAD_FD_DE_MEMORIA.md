# Sensibilidad FD del mapa de memoria

## Protocolo previo

El corte anterior resuelve Jfd·X=B con fracciones exactas sobre sus
coeficientes binary64 y conserva el desacuerdo de reset de 1,34857×10⁻⁶,
frente a gate 10⁻⁸. Esta auditoría estudia dependencia de la aproximación
FD; no cambia ese resultado ni selecciona una variante del motor.

Se reutiliza el primer intervalo de **las cuatro ventanas** de memoria,
con los mismos estados completos, reloj, parámetros, J mixto y B guardados.
Los pasos centrales fijados son **10⁻⁴, 10⁻⁵, 10⁻⁶, 10⁻⁷ y 10⁻⁸ V**.
Para cada caso se calculan los 94×94 coeficientes y se resuelven los 25 RHS
con el solver racional verificado, para **40 matrices** en total:

1. FD del residuo completo de incrementos: las mismas ecuaciones discretas
   del contraste anterior. A ±1 µV debe reproducir Jfd y X archivados en bits.
2. FD de las corrientes estáticas sobre los 94 nodos, más el sello lineal
   exacto de ramas RC y el Jacobiano existente de cargas de juntura /dt.
   Esta segunda ruta comparte esas derivadas dinámicas con el mapa mixto;
   sirve como diagnóstico de separación, sin ser verificación independiente
   de toda la derivada de cargas.

No se ajusta el denominador FD a la perturbación representable: usa 2·paso,
como el productor original. Se registra el error de la perturbación binaria
real, tanto del incremento como del nodo absoluto reconstruido, para no
atribuir automáticamente toda diferencia al truncamiento del FD.

Se conserva residuo racional exactamente cero, ambos errores hacia atrás
binario/Decimal80 con gate **10⁻¹⁰**, diferencia escalada respecto de X mixto
con gate **10⁻⁸**, componente máxima, matrices completas y cada fallo.
Se compara también la matriz J respecto de J mixto como diagnóstico,
sin introducir un gate nuevo para J ni promover un paso favorable.

Las fuentes se identifican por SHA antes/después y se guardan sin pérdidas.
Los informes anteriores permanecen intactos. No se ejecutan trayectorias
no lineales nuevas ni se admite el mapa completo, una cota temporal,
identificación física, audio o tiempo real. El gate original de reset sigue
abierto independientemente del resultado de otros pasos.

`python tools/loudness_latch_bdf_fd_sensitivity.py`
