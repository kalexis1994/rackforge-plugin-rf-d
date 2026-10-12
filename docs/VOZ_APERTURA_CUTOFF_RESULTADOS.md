# Apertura del cutoff: diagnóstico DC/AC de la cadena

2026-10-12. Misma revisión CA3046, R61=200 Ω, RANGE=0,1 y controles
de VCA=2 V. [Protocolo previo](VOZ_APERTURA_CUTOFF_PROTOCOLO.md),
[intento rechazado](../evidence/voice_cutoff_opening01.json),
[medición admitida](../evidence/voice_cutoff_opening02.json),
[QA](../evidence/voice_cutoff_opening_tests01.json).

J7 aparece en decenas de µV en la escena temporal de diagnóstico.
Antes de amplificar para escuchar, se estudia el control eléctrico del
panel. Se reutilizan los tres DC propios del oráculo de66 nodos,
cutoff0/0,5/1: no son la raíz de memoria dinámica corregida ni nuevas
raíces. Se extienden a68 nodos con BUS=0 y C10_LEFT=pin6. Biblioteca y
componentes no cambian; el parámetro variado es el control de cutoff.

El exportador nativo entrega G y C en S/F. KCL independiente y FD centrales
1/2 µV verifican G; incidencias originales verifican C, incluyendo C27
y C10/emphasis. BUS ideal se normaliza a1 V infinitesimal, sin movimiento
AC de controles, rieles u otras fuentes. Se resuelven67 nodos complejos,
observando J7 y admitancia de entrada. Ambos solves usan NumPy: independencia
del montaje/KCL, no dos implementaciones distintas de álgebra lineal.

Fundamental 410.801787144 Hz, del periodo del candidato fijo anterior.

| Cutoff eléctrico | Cola µA | J7/BUS f | J7/BUS 2f | J7/BUS 4f | J7/BUS 8f |
|---|---:|---:|---:|---:|---:|
| 0.0 | 0.243120956 | 5.42246345e-07 | 2.70763023e-07 | 1.35419521e-07 | 6.77191492e-08 |
| 0.5 | 6.82489851 | 0.00447865556 | 0.000349261021 | 2.34096501e-05 | 1.60510642e-06 |
| 1.0 | 144.421881 | 0.240746762 | 0.238763604 | 0.208234025 | 0.082072438 |

Abrir0,5→1 eleva |J7/BUS| en la fundamental 53.754248 veces.
Esto elige una hipótesis de escena, no predice el nivel de una onda grande.
La carga que vea VCO/BUS también cambia; el próximo recorrido debe volver
a cerrar esa carga y conservar sus propias memorias. No construir audio
desde estos fasores ni extrapolar saturación/autoscilación/sonido vintage.

Tres candidatos DC, 408 columnas FD, 48 solves complejos y 24 observaciones
de transferencia. Gates sin cambios. Peor ratio G
1.16039894e-05;
peor ratio de voltaje AC
0.000903581729.
Residuos complejos≤1e−11 A/V y matriz C≤1e−16 F. Se reportan todos los
armónicos, magnitudes, fase y admitancias en el recibo, sin afirmar que
el piso absoluto resuelva relativamente cada término débil.

El intento01 falló al compilar por comillas/literales Rust del exportador.
Fuente, diagnóstico y compilación repetida idéntica conservados. Intento02
repara sólo esa sintaxis y añade numeración de intento al wrapper; input
DC por bytes y auditor/gates iguales. Sin rechazo eléctrico ni cambios
del kernel. Medición 0.964809 s, auditor 0.310919 s,
salidas 1559648 bytes. Reserva1 GiB,
estimación8 MiB, stack32 MiB; compile/export/auditor≤120 s, total≤480 s.

248 tests Rust heredados por identidad. Sin nueva biblioteca, trayectoria,
raíz, audio, SPICE, fidelidad física o RT. Siguiente: un banco temporal
corto de cambio de cutoff, respetando carga entrante y el caso nominal.
