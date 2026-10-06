# Refinamiento lineal: VCO mínimo completo con BUS variable

2026-10-06. [Protocolo congelado](NEWTON_REFINAMIENTO_LINEAL_PROTOCOLO.md)
y [preparación, replay y presupuesto](NEWTON_REFINAMIENTO_IMPLEMENTACION.md).
**La variante pasa su control y completa el VCO aislado con BUS variable.**
No se cambian componentes, tarjetas, tolerancias, integración o historia.

## Aritmética C y preservación

La [comprobación compilada](../evidence/voice_refine_arithmetic02.json) pasa
280 casos: productos FMA, cancelación, sub-ULP, signos, límites y rechazo de
entradas fuera del dominio, incluidos los 266 residuales de las matrices
originales. Entradas binary64 exactas se contrastan con Decimal de 160 dígitos.
Se comprueba una cota numérica de 1e-30 por suma de magnitudes de términos;
no es una tolerancia del circuito.

El primer harness no compiló sin el PATH UCRT64. Se preservan su helper,
log vacío y [recibo de rechazo](../evidence/voice_refine_arithmetic_rejection01.json).
Ese helper no persistía el código numérico del compilador: sólo se registra
que fue no cero. El retry incorpora el mismo PATH que el runner SPICE;
header, fuente C y flags aritméticos permanecen idénticos.
Build07 conserva preparación/compilación sin runs SPICE. Build08 copia
build06 y añade la variante con replay; sólo cambia NIiter y añade un header.

## Replay con los factores reales

La [auditoría](../evidence/voice_refine_validation01.json) reproduce parches,
inventarios de 4338 archivos, build, compilador, runtime, fuentes y decks.
El replay calcula las tres correcciones usando el **mismo objeto de factores
KLU** del solve original, sin otra factorización ni evaluar dispositivos.
Mantiene publicada la solución original y reproduce exactamente las 7724
filas previas y las matrices/RHS/soluciones de las iteraciones 100/101.

| Iteración | Error de voltaje original máximo | Error máximo tras tres correcciones | Error máximo de corriente tras corregir |
| --- | --- | --- | --- |
| 100 | 101.983089 µV | 0.121714 nV | 3.514e-17 A |
| 101 | 83.692285 µV | 0.099879 nV | 2.914e-17 A |

Se registran residual, corrección y solución como par de doubles en cada
paso; las operaciones compiladas se contrastan otra vez con entradas exactas.
Ambas soluciones finales pasan las escalas diagnósticas de voltaje/corriente
del protocolo. Es un contraste lineal de dos sistemas concretos; no una
certificación de todo sistema no lineal posible.

## Banco secuencial

Los [cinco recibos](../evidence/voice_refine_runs01.json) se ejecutaron con
600 s de presupuesto, fijado antes de medir y separado de itl4/tolerancias.
No hubo timeout ni error de dominio/finitud. Todos conservan rieles, R45,
tarjetas y decks originales salvo export/flags de laboratorio.

| Run | Filas | Cobertura | Resultado |
| --- | ---: | --- | --- |
| Apagado, BUS cero | 219538 | 40 ms | Exacto al baseline |
| Apagado, BUS variable | 7724 | 2.277414365 ms | Exacto al rechazo previo |
| Replay, BUS variable | 7724 | 2.277414365 ms | Exacto; correcciones no publicadas |
| Activo, BUS cero | 186946 | 40 ms | Todos los gates pasan |
| Activo, BUS variable | 186967 | 40 ms | Trayectoria completa |

Control activo frente al baseline completo, sin alineación:

- Máxima diferencia en cinco voltajes, grilla absoluta de 5 µs: **57.819469 µV**,
  frente al gate de 5 mV.
- Frecuencia asentada: 439.142720441 Hz frente a 439.142720382 Hz;
  diferencia **2.3263e-7 cent**, frente a 1 cent.
- **17 resets en ambos**, máximo desfase **4.983125 ps**, frente a 10 ns.
- Diferencia DC máxima: 3.997e-15 V y 2.711e-20 A en Iport.

El BUS variable antes rechazaba a los 2.277 ms; ahora completa los 40 ms
con la misma PWL de retorno y la misma tarjeta. No se ajusta el modelo para
obtener ese resultado. El menor número de filas no mide rendimiento RT:
es otro reloj adaptativo. Ambos runs activos tardaron aproximadamente 97 s.

## Admisión y siguiente frontera

Se admite **esta variante local para estos dos VCO mínimos**. El replay
demuestra que corregir el solve del A/RHS original reduce su error; el banco
demuestra que, en estas condiciones, publicar esas correcciones permite
completar la trayectoria. No atribuye toda la causalidad al binario oficial,
cuya trayectoria difiere; el runner de producción conserva su gate de EXE.

No se admite aún la voz VCO/filtro/VCA/contorno, cierre de R45 con la red
completa, fidelidad física o RT. El retorno PWL sigue siendo una frontera
impuesta de un laboratorio anterior. No hay audio nuevo; el WAV previo
permanece intacto. Pasan [70 regresiones](../evidence/voice_refine_tests02.json),
sin nuevos solves SPICE o compilaciones en QA.

Próximo: [voz monolítica con refinamiento](VOZ_REFINAMIENTO_UNION_PROTOCOLO.md),
primero control nominal y después el banco conjunto y sus contrastes.
