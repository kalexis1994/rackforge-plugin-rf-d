# Candidato dinámico: calendario propio y retornos posteriores

2026-10-12. Congelado antes de medir. Se prueba el candidato a=1 de
[la dirección contrastada](VOZ_CORRECCION_DINAMICA_RESULTADOS.md), en la
misma escena CA3046, R61=200 Ω, mezcladores apagados. Se extraen por bytes
sus 400 valores HIGH/LOW, sin resolver otra raíz ni modificar componentes.
Dos motores adaptativos propios, máximo de medio paso 125 ns y 62,5 ns.
Meta 5373952000 ticks = 10,25 ms, cuatro cruces crecientes x43=−2,
tres intervalos entre cruces. Una medición corta no acredita asentamiento.

## Contratos

La biblioteca y compilador anteriores se conservan. El llamador deriva de
`joint_corrected_cycles_runner.rs` por sustituciones declaradas y verificadas:
duración, presupuesto, todos los eventos, tercera restauración y comparación
por bits de los cinco estados/pares de cada solve restaurado. Cada perfil
tiene archivos y estado propios; dos procesos de laboratorio independientes.
Esto no modifica ni acredita el procesamiento de audio.

Se conserva traza completa, estados antes/después de cada cruce, checkpoint
a 2 µs y cada 250 µs, estado final, corrientes e integrales Radau. Auditor
Decimal100 de coarse/mid/end al primer intervalo, cada cruce y último
intervalo: seis selecciones por perfil, 36 candidatos/14400 ecuaciones,
24 observaciones de corrientes y 12 contrastes LTE. No busca raíces propias.
Se verifica procedencia del evento en el candidato nativo seleccionado.

Gates heredados: ecuaciones 2e−11 A/2e−10 V, corrección 1 µV/1 nA,
LTE y comparación al mismo reloj 2 µV/2 nA; KCL C1/BUS≤1e−12 A,
balance integrado C1≤0,002. C27: error de balance≤1e−12 A·duración;
identidades de media del panel≤1e−9 V. Restauraciones a 0,25, 2,25 y
7,25 ms, estado/etapas por bits. Refinamiento: cada periodo≤1 cent;
deriva de cada rama≤2e−8 V +1e−4 relativo entre resoluciones.

Se informa la deriva de las 18 ramas y J7 en los tres intervalos, incluyendo
signos, ramas que empeoran y comparación con el calendario fijo anterior.
Hipótesis de persistencia de la mejora: todos los intervalos mantienen
L2 y máximo≤0,01 de la base anterior, y |deriva J7|≤0,01 de esa base.
Este criterio es de laboratorio; si falla se conserva el rechazo y no se
presenta como inicialización estable. Pasarlo tampoco establece una cota
asintótica ni identifica fidelidad física. Separar completitud/auditoría,
refinamiento y resultado de la hipótesis.

## Recursos y fallo

Compile≤120 s; cada perfil≤7200 s, máximo 65000/100000 intervalos;
campaña≤7400 s, límite administrativo 9000 s, auditor≤300 s.
Dos stacks de 32 MiB, RAM inicial≥1 GiB, reserva disco 1 GiB,
estimación 64 MiB, vigilancia cada 250 ms. Cada proceso conserva stdout,
stderr, checkpoint y datos parciales. Rechazo eléctrico: replay del único
advance fallido desde su checkpoint antes de modificar nada. Fallo de
auditor: fuente, excepción y repetición idéntica conservadas. Stop por
recursos no admite cobertura completa ni justifica relajar gates.
