# Extensión de recursos y continuación de prefijo

Antes de ejecutar nueva física. Heredar todos los parámetros y gates del
[protocolo de ciclos](VCO1_RADAU_CICLOS_PROTOCOLO.md), incluyendo 30 ms,
asentamiento 15 ms, pasos 250/125 ns y Decimal100 seleccionado.

El banco02 se interrumpió administrativamente tras observar coste alto;
no hubo rechazo eléctrico conocido. Su adaptador rechazó una fila parcial
al cerrar stdout. Retener recibo, logs, gzip cerrado y bytes de las fuentes.
El tail parcial no codificado no se puede recuperar: no afirmar identidad
con el flujo nativo entero de ese proceso. Decodificar sólo bloques
completos conservados y escoger la última pareja completa de endpoints
(initial más número par de endpoints). Retener también la fila adicional
si existe, sin incorporarla al prefijo lógico. Verificar todos sus gates.

Continuar el perfil250 desde hi/lo, tick absoluto y propuesta reconstruida
del último par completo: LTE<=0,25 implica min(4*half_ticks,2*maximum),
en otro caso 2*half_ticks. Guardar checkpoint privado por hash y validar
echo inicial exacto. No cambiar kernel, Newton, control LTE o carga. El
runner añadido sólo admite checkpoint/clock/propuesta y exporta tick
inicial. Su solve inicial de startup nominal continúa verificándose; en
resume la dinámica usa exclusivamente el checkpoint, no esa raíz DC.
Si la fila adicional sobrevive, compararla por bytes con la primera fila
nueva: diagnóstico de continuidad, además del echo de memoria.

Procesos seriales, 2400 s por proceso y reserva 1 GiB monitoreada, pila
8 MiB; no es coste de producto. Resource preflight mínimo 128 MiB sobre
reserva no predice tamaño. Nuevos stdout conservan también un tail parcial
si ocurre interrupción; comprimir sólo filas completas. No relanzar una
trayectoria completa por una interrupción administrativa de recursos.

El stream lógico250 concatena prefijo admitido y continuación omitiendo
el echo inicial. Perfil125 empieza propio desde cero. Hash de cada gzip,
longitud/SHA de stdout nuevos frente a decodificación y hash del stream
lógico completo. No escribir una copia grande concatenada. Recalcular
mediciones del stream lógico completo; declarar que la trayectoria250
usa dos procesos y las raíces Decimal100 sólo intervalos seleccionados.
Un replay interrumpido administrativamente no es reproducción numérica
completa. Si fallan física/gates, preservar su tupla y replay específico.
