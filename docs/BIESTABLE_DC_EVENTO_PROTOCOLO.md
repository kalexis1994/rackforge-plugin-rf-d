# Protocolo: recinto de DC y dominio del evento KEY

Congelar helper, productor y protocolo antes de medir. Reutilizar el DC
compensado KEY=0 del reloj completo y los parámetros binarios nominales
sintéticos existentes. No resolver otro DC ni ajustar valores. Construir
el grafo estático independiente de 94 nodos y su Jacobiano Decimal100 en
el punto publicado, y un único precondicionador binary64 mediante inversa
NumPy. Este candidato offline no queda admitido en el motor.

## Prueba de raíz local

Levantar exactamente los potenciales high+low y todos los coeficientes
binarios. F es la ley estática ideal Ebers–Moll/Shockley y resistiva de ese
grafo. Mantener dominio de exponentes <=45 y los recintos exteriores
racionales de 256 bits ya validados. Precondicionar cada sello de corriente
y Jacobiano antes de encerrar su única exponencial, preservando cancelaciones.

Para T(v)=v-X*F(v), punto x y caja infinita de radio r, acotar
D=I-X*J(caja), eta_i=abs((X*F(x))_i), q_i=sum_j abs(D_ij), q=max_i q_i.
Si q<1 y eta_i+r*q_i<r en todas las filas, T es contracción y transforma
la caja en sí misma: existe una raíz única local. X es no singular porque
X*J es invertible bajo esa misma prueba; un punto fijo implica F=0.
El error posterior respecto a x es <=max_i eta_i/(1-q).
Esta prueba no elige una rama global ni demuestra fidelidad física.

Medir los cuatro radios fijados: 1/10^9, 1/10^8, 1/10^7 y 1/10^6 V.
Preservar todos los resultados; el caso primario es el primero aceptado
en ese orden, sin búsquedas adicionales. Guardar defecto intervalar,
sumas, imagen, exponentes, precondicionador y prueba posterior.
Si ninguno pasa, conservar el fracaso y no publicar una cota de anclaje.

## Publicación de memoria y evento

Desde el recinto posterior primario, reconstruir cargas ideales: 21 ramas
lineales y cuatro junturas monótonas. Contrastar con las memorias publicadas
(pares high+low y QBE/QBC). Guardar error de carga, error de coordenada y
norma infinita ponderada inicial. Escalas lineales C y S=1e-12 C/V de junturas
son las ya existentes. Fijar Wlineal=1 y Wjunction=dyadic_floor(S/Cupper(x)),
con la capacitancia exterior en el punto. Esta norma inicial debe convertirse
explícitamente si el siguiente tramo usa otros pesos o métricas.

Auditar los elementos que conectan KEY. Para CR10, levantar n*vt y el
voltaje de su cátodo en todo el recinto de DC. Evaluar el exponente
con KEYpost=10 manteniendo voltajes del DC: si el inferior excede 45,
la hipótesis de continuidad de todos los potenciales es inadmisible en
el dominio congelado. Cuantificar Vcathode_post>=KEYpost-45*n*vt y
el salto mínimo respecto al recinto previo. Comprobar que ese nodo no
tiene puertos de las 25 memorias modeladas. No confundir ausencia de
capacitancia modelada con identificación física de todas sus parasíticas.

Esta auditoría no resuelve el estado consistente a t=0+, no evalúa la
exponencial fuera de dominio y no mueve/clipea el límite 45. El DC KEY=0
puede tener error acotado mientras el anclaje posterior sigue abierto.
La continuidad de cargas requiere evento con corrientes acotadas y una
resolución algebraica posterior explícita antes de interpolar el arranque.

## Regresiones y alcance

Probar la inclusión contractiva en familias lineales y no lineales con
raíz conocida, incluyendo q>=1 e imagen fuera de caja. Contrastar sellos
precondicionados contra productos puntuales independientes y Decimal80/100;
verificar conservaciones de corriente, guards, todos los radios y los
recintos de carga por monotonía. Reconstruir desigualdad del evento, fuentes,
bytes y destinos. Congelar datos y tests antes de validar, preservar intentos.

No cambiar gates de 10 pA, 10 nV, 10 fV, backward 1e-10 o 1 mV global.
La prueba de existencia es independiente de admisión de álgebra binary64.
El error DC es numérico del modelo nominal sintético. No se certifican
estado post-KEY, trayectoria, resto no lineal temporal, física, audio o deadline.
