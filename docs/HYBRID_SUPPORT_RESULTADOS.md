# Dos optimizaciones de factores rechazadas por costo

## Motor vigente y decisión

**Se mantiene el solver directo admitido en `7c0524273048099f3fd246562c9b87d7cadffb61`.**
Los módulos `support_hybrid_*` son candidatos experimentales rechazados.
Ninguna de sus dos variantes se promueve como optimización. El cierre
[QA](../evidence/hybrid_support_tests01.json) verifica los experimentos y
conserva el solver/control activo y su admisión anterior; su campo passed
no significa que estos candidatos hayan pasado costo.

## Perfil de la implementación vigente

El [perfil](../evidence/hybrid_factor_profile01.json), derivado desde el
directo vigente, mide 2,5567 s de ensamblado/validación, 3,5254 s de
factorización, 0,8629 s de sustitución, 0,1448 s de backward, 0,0048 s
de refinamiento y 6,7080 s de evaluación completa de Newton. Incluye
cuatro replays; no desglosa toda la búsqueda de línea/solves fallidos.

Contadores de eliminación: **5.852.929.116** productos de actualización;
**1.646.662.501** con coeficiente superior pivote no nulo (28,13 %).
La diferencia sugiere trabajo evitable, pero no predice el tiempo de una
implementación con accesos y control de flujo diferentes.

## Candidatos y costo sin instrumentación

[Protocolo previo](HYBRID_SUPPORT_PROTOCOLO.md),
[ensayo 01](../evidence/hybrid_support_native01.json) y
[ensayo 02](../evidence/hybrid_support_native02.json):

| Candidato, techo full 32 µs | Control fresco | Candidato | Ratio |
|---|---:|---:|---:|
| Lista de soporte pivote real | 16,0790201 s | 17,1730345 s | 1,068040 |
| Recorrido contiguo y trabajo nulo evitado | 16,1235435 s | 16,6350208 s | 1,031722 |

Tiempos por los mismos 60 ms simulados. El primero añade una lista
ordenada construida desde cada fila pivote después de swaps, incorporando
fill-in y cancelaciones. Evita productos con coeficiente cero y cruces
con factor cero. Es correcto, pero **6,80 % más lento en este ensayo**.

El segundo retira la lista y conserva el recorrido contiguo. Evita
actualizaciones de cruces con factor cero y restas triangulares con
coeficiente cero cuando el acumulador es no nulo. Mantiene la operación
si éste es cero, conservando su semántica de signo. Es correcto, pero
**3,17 % más lento en este ensayo**.

Ambos incumplen el gate previo ≤0,90; se conservan fuentes, entrada y
replays sin cambios. No se debilita el gate ni se cambia el control para
admitirlos. No se midió ensamblador, vectorización o comportamiento de
cache: no atribuir causalmente la regresión a uno de esos mecanismos.
Una medición por candidato tampoco caracteriza variación estadística.

## Verificación numérica y nuevos fixtures

- En ambos candidatos: 24 matrices/1.336.704 entradas reconstruidas del
  CSR real y 192 direcciones iguales bit a bit al control. Máximo 0,972279
  del gate frente a monolítico refinado, 2 nV+1e-7·abs(ref); ese margen
  numérico es condicionado y no demuestra precisión física.
- 33 rechazos/retries exactos de frontera lineal, 24 enlaces legales
  añadidos/restaurados y un probe de cancelación entre etapas, reejecutados.
- Nuevos: 16 RHS sobre dos fixtures algebraicos que provocan fill-in,
  cancelación, swaps y reacción de puertos/cargas entre etapas. Direcciones
  iguales bit a bit al solver directo. Son fixtures del kernel lineal,
  sin atribuirles una interpretación de circuito o de sonido físico.
- Nuevo: entradas finitas que producen overflow en la eliminación;
  rechazo SingularJacobian y recuperación válida exacta. Se mantiene la
  comprobación completa de finitud de factores y dirección.
- Dos trayectorias propias por candidato, 962 observaciones y estados
  finales iguales al directo. ROOT/GRID/SOLVER serializados idénticos antes
  del FINAL cronometrado; 99.922 solves/499 refinamientos por candidato.
- Backward ≤9,9852e-12; Newton ≤0,999722 pA/1,87210 nV; estimador ≤0,950788.
  Heap cero, ocho replays y diez rechazos atómicos de paso por candidato.
- [Auditoría original](../evidence/hybrid_support_audit01.json) del segundo:
  5712 filas con Amount, ≤0,719007 pA/0,325050 nV. Los endpoints del primero
  coinciden con el mismo control; no se ejecuta otra trayectoria original
  independiente. Voz completa y refinamiento temporal conservan sus gates.

## Alcance y continuación

Voz nominal CA3046/SVC-204D, 40–100 ms, KEY OFF 75 ms, mismo perfil VCO,
reloj, semilla, 118 estados HIGH/LOW, puertos y cargas. Fuentes físicas
heredadas SVC-9 pp.9/13/19 y p.10. Sin constantes audibles nuevas, cambios
eléctricos, identificación física o ampliación de arranque/CV general.
Los contrastes eléctricos/FD anteriores se heredan por identidad.

Compiler/rlib congelados; sin Cargo, biblioteca, WAV ni inputs privados
nuevos. Un `tmp/lab-current`, vacío tras retirar semilla y ejecutables;
recibos comprimidos de observaciones, etapas y fallos, sin carpetas de
muestras (~6,00 MB antes de QA). Se protegen las 4053 fuentes y 8769
inputs privados anteriores.

Siguiente prioridad: perfilar las contribuciones de la evaluación eléctrica
vigente antes de otra transformación; es la sección mayor medida. Mantener
la unión funcional y sus gates. La cadena detallada sigue offline.
