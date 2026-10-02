# J66 compensado sobre el reloj completo: protocolo previo

Extender la variante `increment-pair/compensated-static-J66/v1`, ya
contrastada en cuatro ventanas, al reloj publicado E4G8 de **0..3 ms**.
Referencia congelada: `evidence/loudness_latch_bdf_growth_dc.json.gz`,
SHA256 `d912d493022638b37f23b2b6d5c1eff345b387e8eeed1e42e3a86c710168f0dd`.
El corte previo RF-D es `c28e5c2`. No hay unidad física de referencia.

## Experimento fijado

1. Validar el linaje de los **6.486 intervalos publicados**, incluyendo
   los dos medios de arranque. Verificar los hashes de historial entrante
   de cada ensayo aceptado, el estado anterior publicado, fuentes,
   intervalos y tiempos exactos. No ejecutar los 49 rechazos históricos,
   predictores ni sombras del controlador; son otros ensayos.
2. Recalcular una vez el DC inicial con la variante (su ruta DC heredada
   permanece igual) y comparar el estado completo tipado/canónico con el
   DC archivado. Si no coincide, conservar ambos y detener la trayectoria.
   No sustituir un DC distinto por el archivado para aprobar el experimento.
3. Avanzar la secuencia publicada, KEY=10 V, r61=200 Ω, BUS=0 y parámetros
   Q25/Q15 `finite_transit` escala 1. Cada paso parte del estado propio
   anterior; no reinsertar memorias ni semillas de referencia. Mantener
   exactamente BE de arranque/BDF2, Newton, búsqueda lineal y presupuestos.
   Mínimo de dominio 1 ps; razones BDF2 ≤2.
4. Gates heredados: Newton KCL <10 pA y corrección <10 nV; publicación
   directa desde historiales reales KCL <10 pA, ecuación de rama <10⁻¹⁴ V
   y restauración tipada exacta. Ante fallo guardar intervalo, estado
   entrante, diagnóstico y candidato disponible; detener sin reset,
   cambio de raíz, recuperación por otra semilla o reducción del intervalo.
5. Comparar todos los 94 nodos compensados y 25 memorias en cada instante
   publicado con gate **10 nV absoluto** para cada familia. Las cuatro
   cargas usan escala 10⁻¹² C/V sólo como coordenada numérica. Una diferencia
   contra referencia fallida no detiene un solve/publicación válido;
   conservar todos los máximos, primeros fallos e índices/nodos/memorias.

Archivar la secuencia fuente, DC nuevo, todos los estados, incrementos,
publicaciones, diferencias y linaje del candidato, además del último estado
válido y cualquier fallo. Registrar intentos, pasos válidos/solucionados,
iteraciones y hash de fuentes antes/después. El reloj de referencia es
impuesto: **no se aplica ni se valida el controlador adaptativo E4G8**.

No relajar los gates después de medir. El gate de equivalencia a reloj fijo
es distinto del refinamiento temporal global de 1 mV, aún fallido en los
informes anteriores. Tampoco admite física vintage, audio, rendimiento del
callback o error entre muestras. Contorno y carga siguen compartidos.

`python tools/loudness_latch_bdf_static_precision_fixed_clock.py`
