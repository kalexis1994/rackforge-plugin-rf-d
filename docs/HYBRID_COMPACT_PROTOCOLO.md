# Filas compactas entre evaluador y solver

## Función y gates previos

Las anotaciones inline y luego la copia contigua conservaron las ecuaciones
pero no pasaron costo: 1,005726 y 0,972211 del control fresco. Quedan
rechazadas. Esta variante parte del evaluador y solver directos admitidos,
sin esas modificaciones, y cambia su interfaz intermedia.

Después de cada evaluación completa, inspeccionar las 118×118 entradas
DC/masa y guardar su unión no nula por filas/columnas ascendentes. Campos
privados, capacidad 2048 por etapa, finitud y límite comprobados. Cada
coeficiente real se inspecciona; sin máscara aprendida o umbral distinto
de cero exacto. Los ceros compartidos se reconstruyen como +0, igual al
CSR original. Rehacer las filas para cada estado/h; no guardar números
de un solve anterior. Las cargas y 118 estados HIGH/LOW siguen completos.

El solver combina esas filas con los mismos pesos Radau y ensambla los
mismos interiores, cruces y residual, en el mismo orden. Se conservan
pivotes, factores, escalas, finitud, backward y refinamiento. Evaluación
eléctrica, residual de trials y controles mantienen su implementación.
No se cambia constante audible, ley de dispositivo ni parámetro físico.

Gates antes de medir:

- 48 matrices de etapa: reconstruir DC/masa de las filas reales, igualdad
  numérica de ceros y bit a bit de entradas no nulas. 24 matrices Radau
  completas, 1.336.704 entradas iguales bit a bit al control.
- 192 direcciones iguales bit a bit al directo y dentro del gate del
  monolítico refinado, 2 nV+1e-7·abs(ref). Rechazar NaN/Inf de matrices,
  pesos/RHS, enlaces entre interiores, capacidad y singularidad, con
  retry válido exacto. Enlaces legales nuevos y cancelación conservados.
- Dos trayectorias 40–100 ms, techos full 64/32 µs: 962 observaciones y
  estados finales frente a directo. Gates heredados de nodos/cargas/J7,
  voz completa y refinamiento temporal. Auditoría original de 5712 filas
  con Amount: 20 pA/2 nV, sin otra trayectoria original independiente.
- Newton 1 pA/2 nV, backward ≤1e-11, hasta tres refinamientos y mismo
  estimador. Heap cero, ocho replays y diez rechazos atómicos de paso.
- Benchmark sin timers, control directo fresco al techo 32 µs, mismos
  compiler/rlib/flags: ratio ≤0,90. Un ensayo no establece RT ni variación
  estadística. El tamaño de las estructuras no acredita pico de stack.

Dominio nominal CA3046/SVC-204D, KEY OFF 75 ms, fuente VCO/historia/reloj
heredados, SVC-9 pp.9/13/19 y p.10. Sin ampliar arranque/CV/fidelidad física.
Un tmp/lab-current, retirar binarios/semilla tras recibos; fallos con
fuente/entrada/replay antes de corregir. Sin WAV, muestras, Cargo o rlib nueva.

## Primer rechazo compacto y ajuste de interfaz

El primer compacto conserva matrices, direcciones y trayectorias, pero
cuesta 0,917327: rechazo frente al gate 0,90, con fuente/entrada/replay en
`hybrid_compact_native01.json`. El siguiente pasa Parts por referencia al
preparador y añade inline(always) a éste y a Matrix::new. Conserva capacidad
2048, inspección completa, metadatos privados y todos los gates. No se mide
pico de stack ni se atribuye un ahorro a copias concretas del binario sin
inspección adicional. Control fresco y gate 0,90 intactos.
