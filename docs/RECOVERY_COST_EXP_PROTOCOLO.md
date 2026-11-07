# Una transición exponencial para el mismo circuito híbrido

Previo, 2026-11-06. Joint, predictor y especialización conservan sus bancos
rechazados. El ensamblador confirma dos llamadas al solve de etapa por paso;
la especialización no acredita mejora. No inferir sus causas de caché/CPU.

Probar un integrador distinto, separando error temporal y constitutivo.
Eliminación algebraica propia con las MISMAS12 leyes y18 memorias:

    x=Xq*q+Xu*u-Xn*n(E*x)
    qdot=A*q+b*u+H*n(E*x)

Obtener Xn/H por Schur de G y D con las mismas coordenadas de capacitor.
Integrar exactamente la parte lineal y la entrada afín. Aproximar n(t)
por FOH entre los endpoints, con pesos N0/N1 calculados por exponencial:

    qbase=F*qold+U0*uold+U1*unew+N0*nold
    qnew=qbase+N1*nnew
    xnew=Xq*qbase+Xu*unew-(Xn-Xq*N1)*nnew

Resolver las12 leyes simultáneas de endpoint, residual2e-13 y presupuesto12,
con el precondicionador6 y predictor ya contrastados. Corrientes BC y cargas
se conservan. Cambia la cuadratura temporal, no la constitución. No exigir
igualdad1e-10 con SDIRK: medir esa diferencia y rechazar si no pasa gates.

Gates previos: identidades Schur/capacitivas<=1e-11; mapas exponenciales
complejos residuales<=1e-10; semigrupo<=1e-10; Rust/Python mismo método
<=1e-10 V/1e-14 A, carga<=1e-11 V;48 endpoints con12 leyes, residual<=2e-13,
KCL algebraico<=1e-12 A y balance de transición<=1e-11 V. Rechazo/retry/heap
con los mismos fixtures numéricos. Estados finos del mismo híbrido y
comparación con las reservas físicas existentes se publican por separado.

Tres reservas .1 V a384 kHz y referencia250 ns, consultas parciales desde
estados propios: nodos retenidos<=1uV, panel<=2nA, RMS J7<=.001, pico<=.003,
media<=1uV/fallback1nV. Sin interpolar nodos rápidos ni tomar estados del
oráculo como semilla. Comparar además contra el MISMO híbrido a250 ns,
gate nodal1uV, explicitando que no es una referencia física independiente.

Banco1200 más confirmación4800 si pasa, objetivo50% de2.6667 ms en TODAS
las filas, primer bloque/FIR idénticos. Conservar rechazos y replay antes
de otra corrección. No admite la voz completa. Una variante nueva justifica
ampliar sólo el límite de recibos nuevos a10MiB sin QA, con diferencias
lossless y consultas dispersas; no más WAV, SPICE, biblioteca o caché.
