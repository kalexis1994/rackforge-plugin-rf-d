# Protocolo: generador firmado y modos de junturas

Congelar este protocolo, helper y productor antes de ejecutar. Mantener
CA3046, parámetros sintéticos, pesos, ocho intervalos no contiguos y 64 celdas
del certificado espectral. No cambiar propagación, gates, circuito o audio.

## Construcción exacta

Reconstruir sólo los 16 elementos H_inverse[115:119,115:119] con la misma
fórmula Neumann de primer orden del corpus. El producto E*D*X utiliza sus
119 términos completos, sin truncar el defecto al bloque de junturas.
Conservar cola por fila y ambas intersecciones anteriores. Verificar que
(B+Bᵀ)/2 coincide exactamente con el recinto simétrico ya archivado, donde
B=-W_J H_inverse_JJ W_J^-1 y W es el peso positivo previamente fijado.
No resolver una nueva inversa ni generar trayectoria.

Elegir rho, potencia de dos positiva >=max(1,||B||infinito intervalar),
por una regla determinista. A=B/rho conserva signos de partes reales de
autovalores. El tiempo normalizado es tau=rho*t; rho tiene unidades 1/s.
Formar det(zI-A)=z^4+a1*z^3+a2*z²+a3*z+a4 con suma firmada de todos
los menores principales. Determinantes por permutaciones racionales;
intervalos exactos, sin tolerancia, diagonalización flotante o fitting.

## Certificado Routh

Delta2=a1*a2-a3; Delta3=Delta2*a3-a1²*a4. Primera columna:
[1,a1,Delta2/a1,Delta3/Delta2,a4]. Si a1 o Delta2 incluyen cero,
no dividir y conservar resultado indeterminado. Si cualquier elemento
incluye cero, no asignar conteo. Sólo signos estrictos de todos los
recintos permiten contar cambios: número de raíces Re(z)>0, con
multiplicidad, para toda matriz del recinto. Conteo cero certifica Hurwitz
del bloque congelado; a4<0 también prueba una raíz real positiva por
continuidad del polinomio mónico. No sustituir un resultado indeterminado
con el centro, ni relajar incertidumbre para obtener signos.

Derivación del algoritmo de Routh: [ECE 486, Illinois, Lecture 7](https://courses.physics.illinois.edu/ece486/fa2026/documentation/handbook/lec07.html),
sección Routh–Hurwitz, consultada 2026-10-03. Las fórmulas de grado cuatro
anteriores se obtienen sustituyendo las dos primeras filas en su recurrencia.

## Alcance y regresiones previstas

Archivar B, rho, cinco coeficientes, Delta2/3, columna, signos y bloqueos
para las 64 celdas. Comparar con mu2 anterior, sin modificar ninguna cota.
Estabilidad puntual de matrices congeladas no implica estabilidad de un
sistema variable ni del generador completo de 25 memorias; el bloque
aislado omite acoplamientos. Anclaje, restos no lineales, recorrido completo,
1 mV, fidelidad y admisión de audio/deadline siguen abiertos.

Regresiones: factores de raíces conocidas con 0..4 raíces derechas,
pares complejos, caso estable no normal con mu2 positiva, recintos con
centro estable y vértice inestable, casos singulares sin división por cero,
igualdad del slice con Neumann completo, coeficientes contra determinante
evaluado independientemente y replay de todas las celdas, fuentes y bytes.
Congelar datos y tests antes de validar; preservar todos los intentos.
