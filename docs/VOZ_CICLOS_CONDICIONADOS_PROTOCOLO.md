# Ciclos desde la raíz conjunta condicionada

2026-10-09, contrato previo. Continuar exactamente ambos checkpoints de
500 µs hasta 5,25 ms (2.752.512.000 ticks). Misma revisión CA3046 nominal,
escena, parámetros y biblioteca compilada del banco de inicialización.
No resolver un nuevo arranque ni sustituir cargas del prefijo.

## Identidad, recursos y cobertura

Derivar el caller de continuación anterior con cuatro cambios declarados:
exigir checkpoint a 500 µs/perfil correcto; abrir ledger de eventos;
guardar estados compensados de ambos extremos del bracket de reset y
las integrales C1 acumuladas; cerrar ese ledger. La física y el motor no
cambian. Scene reconstruye parámetros, sin usar su semilla como memoria.
El caller compila contra el mismo .rlib identificado por SHA256.

Dos procesos seriales, cada uno <=1800 s; total <=3600 s con compilación
<=120 s. Presupuesto total de intervalos heredado: 32.000/48.000 para
máximas medias etapas de 125/62,5 ns; restar los 2009/4006 ya completados.
Estimar 40 MiB nuevos, reserva de disco 1 GiB. Muestrear cada 250 ms;
stop cooperativo y checkpoint ante falta de reserva o tiempo, con 20 s
de gracia antes de terminar. Preservar intento, sources, exports y ledger
si falla. Replay inmediato de rechazo eléctrico desde final.ckp, sin
reinterpretar un stop administrativo. No relajar presupuesto silenciosamente.

## Gates heredados y análisis nuevo

- Unión prefix→continuación con checkpoint idéntico por bytes, clock y
  propuesta del motor; trace por codec sin pérdida y todas sus medias etapas.
- 22 checkpoints de 0..5,25 ms cada 250 µs, 200 coordenadas compartidas
  a 2 µV/2 nA en Decimal100. Dos replays exactos por perfil, sumando
  el de 250 µs al de 2,25 ms, excluidos de integrales y contadores.
- Residual/corrección/LTE<=1; BUS y C1 instantáneos<=1e-12 A;
  balance C1 integrado relativo<=0,002. Dos cruces de rampa ascendentes
  por −2 V por perfil. Frecuencia de ese ciclo refinada<=1 cent y
  extremos de saw/tri/pulse/BUS/J7 refinados<=5 mV, gates anteriores.
- Oráculo independiente en first/reset1/reset2/final de cada continuación:
  full/mid/end con dos etapas cada par, 9600 ecuaciones de 48 puntos,
  ocho diferencias LTE y 48 corrientes terminales en 16 endpoints;
  gates heredados, incluida corriente<=2e-11 A. Candidatos nativos
  declarados; no afirmar búsqueda de raíces ni segunda integración completa.

El ledger de eventos publica dos estados high/low por cruce, ticks de
ambos extremos y cuadratura C1 acumulada. Contrastar el bracket con trace
y bancos de etapas seleccionadas. Comparar estado real de endpoints y
cargas de los 18 capacitores, incluidos C27/C10, entre cruces consecutivos.
Cerrar C1 con la diferencia de cuadraturas y de rampa de esos endpoints,
con el gate integrado relativo heredado. La quadratura sigue siendo nativa;
el endpoint y su carga se decodifican independientemente.

Interpolar además en Decimal100 los estados dentro de cada bracket hasta
la fase rampa=−2 V y reportar la diferencia de cargas/200 coordenadas.
Esa interpolación es un diagnóstico observacional: no es otra solución
del circuito, ni una cota continua o un gate nuevo de periodicidad.
Guardar los anchos de bracket y la diferencia de fase de endpoints.
Dos cruces definen un periodo medido, pero no una secuencia de periodos
convergentes. No admitir asentamiento aunque un estado aislado coincida.
Los 248 tests Rust se heredan por identidad; no reejecutarlos para este
caller de laboratorio. Sin nuevo audio, SPICE, fidelidad o deadline.
