# VCO1 CA3046: circuito funcional, convergencia y calibración

Fecha: 2026-10-05. Primer oscilador aislado de la revisión CA3046,
condicionado por los dispositivos y fronteras documentados en
[el oráculo](VCO1_ORACULO_CIRCUITO.md). No es una unidad vintage medida,
una voz completa ni una implementación en tiempo real.

## Qué se cerró

Una misma netlist une IC1/IC3, Qa/Qb/Qc, R42/R78, C1/C2, amplificador
FET, Schmitt/reset, triángulo, pulso y panel. El circuito genera las ondas;
no se imponen frecuencia, corriente de Qa, umbral de C1 ni resets periódicos.
Los controles/rieles, carga adicional de -4 V y voltaje del mixer siguen
siendo fronteras de laboratorio.

La prueba funcional reveló errores anteriores de lectura en seis retornos
que se asignaban a 9B y pertenecen a -10 V. También se preservó/refutó
una corrección intermedia errónea de Q2. [Auditoría](VCO1_AUDITORIA_RETORNOS.md).
El grafo, los helpers, sus pruebas y las descripciones vigentes se corrigieron.
Las corridas rechazadas siguen disponibles por hash; no se usan como referencia.

## Banco de convergencia

14 escenas de 30 ms, observación tras 15 ms, máximos de paso 500/250/125 ns,
Gear2 y Trapezoidal2, dos perfiles de C4, CV de teclado y selector de pulso.
[Datos íntegros comprimidos](../evidence/vco1_circuit_convergence_v1.json.gz),
[almacenamiento](../evidence/vco1_circuit_convergence_storage.json) y
[revalidación](../evidence/vco1_circuit_validation.json).

| Comparación | Diferencia de frecuencia (cent) | Mayor diferencia de extremos de salida (V) | Pico por fase, diagnóstico (V) |
| --- | ---: | ---: | ---: |
| c4-10-refinement | 3.96797947e-06 | 5.84216238e-07 | 0.000203455461 |
| c4-10-method | 5.98974576e-05 | 1.0685041e-06 | 0.00202430476 |
| c4-100-refinement | 3.94399529e-06 | 5.21521439e-08 | 0.000165399881 |
| c4-100-method | 6.15056133e-05 | 4.12320533e-07 | 0.00131954546 |

Los cuatro contrastes pasan **1 cent / 5 mV** predefinidos. La comparación
por fase usa el último ciclo de cada trayectoria y se informa separada;
no constituye una cota de error al mismo reloj ni entre muestras.
La máxima dispersión relativa de periodos es 5.251e-10 y el máximo
balance integrado relativo Qa/Q10 frente a C1 es 3.839e-6, contra límite
0.002. No se omiten límites de corriente/carga de puerta en esa observación.

La netlist sin calibrar entrega 410.80177 Hz en C4=10 pF y 410.70150 Hz
en C4=100 pF. Las salidas del primer perfil, con la escena de panel
especificada, son aproximadamente:

| Nodo | Mínimo (V) | Máximo (V) |
| --- | ---: | ---: |
| C1 | -3.99021 | -0.00064 |
| Colector Q3 | -4.19671 | +3.98043 |
| Sierra 9B | -1.86011 | +1.87230 |
| Triángulo 21B | -1.95326 | +1.65170 |
| Pulso 20B | -4.29734 | +0.00656 |

Son valores del modelo condicionado, sin identificación de amplitudes
vintage. El selector de pulso entrega HIGH 48.58%, 30.42% y 18.74% en los
contactos inferiores 10/11/12. Su validador inicial confundió HIGH con
el tiempo de estado negativo; el fallo quedó congelado. La corrección
revalida las mismas 14 trazas completas, con **cero nuevos solves**,
circuito y tolerancias intactos. [Recibo](../evidence/vco1_circuit_validation.json).

## Ajuste de frecuencia y escala

[Protocolo previo](VCO1_CALIBRACION_PROTOCOLO.md), basado en los objetivos
de B-TUNE; CV de placa explícito, sin adjudicarlo al panel real. Se ajustan
sólo R11 y R8 en sus pistas documentadas. C4=10 pF, resto de tarjetas y
fronteras sin cambiar. R11=**521.31266 ohm**, R8=**0.26134047** de fracción
eléctrica. Son trims del modelo de laboratorio, no ajustes de una unidad.

14 solves: diez ensayos de búsqueda más cuatro verificaciones a 125 ns.
Los puntos intermedios no participaron en el ajuste ni reciben una
corrección por nota. [Banco](../evidence/vco1_circuit_calibration_v1.json.gz),
[hashes](../evidence/vco1_circuit_calibration_storage.json).

| Escena | CV de placa (V) | Meta (Hz) | Resultado (Hz) | Discrepancia absoluta (cent) |
| --- | ---: | ---: | ---: | ---: |
| low | -3.1 | 220 | 220.000009328 | 7.34065931e-05 |
| middle1 | -2.1 | 440 | 439.142719258 | 3.37636666 |
| middle2 | -1.1 | 880 | 877.840905566 | 4.25283047 |
| high | -0.1 | 1760 | 1760.000112584 | 0.00011074349 |

Extremos pasan 0.1 cent e intermedios reservados pasan 5 cents. Esta última
es una tolerancia declarada del laboratorio, no una especificación Moog.
Se conserva la curvatura observada y queda pendiente un barrido completo.

## Primera escucha reproducible

`python -B tools/render_vco1_circuit.py` produce archivos locales en
`artifacts/vco1-circuit/`. [Recibo de escucha](../evidence/vco1_circuit_listening.json).
El montaje contiene sierra, triángulo y pulso, 0.75 s cada uno con pausas
0.15 s. Usa el ciclo estacionario **sin calibrar, 410.80177 Hz** del banco,
52 armónicos bajo 21.362 kHz, 48 kHz PCM16 mono. La adaptación quita DC,
escala fija 8 V/full scale y fades 10 ms; no normaliza amplitudes por onda.

El adaptador integra la interpolación lineal no uniforme del ciclo real
para obtener Fourier. No sustituye los formadores por ondas analíticas,
pero repite ese ciclo: **no simula SPICE durante los 2.55 s del montaje**.
No incluye mixer/filtro/VCA y no sirve como evidencia de parecido físico.

## Estado y siguiente bloque

VCO1 funciona en el oráculo de circuito nominal, con incertidumbres
semiconductoras explícitas. Falta identificar mejor las tarjetas, barrer
trims/control/modulación, representar las otras cargas compartidas y
conectar el mixer real. El siguiente bloque implementará la ruta portable
contra este oráculo, conservando sus cargas y formas, antes de optimizar.
No se promoverán C2 completo, C5, C6 ni C7 por estos resultados.

## Pruebas de regresión

[Primera suite](../evidence/vco1_circuit_tests.json) y
[verificación final con calibración](../evidence/vco1_circuit_final_tests.json)
con comando, salida, fuentes antes/después y replay de los cuatro exports
de verificación de afinación. La suite final cubre grafo, dispositivos,
convergencia, polaridad, integración de escucha y notas reservadas.
