# Comparación dirigida entre bloques de memoria

## Variante fijada antes de medir

Se reutilizan las 64 inversas ideales encerradas y los residuales por celda
del bloque anterior. No se resuelven matrices ni trayectorias nuevas.
Se conservan índices, ocho celdas, pesos constantes y todos los gates.
La partición procede de las ramas del descriptor documental CA3046:
17 memorias de audio (0..16), C10 (17), C2 (18), C4 (19), C7 (20) y
las cuatro cargas de juntura Q25/Q15 (21..24). No se ajusta a resultados.
Las coordenadas de carga normalizadas conservan sus escalas sintéticas.

Para cada bloque a, u_a=max(i en a)|w_i e_yi|. B=-Hinv_memoria.
La desigualdad de Dini para el tangente ideal es u'<=M*u+g, con
M_aa=max(i en a)[Bii_superior+sum(j en a,j!=i) wi/wj*|Bij|sup],
M_ab=max(i en a)sum(j en b)wi/wj*|Bij|sup para a!=b.
M es Metzler: los términos diagonales conservan signo y los acoplamientos
entre bloques son no negativos y dirigidos. No se usa módulo en la diagonal.

La norma integrada del forzamiento de cada bloque se acota sumando,
por columna del residual y restricción, su máximo entre filas del bloque
multiplicado por el L1 correspondiente. No usar máximo de integrales por
fila. La conversión a voltaje conserva por cada nodo y bloque la suma
|Hinv_nodo,memoria|/w, además del residual algebraico puntual del nodo.

## Núcleos positivos exteriores

Para una celda de duración h, elegir a=max(0,-min Mii), C=M+aI>=0.
Fijar dominio max(||C*h||inf,a*h)<=4096. Escalar por potencias de dos
hasta que ambos sean <=1/2, sin refinamiento en función de resultados.
Redondear exteriormente a 256 bits. Evaluar exp(C*delta) con 32 términos
positivos y cola rho^33/33!/(1-rho/34), con rho=||C*delta||inf<=1
después del redondeo. El soporte transitivo conserva ceros exactos.
Multiplicar por el recinto superior racional de exp(-a*delta).
Cada producto matricial diádico se calcula exactamente con enteros antes
del redondeo exterior. No usar expm de coma flotante en el certificado.

El recinto de pico inicial es exp(Mpositivo*delta), donde sólo se elimina
la parte negativa de la diagonal. Acota exp(M*t) para 0<=t<=delta.
Al duplicar una celda, E2=E*E y P2=max_entrada(P,P*E).
Conservar E y P, desplazamiento, escala, cola y hashes. Esta recurrencia
acota todos los tiempos, no sólo los extremos ni muestras temporales.

Con vectores entrantes de anclaje A y forzamiento F, y L1 por bloque b:
Aend=E*A; Fend=E*F+P*b; Apeak=P*A; Fpeak=P*(F+b).
El forzamiento puede concentrarse al final, por eso usa el núcleo de pico.
Inicializar A con unos expresa un anclaje ponderado desconocido común,
no error inicial nulo. Inicializar F con ceros aísla el término forzado.
Conservar cada nodo al transformar los picos y luego tomar el máximo.

## Alcance y refutaciones

Archivar comparación completa con las cotas escalares anteriores; no
intersectar resultados ni ajustar bloques tras medir. La mejora puede no
ocurrir. Las ocho celdas son contiguas dentro de cada intervalo, pero los
ocho intervalos seleccionados no se encadenan. N_I/N_Q, DC, anclaje y
recorrido completo siguen pendientes. No se admite audio, física, deadline
ni una inversa binary64 anteriormente rechazada. 1 mV global sigue abierto.

Regresiones: cascada triangular con exponencial conocida, pico interior,
contracción y forzamiento tardío; métricas por bloques y máximos de columnas
con ejemplo racional independiente; guard de partición y dominio;
reconstrucción de las 64 matrices, núcleos y presupuestos; fuentes y
almacenamiento canónico; corpus ampliado y destinos de archivo distintos.
