# Presupuesto de ejecución de la observación

2026-10-06. El control con la sonda corregida agota 120 s antes de exportar
40 ms. Su log alcanza aproximadamente 39.154 ms. Se preservan
[recibo y fuentes](../evidence/voice_kcl_budget_rejection01.json).
Sin export completo, ese intento no admite la observación.

Repetir solamente BUS cero con sonda encendida y límite de proceso 240 s.
Usar el mismo ejecutable y módulo, inicialización, circuito, integrador y
tolerancias. El runner derivado debe diferir del congelado únicamente en
`timeout=120` → `timeout=240`, verificándolo en bytes antes de ejecutar.
Las otras tres trayectorias completas del banco conservan sus recibos.

El límite de proceso mide segundos de ejecución en el equipo; no es el
paso mínimo del integrador, una tolerancia eléctrica o un deadline de audio.
La admisión sigue exigiendo identidad exacta de los 40 ms y seis vectores
frente al baseline, además de los registros completos de la ventana.
