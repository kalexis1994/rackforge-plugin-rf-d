# Soporte actual de la fila pivote en el motor directo

El [perfil de ejecución](EXECUTION_COST_PROTOCOLO.md) localiza trabajo
en preparación/factorización. Candidato separado sobre el directo activo:
en cada pivote, después de permutar filas, inspeccionar la fila actual y
guardar sus columnas no nulas estrictamente a la derecha del pivote.
Usar ese listado ascendente para las actualizaciones del interior y las
cuatro reacciones del borde. Incluye el fill creado por pivotes anteriores.
No hay máscara de una escena ni soporte numérico cacheado entre solves.

No cambiar ensamblaje, orden de pivotes/operaciones no nulas, escalas,
capacidades, leyes de dispositivos, cargas, puertos, estimador o dominio.
Usar arrays fijos. Mantener guards finales de finitud, backward ≤1e-11 y
tres refinamientos. Saltar productos por cero puede cambiar signos de cero;
las direcciones y trayectorias son el gate efectivo, sin tolerancia nueva.

Antes del costo: 24 pares/48 etapas, coeficientes físicos idénticos,
192 direcciones frente a la referencia estructurada anterior y solve
completo refinado (2 nV+1e-7·abs(ref)). Probar nuevos enlaces legales,
fill/pivoteo, cancelaciones, no finitos, singularidad, capacidad, recuperación
exacta y los rechazos heredados. Dos ramas 64/32 µs con gates del directo
y de voz reservada, refinamiento, ocho replays, diez rechazos y heap cero.
Auditoría independiente de 5712 filas originales, 20 pA/2 nV.

Medir sin timers contra el directo fresco 32 µs, toolchain/flags/rlib iguales.
Gate ≤0,90 sin reajuste. Aunque pase, este recibo no acredita deadline RT,
fidelidad de hardware o un dominio mayor. No modificar fuentes históricas;
registrar selección explícita sólo después del cierre y de la integración.

Compartir el presupuesto de recibos de este bloque de ejecución (8 MiB sin
QA). Un solo tmp/lab-current, sin WAV, librería, Cargo ni muestras nuevas.
Preservar fallos y replay sin cambios antes de corregir o retirar binarios.
