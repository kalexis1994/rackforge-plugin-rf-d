# Recintos de Q(v) y magnitud del residual: protocolo

Declarado antes de medir, sobre los mismos 496 intervalos y un soporte mixto.
Fuentes, trayectorias, parámetros y gates anteriores intactos. Cero solves nuevos.
Se conserva la carga constitutiva vigente y el knee binary64 FC*VJ. No reemplazar
su continuación por una fórmula distinta ni modificar su denominador VJ*(1-FC).

Aritmética racional con redondeo exterior diádico de 256 bits. log(x), x>0:
reducir por potencias de dos a y en [1,2), z=(y-1)/(y+1) en [0,1/3).
log(y)=2*sum(k=0..63,z^(2k+1)/(2k+1)); cola positiva <=
2*z^129/(129*(1-z²)). Acotar cada operación y log(2) con la misma serie.
Presupuesto de reducción |k|<=4096; guards fallan sin recorte. Potencias
positivas se encierran mediante exp(p*log(x)), usando la exponencial congelada.

Q y C se evalúan por debajo y encima del knee con recintos exteriores.
Dominio declarado: Cj>=0, VJ>0, 0<=M<=1, 0<=FC<1, knee<VJ, T>=0,
Is>0, emisión>0 y exponente<=45. Q y C son continuas; C es no decreciente
en este dominio. Un intervalo de v permite usar C(vmin),C(vmax), incluso
cruzando el knee. No suponer Q'' continuo ni una fórmula suave para todo el soporte.
Se conservan las 21 memorias lineales y se sustituyen sólo cuatro cargas
no lineales por Q(v) en la reconstrucción, nunca en estados publicados.

Delta Q constitutiva y su incidencia se suman al recinto estático anterior.
Se acotan balance (C) y media (A), con clasificación <10 pA, >=10 pA o inconclusa.
Se contrasta Gauss16 guardado mediante la condición suficiente exacta
1e-30+1e-8*abs(valor), estrictamente menor que el gate binary64 original.

Magnitud superior: aproximar la corriente estática con Taylor centrado de
grado 6, polinomio de grado <=18. Resto <=exp(c+rho)*rho^7/7!, más
incertidumbre de exp(c). Añadir tasas exactas de Q polinómica. Redondear
coeficientes sólo después de cancelar sellos; sumar sus errores absolutos
como cota uniforme en z en [0,1]. Dividir en ocho celdas fijas y usar
Bernstein de cada residual polinómico más su resto para acotar Rpol.
Para Rconst añadir la incidencia del recinto de C(v)*v' menos Qpol'.
La tasa lleva 1/duración; el máximo por celda multiplicado por duración/8
acota integral |R_j| dt, C. El módulo del balance da cota inferior separada.
La consistencia inferior<=superior no demuestra que la cota sea estrecha.

Regresiones: log con series racionales y testigos independientes; Q/C por
ambas piezas, M=1, knee continuo y monotonía; resto de polinomio y signos;
todos los balances/recintos, ocho replays y 24 consultas interiores de Rconst
contra Decimal120. Conservar fallos por recibos completos y SHA antes/después.
Esquemas de datos y recibos propios. Sin admisión de 1 mV global, estabilidad
no lineal, error inicial, cobertura desde DC, física, voz, audio o deadline.
