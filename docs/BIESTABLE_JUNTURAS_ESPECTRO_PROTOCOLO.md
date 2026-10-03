# Certificado espectral racional de las junturas RMS

## Variante previa a medición

Se mantienen la norma RMS de cuatro junturas, los otros cinco bloques,
pesos, referencia de anclaje, acoplamientos, forzamiento, conversiones nodales
y ocho celdas de cada uno de los ocho intervalos seleccionados. Sólo cambia
la cota superior de mu2 en la diagonal de la comparación de junturas.
Se leen las partes simétricas encerradas y validadas del bloque anterior;
no se resuelven inversas del circuito ni trayectorias nuevas.

Para el recinto simétrico S, definir centro C=(lo+hi)/2 y radio R=(hi-lo)/2.
Para toda matriz S real de ese recinto, ||S-C||2<=delta=max_i sum_j Rij,
porque R es simétrica. Weyl da lambda_max(C)-delta<=lambda_max(S)
<=lambda_max(C)+delta. No certificar sólo el centro ni borrar el radio.

## Bisección exacta y prueba de positividad

Fijar 32 bisecciones racionales, sin ajuste tras observar resultados.
El límite inferior inicial es max Cii por Rayleigh. El superior inicial
es Gershgorin(C)+1/s; el incremento estricto es margen numérico de prueba,
no constante audible ni cambio de tolerancia del circuito.
Para cada alpha, evaluar alpha*I-C mediante LDLᵀ exacto sin pivoteo.
Todos los pivotes positivos certifican positividad definida y alpha>lambda_max(C).
Un pivote <=0, incluido cero, rechaza positividad estricta y deja
alpha<=lambda_max(C). No dividir por cero ni usar tolerancia de autovalores.

El superior final conserva su L y pivotes positivos; cada consulta conserva
alpha, resultado, primer pivote rechazado e identidad SHA de todos los
pivotes calculados. Centro y fuente congelados permiten reconstruir las
33 consultas por celda, incluido el seed, y ambas ramas de la bisección.
Agregar delta al superior y restarlo al inferior para el recinto completo.
Intersectar siempre el superior resultante con Gershgorin(S) anterior:
ambos acotan la misma mu2, norma y coordenadas. Conservar bruto y final.
Esto no permite intersectar medidas de normas distintas.

## Propagación y alcance

Reemplazar sólo M_JJ por el superior final. Reutilizar la política de
núcleos positivos exteriores de extremo/pico y el forzamiento tardío.
Archivar las referencias de cada celda anterior y los certificados nuevos;
los componentes sin cambios se reconstruyen por índice y SHA, sin duplicarlos.
Conservar todas las comparaciones nodales; un cambio del recinto de matriz
no obliga a que las aproximaciones exteriores de núcleos mejoren en todo caso.

Un límite inferior positivo de mu2 indica crecimiento de alguna dirección
en esa norma instantánea; no demuestra crecimiento observado de la trayectoria,
inestabilidad del Moog ni error no lineal. Los ocho intervalos son no contiguos.
Restos N_I/N_Q, anclaje/DC, recorrido completo, fidelidad física, audio y
deadline siguen pendientes. Los gates binary64 rechazados permanecen iguales;
1 mV global sigue abierto.

Regresiones: factorización y reconstrucción racional, pivote nulo e indefinido,
matrices de autovalores conocidos por similitud ortogonal racional, vértices
simétricos de un recinto pequeño para contrastar radio, clasificación y signos,
reconstrucción de todas las consultas de las 64 celdas y propagaciones,
componentes RMS intactos, fuentes, almacenamiento y corpus ampliado.
