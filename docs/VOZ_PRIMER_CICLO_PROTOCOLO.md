# Primer ciclo con carga activa: campaña previa

2026-10-08. CA3046 clásico nominal25 °C, C4=10 pF, R8=0,5/R11=500 Ω,
CV seis veces−2,1 V, cadena nominal R61=200 Ω. SVC-9 pp.5/19/13/10,
[modelo conjunto](VOZ_BUS_CONJUNTO_PROTOCOLO.md) y
[motor temporal](VOZ_MOTOR_TEMPORAL_PROTOCOLO.md) heredados por identidad.
Solo OSC1 ON representado explícitamente; otras cuatro ramas fuera del
subgrafo. Loudness/Q21 y demás controles de cadena permanecen impuestos.
Inicialización condicionada anterior; no DC propio de la voz completa.

## Banco y puertas

Dos máximos de medio paso125/62,5 ns, mismos controles, hasta5,25 ms
(2752512000 ticks). Checkpoints comunes cada0,25 ms (131072000 ticks).
Cada intervalo mantiene LTE2 µV/2 nA, Newton64/24 y rechazo atómico.
Comparar las200 coordenadas a los21 relojes comunes:2 µV/2 nA, sin alinear
fase ni recalibrar CV. Máximos de intervalos32000/48000 por perfil.

Marcador de reset: cruce ascendente de RAMP_C1 por−2 V interpolado
linealmente entre endpoints. Es una observación del reset, no gatillo del
motor. Pedir dos cruces por perfil para delimitar un ciclo; informar sus
brackets y tamaños de paso. Un ciclo transitorio no acredita periodicidad
asentada. Comparar frecuencia de ese ciclo<=1 cent y extremos de sierra,
triángulo, pulso, BUS y J7<=5 mV entre resoluciones (puertas heredadas
del banco VCO); no comparar fidelidad contra el oscilador descargado.

Observar Qa/Q10 colector y Q7 gate usando corrientes Radau, con sus cargas
no lineales. Derivada C1 coherente con ambas etapas: KCL instantánea<=1e-12 A.
Integrar ambas corrientes de etapa con pesos3/4 y1/4, no trapecios de
endpoints; comparar integral con−C1 ΔV. Balance relativo<=0,002,
normalizado por integral de la suma de valores absolutos de las tres
corrientes. BUS/R45/C27 mantiene puerta1e-12 A. No excluir Q7 del balance.

Las traces binarias registran cada medio endpoint admitido, sus gates,
señales y corrientes; no exportan todas las400 coordenadas en cada paso.
Checkpoints guardan estados high/low por bits y metadata de reloj/propuesta.
Parámetros se reconstruyen con el builder nominal ligado a fuente, no
se declara un formato general de presets. Verificar restore desde bytes
y una continuación exacta en0,25 y2,25 ms por perfil.

Contrastar etapas seleccionadas del arranque, primer reset y final con
el oráculo nodal anterior; candidatos nativos declarados. Puertas del
oráculo sin relajación. Si una campaña falla, guardar su último estado,
traza parcial, fuente y comando; replay local desde ese checkpoint antes
de reparar. No volver a ejecutar un prefijo intacto para medir ese fallo.

## Recursos

Compilador fijado y stack32 MiB. Reserva1 GiB; estimación48 MiB adicionales:
build16 MiB, traces<=25,6 MB, checkpoints<=2 MB y recibos/margen.
Límites900 s por perfil y1800 s globales. Vigilancia de disco y parada
cooperativa con checkpoint; distinguir cancelación administrativa de
rechazo eléctrico. Archivos en directorios nuevos ignorados, nunca sobrescribir
un intento. No borrar evidencia protegida para ampliar la campaña.

No hay nuevo audio previsto antes de admitir este banco. Modelo de laboratorio,
sin hardware de referencia, dispersión vintage, nota completa o admisión RT.
