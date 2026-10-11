# Retorno desde la raíz condicionada: contrato previo

2026-10-11. Model D clásico CA3046, memoria corregida 0, máximo original
125 ns, circuito y biblioteca congelados. R61=200 Ω y escena heredada.
Se retiran las retenciones artificiales al liberar la raíz, fase x43=0.

## Dominio y recorrido

Usar el estado HIGH/LOW, corrientes y B218×18 admitidos en
[la base condicionada](VOZ_BASE_CARGAS_CORREGIDAS_RESULTADOS.md).
Comprobar por bits la raíz recalculada desde el seed frío y la base.
Propagar las 18 columnas Bx desde t=0 hasta el segundo bracket: 42544
medios pasos del calendario guardado. Los brackets son 20188/20189 y
42542/42543. Todos los siete observables deben reproducir la traza por
bits; seis fixtures completos y las primeras dos matrices S también.
El calendario se mantiene fijo para las historias perturbadas.

Seleccionar antes de medir 20 operadores: 0,1,2,64,256,1024,4096,8192,
12288,16384,20186,20187,20188,20189,24576,32768,40960,42541,42542,42543.
El contraste independiente de cada operador recibe U nativa. Sólo los
dos primeros pasos propagan una base independiente propia completa.
Auditar sus 400 ecuaciones y la recurrencia en puntos adyacentes.

## Eventos y FD de C27

Usar el observador interpolado x43=−2 creciente ya admitido; adaptar
únicamente el import para 18 RHS. Comparar por bits las proyecciones con
dos lotes de nueve. Con Z1,Z2 y t1,t2, observar T=t2−t1 y D=Z2−Z1,
dT=dt2−dt1 y dD=dZ2−dZ1. Separar derivada del tiempo y estado proyectado.
La proyección de rampa escalada debe ser ≤1e−18 V.

FD completa únicamente de la columna objetivo 5, C27. Cada signo resuelve
su raíz condicionada de 218 filas; mantener las otras 17 coordenadas y
fase. No sustituirla por una inyección del nodo 139 con BUS fijo.
Cuatro historias propias: ±epsilon y ±epsilon/2. Reducir epsilon antes
de esas historias mediante el máximo nativo de TODAS las coordenadas
de Bx inicial y las 400 coordenadas de TODAS las etapas: gain≥1;
gain=max(1,1e−5·|respuesta|/escala), escalas 1e−5 V y 1e−8 A;
epsilon=1e−5/gain V de objetivo. Registrar que el auditor independiente
verifica límites en muestras, no reproduce la reducción de todos los pasos.

Raíces: gates del oráculo heredado, 218 filas, fase/cargas≤1e−11 V.
Base: 1e−6 V/V o 1e−10 A/V +3e−4 relativo. Etapas y FD de eventos/deriva:
1e−8 V o 1e−11 A +1e−4 relativo sobre cambios escalados. Tiempo/periodo:
1e−17 s +1e−4 relativo. Ramas capacitivas: 2e−8 V +1e−4 relativo.
Observador de estado: 1e−13 V o 1e−16 A; alpha≤2e−15.
Control nulo en los 20 operadores y ambos eventos.

## Recursos y promoción

Biblioteca y rustc por SHA heredados; compilar sólo el caller con opt2,
stack 32 MiB, sin audio ni SPICE. Reserva 1 GiB, estimación 64 MiB,
vigilancia 250 ms; compile≤120 s, run≤4400 s, éxito≤4560 s,
administrativo≤9000 s incluyendo replay, auditor≤300 s.
El intervalo anterior empleó 1620,69 s para 22356 pasos y cuatro historias;
éste recorre 42544 y 18 RHS, por eso el presupuesto crece antes de medir.
Conservar salidas parciales, fuentes y replay idéntico ante rechazo.

Admisión limitada al dominio/calendario medido y columna C27 con FD.
Las otras 17 columnas tendrán operadores contrastados, sin FD completa.
No acredita mapa de Poincaré, asentamiento, adaptación, evento continuo,
fidelidad física o tiempo real. 248 tests Rust heredados por identidad.
