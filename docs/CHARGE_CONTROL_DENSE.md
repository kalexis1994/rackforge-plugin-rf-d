# Consulta temporal de la transición exponencial

Previo al contraste exponencial, 2026-10-31. Para comparar el estado local
entre muestras384 kHz con la referencia250 ns, usar la misma transición
exponencial en el tramo parcial, no una recta entre potenciales de nodos
rápidos. La entrada sigue siendo la FOH del kernel.125 fracciones temporales
posibles por punto de operación, preparadas sólo en el auditor Python.

La consulta parte del estado Rust HIGH/LOW y mantiene las cargas al entrar
al índice derecho. En un reloj común exacto devolver el endpoint publicado,
incluyendo el marcador izquierdo del salto. No modifica audio ni usa el
estado de referencia como semilla. Todos los puertos y los nodos retenidos
se comparan con los mismos gates; informar además el contraste por
interpolación lineal anterior. No usar dense output para admitir el bloque
FIR o el sonido entre muestras, que requieren contraste de tasa separado.

Los rechazos constitutivos y del banco SDIRK anterior permanecen. El
contraste continuo local y el coste del método exponencial se publican
separados de la admisión de voz, siempre falsa en este bloque.
