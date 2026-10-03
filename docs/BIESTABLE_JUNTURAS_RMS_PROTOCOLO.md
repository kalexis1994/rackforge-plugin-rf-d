# Cancelaciones firmadas del grupo de junturas

## Norma declarada antes de medir

Se conservan las seis particiones físicas, pesos W, 25 memorias, 94 nodos,
ocho intervalos no contiguos y ocho celdas por intervalo. Sólo cambia la
norma del bloque de cuatro junturas Q25/Q15: uJ=||WJ*eJ||2/2, RMS ponderada.
Los otros cinco bloques mantienen máximo ponderado. Las coordenadas del
descriptor y sus escalas sintéticas no cambian; no se altera el motor.

RMS<=infinito permite mantener el mismo anclaje desconocido de referencia,
||W*e(0)||infinito: su vector de coeficientes iniciales sigue siendo unos.
La desigualdad inversa infinito<=2*RMS requiere cambiar las conversiones.
No comparar directamente coeficientes referidos a normas distintas sin ello.

## Diagonal y acoplamientos

Sobre las mismas inversas ideales encerradas, BJ=-WJ*Hinv_JJ*WJ^-1.
Sumar primero los intervalos firmados Sij=(Bij+Bji)/2. La medida
logarítmica euclídea es lambda_max(S); se acota mediante Gershgorin:
mu2_superior=max_i(Sii_superior+sum(j!=i) max_abs(Sij)).
Esta cota puede ser conservadora y no tiene que mejorar mu_infinito.
No se intersectan cotas de medidas logarítmicas de normas diferentes.
Archivar S por entrada y ambas diagonales, sin ajustar pesos al resultado.

Para recibir J desde un bloque infinito b, acotar cada fila por suma
de magnitudes, tomar la raíz de la suma de cuadrados de esas cuatro
cotas y dividir por 2. Para enviar J hacia un bloque infinito a,
tomar el máximo de la norma euclídea de cada fila ponderada y multiplicar
por 2. Estas cotas son normas inducidas superiores; no borrar signos de
los términos internos antes de formar la parte simétrica.

El L1 de forzamiento de J suma, por columna, la norma euclídea de las
cuatro filas de W*Hinv, dividida por 2, por el presupuesto L1 correspondiente.
No sustituir integral de norma por norma de integrales firmadas.
La conversión del bloque J a cada nodo usa 2*norma2 de su fila Hinv/W.
Los otros grupos y el término algebraico puntual permanecen iguales.

Las raíces usan isqrt del entero floor(x*2^512). Los extremos son
k/2^256 y (k+1)/2^256, coincidentes sólo si el primero al cuadrado es x.
Conservar cero exacto; rechazar x negativo. Cada norma y conversión
incluye el extremo superior racional, sin sqrt de coma flotante.

## Propagación y límites

La matriz de comparación sigue siendo Metzler; se reutilizan los núcleos
de extremo/pico exteriores, con 32 términos, 256 bits y dominio 4096.
El forzamiento nuevo sigue usando el núcleo de pico. No se cambia la
partición temporal ni se unen ventanas. Se archivan todas las comparaciones
con el bloque anterior, incluso si RMS empeora alguna ventana o coeficiente.
No hay intersección retrospectiva ni solución nueva del circuito.

La desigualdad pertenece al tangente ideal variable conocido. Anclaje/DC,
restos N_I/N_Q, recorrido completo, parámetros físicos, audio y deadline
siguen pendientes. Las inversas binary64 rechazadas conservan sus gates;
1 mV global sigue abierto. Menor diagonal interna no implica menor cota
nodal, contracción del circuito real ni fidelidad sonora.

Regresiones: raíz isqrt frente a desigualdades racionales y testigo Decimal;
rotación antisimétrica y parte simétrica intervalar; conversions y anclaje
RMS/infinito; columnas de forzamiento disjunto; reproducción de las 64
inversas, métricas y propagaciones; fuentes, bytes y corpus ampliado.
