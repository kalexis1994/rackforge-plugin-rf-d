# Descriptor ponderado y variación ideal: protocolo

Se declara antes de medir las ocho consultas congeladas del descriptor:
cuatro ventanas, subdivisiones 2/4, índice 31. No hay nuevos solves.
Los resultados y todos los rechazos anteriores son entradas inmutables.

## Pesos constantes por intervalo

Se fija ||y||W=max_i |w_i*y_i|. Las 21 memorias lineales tienen w=1.
En junturas, w es la potencia de dos inferior o igual a S/C del punto medio,
obtenida exactamente de la fila del descriptor binary64 archivado.
Se comprueba w<=S/C<2w. Es una escala local comparable a voltaje; no una
calibración física ni un ajuste para minimizar el resultado. Se congela por
intervalo: no aparece W'W^-1. No extrapolar pesos cambiantes sin ese término.

La medida logarítmica es
muW=max_i(Bii+sum(j!=i) (wi/wj)|Bij|).
El forzamiento integrado usa sumas de máximos de columna de W*Fr y W*Fd.
El voltaje usa ||L*W^-1||inf y su forzamiento puntual. Mantener coeficiente
del anclaje ponderado y también conversión conservadora desde norma sin pesos;
no comparar anclajes de normas distintas como si fueran el mismo error.
El término forzado con anclaje cero es comparable sólo dentro del diagnóstico.

## Matriz ideal en ocho celdas de todo el intervalo

Se divide u=[0,1] en ocho celdas fijas. Cada voltaje cúbico conocido usa rango
Bernstein racional. Se encierran exponenciales y capacitancias con los helpers
racionales exteriores ya congelados. Los coeficientes físicos binary64 se
levantan exactamente, pero todas sus operaciones constitutivas se tratan como
ideales: 1/R, beta, exponenciales, capacitancias, C/S y R*C. Se mantiene el knee
binary64 y denominador de continuación; C es monótona continua y puede
encerrarse con endpoints incluso si la celda cruza el knee.

Para reducir pérdidas de dependencia se precondicionan sellos analíticos de
rango uno antes de encerrar cada coeficiente: X*c y luego su incidencia de
columna. Los sellos BE/BC de Ebers-Moll conservan todos los dispositivos,
polaridad y terminales fijos. La capacitancia de juntura usa su incidencia
orientada. No sumar primero un Jacobiano intervalar nodal que pierda esas
cancelaciones. Cada operación exterior usa diádicos de 256 bits.

Para H_ideal(u), E(u)=I-D*X*H_ideal(u)*D^-1. Se archivan recintos por entrada,
sumas de magnitudes por fila y q superior en cada celda. q<1 prueba la inversa
a lo largo de esa celda, incluyendo incertidumbre de redondeo de H del punto
medio frente a la matriz ideal. Si cualquier celda tiene q>=1, se conserva
el bloqueo de ese intervalo sin refinar ni cambiar pesos después de medir.

Si las ocho celdas contraen, el q máximo produce recintos uniformes por entrada
para H_ideal(u)^-1 alrededor de X con la misma prueba Neumann anterior.
La medida logarítmica y máximos de columna uniformes permiten Gronwall para
la ODE tangente con coeficientes variables a lo largo del interpolante conocido.
No son una cota del DAE no lineal: N_I/N_Q, anclaje y cobertura faltan todavía.
No se promueve el mapa binary64 rechazado ni se relajan sus gates.

Regresiones: pesos diádicos/domino, similitud y presupuesto RC independientes,
contraejemplo de pesos variables, sellos precondicionados frente a matrices
Decimal120, extremos e interiores de celdas, prueba temporal manufacturada,
recintos, cobertura y replay, fuentes/bytes y corpus. Cero solves nuevos de
circuito o matrices. 1 mV global, física, voz completa, audio y deadline abiertos.
