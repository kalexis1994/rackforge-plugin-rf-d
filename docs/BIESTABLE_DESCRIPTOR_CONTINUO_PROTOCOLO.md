# Descriptor continuo: protocolo

Se declara antes de medir: ocho consultas, índice 31 y u=1/2 en las cuatro
ventanas y subdivisiones 2/4 congeladas. No se publican estados nuevos.
Las 21 cargas lineales usan escala C; QBE/QBC conservan 1 pF exclusivamente
como coordenada. Las incidencias incluyen polaridad y terminales fijos.
No identificar las memorias BDF hipotéticas con estados continuos libres.

## Ecuaciones y signos

Para las cargas lineales y=Q/C. La rama verifica
`y-Gv+R*C*y'=d`, incluyendo el voltaje fijo en Gv. Para las cuatro
junturas y=Q(v)/S y P=(Cj/S)*G. El residual nodal es
`r=I(v)+A*S*y'`. Se sustituye únicamente en este diagnóstico la carga
polinómica de juntura por Q(vpol): su d es cero y su residual es precisamente
el de tasas constitutivas correlacionadas. Las 21 restricciones conservan
el interpolante y sus certificados anteriores. Las fuentes son constantes.

Para error exacto menos reconstrucción:
`H*[e_v; e_y']=[-r-N_I; -e_y-d+N_Q/S]`,
`H=[Jstatic, A*S; -P, diag(R*C)]`.
N_I es el resto de I y N_Q el resto de Q tras quitar sus tangentes;
N_Q=0 en ramas lineales. C10 mantiene R=25,5 kΩ y C=10 µF.
No usar J de Newton BDF, que incorpora dt, como descriptor continuo.

Si H es invertible, su inversa separa voltaje, tasa, memoria y forzamiento.
La independencia de incidencias se comprueba con rango racional; el rango
por sí solo no prueba invertibilidad de H, índice ni estabilidad no lineal.
Se contrastan las matrices Decimal80/100 redondeadas a binary64.
Ese acuerdo no encierra la derivada transcendental exacta.

## Certificado de la matriz levantada

Se resuelve H X=I con el solver equilibrado existente, conservando ambos
backward gates de 1e-10 y sus ocho refinamientos máximos. Todo fallo se guarda.
Con D igual a sus escalas de columnas positivas:
`E=I-D*X*H*D^-1`, `q=||E||inf`, calculados como racionales exactos desde
los binary64. q<1 prueba inversa única de esa H levantada. La serie de Neumann
acota cada entrada por
`|Hinv_ij-X_ij| <= q/(1-q)*max_k |D_k X_kj|/D_i`.
Guardar H, X, escalas, sumas de fila, q y picos por columna. No promoverlo
a certificado de H ideal ni a recinto de matrices en todo el intervalo.

## Presupuesto congelado con memoria

Sólo para la ODE lineal constante asociada a esa H:
`e_y'=B e_y+F_r r+F_d d`, con B=-Hinv[94:,94:].
Se acota la medida logarítmica infinito
`mu=max_i(Bii+sum(j!=i)|Bij|)` usando los recintos de inversa.
El presupuesto integrado de forzamiento por fila es
`sum |F_r|*L1(r)+sum |F_d|*L1(d)`; L1(r) está en C y L1(d) en V*s.
La cota uniforme es `exp(max(mu,0)*h)*(error_inicial+presupuesto)`.
El voltaje suma la ganancia de memoria y su forzamiento puntual.
Se guarda el coeficiente del error inicial desconocido y un término con
anclaje cero exclusivamente para el modelo congelado. No asumir anclaje
cero del circuito. Exponencial racional exterior heredada, dominio <=4096;
si se excede se archiva el bloqueo, sin escoger pesos tras medir.

Regresiones: RC racional independiente, signos y resto no lineal manufacturado,
Neumann con perturbación y matriz singular, todas las ocho consultas con
replay de certificado, leyes/incidencias/RC, fuentes y almacenamiento.
El límite verdadero requiere cobertura continua, variación de H, restos no
lineales, anclaje y pesos adecuados. 1 mV global, física, audio y deadline
siguen abiertos. No se califica el resultado congelado como propagación real.
