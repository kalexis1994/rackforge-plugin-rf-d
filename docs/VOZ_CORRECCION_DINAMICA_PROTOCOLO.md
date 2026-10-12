# Primera dirección de corrección dinámica: contrato previo

2026-10-12. Model D clásico CA3046, memoria corregida 0, escena heredada
R61=200 Ω. Biblioteca, dispositivos y controles intactos. Se modifican
únicamente los 18 objetivos del condicionador de 218 filas, con fase x43=0.

## Hipótesis y dominio

Usar la matriz nativa A18×18 de derivada de deriva de tensiones de rama
y b18 de deriva entre los dos primeros resets de
[la campaña anterior](VOZ_RETORNO_CONDICIONADO_RESULTADOS.md).
Sólo C27 tiene FD completa previa: A sirve como hipótesis, no como matriz
completa admitida. La nueva prueba admite únicamente su dirección elegida.

La fila 16 tiene deriva cero en esta frontera. Fijar delta_v16=0, resolver
las otras 17 filas/columnas por SVD truncada: conservar s>1e−8·s_max.
Elegir la solución de norma mínima; aplicar escala común si max|delta_v|
supera 0,1 V. La inspección previa encuentra rango 16 y max|delta_v|≈4,24 mV.
Verificar independientemente reconstrucción SVD, ortogonalidad y ecuaciones
normales en Decimal100. Registrar el residuo fuera del rango: no ocultar
la dirección casi nula ni declarar cierre exacto.

Definir v(a)=v0+a·delta_v, a adimensional. Todas las perturbaciones y el
candidato resuelven su propia raíz; fase y objetivos no variados se retienen.
La respuesta inicial es B218×18·delta_v y las respuestas temporales se
contraen de las matrices guardadas de la base anterior. No se vuelve a
simular ni se vuelve a admitir esa base.

## FD y candidato

FD a dos tamaños ±epsilon_a y ±epsilon_a/2. Límite conservador heredado:
epsilon_a=1e−5/sum(gain_k·|delta_vk|); gain_k incorpora el máximo nativo
de Bx inicial y de todas las etapas del recorrido anterior. La desigualdad
triangular puede sobreestimar la ganancia de una combinación que cancela;
registrarlo. Es una cota derivada de máximos nativos, no independiente.

Cuatro historias completas propias por el mismo calendario de 42544
medios pasos. Quinta historia para candidato a=1. Detectar ambos cruces
x43=−2 crecientes en cada historia; guardar índices, ticks, h, dos estados,
alpha y estado en fase. El candidato puede cambiar de bracket. Reconstruir
tiempos con sus relojes propios; no restar sólo alpha de brackets distintos.
Conservar veinte operadores preseleccionados y siete observables en todas
las historias para comparar fase y mismo reloj.

Gates heredados de cambios escalados: 1e−8 V o 1e−11 A +1e−4 relativo
para raíz/dirección, etapas, eventos y deriva. Tiempos/periodo 1e−17 s
+1e−4 relativo, ramas 2e−8 V +1e−4 relativo. Raíces: oráculo heredado
de 218 filas y fase/cargas≤1e−11 V. Observador: 1e−13 V o 1e−16 A,
alpha≤2e−15. Informar efecto/piso; un pase no resuelve efectos relativos
por debajo del piso. Todos los 100 candidatos seleccionados se auditan
con ecuaciones independientes; sin propagación independiente completa.

La mejora del candidato se admite por resultado medido, no por predictor:
norma L2 y máximo absoluto de las 18 derivas≤0,5 de la base, y |deriva J7|
≤la base. Publicar cambios de cada rama, empeoramientos y error de predicción.
Si falla, conservar la refutación. Esto no acredita periodicidad asentada,
mapa de Poincaré, calendario adaptativo ni refinamiento entre perfiles.

## Recursos y equivalencia

Cuatro workers de laboratorio, cada uno con stack 32 MiB y estado propio.
Workers 0–3 recorren los cuatro signos/tamaños; worker 0 procesa después
el candidato. Parámetros y calendario compartidos son inmutables; archivos
y candidatos propios. Los kernels no cambian. Verificar al menos un prefijo
de 64 pasos de cada historia contra ejecución serial por bits; no afirmar
optimización de audio ni deadline por esta organización del laboratorio.

Compilar únicamente caller opt2 con rustc/biblioteca por SHA heredados.
Reserva de disco 1 GiB, estimación 64 MiB; RAM libre inicial≥1 GiB;
stack reservado para workers 128 MiB, vigilancia 250 ms. Compile≤120 s,
run≤3400 s, éxito≤3560 s, administrativo≤7200 s incluyendo replay,
auditor≤300 s. Presupuesto basado en historias seriales previas de
688–772 s, cuatro workers y una historia adicional serial. Conservar
fuentes, datos parciales y replay idéntico ante rechazo. 248 tests Rust
heredados por identidad; sin nueva biblioteca, audio, SPICE, fidelidad o RT.
