# Biestable: residuo representable y origen de carga

## Repetición del fallo

Continúa el [barrido adaptativo desde DC](BIESTABLE_TRAYECTORIA_ADAPTATIVA.md), cuya política B se detuvo a 2,444484901 ms. El [informe de diagnóstico](../evidence/loudness_latch_rejection_audit.json) reconstruye el último estado aceptado y repite el primer intento rechazado por solve: h=95,367431640625 ps.

El paso completo y el primer medio paso pasan. **Falla el segundo medio paso**, de 47,6837158203125 ps, desde el mismo candidato intermedio. La llamada real de producción, el observador con Jacobiano híbrido y el observador completamente FD reproducen el rechazo. No se publican sus estados ni se modifica el informe original.

Fuente ejecutable: `tools/loudness_latch_rejection_audit.py`. Las conexiones, parámetros y unidades siguen siendo los del [biestable condicionado](BIESTABLE_CARGA_NO_LINEAL.md). Las cuatro regresiones reproducen el fallo y sus diagnósticos; hashes y entorno están en el informe.

## Límite concreto en C2

En ambas rutas, tras dos correcciones Newton:

| Cantidad | Resultado |
| --- | ---: |
| Nodo limitante | 92, TIMING_C2 |
| Voltaje C2 | 0,8489549250860621 V |
| Residuo KCL | +1,1002527556570885×10⁻¹¹ A |
| Gate original | abs(KCL)<10⁻¹¹ A |
| Derivada diagonal | 209715,20021 S |
| Corrección requerida en C2 | −5,246414×10⁻¹⁷ V |
| Distancia a cada vecino `float64` | 1,1102230246251565×10⁻¹⁶ V |
| Residuo al vecino inferior | −1,228054×10⁻¹¹ A |
| Residuo al vecino superior | +3,428559×10⁻¹¹ A |

La diagonal está dominada por `C2/dt`, con C2=10 µF. Sumar la corrección Newton al voltaje absoluto no cambia su representación. Ninguno de los dos vecinos inmediatos satisface el gate en ese estado. Las 24 fracciones de line search tampoco reducen el máximo residuo.

El solve lineal tiene residuo ~10⁻²⁶ A en esa última iteración; el Jacobiano FD reproduce el mismo voltaje limitante y residuo. El número de condición estimado por NumPy es ~2,09×10²⁰: es un diagnóstico de escalas, no una prueba de singularidad exacta. Los datos observados sitúan un límite concreto en la representación del voltaje y su compañero capacitivo; no justifican cambiar parámetros del transistor.

No se relaja KCL ni se fuerza aceptación por haber pasado la corrección de voltaje. El siguiente experimento debe representar incrementos/compensación de cargas y contrastar su publicación antes de usarlos en una trayectoria. Este diagnóstico de un intervalo no resuelve toda la convergencia anterior.

## Sensibilidad del estimador al cero convencional de Q

La política inicial compara el error entre cargas de dos candidatos mediante:

```text
ratio = abs(Qcompleto−Qfino) /
        [Qabs + Qrel·max(abs(Qcompleto),abs(Qfino))]
```

El numerador es invariante al cambio `Q→Q+Q0`; el denominador relativo no lo es. Para una carga conservativa, sumar una constante a Q y a su historial no cambia `(Qnuevo−Qprevio)/dt`, su derivada ni la KCL terminal. Q(0)=0 es la referencia convencional adoptada en el helper, no una medida de la carga absoluta de la pieza.

Se repiten dos rechazos dominados por carga, uno por política, desde sus historiales originales. Se evalúan **sombras matemáticas** con desplazamientos comunes −1 nC/0/+1 nC por carga orientada. No son parámetros físicos, cambios del dispositivo, nuevos estados publicados ni correcciones de las trazas.

| Caso | Ratio con Q0=0 | Ratio con Q0=±1 nC |
| --- | ---: | ---: |
| Política A | 1,136517 | ≈2,8133×10⁻⁶ |
| Política B | 1,813577 | ≈2,79125×10⁻⁶ |

El criterio de carga cambia de rechazo a aceptación en esas sombras aunque el incremento terminal sea algebraicamente idéntico. El cálculo de los ratios mantiene exactamente el numerador original y desplaza sólo el denominador, aislando la sensibilidad de escala. La identidad terminal se verifica en Decimal de 80 dígitos desde los valores binary64 guardados, separándola del redondeo que introduciría un desplazamiento grande en `float64`. Los rechazos originales permanecen intactos.

Este contraejemplo cuestiona el uso de la magnitud absoluta de Q como escala relativa del adaptador, especialmente cerca de su cero. No demuestra por sí solo qué criterio alternativo cumple los errores de la trayectoria.

## Siguiente contrato y límites

Estudiar por separado:

1. Coordenadas de incremento y memoria compensada para los capacitores lentos, con KCL y conservación a publicación.
2. Control de error en observables independientes del origen de carga: diferencias de juntura o incrementos/corrientes con unidades explícitas.
3. Refinamiento de la trayectoria completa, conservando la discrepancia anterior de 5,006 V y contrastando con otra integración.

Un criterio nuevo debe tener versión, razón de sustitución y gates declarados antes del próximo barrido. No se reinterpretan los 2982 intervalos anteriores como un refinamiento exitoso. El transporte y las cargas omitidas siguen abiertos; el diagnóstico no admite Note On/Off físico, audio ni tiempo real.

```powershell
python tools/loudness_latch_rejection_audit.py
python -m unittest discover -s tests -p test_loudness_latch_rejection.py -v
```
