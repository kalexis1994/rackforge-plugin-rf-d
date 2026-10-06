# VCO aislado: representación, regularización y estado de reset

2026-10-06. **El reset bajo carga variable sigue rechazado.** Este bloque
contrasta dos hipótesis numéricas y prepara una reproducción con estados
internos. No cambia las tarjetas del modelo aceptado ni produce audio nuevo.

## Representación del JFET

El [protocolo](JFET_RESET_REPRESENTACION_PROTOCOLO.md) separa el canal de
ambas junturas cargadas con las mismas constantes de LEVEL=1, B=1 y 25 C.
Los dos bancos terminales de 20 microsegundos pasan los gates originales.
El segundo observa máximo de corriente **48.203219 pA**, razón máxima
error/límite **0.000308572**, e integral máxima **5.41101e-19 C**.

El ensayo 01 conserva un fallo del adaptador previo al control. El
[ensayo 02](../evidence/voice_jfet_decomposed02.json.gz) sí ejecuta ese
control: rechaza a **2.277410733 ms**, con log que señala `xic3.4`, nodo
interno del 741. El caso posterior de BUS variable queda no medido.
La equivalencia terminal no admite el circuito completo. Un nombre distinto
en el log no demuestra que otro dispositivo sea la causa del fallo.

## Regularización decreciente

Se vuelve a las primitivas originales y se añade `rshunt` explícito como
perturbación numérica, según el [protocolo](VCO_REGULARIZACION_PROTOCOLO.md).
No se interpreta esa conductancia como fuga física de una placa.

| Ensayo | Control BUS=0 | Resultado |
| --- | --- | --- |
| [1 Gohm](../evidence/voice_vco_rshunt01.json.gz) | Completa 40 ms | Rechaza contraste: 8.095329 V en grilla y 17.515484 microsegundos en cruces |
| [10 Tohm](../evidence/voice_vco_rshunt02.json.gz) | Rechaza a 2.277411170 ms | Log vuelve a señalar JQ7_left |

En 1 Gohm la frecuencia cambia 0.783129 cent, dentro de 1 cent, pero
las otras magnitudes fallan. Cumplir únicamente frecuencia ocultaría el
desplazamiento del reset. Los niveles siguientes de ambas series y los
casos de BUS variable quedan **no medidos por parada al primer rechazo**.
No hay regularizador seleccionado ni aproximación admitida a conductancia cero.
Se excluyeron capacitores `Q=` del ensayo: una carga a sus nodos generados
alteraría el modelo de estado, como documenta ngspice en el reporte 848.

## Reproducción con once observables internos

La [primera sonda](../evidence/voice_reset_state_probe01_rejection.json)
intentó exportar un nodo inexistente: conserva el error, sin inventar una
traza. La [segunda](../evidence/voice_reset_state_probe02.json) valida los
nombres contra el OP congelado, mantiene las primitivas originales y sólo
añade observaciones. **Reproduce exactamente los 7729 tiempos y seis
vectores originales**, incluida corriente de puerto, hasta
2.277414319 ms. No añade shunts ni cambia inicialización o tolerancias.

Los últimos 100 ns contienen **692 estados aceptados**. Algunas magnitudes:

| Nodo | Mínimo, V | Máximo, V | Último aceptado, V |
| --- | ---: | ---: | ---: |
| Rampa C1 | -3.076433 | -0.055736 | -0.055736 |
| 741 IC3, nodo 4 | -4.546410 | -4.500778 | -4.505013 |
| Fuente común E402 | -1.583964 | 1.134024 | 1.134024 |
| Base Q10 | -0.801651 | -0.790107 | -0.793927 |

Es un prefijo aceptado durante reset, no una captura de las iteraciones
Newton que fallan después. La sonda demuestra que observar esos nodos no
altera esta reproducción; no demuestra convergencia del siguiente paso.
Los archivos completos permanecen privados y sus hashes están en los recibos.

## Auditoría y regresiones

La [auditoría ampliada](../evidence/voice_reset_representation_validation02.json)
verifica cinco recibos de representación/regularización y dos de observación.
Reproduce ambos bancos terminales, el contraste rechazado y la ventana interna
sin nuevos solves. Comprueba el ejecutable, fuentes Git, archivos privados,
compresión y tarjetas/grafos idénticos a la revisión anterior. Conserva
también la [auditoría inicial](../evidence/voice_reset_representation_validation.json).

Una regresión detectó que el adaptador de contraste podía ignorar NaN en
un voltaje posterior a otros valores finitos. Se conserva el
[rechazo original](../evidence/voice_reset_test_rejection.json) y su
[fuente exacta](../evidence/voice_reset_test_rejected_source.py). Ahora exige
finitud de toda la matriz, shape correcto y reloj completo creciente.
Los exports ya medidos eran finitos y sus contrastes se reproducen sin
cambiar números ni gates. La [regresión final](../evidence/voice_reset_tests.json)
incluye ambos casos negativos y validación de nombres de nodos.

## Siguiente bloque

Usar esta reproducción exacta para observar residual, corrección Newton y
limitadores durante el intervalo rechazado. Distinguir la última instancia
señalada por el solver de la causa comprobada. Mantener los controles que
completan como comparación antes de volver al cierre R45 y contorno físico.
El [banco conjunto](CONTORNO_VCO_UNION_RESULTADOS.md) conserva su rechazo;
refinamiento, nota larga, identificación vintage y tiempo real siguen abiertos.
