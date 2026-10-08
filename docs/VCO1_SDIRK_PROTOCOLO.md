# VCO1: SDIRK2 sobre cargas y flujos, ensayo de laboratorio

2026-10-08, base 5d073dd. CA3046 nominal a 25 °C, controles/mixer impuestos. Conserva circuito y producción publicados. Copia privada fine/linear/data exacta del diagnóstico de grilla 02, sin nueva extensión de dominio; piso efectivo 1,9073486328125 ps y pila de laboratorio 8 MiB.

## Derivación

La DAE es F(x)+dQ(x)/dt=0: Q contiene incidencias de cargas de placa/BJT/JFET/741 y −L I en las cuatro restricciones inductivas. Las restricciones algebraicas tienen Q=0. No aplicar RK directamente a voltajes no lineales ni ponderar historias de tensión para aproximar cargas.

Se prueba la tabla A=[[γ,0],[1−γ,γ]], b=[1−γ,γ], c=[γ,1], γ=1−1/sqrt(2). Fuente del método: [Alexander1977, SIAM14(6),1006–1021](https://epubs.siam.org/doi/10.1137/0714068); tabla y R(z) en [documentación primaria MOOSE/INL](https://mooseframework.inl.gov/source/timeintegrators/LStableDirk2.html). R(z)=(1+(1−2γ)z)/(1−γz)^2; orden dos y amortiguación L para la ecuación lineal. Esto no demuestra orden global en esta DAE, conmutación, precisión continua o ausencia de reducción de orden.

Etapa1: F(x1)+(Q(x1)−Q(x0))/(γh)=0. Etapa2: F(x2)+(Q(x2)−Q(x0))/(γh)−a*(Q(x1)−Q(x0))/(γh)=0, a=(1−γ)/γ. El historial de etapa2 siempre es x0; x1 es sólo semilla y forcing fijo de cargas/flujos. Conservar incidencia/masa y restricciones algebraicas sin forcing. Sólo x2 se convierte en memoria provisional; step doubling publica ambos endpoints después de verificar todo. γ,a y γh redondeados binary64 explícitos y reproducidos en Decimal100. Correcciones en lo de primer orden heredadas y declaradas.

Gates Newton 1e-13 A/1e-11 V y corrección 2e-9 V/2e-12 A; 64/24, Armijo sobre corrección. Referencia Decimal100 2e-14 A/2e-12 V y corrección 2e-10 V/2e-13 A, masa 1e-11 A; contraste 2e-7 V/2e-10 A. Step doubling: full frente a dos half, sin división por tres o extrapolación, 2 µV/2 nA en las 134 incógnitas.

## Banco previo a continuación

Dos historias: rechazo inicial Q6 y último estado del rechazo XIC3.7. Para cada una, tres pasos SDIRK full/mid/end con medio paso 15,2587890625 /30,517578125 /61,03515625 /122,0703125 ps. Exportar las dos raíces internas por paso, sus ratios, historial y forcing. Resolver cada etapa con leyes/incidencias Decimal100; etapa2 se inicializa desde etapa1 independiente, nunca desde candidato nativo. Conservar fallos y repetir sin cambios antes de reparar; no admitir un cero placeholder. Verificar 48 raíces y comparar error temporal de ambas rutas.

Sólo si pasan las raíces locales, intentar 50 µs desde la historia Q6, máximo half500 ns, reloj entero de 1,9073486328125 ps, mínimo half8 ticks (etapa efectiva ≥piso heredado), controlador20 intentos. Sólo aceptar memoria hi/lo y reloj completo; logs/I/O fuera del kernel. Reserva2 GiB con monitor, presupuesto180 s por proceso. Export completo de endpoints, etapas y dt real; fallo original/replay conservados. Contrastar cuatro intervalos aceptados con Decimal100 (primero, último, dos con mayor cambio nodal). No declarar período/refinamiento/audio/RT por este recorrido condicionado. No lanzar ciclos completos en este bloque.

## Procedencia del nodo y alcance

XIC3.7 es la base de Q2 interna, ligada a entrada+ y estado de modo común por EOS; no es el nodo de salida. La tarjeta TI preservada contiene C4/etapa diferencial, dos capacitores posteriores, L2/mode común y L3/salida. Su numeración/polos nominales no demuestra cuál causa el rechazo observado. El ensayo cambia discretización y permite contrastar coste/cobertura; no elimina estados o redefine parámetros físicos.
