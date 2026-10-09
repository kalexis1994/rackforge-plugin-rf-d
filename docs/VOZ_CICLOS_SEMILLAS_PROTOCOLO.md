# Ciclos desde cargas prescritas: dos memorias y dos resoluciones

2026-10-09. Misma escena CA3046 nominal del
[condicionador](VOZ_CARGAS_SEMILLA_PROTOCOLO.md); SVC-9 p.5 y pp.19/13/10
según [BUS](VOZ_BUS_CONJUNTO_PROTOCOLO.md). Las constantes eléctricas,
tarjetas, Newton y motor temporal permanecen congelados.

## Función

Liberar las dos raíces id/guess=0 admitidas, sin recomputarlas ni modificar
sus cargas. Empaquetar sus 400 floats high/low exactamente como checkpoint
a reloj cero, propuesta `2*maximum_half_ticks`, attempts=20, reservado=0.
Estas historias nuevas tienen procedencia propia; no sustituyen las
trayectorias históricas. Scene solo construye los parámetros: su lift no
se publica como memoria del motor restaurado.

Cuatro perfiles seriales hasta 5,25 ms/2.752.512.000 ticks: objetivos 0/1
y media etapa máxima 125/62,5 ns. Frontera adicional en 2 µs para verificar
exactamente los endpoints de liberación ya admitidos. Después anclas cada
250 µs y dos replays exactos de restore, a 250 µs/2,25 ms. Cada perfil
mantiene su checkpoint final completo, aunque la campaña falle.

## Observaciones y gates

Gate nativo heredado: Newton 1e-13 A/1e-11 V y 2e-9 V/2e-12 A;
LTE 2 µV/2 nA, KCL BUS/C1 1e-12 A. Cuadratura C1 de corrientes completas
Qa/Q10/Q7 con pesos Radau 3/4 y 1/4; balance de carga relativo ≤0,002.
Dos resets por perfil dan un periodo observado, sin periodicidad asentada.
Guardar brackets completos, estados high/low y ledger acumulado en resets.

Añadir cinco integrales Radau: saw, BUS, entrada 6, corriente cursor→BUS
y `0,5*saw−BUS`. Unidades V·s o C. La identidad del panel nominal
`I=(0,5*saw−BUS)/(39250 Ω)` exige media del desbalance cero si C27 repite
carga. Comprobar por endpoints reales `ΔQ_C27+∫I dt=0`, error absoluto
≤1e-12 A multiplicado por duración; identidad integral de panel dentro de
1e-9 V al dividir por duración. Comprobar en puntos nativos seleccionados
las etapas con el oráculo; el ledger completo no es otra integración
independiente ni una segunda cuadratura de todas las etapas.

Reusar el contraste de etapas y corrientes: first/reset1/reset2/final,
full/mid/end. 9600 ecuaciones por memoria (48 puntos de etapa), 48
corrientes de terminales por memoria en 16 endpoints, gates previos.
Comparar 200 coordenadas a 22 relojes no iniciales (2 µs y anclas); 2 µV/
2 nA, frecuencia ≤1 cent y extremos ≤5 mV entre resoluciones. Medir las
18 cargas por ciclo y J7 a fase interpolada Decimal100; es observación,
no nueva solución temporal. Ninguna tolerancia de asentamiento se infiere
del gate de refinamiento. Comparar con ambas historias anteriores sin
trasladar cuadraturas o fases de una a otra.

## Recursos y preservación

Compilar solo caller contra la biblioteca admitida, stack 32 MiB. Máximo
32000/48000 intervalos por perfil, 1800 s por perfil, 7200 s globales.
Reserva 1 GiB + 64 MiB estimados; disco cada 250 ms, stop cooperativo y
20 s de gracia. Compresión transparente de cinco registros exactos ya
protegidos, hashes/tamaños comprobados antes y después; no borrar datos.
Preservar fallo y replay eléctrico antes de reparar o reiniciar. Sin
audio, SPICE, deadline, fidelidad física ni encendido físico nuevos.
