# Inversa estructurada y propagación por celdas: protocolo

Se declara antes de medir sobre las 64 celdas ya certificadas: ocho intervalos,
cuatro ventanas, subdivisiones 2/4 e índice 31. Los pesos y todos los parámetros,
particiones, datos y gates anteriores quedan intactos. Cero nuevos solves.

## Primer término de Neumann y resto por fila

Para E=I-D*X*H(t)*D^-1, Y=D*X y q=||E||inf<1:
D*H(t)^-1=Y+E*Y+sum(k>=2) E^k*Y.
Si r_i encierra la suma absoluta de la fila i de E y p_j=max_k |Y_kj|,
el resto de cada entrada está acotado por r_i*q/(1-q)*p_j.
El primer producto E*Y usa recintos firmados, conservando cancelaciones.
Las entradas de E y Y son diádicas: denominadores comunes por matriz y columna
permiten sumas enteras exactas sin redondeo de producto. Se guardan hashes
canónicos de los recintos brutos y finales; todos se reconstruyen desde
las matrices E, X, D congeladas y este helper, sin nuevos solves.

La intersección siempre declarada usa el recinto de primer orden, el recinto
por fila X±r_i/(1-q)*p_j/D_i y el recinto global anterior X±Q/(1-Q)*p_j/D_i.
Q es el máximo q de las ocho celdas. Una intersección vacía falla; no seleccionar
un método favorable. Archivar q, r_i, ceros, entradas estrechadas y hashes.

## Forzamiento distribuido por las celdas existentes

Las 94 corrientes usan los recintos rectangulares previos por celda; en los
cuatro nodos activos se sustituyen por los segmentos correlacionados previos.
Comprobar que sus recortes cubren cada celda sin huecos ni solapamientos.
L1 suma duración*ancho*máximo absoluto por segmento. No usar balances firmados.
Las 21 restricciones lineales usan Bernstein de sus polinomios en cada celda;
las cuatro junturas mantienen Q(v) y defecto constitutivo cero del diagnóstico.
Se comprueba que la suma por celda no exceda cada presupuesto global anterior.

Los recintos asimétricos de inversa dan muW, norma integrada del forzamiento,
||L W^-1||inf y forzamiento puntual. Los pesos permanecen constantes en todo
el intervalo. No intercambiar máximo e integral del forzamiento.

## Composición contigua y anclaje

Para cada celda de duración h y mu superior, Gend=exp(mu*h) y
Gpeak=exp(max(mu,0)*h). Con anclaje A y término forzado F entrantes:
Aend=Gend*A; Fend=Gend*F+Gpeak*presupuesto_L1.
Apeak=Gpeak*A; Fpeak=Gpeak*(F+presupuesto_L1).
El voltaje usa el máximo entre celdas de L*Apeak y L*Fpeak+forzamiento_puntual,
conservando coeficientes separados de anclaje desconocido. No sustituir el
máximo interior por el valor final; mu negativa puede contraer el endpoint
sin reducir una inyección tardía ni el máximo inicial. Exponenciales racionales
exteriores heredadas, dominio |mu*h|<=4096, sin clipping ni fallback.

Las ocho celdas son contiguas dentro de cada intervalo. Los ocho intervalos
seleccionados no lo son y no se encadenan entre sí. Esta propagación corresponde
al tangente ideal sobre el interpolante conocido. N_I/N_Q, anclaje, recorrido
completo y fidelidad física siguen pendientes; 1 mV global permanece abierto.

Regresiones: producto diádico frente a Fraction independiente, Neumann y resto
por fila con inversas racionales conocidas, intersecciones y guards, inyecciones
disjuntas, contracción endpoint versus máximo interior, continuidad, todos los
64 replays, repartición y cobertura, fuentes/bytes/corpus. Ningún mapa binary64
rechazado se admite y el motor de sonido no cambia.
