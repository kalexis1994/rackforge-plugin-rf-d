# Liberación conjunta hasta 500 µs

2026-10-09. [Contrato previo](VOZ_PREFIJO_CONDICIONADO_PROTOCOLO.md),
[recibo nativo](../evidence/voice_joint_prefix_native01.json),
[contraste independiente](../evidence/voice_joint_prefix_reference01.json) y
[auditoría](../evidence/voice_joint_prefix_tests01.json).
Misma escena CA3046 nominal, biblioteca eléctrica compilada congelada y
raíz0 de inicialización idéntica en sus 400 componentes high/low.
No reemplaza la historia del banco anterior de ciclos.

## Banco completado

| Máxima media etapa | Intervalos aceptados | Medios endpoints publicados | Duración de proceso | Balance relativo C1 |
|---|---:|---:|---:|---:|
| 125 ns | 2009 | 4018 | 67,73 s | 1,020e-14 |
| 62,5 ns | 4006 | 8012 | 137,06 s | 1,019e-14 |

Cada perfil completa exactamente 262.144.000 ticks, 500 µs; checkpoints
en 0, 250 y 500 µs. Ambos restores a 250 µs reproducen el siguiente
intervalo bit a bit; los replays no se suman a integrales ni contadores.
Final.ckp coincide con el último checkpoint. Sin rechazo ni stop.
Los 6015 intervalos/12.030 medios endpoints conservan los gates nativos.
Máximo LTE 0,475618; BUS<=1,017e-20 A y C1<=2,202e-14 A.

El balance de C1 usa la cuadratura nativa de las dos etapas Radau con
Qa/Q10/Q7 y la diferencia de los endpoints decodificada independientemente
en Decimal100. No se integra aquí una segunda trayectoria completa con
el oráculo Python. Los endpoints de ambos perfiles coinciden en los
relojes comunes: peor fracción del gate 2 µV/2 nA, **1,539e-8**.

## Contraste y cargas

Se comprobaron 24 puntos de etapa, 4800 ecuaciones, cuatro diferencias
LTE y 24 corrientes terminales en ocho endpoints seleccionados.
Mayor fracción del gate independiente de residuos 0,001220; corrección
0,000007125. Error máximo de corriente 1,320e-18 A frente a 2e-11 A.
Se usan los candidatos nativos declarados: cero raíces independientes
nuevas. Los 248 tests Rust anteriores se heredan por identidad; ninguno
se reejecuta o se cuenta como nuevo.

Las 18 tensiones/cargas de capacitores antes/después quedan en el recibo.
C27, incidencia 6↔BUS, cambia +0,255123 mV (+2,55123 nC); C10, 67↔7,
cambia +5,10812 nV (+5,10812e-14 C). Esto describe el prefijo liberado,
no un balance por ciclo ni una calibración física de esos componentes.
BUS va aproximadamente de +0,930032 a +0,924970 V. J7 registrado abarca
−0,457490 µV..+0,000178312 µV. Son extremos de endpoints observados,
no un bound de máximos entre ellos ni un nivel estacionario audible.
No hubo cruce de reset en este prefijo; no se estima su frecuencia.

## Recursos y siguiente etapa

Un proceso de compilación del caller, reutilizando la biblioteca eléctrica
con SHA256; dos procesos temporales seriales. Campaña 205,72 s, outputs
privados 4.025.822 bytes, mínimo de disco muestreado 1.169.199.104 bytes,
por encima de la reserva de 1 GiB. Muestreo cada 250 ms; no es una medida
continua ni de heap/deadline. Stack de laboratorio 32 MiB.
No se generó audio ni se ejecutó SPICE.

Continuar los ciclos desde estos checkpoints, con el mismo reloj,
parámetros, incrementos y cargas compensadas. Mantener las fronteras
impuestas y diferenciar esta inicialización de la importada del banco
anterior. Medir estado/carga a la misma fase por ciclo antes de admitir
asentamiento. El prefijo queda admitido; ciclos desde esta raíz, encendido
físico, voz completa, fidelidad y tiempo real siguen pendientes.
