# Menor coste con las mismas leyes y cargas

2026-11-06. Núcleo experimental de recuperación y par de entrada, Model D
CA3046/SVC-9 Fig.9-11 p.13. R61=200/L1, R14=25k, cutoff .49/.50/.51,
loudness1/2=2 V. Mismas12 leyes Ebers–Moll, 18 memorias, puertos, 384 kHz
internos y FIR48 kHz. Sin cambio del motor de escucha ni de las constantes.

## Cambios y validación

- Evaluar defecto y derivada juntos elimina trabajo repetido. La primera
  fórmula falló cerca del umbral .001; ampliar Horner a grado12 hasta .125
  corrigió la cancelación. Decimal80 pasa en las doce uniones y tres DC.
- Usar los defectos anteriores para iniciar Newton reduce iteraciones sin
  modificar el residual2e-13. La especialización por punto fijo no mejora
  el banco medido. Rust y Python coinciden en sinusoides y reservas numéricas
  de saltos/rampas; quedan replays, rechazos atómicos y cero heap.
- La variante exponencial hace una resolución por muestra. Elimina las
  variables algebraicas por Schur, integra exactamente la parte lineal y
  usa FOH para la corriente no lineal entre endpoints. Cada endpoint sigue
  resolviendo las doce leyes y conserva las cargas. Se contrastó el mapa
  con exponencial aumentada independiente y 48 endpoints con balance y KCL.

En las tres reservas .1 V a384 kHz, el error nodal retenido contra el
circuito completo fue .878/.924/.968 µV, con puertos completos y RMS
relativo J7 <=.000066. Contra el MISMO híbrido integrado con SDIRK a250 ns,
el máximo nodal sobre la rejilla completa fue9.02 nV. Las consultas de
auditoría parten de cargas y defectos reconstruidos de los nodos propios
de Rust. El oráculo conserva estados dispersos y puertos densos. No se
amplía el dominio a 1 V, cutoff dinámico, otros controles o audio físico.

La lectura del FIR por dos tramos evita el módulo dentro del producto
escalar. Conserva por bits voltaje, índices y latencia en cuatro escenas
con particiones no uniformes. Los vectores y endpoints de circuito del
binario con esta lectura también son idénticos. La lectura se descarta por
coste observado; el candidato conserva el FIR original.

## Plazos observados

Bloques128 a48 kHz, 1024 pasos internos, cutoff .50, plazo2.667 ms y
margen objetivo1.333 ms. Cero heap. Todos incluyen el primer bloque,
80 frames por latencia y128 después. VCO, contornos, host y generador de
entrada no están dentro del coste. Bancos secuenciales sin atribuir causa
a los picos de pared ni seleccionar el mejor replay.

| Variante | Bloques | Mediana | Máximo | Plazos perdidos |
| --- | ---: | ---: | ---: | ---: |
| Referencia SDIRK6 de esta sesión |1200|1.865 ms|3.547 ms|38|
| Evaluación conjunta |1200|1.824 ms|3.355 ms|5|
| Semilla de defecto |1200|1.364 ms|3.597 ms|1|
| Especialización fija |1200|2.171 ms|29.401 ms|320|
| Exponencial, FIR original |1200|0.743 ms|1.144 ms|0|
| Exponencial, confirmación |4800|0.740 ms|4.800 ms|1|
| Exponencial, FIR por tramos |1200|1.187 ms|66.142 ms|146|

La transición exponencial reduce la mediana ~60% frente a la referencia
de esta sesión. El banco inicial pasa también el objetivo50%; el largo
rechaza la admisión. Su replay tuvo cero plazos perdidos pero máximo1.772
ms, y tampoco cumple margen. La variante no se integra al motor RT.
Siguiente: separar coste del núcleo y colas de latencia en el host antes
de sumar VCO/contornos; conservar el candidato como control numérico.

Protocolos: [coste](RECOVERY_COST_PROTOCOLO.md), [ley](RECOVERY_COST_LAW_CORRECCION.md),
[transición](RECOVERY_COST_EXP_PROTOCOLO.md), [mapas](RECOVERY_COST_EXP_MAPAS.md)
y [FIR](RECOVERY_COST_FIR_PROTOCOLO.md).
[Banco exponencial](../evidence/recovery_cost_exp_native01.json),
[FIR](../evidence/recovery_cost_fir_native01.json) y [QA](../evidence/recovery_cost_tests01.json).
Se preservan fallos y replays de ley/identidades/coste, fuentes, 8769
inputs y escucha anterior. No nueva biblioteca, campaña SPICE, WAV o caché.
