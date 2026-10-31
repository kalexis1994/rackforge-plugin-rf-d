# Corrección temporal del candidato local

Previo, 2026-10-31, después del rechazo SDIRK384 kHz. Mantener G, M,
DC, puntos .49/.50/.51, capacitancias, corriente de puerto y estado
absoluto compensado. Corregir sólo la transición de la ODE lineal local
con entrada afín entre muestras. No ajustar usando la reserva dinámica.

A=-diag(C)^-1*K, b=diag(C)^-1*B, E=exp(h*A). Para r=h*lambda,
phi1=expm1(r)/r y phi2=(expm1(r)-r)/r^2, con serie cerca de cero.
q_next=E*q+h*(phi1-phi2)*b*u_old+h*phi2*b*u_new. Preparar fuera de audio
por diagonalización; publicar condicionamiento, residuales y semigrupo.
No usar la exponencial para afirmar linealidad del circuito no lineal.

Gates auxiliares: parte imaginaria de matrices reales<=1e-10, semigrupo
E(h/2)^2-E(h)<=1e-10; identidades A*(g0+g1)=(E-I)*b y
A*g1=(g0+g1)/h-b relativas1e-8 + absoluto1e-10, y diagonalización
con residual relativo<=1e-10. Conservación A_inc*Xq=I y A_inc*Xu=0
heredada sin cambio. Contrastar mismo corpus fino ya congelado y Rust
con Python<=1e-11 V/1e-15 A. Mismos gates físicos, sin relajar1 uV.

Medir de nuevo1200 bloques porque cambia el método; no sustituir el
banco SDIRK rechazado ni atribuir diferencias de coste a una causa no
aislada. Toda admisión de la familia o de la voz seguirá condicionada
por el rechazo constitutivo. Sin WAV nuevo ni otro oráculo no lineal.
