# Siguiente bloque: reducción algebraica del ladder con puertos y cargas

## Estado y decisión

El directo sigue siendo la implementación admitida. Las cuatro variantes
de interfaz fallan su gate de costo; no se promueven ni se cambian sus gates.
Continuar con una transformación de las ecuaciones locales, usando esa
unión funcional como control y oráculo offline. Este documento fija trabajo
siguiente; no acredita una reducción ejecutada.

## Primer dominio local

Partir de los nodos 0–15 del grafo audio documental de 66 nodos,
SVC-9 p.13/Fig.9-11, CA3046 y las tarjetas nominales admitidas. Registrar
los cuatro capacitores entre (8,12), (9,13), (10,14), (11,15), 68 nF cada
uno, con su ΔQ compensada. Mantener las conexiones a TAIL (nodo 5),
entradas 6/7, salidas 11/15 y alimentación fija de la red de bias.

Los acoplamientos (16,11)/(17,15), 0,22 µF, y los acoplamientos de entrada
hacia BUS/C10 permanecen explícitos en el padre. Sus corrientes y cargas
cruzan la frontera una sola vez. Publicar la tabla de pertenencia de cada
componente/puerto antes de derivar o implementar el kernel local.

Usar los cuatro voltajes de capacitor como coordenadas de carga y separar
las variables algebraicas de bias, common mode y corrientes de transistor.
Derivar sus relaciones desde las mismas ecuaciones, con beta finita y
uniones BE/BC; conservar las reacciones de entrada, salida y TAIL. El
cuarto capacitor une puertos de salida: registrar esa incidencia en la
masa del padre, sin duplicarlo ni suponer que es una memoria interna libre.

La primera variante reconstruye todos los voltajes/corrientes originales
desde la carga y los puertos. Mantener historial HIGH/LOW, cargas anteriores
y controles como entradas separadas. Toda preparación local pertenece a
la receta/estado/h actual y rechaza entradas fuera de su dominio.

## Orden de implementación y gates

1. Ledger de nodos, componentes, cargas y puertos contra el grafo admitido;
   comprobación de que cada corriente/capacitor aparece una sola vez.
2. Ecuaciones locales y reconstrucción en unidades V/A/C/S, incluyendo
   Jacobiano de reacción de puertos y masa de las cargas. Declarar
   incógnitas que siguen requiriendo solve y las eliminadas exactamente.
3. Kernel en fixtures de trayectorias admitidas, referencia completa y
   columnas FD; mantener 20 pA/2 nV en ecuaciones originales y gate
   derivativo 2 nS+2e-5·abs(FD). Probar cargas de frontera, no finitos,
   singularidad y recuperación válida exacta.
4. Insertar el kernel en la voz funcional 40–100 ms, sin recalibrar VCO o
   semilla. Mantener gates completos de J7, C2/C5, BUS, R59/R60, estados
   reconstruidos, h, heap y publicación atómica.
5. Control fresco y costo final sin timers. Mantener gate 0,90 para ese
   ensayo, además de condiciones eléctricas. No atribuir RT o fidelidad
   física a una mejora local/nominal.

Las memorias no se eliminan por lentitud aparente o una escena favorable.
Si una relación sólo resulta aproximada, declarar antes de medir su error,
unidades y dominio en otro protocolo; esta primera etapa busca eliminación
algebraica de ecuaciones vigentes. Evitar nuevas muestras/builds permanentes;
usar el área temporal única y recibos acotados.
