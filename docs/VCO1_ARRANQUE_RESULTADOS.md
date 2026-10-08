# VCO1: arranque propio y diagnóstico del reset

2026-10-08. CA3046 nominal a 25°C, panel SW6 3/10, nivel 0.5, ON,
CV/rieles y mixer impuestos. [Protocolo previo](VCO1_ARRANQUE_PROTOCOLO.md).

## Arranque admitido

`vco1_startup` deriva una semilla con KCL/KVL, transporte exponencial,
saturación y ambos puertos 741 propios. No lee estados, tablas de notas o
frecuencias. El Newton anterior verifica las 134 ecuaciones juntas; la
fuente C1=0 se contabiliza explícitamente y se retira para Euler.

La [producción optimizada](../evidence/voice_vco1_startup_native01.json)
pasó diez arranques: C4=10/100pF, controles nominales y cuatro CV de teclado
con trims calibrados. Frente a los dos DC SPICE nominales conservados:
error máximo 3.22656e-9V / 1.07100e-13A. Iteraciones máximas: 15.
Dos tests eléctricos y uno aislado sin heap: 16 arranques y 128 pasos,
cero asignaciones. Rechazo por presupuesto seguido de retry idéntico.

El [cálculo independiente](../evidence/voice_vco1_startup_reference01.json)
parte de las mismas semillas analíticas, no de las raíces nativas: incidencias
y pivotes Decimal100, leyes de dispositivo binary64 declaradas. Diez raíces,
error máximo 8.55760e-13V / 4.84222e-16A. Comprueba fuente de arranque,
masa, todas las KCL y restricciones con tolerancias más estrictas.
El rechazo SPICE anterior del arranque calibrado permanece en su recibo;
estas raíces nuevas no convierten ese proceso fallido en éxito.

## Ciclos completos todavía rechazados

El [banco de paso fijo](../evidence/voice_vco1_native_cycles01.json)
se rechazó a 2.434ms / 500ns. Los diagnósticos a 250ns y 125ns se
rechazaron a 1.18425ms y 2.434125ms. Todos tienen prefix completo,
comando, código, bytes originales y replay sin cambios. El intervalo
500ns también se rechaza en el solver independiente; extrapolar el estado
por potencias de dos tampoco completa los tres casos.

El [diagnóstico separado](../evidence/voice_vco1_reset_diagnostics01.json)
conserva esos fallos. Una copia privada cambió exclusivamente los cuatro
límites de paso inferior, sin cambiar las leyes, y redujo el paso ante
rechazo. Completó 30ms con 60382 pasos aceptados / 431 rechazos,
mínimo 1.953125ns. Frecuencia 410.76756Hz; balance Qa/Q10-C1 0.00109733
pasa 0.002. La dispersión entre períodos 6.02698e-5 **no pasa 1e-5**.
La copia no forma parte de producción y repetir la medición conserva el
rechazo. No hay admisión de refinamiento, calibración temporal o audio.

La [QA de publicación](../evidence/voice_vco1_startup_tests01.json)
cubre 223 controles: tres nuevos ejecutados y 220 heredados por identidad.
No se cuentan los procesos de diagnóstico como tests aprobados. Corpus y
versiones medidas archivados por SHA, sin SPICE nuevo ni audio nuevo.

## Siguiente bloque

Derivar una API de subpasos que reutilice exactamente las leyes y memorias
anteriores; verificar stamps/raíces independientes para pasos pequeños.
Añadir control de precisión temporal del reset y medir los mismos gates,
con protocolo propio previo a su campaña. Después escenas reservadas,
carga activa (transferir R6/R45), cadena y voz. No se admite DC libre,
toda la caja de controles, identidad física o tiempo real.
