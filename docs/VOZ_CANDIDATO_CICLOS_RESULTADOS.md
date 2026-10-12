# Candidato dinámico: cuatro resets con calendario propio

2026-10-12. Model D clásico CA3046, misma escena R61=200 Ω, controles
impuestos y mezcladores apagados. [Contrato previo](VOZ_CANDIDATO_CICLOS_PROTOCOLO.md),
[inputs](../evidence/voice_candidate_cycles_inputs01.json),
[nativo](../evidence/voice_candidate_cycles_native01.json),
[auditor](../evidence/voice_candidate_cycles_reference01.json),
[QA](../evidence/voice_candidate_cycles_tests01.json).

## Estado inicial y recorrido

En el contrato, el bloque OnMixer tiene sus switches apagados; OSC1 sigue
ON por su circuito explícito de panel SW6, alpha=0,5, en VCO1. No es una
escena de silencio ni se duplica OSC1 en el bloque OnMixer.

Se toman exactamente los 400 floats HIGH/LOW de la raíz a=1 anteriormente
contrastada. Sin nueva raíz, cambio de objetivo, componente o kernel.
Los dos checkpoints sólo difieren en el límite/propuesta de paso temporal.
Cada motor decide su propio calendario desde ese estado, hasta 10,25 ms:
cuatro cruces crecientes x43=−2 y tres retornos posteriores observados.
La biblioteca, compiler, flags y escena son los anteriores.

La mejora cumple el criterio previo en los tres intervalos y ambos perfiles.
Se admite el recorrido adaptativo refinado en esta escena y duración.
El umbral de laboratorio exige L2/máximo de deriva y |deriva J7|≤0,01 de
la base anterior en todos los intervalos. No es una tolerancia de sonido,
cota asintótica o certificado de periodicidad. Los recibos contienen los
estados completos, signos y ramas que empeoran respecto al candidato fijo.

| Máximo medio paso ns | Intervalo | Periodo ms | L2/base | Máximo/base | Deriva J7 µV |
|---|---:|---:|---:|---:|---:|
| 125 | 1 | 2.43426399616 | 0.00218670557 | 0.00199744081 | -0.63027729 |
| 125 | 2 | 2.43426399531 | 0.00121304493 | 0.00151694217 | -0.467524109 |
| 125 | 3 | 2.43426399667 | 0.00160032422 | 0.00193538261 | -0.13739545 |
| 62.5 | 1 | 2.43426400773 | 0.00218670631 | 0.00199744937 | -0.630279832 |
| 62.5 | 2 | 2.43426400751 | 0.00121305388 | 0.00151694774 | -0.467525663 |
| 62.5 | 3 | 2.43426400402 | 0.00160034577 | 0.00193541214 | -0.137393591 |

Las derivas se observan entre estados interpolados en la misma fase,
utilizando los brackets y relojes propios. La interpolación es una
observación; no reemplaza un candidato admitido ni confirma un solve en
la superficie de evento. PLUS/masa se cancelan en diferencias de rama.

## Las 18 ramas, perfil 125 ns

| Rama | Retorno 1 µV | Retorno 2 µV | Retorno 3 µV |
|---|---:|---:|---:|
| 0 | 1.24147346 | -0.297920897 | -0.337343703 |
| 1 | 1.45319087 | 0.1194473 | -0.314788303 |
| 2 | -0.446108349 | 0.434676278 | -0.175042834 |
| 3 | -0.493506709 | 0.0577902649 | -0.23196674 |
| 4 | 0.00781084504 | 0.00151002458 | -0.00351146388 |
| 5 | 6.17969878e-05 | 8.40317858e-05 | 7.85559172e-05 |
| 6 | 0.558735195 | 0.371868586 | 0.233268339 |
| 7 | -1.34763555 | -1.01630978 | -0.759202192 |
| 8 | 1.23145 | -0.783949612 | -1.58772553 |
| 9 | 7.29282279 | -1.36190219 | -7.47002661 |
| 10 | 0.0252506695 | 0.0171555097 | 0.0125522122 |
| 11 | 0.227848495 | 0.201986447 | 0.178938776 |
| 12 | 1.84402973 | -0.413722169 | -1.88441126 |
| 13 | 1.10692985 | -0.277414969 | -1.0309664 |
| 14 | -7.70955364 | -5.85496549 | -1.76755327 |
| 15 | 0.317690185 | 0.0984986287 | -0.0182282962 |
| 16 | 0 | 0 | 0 |
| 17 | 0.128806538 | -0.00259864424 | -0.114981644 |

Se conserva una comparación al mismo reloj además de las medidas por fase.
42 checkpoints comunes posteriores al inicial (2 µs y 41 anclas de250 µs).
Peor ratio de error de estado frente a 2 µV/2 nA:
0.0622005896.

| Intervalo | Diferencia de periodo cents | Ratio deriva de ramas | Ratio deriva J7 |
|---|---:|---:|---:|
| 1 | 8.22920913e-06 | 0.00173471799 | 0.000252561113 |
| 2 | 8.67701068e-06 | 0.00474616251 | 0.000154659461 |
| 3 | 5.2226055e-06 | 0.0054939147 | 0.000185701155 |

Periodo≤1 cent; ramas≤2e−8 V +1e−4 relativo; J7≤1e−8 V +1e−4 relativo.
Estos gates comparan discretizaciones, no unidades vintage.

## Auditor y conservación

Seis selecciones por perfil: primer intervalo, cuatro cruces y último
intervalo, cada una con coarse/mid/end. Decimal100 verifica 36 candidatos
y 14400 ecuaciones, 24 observaciones de corrientes de terminal y doce LTE.
Los eventos pertenecen por estado y reloj a los medios pasos admitidos
seleccionados. No hay búsqueda independiente de raíces ni integración
independiente de todas las etapas.

Restauración desde codec a 0,25, 2,25 y 7,25 ms en cada perfil: seis
replays, comparando por bits todos los estados candidatos/incrementos de
los tres pares, ratios, relojes, h e intentos del advance. C1/BUS KCL≤1e−12 A; balance integrado
C1≤0,002. Los ledgers Radau verifican carga C27 y media del panel en los
tres intervalos y recorrido completo, sin suponer una media DC de la saw.

Nativo 2869.963783 s, auditor 11.937777 s,
salidas 46629218 bytes. Dos procesos de
laboratorio, stacks de32 MiB, RAM inicial≥1 GiB; reserva disco1 GiB,
estimación64 MiB. Presupuestos previos: compile120 s, perfil7200 s,
campaña7400 s, administrativo9000 s, auditor300 s. Completos y sin replay
de fallo; las restauraciones son controles de continuación.

248 tests Rust heredados por identidad, sin recompilar la biblioteca.
Sin nuevo audio, SPICE, fidelidad física o RT. Esta prueba cubre varios
retornos adaptativos; la evolución posterior y otras escenas siguen sin
cota global. El siguiente bloque debe avanzar los controles/cargas de la
voz funcional, conservando este estado como candidato identificado.
