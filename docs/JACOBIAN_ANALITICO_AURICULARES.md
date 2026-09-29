# Jacobiano analítico de la etapa activa de auriculares

El [oráculo de placa 3](../tools/headphone_amp_active_dc_reference.py) usa once KCL de corriente **saliente** para Q16/Q11/Q10, CR1/CR2 y nueve resistores. Las conexiones y los valores nominales proceden de **SVC-9 Fig. 9-8, PDF p. 10** (SVC-204D p. 66). Las leyes condicionales son Ebers–Moll simple para BJT (Nagel y Pederson, *SPICE*, 1973, PDF pp. 4–5) y Shockley para los diodos 1N458A de **placa 3**; `I_S`, `β_F`, `β_R`, idealidad y temperatura siguen impuestos, no medidos. Los CR1/CR2 de placa 4 son componentes distintos.

El [Jacobiano](../tools/headphone_amp_active_dc_reference.py) devuelve `J_ij = ∂KCL_i/∂V_j` en siemens. Cada resistor `R` entre dos nodos estampa `+1/R` en ambas diagonales y `−1/R` en las posiciones cruzadas. Para un BJT se transforman las tensiones PNP con `p=−1` (NPN: `p=+1`), y se definen `g_f=I_S exp[p(V_B−V_E)/V_T]/V_T` y `g_r=I_S exp[p(V_B−V_C)/V_T]/V_T`. Como la corriente externa también cambia de signo para PNP, las dos inversiones se cancelan en las derivadas. En el orden de columnas `B,C,E`, las tres filas del dispositivo son:

| KCL | ∂/∂B | ∂/∂C | ∂/∂E |
| --- | ---: | ---: | ---: |
| B | `g_f/β_F+g_r/β_R` | `−g_r/β_R` | `−g_f/β_F` |
| C | `g_f−(1+1/β_R)g_r` | `(1+1/β_R)g_r` | `−g_f` |
| E | `−(1+1/β_F)g_f+g_r` | `−g_r` | `(1+1/β_F)g_f` |

Cada diodo ánodo→cátodo estampa la misma matriz de dos terminales con `g_D=I_S exp[(V_A−V_K)/(nV_T)]/(nV_T)`. La temperatura es Kelvin, tensiones en voltios, corrientes en amperios; el dominio exponencial y la coherencia térmica son los mismos que los del residuo KCL. No se añaden capacitancias de juntura, Early, fugas de placa ni dispersión de dispositivos.

La [regresión](../tests/test_headphone_amp_active_jacobian_reference.py) contrasta los **121 elementos** contra diferencias centrales de `10 µV`, en tres combinaciones de sesgo diodo/β y también en tensiones perturbadas `1 mV`. Usa tolerancias `5×10⁻⁷` relativas y `2×10⁻⁹ S` absolutas; además comprueba rechazo de dominio. El punto DC y la [transferencia AC](AC_AMP_AURICULARES.md) usan esta misma derivada. En el [transitorio aislado](TRANSITORIO_AMP_AURICULARES.md) se agregan `C/Δt` y la carga J7; en el [acoplado de 62 nodos](TRANSITORIO_AURICULARES_ACOPLADO.md) se reemplazan sólo las doce columnas de placa 3, y las primeras cincuenta permanecen por diferencia finita.

En la [malla corta de 256 pasos](ESTRES_TRANSITORIO_AURICULARES.md), una corrida local pasó de `11,7 s` con el grafo ya preparado a `10,1 s` con estas columnas analíticas (≈`39 ms/paso`). El máximo residuo KCL se mantuvo en `9,6969×10⁻¹¹ A` y el máximo de iteraciones en 7. Es una medición orientativa de Python, no una garantía de rendimiento ni una mejora de fidelidad física. La matriz densa y el resto del Jacobiano numérico siguen impidiendo usar este solver en audio en vivo.

La [comparación de trazas](COMPARACION_JACOBIAN_AURICULARES.md) conserva una ruta de 62 columnas por diferencias finitas y coteja estados completos, KCL, conmutación y coste con la ruta híbrida.

En la ruta híbrida, además, las primeras cincuenta perturbaciones evalúan sólo las KCL anteriores y actualizan analíticamente la carga lineal; el único acoplamiento de una de esas columnas a las filas activas es `−C19/Δt` desde el cursor R21 a la base de Q16. La derivación y su cotejo temporal están en la comparación anterior.
