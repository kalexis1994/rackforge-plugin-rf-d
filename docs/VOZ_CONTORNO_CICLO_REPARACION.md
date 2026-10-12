# Apertura con C7 cargado: reparación del predictor

Declaración previa a la campaña02, 2026-10-12. La campaña01 y su
replay rechazaron en5212471296 ticks (9.942 ms), al abrir S, con
`PrecisionLimit(Nonlinear(IterationBudget))`. Se preservan fuentes,
checkpoint entrante y destino. C7 estaba a2.040774365856582 V.

El predictor de apertura del kernel antiguo usaba solamente S abierto
y TRIGGER_C<1 V para proponer Q12/Q18 y el nodo de gatillo. C7 cargado
mantiene activo otro camino de gatillo: esa estimación no es adecuada.
El diagnóstico04 repite por bytes el rechazo y rollback del checkpoint;
la propuesta converge en el mismo destino con half16 ticks y LTE<1.
Esto prueba un paso, no el recorrido completo.

La copia `joint_contour_cycle_kernel.rs` añade C7<0.1 V como condición
de elegibilidad de esa estimación inicial. Es un límite numérico del
predictor, no una constante física ni un umbral identificado del Moog.
Fuera de esa condición Newton comienza con incremento cero, conservando
la historia. No se alteran ecuaciones, cargas, tolerancias, budgets,
adaptación, observaciones ni el kernel histórico. El guard se comprueba
por sustitución exacta de una única condición; el runner cambia sólo su
binding al kernel nuevo. Exigir prefijo aceptado idéntico a campaña01,
cuatro perfiles completos y auditor independiente según el protocolo.

El diagnóstico auxiliar01/02 tuvo una colisión de nombres: el runner
`proposed.rs` sobrescribía el kernel homónimo y se incluía a sí mismo.
Sus stderr originales no fueron retenidos. El intento03 además descubrió
que el escritor de recibos exige nombres exclusivos. Se conservan los
archivos sobrevivientes y los recibos disponibles; diagnóstico04 separa
`proposed_kernel.rs` y registra cada comando antes de comprobarlo.
Estos errores del auxiliar no constituyen evidencia sobre el circuito.
