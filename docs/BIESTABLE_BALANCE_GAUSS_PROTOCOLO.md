# Balance integrado: variante Gauss declarada

Declarada el 2 de octubre de 2026 después del contraste Simpson 32/64:
125/496 intervalos pasan ese contraste y 371 fallan. El informe, las
cuadraturas y el primer fallo de regresión se conservan. No se relajan
1e-30 absoluto +1e-8 relativo ni 10 pA, ni se modifica la trayectoria.

Se usan Gauss-Legendre **4/8/16 puntos**, con contraste final **8/16**,
sobre los mismos 496 intervalos y soporte mixto. La composición Q(v),
puentes constitutivos, incidencia y certificados de dominio se mantienen.
Es una variante de integración del diagnóstico, no del sinte.

Las raíces de Legendre se calculan con Newton escalar a Decimal80/100,
semilla coseno binary64, presupuesto 32 y corrección <10^(-precision+8).
Se conservan nodos, pesos e iteraciones, y momentos hasta grado 2*n-1
con los gates heredados. Son **28 raíces escalares**, cero solves nuevos
del circuito. Toda preparación se hace dentro de su precisión explícita.

Se contrastan la integral estática y la carga de las piezas/puentes frente
a extremos constitutivos. Se guarda también Simpson64 frente a Gauss16
con todos sus incumplimientos. Coincidencia de cuadraturas no acota el
resto ni el error de reconstrucción; no se admite error global de voltaje.

Regresiones: reglas/momentos, continuidad y puentes heredados, todos los
balances/incidencias, 24 comparaciones con Gauss4 de fórmula cerrada y
replays seleccionados a ambas precisiones, fuentes/bytes y alcance.
Los fallos iniciales se preservan por recibo/fuente, incluidos el testigo
Decimal 0^0 inválido y la suposición de que Simpson64 pasaría el contraste.
El testigo se corrige y el informe Simpson se valida como control negativo;
sus gates numéricos fallidos permanecen iguales.

Sin constantes audibles nuevas, cambios de raíz/historial/controlador,
física admitida, audio, deadline o cota temporal global de 1 mV.
