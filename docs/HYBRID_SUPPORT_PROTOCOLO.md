# Soporte real de la fila pivote

## Decisión previa

El perfil vigente `hybrid_factor_profile01.json` atribuye 3,5254 s a
factores, 2,5567 s a ensamblado/validación y 6,7080 s a evaluación completa
de Newton. Los contadores de eliminación registran 5.852.929.116 productos
de actualización y 1.646.662.501 con coeficiente pivote no nulo. Incluyen
replays exactos; el perfil no desglosa todos los trials/solves fallidos.

Derivar el candidato desde el directo admitido. En cada columna, después
del pivoteo, construir una lista ordenada con los coeficientes superiores
realmente no nulos de la fila pivote. Actualizar interiores y cruces sólo
con esa lista. Un cruce cuyo factor es exactamente cero conserva la
división/almacenamiento del factor y evita sus actualizaciones nulas.

El soporte se reconstruye desde la fila numérica actual, incluidos fill-in
y cancelaciones. No se reutiliza una máscara de una escena o de otra
columna/estado/h. Mantener pivoteo, filas completas, bordes de cuatro
puertos, cargas, historial HIGH/LOW, residual compensado y comprobación
completa de finitud de factores. Si se genera un no finito, no publicar
una solución. Sin constantes audibles ni modificaciones eléctricas.

Voz nominal CA3046/SVC-204D 40–100 ms, KEY OFF a 75 ms, perfil VCO, reloj,
semilla y 118 estados del control. Fuentes heredadas SVC-9 pp.9/13/19 y
p.10. No ampliar dominio a arranque, CV general o identificación física.

## Gates fijados antes del benchmark

- Reconstrucción de 24 matrices/1.336.704 entradas iguales bit a bit;
  192 direcciones iguales bit a bit al control y dentro de
  2 nV+1e-7·abs(ref) del solve monolítico refinado.
- Mantener 33 rechazos/retries exactos, 24 nuevos enlaces legales
  incorporados/restaurados y probe de cancelación entre etapas. Añadir
  fixtures algebraicos de fill-in/cancelación y permutación con cargas
  de puertos para contrastar soporte recalculado contra el solver previo.
- Dos trayectorias propias, techos full 64/32 µs: 962 observaciones,
  estados finales y cargas frente a directo. Gates heredados de nodos
  20 µV+2e-6·abs(ref), cargas 2 nA+2e-5·abs(ref), J7 RMS 0,1 %, pico
  0,3 %, media 1 µV. Mantener voz completa y refinamiento temporal.
- Auditoría de 24 pares/5712 filas originales con Amount: 20 pA/2 nV.
  Candidatos nativos auditados, sin otra trayectoria original independiente.
- Newton 1 pA/2 nV, backward ≤1e-11, máximo tres refinamientos y estimador
  sin cambios. Heap cero, ocho replays exactos y diez rechazos atómicos.
- Control directo fresco al techo 32 µs, mismos compiler/rlib/flags,
  sin timers internos. Costo candidato/control ≤0,90. Un único ensayo
  no establece estabilidad estadística, otro host o deadline RT.

Un `tmp/lab-current` y recibos compactos; retirar ejecutables y semilla
después de guardar resultados. Fallos con fuente/entrada/replay antes
de corregir; sin nuevos WAV, muestras, Cargo o biblioteca.


Se añade un fixture finito cuyo factor produce overflow, exigiendo
SingularJacobian y retry válido exacto. La prueba confirma que omitir
actualizaciones nulas mantiene el rechazo de factores no finitos.

## Rechazo y siguiente candidato

La lista de coeficientes reales conserva todos los contrastes numéricos,
pero cuesta 1,068040 del control: rechazo con fuentes/entrada/replay
en `hybrid_support_native01.json`. Menos productos no aseguró menor costo;
no se admite esa lista ni se atribuye el resultado a sparsity por sí sola.

El siguiente conserva las actualizaciones contiguas originales de la
fila pivote y la omisión de actualizaciones del cruce con factor cero.
En sustitución triangular/borde sólo omite una resta con coeficiente
exactamente cero si el acumulador es no nulo; conserva la operación cuando
el acumulador es cero para preservar la semántica del cero con signo.
Mantiene orden de todas las restas ejecutadas y chequeos de finitud de
factores/dirección completa. No hay lista ni máscara aprendida; se leen
los coeficientes actuales en cada loop. Mismos gates y control fresco.
