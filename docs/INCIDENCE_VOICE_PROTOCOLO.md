# Etapas desde incidencias actuales, sin matriz global intermedia

## Contrato previo

Partir del directo vigente, CA3046/SVC-204D y las mismas leyes nominales.
No tocar factor/pivotes/escala, capacidades del solve 236, puertos ni cargas.
Reemplazar sólo la representación de J/M globales por etapa: reunir filas
de contornos 56 y audio 68 con el mapa documental existente. Contornos
primero; después sumar audio con los mismos guards independientes g/m≠0.
Omitir C18 del audio como antes. Añadir la derivada del VCO al final.

El paquete guarda J y masa separados, columnas únicas y ordenadas por
fila, a partir de coeficientes actuales. Incluye todo enlace emitido por
los componentes, también uno nuevo legal; no aprende soporte de una escena.
Conservar cancelaciones y el orden de acumulación de nodos compartidos.
Al unir Radau, usar exactamente B[i][j]·mass+dc y el orden original del CSR.
Capacidad del paquete 4096 entradas por etapa, con rechazo previo al exceso;
la capacidad temporal 4096 del directo sigue vigente. No ampliar dominio.
FULL=false conserva la ruta residual sin producir una tangente válida.

Matrices globales sólo para contraste de laboratorio. Buffers/arrays fijos,
sin heap, locks, IO, logs o serialización en procesamiento. Rechazar paquetes
incompletos, no finitos, índices/capacidad inválidos y sumas con overflow.
Actualizaciones inválidas del paquete no publican cambios parciales.
Conservar backward ≤1e-11 y tres refinamientos; rechazar normalización no
finita, incluyendo cancelaciones de productos finitos. Newton 1 pA/2 nV,
estimador y estado HIGH/LOW completos permanecen iguales.

## Gates

- 24 pares/48 etapas: DC, carga e historial iguales al directo, J/M físicos
  iguales numéricamente; matriz temporal/CSR idénticos. Comparar FULL y
  residual, derivada VCO y reacciones de TAIL/VCA_BASE/BUS.
- 192 direcciones: idénticas al estructurado anterior y dentro de
  2 nV+1e-7·abs(ref) del solve completo refinado. Pruebas de enlaces nuevos,
  cancelación, singularidad, capacidad, no finitos y recuperación exacta.
  Probar además orden/duplicados/actualización atómica del paquete y overflow
  de normalización. No relajar gates si cambia el adaptador de laboratorio.
- Dos ramas 40–100 ms, KEY OFF 75 ms, máximos 64/32 µs. Gates frente al
  directo y voz reservada; refinamiento, ocho replays, diez rechazos y heap
  cero. Auditoría independiente de 5712 filas originales, 20 pA/2 nV.
- Costo sin timers frente al directo fresco 32 µs, ratio ≤0,90. Si pasa,
  declarar admisibilidad numérica/costo separada de integración y RT.

Compilador/rlib congelados, rustc directo sin Cargo. Un tmp/lab-current,
vacío después de recibos; sin WAV/cache/muestras nuevas. Archivos de fuente
por commit/ruta/SHA e imágenes de cambios. Preservar fallos y replay sin
cambios antes de corregir. Recibos ≤8 MiB sin QA; tests heredados por
identidad y sin nueva fidelidad física o extensión de controles/arranque.
