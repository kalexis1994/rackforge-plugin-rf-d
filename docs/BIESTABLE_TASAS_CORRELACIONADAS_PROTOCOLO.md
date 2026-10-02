# Variante de tasas correlacionadas: protocolo

Se declara antes de medir sobre 496 intervalos y el soporte mixto anterior.
La cota rectangular y todos sus resultados permanecen intactos. Sólo cambian
recintos del diagnóstico; ninguna trayectoria, carga publicada, constante
física, control, root, tolerancia o gate. Cero solves nuevos.

Taylor de capacitancia de grado 6, ocho celdas y aritmética exterior diádica
256 bits. Cubierta de knees heredada, profundidad 40. Se normaliza el soporte
a z en [0,1]; piezas suaves y brackets se conservan. Coincidencia idéntica
del knee sigue requiriendo otra política, sin fallback silencioso.

En cada pieza suave se forma C(v(z)) como polinomio con resto uniforme.
Agotamiento debajo del knee: c=v en el centro de la pieza,
w=(v-c)/(VJ-c), rho=max|Bernstein(w)|<1. Serie binomial hasta grado 6:
(1-w)^(-M)=sum(k=0..6,(M)_k*w^k/k!); resto absoluto <=
(M)_7*rho^7*(1-rho)^(-M-7)/7!. Multiplicar por el recinto de
Cj*(1-c/VJ)^(-M), incluyendo su incertidumbre. Encima del knee, la
capacitancia de agotamiento es afín en v con el Ck y denominador vigentes.
La difusión usa Taylor6 de exp(v/emisión) y resto exponencial heredado.
Todas las potencias y exponenciales se encierran con los helpers congelados.

Multiplicar el polinomio C por v' y restar Qpol' antes de acotar. Su resto
es resto_C * max|v'|; v' lleva 1/duración. Sellar esas diferencias en los
nodos de Q25/Q15, cancelarlas con el residual polinómico anterior y sólo
entonces redondear coeficientes y aplicar Bernstein. Grado final <=20.
Las contribuciones de esos nodos se consultan con un grafo filtrado que
conserva cada dispositivo conectado a ellos; no cambia la topología original.
Los nodos ajenos conservan sus certificados anteriores sin recalcularlos.

Dentro de cada bracket se usa un recinto puntual rectangular de C*v'-Qpol',
con C monótona continua. Se conservan su ancho y contribución L1. No usar
el cambio firmado de carga como cota de integral absoluta ni inventar raíz.
Las ocho celdas se cortan además en los límites de piezas/brackets. El
recinto final es siempre la intersección con el recinto anterior de la celda.
Una intersección vacía falla: no elegir un método por resultado favorable.

Cota puntual y L1 (C) se guardan con sus valores brutos y finales. Se comprueba
no crecimiento, cobertura completa del soporte, compatibilidad con cotas
inferiores heredadas y casos bajo el umbral binary64 de 10 pA. Los balances
firmados y las medias anteriores no se recalculan ni se reinterpretan.

Regresiones: binomial frente a serie independiente/M=0/M=1 y ambas piezas;
capacitancia y tasas frente a Decimal200/120; grafo filtrado frente a corriente
completa en nodos activos; todos los recintos, ocho replays y bracket mixto;
fuentes, bytes, recibos completos y corpus. Sin cierre de 1 mV global,
estabilidad no lineal, anclaje desde DC, cobertura temporal global, física,
voz completa, audio ni deadline. El certificado pertenece al interpolante.
