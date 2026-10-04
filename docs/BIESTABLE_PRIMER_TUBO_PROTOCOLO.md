# Protocolo: primer interpolante y comparación no lineal en tubo

Modelo nominal documental y parámetros sintéticos idénticos. Leer origen
post-KEY publicado y primer endpoint real del prefijo; duración exacta
195,3125 ns, levantada del reloj binary64. Ninguna solución no lineal nueva.

## Reconstrucción de dos estados y anclaje

Interpolar linealmente los 94 potenciales y 21 coordenadas de carga lineal
entre los dos estados high+low reales. En cuatro junturas usar Q(v_affine)/S
como memoria constitutiva, no una recta entre Q publicadas. Sus tasas son
C(v)*v'; cuatro polinomios cero son placeholders internos para sellar una
sola vez esa corriente. No representan cargas nulas. Registrar soporte,
polinomios y discrepancia de memoria constitutiva con los valores almacenados.

Las restricciones lineales d=yhat-voltage+R*C*yhat' son polinomios exactos;
las restricciones de juntura son cero por definición. El anclaje de carga
ideal DC se compara con toda yhat(0), incluyendo el desajuste constitutivo
post-publicación. Fijar pesos idénticos a los del DC: lineales uno y junturas
1/8, 1/4, 1/256, 1/512. La conversión de esa norma es identidad (factor uno),
sin reutilizar métricas de ventanas históricas. Mantener la cota nodal del
evento publicado para demostrar que el estado inicial está dentro del tubo.

## Recintos, residual y precondicionadores

Ocho celdas iguales en tiempo normalizado. Tres radios de error potencial
1e-7, 1e-6 y 1e-5 V; ejecutar todos, elegir primer radio aceptado en ese
orden. Escalas de descriptor: potencial uno, tasa 2^-30 s (diádica). Para cada celda
un precondicionador binary64 candidato de H119 en el centro afín, calculado
una sola vez; reutilizarlo en todos los radios. No admitirlo en audio ni
tratarlo como inversa exacta. La prueba exterior incluye su defecto completo.

Encerrar cada exponente/capacitancia sobre la celda más un error de potencial
±radio, con radios de diferencia y dominio <=45. Sellar antes de encerrar.
Este recinto cubre además el Jacobiano medio entre reconstrucción y solución
ideal: los coeficientes medios pertenecen a los mismos intervalos. Con q<1,
encerrar la inversa ideal por Neumann de primer orden, cola por fila y
columnas completas. Conservar matrices, q, hashes y rechazos.

Residual r=Fstatic(xhat)+M*yhat' con juntas constitutivas: Taylor de grado
seis de exponenciales, restos exteriores y ocho subceldas internas por celda,
según el helper constitutivo existente. Encerrar corrientes C(v)*v' por
monotonía y sellar conservación. d lineal por Bernstein exacto. Consultas
Decimal80/100 en u=0,1/4,1/2,3/4,1 como diagnóstico, sin promoverlas a
cota de intervalo ni imponer gates de residual discreto al interpolante.

## Comparación y cierre del tubo

Para e=yideal-yhat y delta_v=xideal-xhat, el teorema del valor medio da
Hbar*(delta_v,e')=-(r,d+e). Por tanto e'=A*e+b con A=-Hbar^-1 en el bloque
de constraints, aunque A dependa de la solución. Acotar norma logarítmica
ponderada con diagonal firmada, forzamiento integrado por máximos de columna,
ganancia nodal desde memoria y término nodal directo. Propagar las ocho
celdas con crecimiento firmado y picos, anclaje conocido y resto ya incluido
en el recinto medio; no usar sólo la linealización en el interpolante.

Aceptar únicamente si todos los recintos son invertibles y la cota nodal
completa permanece estrictamente por debajo del radio, junto con el error
inicial del evento. Continuación: la raíz inicial existe; H invertible da
campo implícito local, corrientes/cargas/tasas son acotadas dentro del tubo,
y una cota estricta impide escape en tiempo finito. Si falla q, dominio,
crecimiento soportado o inclusión, conservar rechazo y duración certificada
cero. No asumir el tubo para afirmar una cota que lo excede.

Este cierre, si pasa, cubre sólo el primer intervalo a t=0+. Global 1 mV,
cobertura completa, parámetros físicos, voz y deadline permanecen abiertos.
Congelar datos/tests/validator antes de validar; conservar todos los intentos
y ampliar el corpus sin modificar fuentes o informes históricos.
