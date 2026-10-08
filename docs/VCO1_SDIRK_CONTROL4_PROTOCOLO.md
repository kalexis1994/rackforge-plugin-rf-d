# SDIRK: mínimo del controlador dentro del dominio existente

2026-10-08. El piso SDIRK01 pasó sus seis raíces y rechazó LTE en XIC3.7: −2,000038009805446 µV, ratio1,0000190049. No ampliar γh ni el dominio de fine: con half4 ticks (7,62939453125 ps), γh≈2,23463 ps permanece por encima del mínimo efectivo ya contrastado 1,90735 ps. El mínimo anterior half8 no agotaba ese dominio.

Un runner nuevo modifica sólo el mínimo full16→8 ticks, de modo que cada half mínimo pase de8 a4. Misma historia, SDIRK, compiler/pila, máximo500 ns, reloj, veinte intentos y gates. Conservar el runner y recibo01. Repetir el banco local para confirmar sus 48 raíces y luego el mismo objetivo condicionado50 µs, con monitor/reserva/presupuesto idénticos. Contrastar las cuatro etapas/endpoint de intervalos seleccionados como antes. No nueva extensión de dt, parámetros o tolerancias. Si falla otra vez, preservar/repetir antes de reparar y cerrar el ensayo; no reducir más el controlador en este bloque.
