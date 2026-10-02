# Integral acotada del residual reconstruido: protocolo

Se declara antes de medir: mismos 496 últimos intervalos y un soporte
mixto de Gauss; trayectoria, parámetros, gates y fuentes anteriores intactos.
Cero solves nuevos. La memoria de este ensayo es Q polinómica almacenada,
no Q(v) constitutiva. El knee no afecta la ley estática, suave, integrada aquí.

Todas las constantes binary64 y polinomios se elevan a Fraction exacto.
La parte resistiva se integra exactamente. Cada término Ebers-Moll/Shockley
se expresa como Is*(exp(P(u))-1) con P cúbico. Se transforma a [0,1],
c=P(1/2), delta=P-c y rho=max(abs(Bernstein(delta))). Se integra exactamente
la suma de Taylor de exp(delta) hasta grado 12. Su resto absoluto integrado
es <=exp(c+rho)*rho^13/13!, multiplicado por ancho, h e Is y luego por
los coeficientes terminales. No se introduce un supuesto sobre el signo.
El máximo Bernstein de P debe cumplir el dominio heredado <=45.

exp racional: 256 bits fraccionarios, redondeo externo entero en cada paso.
Para argumento positivo se reduce por potencias de dos a y<=1 y se suman
64 términos; la cola es <=2 veces el primer término omitido, pues todas
las razones posteriores son <1/2. Se deshace la reducción por cuadrados
con redondeo externo. Para argumento negativo se usa el recinto recíproco.
Rango declarado |argumento|<=4096; salir de él es error, nunca clipping.
No se usa coincidencia Decimal80/100 como certificado del redondeo.

Los extremos racionales se sellan con signos conservadores a 94 nodos.
Delta Q polinómica y su incidencia se calculan exactamente: integral R =
integral f(x)+A*Delta Q. Dividir por duración positiva acota el residual medio.
Se clasifica <10 pA, >=10 pA o inconcluso con el umbral binary64 heredado.
|integral R_j| aporta sólo una cota INFERIOR de integral |R_j|; no una
cota superior ni una conversión a error de voltaje. No sumar intervalos
seleccionados para fingir cobertura desde DC.

Gauss16 guardado se trata como número racional Decimal exacto: distancia
máxima a ambos extremos del recinto contra 1e-30 C +1e-8*abs(Gauss16).
Que el número redondeado esté fuera de un recinto muy estrecho no implica
fallo de ese gate: se conserva ese dato y la distancia certificada.
La cota pertenece a la ley ideal condicional con coeficientes elevados,
no certifica cada operación del evaluador Decimal ni estados físicos.

Regresiones: exp con testigos independientes y extremos; integrales de
exponencial afín de fórmula cerrada, constantes y cúbicas; signos de sellos,
conservación exacta, todos los recintos/gates, replays seleccionados y SHA.
Recibos preservan cualquier fallo completo. Continúan abiertos 1 mV global,
memoria constitutiva acotada, cobertura completa, estabilidad no lineal,
física, voz completa, audio y deadline.
