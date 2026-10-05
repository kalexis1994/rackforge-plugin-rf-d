# Dieciséis macroceldas cierran el primer hueco

El [protocolo](BIESTABLE_MEMORIA_JUNTURAS_PROTOCOLO.md) y productor se congelan
en `b3d34d4` antes de medir. Fuente: resultado real del soporte 32 de la
variante elegida, ancho 8, ensayo 1 del
[segundo banco preparado](BIESTABLE_CONTINUACION_PREPARADA_SEGUNDA_RESULTADOS.md).
P, 22 memorias, curva del soporte 33, reloj y radio 1 µV se conservan.

## Control y primera partición admitida

Orden declarado: 8, 16, 32, 64 macroceldas, todas desde la misma fuente.
El control 8 rechaza con **1,165269957544755 µV**. La partición 16 cierra
con pico local **0,6433234297358821 µV**. Se detiene en la primera admitida;
32 y 64 quedan declaradas y no medidas. No se ajusta radio o reconstrucción.

El control difiere del pico histórico de ancho 1, ≈1,163855757 µV, porque
esa rama transportaba otra memoria del soporte 32. RHS, forcing, acciones
y métricas del control son idénticos a los de esa rama; el cierre se
recalcula con la memoria real elegida. No se toma una salida rechazada.

**34 soportes contiguos hasta ≈350 µs**, extremo exacto
`6456360425798341/18446744073709551616` s. Máximo acumulado
**7,928168411011273e-7 V**, ≤0,793 µV, heredado. La mejora local no lo borra.
C7 termina con **≤472,222 nV**. `first_gap_index=null`,
`stop_reason=declared_first_closure`: no certifica el soporte 34 ni las
seis plantillas futuras del banco anterior.

## Curva y duración física

La referencia conserva su h completo, potenciales, cargas/RC/Q, restricciones
y extremos. Cada macrocelda [a,b] paga h*(b-a), h/8 o h/16, sin modificar
h dentro de la curva. El RHS/acción mantiene ocho subceldas internas en 0..1;
no se confunden con la partición exterior de propagación.

Se recalculan residual, forcing punto/L1, RHS firmado de 119 ecuaciones,
restos independientes, acciones y métricas en cada celda nueva. Se guardan
tres consultas Decimal100 por celda, **72 observadores archivados**. Ninguna
carga o historia se reinicia; el integrador BDF y la trayectoria discreta
original permanecen intactos.

## Memoria que domina el máximo interior

Ambas particiones tienen máximo en nodo 66. El diagnóstico recompone la
suma racional exacta de 22 ganancias×memorias más término directo:

| Macroceldas | Celda del máximo | Anclaje nodo 66, µV | Forcing nodo 66, µV | Parte grupo 21, µV | Directo, V |
| --- | --- | --- | --- | --- | --- |
| 8, rechaza | [1/2,5/8] | 0.146095615 | 1.019174342 | 1.019171933 | 1.961657369e-12 |
| 16, admite | [1/2,9/16] | 0.122807250 | 0.520516180 | 0.520513969 | 1.961640327e-12 |

El grupo 21 reúne las cuatro junturas en norma P. La partición reduce la
cota propagada del anclaje/forcing; el directo permanece ≈1,96 pV. Los
restos independientes se conservan completos. Este ensayo identifica una
mejora del presupuesto de comparación; no atribuye causa física ni
calibra contra un Model D real. No prueba monotonicidad para particiones
arbitrarias ni que dieciséis celdas basten en curvas futuras.

## Certificado reutilizado y contabilidad

Se reutiliza el bloque uniforme anterior de ancho 1, índice 1, soporte 33,
radio 1 µV. Se reconstruyen ledger analítico, dominio completo 0..1 y
recinto inflado, y se restaura la inversa por certificado y SHA de matriz.
**q≈0,058388183<1**, P/pesos/escalas inalterados. Las tres tasas y sus 99
probes LDL se reproducen durante validación; el productor no mide otras tasas.

Preparación explícita única, input
`702c3ba5bb2667e925ecba33545e78ba27d1b2c36819a02e959328711d2eee20`,
estado `5445993d5a65369bbda9c5113dafe27761f7407c42ee804f61f0d1fb3b9b649e`.
Cada budget verifica ambas identidades antes de aplicar el RHS.

| Operación | Cantidad |
| --- | --- |
| Inversa reutilizada / reconstrucción de su prueba | 1 / 1 |
| Conjunto de tasas reutilizado / probes heredados | 1 / 99 |
| Preparaciones nuevas | 1 |
| Budgets nuevos / subcertificados | 24 / 192 |
| Solves / candidatos / certificados inversos / consultas de tasa / sistemas P nuevos | 0 / 0 / 0 / 0 / 0 |

El control también paga sus ocho budgets. Reutilizar certificados no elimina
el recálculo de forcing o acciones. No se mide ahorro de tiempo ni deadline.

## Archivo completo y alcance

**26 artefactos completos**, 24 celdas y dos soportes, suman **37712931 bytes**,
máximo **1487974 bytes**. Cada celda conserva RHS, residual, restos, métricas,
acciones y observadores; cada soporte conserva kernels, cierre, memoria y
diagnóstico, con referencias tipadas a sus celdas. El control rechazado
permanece disponible y los archivos parciales no admiten tiempo.

[Manifiesto](../evidence/loudness_latch_bdf_static_precision_junction_memory_refinement.json.gz)
y [resumen](../evidence/loudness_latch_bdf_static_precision_junction_memory_refinement_summary.json):
**1371265 bytes**, SHA comprimido
`1f9bbb802bc45e7ec165a035941f76057d88db6161c63938fa74a7c573554ff1`;
canónico `36605d64b282d8b02eecb3259139ffb282089ed6ad4b4b89704fab10bf9bc95d`.
[Lanzamiento](../evidence/loudness_latch_bdf_static_precision_junction_memory_refinement_launch.json)
con exit=0, fuente UTF-8 exacta, salidas y snapshots idénticos; 548 entradas
identificadas antes de medir. Datos, ocho tests y validator congelados en
`0b5f724`. [Recibos y corpus](BIESTABLE_MEMORIA_JUNTURAS_ENTRADAS.md)
registran cada intento y recuperan las fuentes históricas.

Circuito nominal/sintético offline. Helpers, integrador, datos/fuentes
anteriores, atributos Git y gates intactos. Cobertura completa, 1 mV global,
identificación física, sonido vintage, voz, audio nativo y deadline siguen
abiertos. Próximo: [continuación refinada](BIESTABLE_CONTINUACION_REFINADA_PLAN.md).
