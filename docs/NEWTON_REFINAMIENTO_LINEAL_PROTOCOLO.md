# Refinar el solve conservando el sistema original

2026-10-06. Variante siguiente, aún no medida. Parte del
[contraste de la matriz completa](NEWTON_MATRIZ_COMPLETA_RESULTADOS.md).
Copiar el build original observado a otro directorio; conservar builds04–06,
la fila equivalente rechazada y todos los recibos. No cambiar componentes,
sellos de dispositivos, flujo, NIintegrate, tolerancias, truncamiento o RHS.

## Variante única declarada

Bandera de laboratorio explícita `RF_D_LINEAR_REFINE=1`. Para cada sistema
real KLU resuelto por NIiter, conservar A efectivo después de diagGmin y b
antes de SMPsolve. Usar los mismos factores KLU y el mismo mapa NewToOld.
Tras el solve original, ejecutar **tres correcciones lineales**:

1. Calcular r=b−A*x desde los binary64 originales. Acumular productos y sumas
   con un par de doubles; producto con error mediante FMA y suma con
   transformación sin error. Registrar implementación y límites de finitud.
2. Resolver A*dx=r con los factores existentes mediante SMPsolve, usando
   un vector temporal separado del RHS/estado del circuito.
3. Actualizar x con suma compensada, reteniendo la parte baja entre las
   tres correcciones. Publicar finalmente una sola solución binary64.

No evaluar dispositivos durante estas correcciones ni volver a factorizar.
Los factores siguen representando exactamente la misma matriz estampada
en términos de entradas; su error numérico se diagnostica por separado.
Aplicar también a DC/arranque de NIiter para que el control pruebe la ruta
real. No activarla sólo en el paso ya rechazado ni seleccionar otra cantidad
de correcciones según el resultado del banco. No reemplazar el inversor
KLU por otro LU al afirmar que se ha probado esta variante.

## Comprobaciones previas y registro

Contrastar el código compilado de productos/sumas compensados con valores
binary64 exactos: cancelación fuerte, coeficientes L2, sub-ULP, signos,
desbordamiento y valores no finitos. Conservar fallos y fuentes. Contrastar
las soluciones seleccionadas con las raíces de 120 dígitos de las mismas
capturas, registrando r, dx y x en cada corrección; usar escalas diagnósticas
por tipo: 1e-8 V + 1e-7*|V| y 1e-13 A + 1e-7*|I|, sin cambiar NIconvTest.
Registrar tanto error de solución como residual exacto, ya que el redondeo
de la raíz puede aumentar una fila L2 aunque mejore sus voltajes.

Reservar memoria e instrumentación fuera de una ruta RT; esta variante es
un experimento de oráculo, no un candidato de audio optimizado. Fallos de
finitud o dimensiones deben quedar explícitos; no ocultarlos con una
saturación o un fallback silencioso.

## Gates secuenciales

1. Variante apagada: BUS cero y variable exactamente iguales a build04 en
   reloj y seis vectores; control de 40 ms completo. Si falla, detener.
2. Variante activa, BUS cero: 40 ms completos; primer punto DC ≤1 µV en
   cinco voltajes y ≤1 pA en Iport. Grilla absoluta de 5 µs, diferencias de
   voltaje ≤5 mV; frecuencia asentada ≤1 cent desde 5 ms; mismo número de
   cruces de rampa a −2 V y diferencia máxima ≤10 ns. Reutilizar el comparador
   congelado del experimento anterior, sin realinear ni recortar reset.
3. Sólo si pasa, BUS variable completo de 40 ms. Un prefijo más largo o
   un reloj distinto de fallo no admite el VCO ni el puerto.

Auditar fuente/build/runtime/entradas antes y después, log, reloj, finitud,
aborto y cobertura junto al exit code. Si falla, conservar el rechazo y
detener esta variante; no cambiar correcciones, umbrales o tolerancias para
rescatarla. Después de una admisión local todavía falta el contraste con
el oficial, cierre R45/contorno, refinamiento y ruta portable. A/RHS ya
contienen redondeo de dispositivos; el refinamiento lineal no demuestra
fidelidad física ni la convergencia no lineal por sí solo.
