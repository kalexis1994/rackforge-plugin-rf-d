# Propagación de historia con calendario fijo

Protocolo previo a medición, 2026-10-10. Escena CA3046, biblioteca y cuatro
historias corregidas idénticas a la admisión anterior. Sólo laboratorio.

## Alcance y ecuación

Doce ventanas: primer intervalo, primer reset y segundo reset de cada perfil
memoria 0/1 × límite 125/62.5 ns. Cada ventana contiene 64 medios pasos
consecutivos realmente publicados. Se conservan sus relojes enteros y tamaños;
las trayectorias perturbadas recorren ese mismo calendario sin adaptarlo.

Para cada paso, en coordenadas absolutas de etapa:

`J_n S_n = -H_x,n U_n`, `U_(n+1) = S_n[etapa final]`.

`H_x,n = -sum(B_i,j) M(x_n)/h_n`. Nueve columnas iniciales unitarias:
43, 5, 12, 139, 199, 194, 157, 117, 98. La última carece de carga y debe
dar cero exacto en todas las etapas. M conserva las unidades generalizadas
de la admisión anterior; no todos sus elementos representan faradios.

Un adaptador resuelve nueve RHS con una sola eliminación. Conserva pivotes,
umbral singular 1e-12 y omite únicamente ceros exactos. Antes de propagar,
contrasta bit a bit las 48 matrices seleccionadas con nueve llamadas al
solucionador escalar admitido. No se cambia la biblioteca física.

## Identidad y perturbación

Los dos primeros pasos de cada ventana deben reproducir incrementos y estados
HIGH/LOW de su banco seleccionado bit a bit. Las siete observaciones de tensión
de cada final deben coincidir bit a bit con la traza histórica. Se exige
continuidad HIGH/LOW entre pasos y calendario exacto sin bytes sobrantes.

Se calcula primero toda la sensibilidad de cada ventana. Para cada dirección
se fija un único epsilon: base 10 µV para tensión o 0.1 nA para corriente,
dividida por el máximo entre uno y la ganancia que haga exceder 10 µV / 10 nA
en cualquier coordenada de cualquiera de las dos etapas de los 64 pasos.
Cuatro historias propias por dirección: ±epsilon y ±epsilon/2. Cada una
continúa desde su propio final. Se compara el cambio escalado, no el cociente
descontextualizado. Gates: 1e-8 V / 1e-11 A + 1e-4 por cambio de referencia.

Un verificador independiente reconstruye masa antigua y Jacobiano absoluto
en cada paso (Decimal100 para VCO, gradiente independiente de cadena con su
dominio previamente declarado), propaga su propia solución y aplica los
mismos gates escalados. No busca raíces no lineales independientes.

## Recursos y decisiones

Preflight: reserva 1 GiB y previsión 96 MiB. Compilación 120 s, campaña nativa
900 s, total 1200 s; pila de laboratorio 32 MiB y vigilancia de disco 250 ms.
Se guardan fuentes, parciales y replay idéntico antes de reparar un rechazo.
Artefactos binarios locales ignorados, recibos y código en Git.

Sólo se admite la derivada compuesta de esas ventanas y calendario fijo.
Quedan pendientes periodo completo, calendario adaptativo, derivada del
tiempo de evento, retorno periódico, fidelidad física y tiempo real.
