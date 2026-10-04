# Protocolo: coordenada particular para el forcing temporal de C7

Modelo documental CA3046 nominal, parámetros sintéticos y gates intactos.
Intentar sólo el séptimo soporte archivado, índice 6, desde ≈6,25 hasta
≈12,5 µs. Fuente: último resultado realmente aceptado de seis intervalos,
22 memorias individuales, P, pesos y pico conocidos. Mismo reloj,
reconstrucción constitutiva, RHS completo y recintos de potenciales.

## Banco congelado

Radios 0,1/1/10 µV; variantes por radio en orden absolute y signed_c7_shift.
Seleccionar el primer par aceptado. Baseline 10 µV identificado por el
informe separado de cierres enteros. Conservar todas las ramas y rechazos.
Reutilizar 16 inversas/tasas y 128 acciones de subcelda por certificado y
SHA; cero solves, precondicionadores, métricas, recintos o consultas de tasa
nuevos. Política de enteros exactos sin límite decimal; dominio de kernel
<=4096 intacto. No extrapolar otro soporte ni transportar una rama rechazada.

## Cambio auxiliar y compensación completa

El descriptor da e_y'=B(t)e_y+f(t), B=-Hbar^-1_memory,memory y
f=-Hbar^-1*R. Sólo C7, coordenada 20, tiene una particular p. Por celda,
p'=f0=-X_binary*R_poly en esa fila, integrada exactamente con su duración
física. Empezar p=0 y continuar el endpoint exacto entre las ocho celdas.
Es una referencia auxiliar candidata, no la respuesta verdadera.

Para z=e_y-p se tiene z'=B(t)z+(f-p')+B(t)p. Acotar f-p' de C7 con el
resto precondicionado, corrección E*Y y cola exterior de la acción archivada.
Intersectar con el defecto de orden cero sólo para esa misma diferencia.
No cancelar errores uniformes o constitutivos independientes. Ocho subceldas
por celda cubren p por Bernstein y todos los términos B(t)p mediante la
inversa intervalar completa. Convertir 21 coordenadas con sus pesos y las
cuatro junturas con P/(2a); pagar todos los acoplamientos, incluida la diagonal.

En otras coordenadas conservar el forcing L1 original y sumar Bp; C7 usa
el resto f-p' más Bp. No intersectar presupuestos de e y z como si fueran
el mismo término. Comparación, tasas, ganancias y normas permanecen iguales.
Para potenciales añadir |Hbar^-1_potential,C7*p| al término directo original.
Propagar kernels de endpoint/pico para z y exigir cierre nodal estricto
para e, origen incluido, dentro del recinto de potenciales original.

Antes de publicar memorias, restaurar p al pico y endpoint de C7 en cada
perfil y al endpoint final. Identificar los campos de z y los kernels que
actúan sobre z; conservar cotas completas de e para cualquier transporte
posterior. Este cambio de coordenadas no altera cargas o trayectoria física.

## Verificación y alcance

Congelar fuentes antes de medir, datos/tests/validator antes de validar.
Probar forcing afín con solución exacta, cambio de signo y control sin
cancelación, incertidumbre variable de matriz, término Bp indispensable,
restos independientes, conversiones primal/cuadrática, continuidad y
restauración del endpoint. Reproducir todas las inversas, compensaciones,
cierres y linaje; ampliar corpus y preservar fuentes fallidas. KCL 10 pA,
corrección 10 nV, rama lineal 10 fV, backward 1e-10 y meta global 1 mV
intactos. Hardware, voz, audio, motor nativo y deadline siguen abiertos.
