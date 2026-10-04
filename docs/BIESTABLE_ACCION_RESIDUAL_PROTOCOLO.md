# Protocolo: acción dirigida del RHS en el cuarto intervalo

Modelo documental CA3046 nominal y parámetros sintéticos intactos. Fuente:
último certificado del prefijo fino, tres intervalos hasta ≈781,25 ns.
Intentar únicamente su cuarto intervalo archivado, índice 3, hasta
≈1562,5 ns. Heredar su memoria real de 22 grupos, pico nodal, P y norma.
No alimentar el experimento con memorias del cuarto intervalo rechazado.

## Banco y datos congelados

Radios en orden 0,1; 1; 10 µV. Dos variantes en orden por radio:
direct_only y direct_and_memory. Ambas comparten circuito, reconstrucción,
recintos medios, inversas, tasas y memoria entrante. La primera cambia
sólo el término algebraico directo; la segunda también el forcing L1 de
memoria. Seleccionar el primer par aceptado. Retener todos los rechazos.
Reutilizar por certificado y SHA las dieciséis inversas y tasas archivadas.
Cero solves, precondicionadores, candidatos de P o consultas LDL nuevos.

## RHS firmado y restos

Recalcular el polinomio constitutivo de grado seis sobre cada celda
archivada con la misma función congelada, incluyendo sus errores uniformes
y las 21 restricciones exactas. Completar 119 componentes con las cuatro
restricciones constitutivas nulas de Q(v). Ocho subceldas internas por
celda. Añadir la corrección C(v)*v'-Qpol' de las junturas usando su ley,
monotonía y dominio previos. Cubrir la magnitud de la corrección nodal y
error uniforme como resto independiente: no asumir que éstos cancelan.

Combinar exactamente las columnas de X_binary con los coeficientes
firmados del RHS antes de acotar su polinomio: Y(u)=D*X_binary*b_poly(u).
No borrar corrientes pequeñas ni regularizar conductancias. Esta identidad
algebraica conserva correlaciones ya justificadas por la expresión común,
sin suponer que las corrientes de una pareja de nodos sean opuestas.

## Acción de la inversa media completa

E=I-D*X_binary*Hbar*D^-1 es el defecto intervalar archivado, con q<1.
Hbar^-1*b=D^-1*(I-E)^-1*Y. El resto RHS se cubre por
sum_j |D_i*X_ij|*remainder_j. En cada subcelda usar Bernstein sobre Y y
sumar ese resto; cubrir E*Y con producto de intervalos firmado. La cola
desde E^2 es row_norm(E_i)*q/(1-q)*max_j |Y_j|, luego dividir por D_i.
Intersectar con la cota de orden cero row_norm(E_i)/(1-q)*max|Y| sólo
porque ambas describen la misma acción. Guardar intervalos, filas, q,
corrección, cola y coeficientes; no usar X_binary*b como prueba de inversa.

Cubrir potenciales puntuales y tasas de memoria. Integrar cotas puntuales
sobre las ocho subceldas para L1; convertir las 21 coordenadas lineales
con sus pesos y las cuatro junturas con P/(2a). Intersectar cada presupuesto
con la cota anterior del mismo término. Mantener comparación, tasas y
ganancias de memoria sin cambios. Los dos modos difieren sólo por qué
presupuestos de forcing sustituyen. La prueba requiere todo el tiempo y
todo el tubo, incluyendo incertidumbre de Hbar y restos constitutivos.

## Cierre, verificación y alcance

Incluir el pico entrante y continuidad real exacta, propagar kernels de
endpoint/pico con forcing tardío, y exigir inclusión nodal estricta. Sólo
ese cierre admite un cuarto intervalo; no extrapolar posteriores. Si
rechaza, conservar los tres anteriores y el mismo primer hueco.

Congelar fuentes antes de medir y datos/tests/validator antes de validar.
Verificar sistema exacto sensible a modo común con RHS dirigido, caso sin
cancelación, incertidumbre de H, resto independiente adverso, polinomio
variable en tiempo, cola e intersección, conversiones de norma, todos los
recintos y cierres. Preservar fallos y ampliar el corpus. Gates históricos
intactos: KCL 10 pA, corrección 10 nV, rama lineal 10 fV, backward 1e-10
y error global 1 mV. Parámetros físicos, audio y deadline siguen separados.
