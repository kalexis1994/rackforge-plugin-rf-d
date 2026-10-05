# Continuación compartida: veinticuatro soportes contiguos

El [protocolo](BIESTABLE_CONTINUACION_COMPARTIDA_PROTOCOLO.md) y productor
se congelan en `7300955` antes de medir. Fuente: variante 0 del
[ensayo compartido](BIESTABLE_RECINTOS_COMPARTIDOS_RESULTADOS.md), sus
dieciséis soportes, resultado real final y P fija. Se usa esa salida exacta,
identificada por SHA; no la salida diferente del control con recintos individuales.

## Banco nuevo y alcance

Se construyen ocho referencias curvas nuevas desde las historias propias,
índices **16–23**, con pasos reales de ≈12,5 µs. Cada plantilla conserva
X/RHS de la burbuja C7, potenciales, cargas, restricciones RC/Q, RHS de
119 ecuaciones, restos independientes y tres observadores Decimal100.
Sus endpoints coinciden exactamente con los publicados por el integrador.
Las plantillas son condicionadas; no admiten tiempo por estar preparadas.

La primera variante declarada, ancho **8**, cierra los ocho soportes en
radio **1 µV**. El radio 0,1 µV rechaza por la cota entrante sin construir
recinto. El banco se detiene en la primera alternativa completa: no se
miden anchos 4/2/1. Si ninguna rama hubiese completado el banco, el protocolo
habría seleccionado el prefijo admitido más largo y el primero en empate.

**Se certifican 24 soportes contiguos hasta ≈225 µs**, extremo exacto
`8301034833169301/36893488147419103232` s. Pico acumulado
**7,928168411011273e-7 V**, ≤0,793 µV, heredado del prefijo anterior.
`first_gap_index=null`, `stop_reason=declared_limit`; el soporte siguiente
no queda certificado por extrapolación.

## Certificado uniforme y transporte

X de bloque se elige en índice **19**, u=1/2, según la regla ordinal central
inferior, con descriptor Decimal100 e inversa candidata binary64. Se
renuevan constante y stamps y se prueba su igualdad sobre las ocho curvas.
El ledger cubre **704 rangos Bernstein completos**, 88 leyes por ocho
referencias, inflados por el tubo futuro de 1 µV. Mantiene C(v) por piezas
y todos los parámetros; la representación afín de rangos no es una curva.

El nuevo recinto completo del descriptor medio cumple
**q≈0,0582166616<1**. Prueba una inversa y tres tasas sobre el dominio
nuevo; no reutiliza la inversa o tasa del bloque de 25→125 µs.
Cada macrocelda recalcula sus acciones firmadas con X, defecto y cola
nuevos, con restos uniformes y constitutivos independientes íntegros.
Cada duración real se paga y las 22 memorias se transportan sin reset.

| Índice | Extremo aproximado, µs | Pico local, µV | Error final real C7, µV |
| --- | --- | --- | --- |
| 16 | 137.5 | 0.377382485 | 0.377315709 |
| 17 | 150.0 | 0.383123165 | 0.383050886 |
| 18 | 162.5 | 0.388851609 | 0.388771157 |
| 19 | 175.0 | 0.394569323 | 0.394476477 |
| 20 | 187.5 | 0.400278694 | 0.400166789 |
| 21 | 200.0 | 0.405983479 | 0.405841999 |
| 22 | 212.5 | 0.411689584 | 0.411501943 |
| 23 | 225.0 | 0.417406291 | 0.417146347 |

Los picos locales siguen en nodo 81, celda [7/8,1]. El máximo local
nuevo es **≤0,418 µV**, distinto del acumulado ≤0,793 µV. La salida real
C7 pasa de ≈371,566 nV a ≈417,146 nV. P, pesos, escalas y conversiones
se conservan. Se adapta únicamente el contador del helper compartido
desde su fuente antigua de ocho soportes a la fuente actual de dieciséis.
No se alteran sus ecuaciones o gates.

## Costes y archivos completos

| Operación nueva | Cantidad |
| --- | --- |
| Candidatos de referencia/burbuja | 8 |
| Candidato de precondicionador de bloque | 1 |
| Prueba de inversa uniforme | 1 |
| Consultas LDL de tasa | 99 |
| Acciones de subcelda | 512 |
| Solves no lineales / sistemas de métrica | 0 / 0 |

En total se preparan **9 candidatos**, con curvas/RHS nuevos pagados en
este banco. El ahorro anterior sobre referencias conocidas no elimina
ese coste. Son conteos del laboratorio offline, no medidas de velocidad
o deadline de audio.

**17 artefactos completos**: ocho plantillas, un bloque y ocho soportes.
Suman **96722715 bytes** comprimidos; el mayor tiene **11246434 bytes**.
Se conservan todas las matrices, certificados y ramas. Cada soporte
identifica su plantilla y bloque. El
[manifiesto](../evidence/loudness_latch_bdf_static_precision_shared_continuation.json.gz)
fija ruta tipada, esquema, tamaño, SHA comprimido/canónico e identidad.
Un archivo parcial no sustituye esta publicación terminada.

Manifiesto: **1341983 bytes**, SHA comprimido
`44d56132e1800e37cde96b1abe09a6b3f6a115ee2dddc0bf8ccf78190e472384`,
canónico `3ad76b94032e1dd4bf5b4e4285075f232284efe0b676c4be957b7e4a8a73a5fa`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_shared_continuation_summary.json).
Datos, siete tests y validator se congelan en `60c169f` antes de validar.
[Corpus y recibos](BIESTABLE_CONTINUACION_COMPARTIDA_ENTRADAS.md).

Modelo CA3046 nominal y parámetros sintéticos. Circuito, integrador,
estados publicados y gates se conservan. 1 mV global, cobertura completa,
identificación física, sonido vintage, voz, audio nativo y deadline
siguen abiertos. Próximo: [preparación exacta de acciones](BIESTABLE_ACCIONES_PREPARADAS_PLAN.md).
