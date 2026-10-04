# Protocolo: congruencia racional y radio dirigido en la misma métrica

Congelar helper, productor y protocolo antes de medir. Reutilizar los seis
candidatos positivos, dos rechazos, pesos, norma, normalización del anclaje,
conversiones, forzamiento y salida del bloque cuadrático anterior.
No buscar otra P ni resolver inversas del circuito. Evaluar los ocho casos;
reset conserva el rechazo y no recibe una nueva propagación.

## Base exacta

P=L*D*Lᵀ proviene de la LDLᵀ racional ya archivada del P redondeado.
Exigir identidad exacta con esa fuente. Invertir la triangular unitaria L
por recurrencia racional, R=L^-1, y verificar R*P*Rᵀ=D. Ésta es una
congruencia interna del certificado; no cambia la norma física numérica,
su anclaje o las conversiones publicadas. Mantener rho anterior, en 1/s.

Para B/rho, T=R*(P*B/rho+(B/rho)ᵀ*P)*Rᵀ/2. Antes de acotar,
compilar una sola aparición de cada coeficiente B[k,q]/rho con peso
(D[i]*L[k,i]*R[j,q]+D[j]*L[k,j]*R[i,q])/2.
Así se preservan cancelaciones exactas y no se multiplican recintos
intermedios independientes. Formar una caja simétrica, centro C y radio Q.

## Perturbación dirigida y tasa

Para toda perturbación simétrica Delta con |Delta_ij|<=Qij,
Delta<=diag(r), r_i=sum_j Qij. La desigualdad se deriva de
2|xi*xj|<=xi²+xj² y acota xᵀDelta*x. Por tanto T<=U=C+diag(r).
No reemplazar r por su máximo ni omitir radios pequeños.

alpha*D-U positiva definida implica S<=alpha*P, con
S=(P*B/rho+(B/rho)ᵀ*P)/2, para toda matriz del recinto original.
La tasa final tiene unidades 1/s: rho*alpha. Seed inferior por Rayleigh:
max_i Uii/Di. Seed superior estricto por Gershgorin de D^-1*U:
max_i (Uii+sum_{j!=i}|Uij|)/Di + 1. D^-1*U es similar a una matriz
simétrica. Usar 32 bisecciones racionales y conservar todas las consultas,
factores superiores y pivotes rechazados. Un pivote cero no se divide.
El inferior pertenece al problema auxiliar U, no a la tasa real del recinto.

Siempre intersectar el superior bruto con el anterior isotrópico de la
**misma P, norma, escala y anclaje**, conservando ambos y la selección.
No intersectar con RMS euclídea o infinito. Cambiar sólo M_JJ de la
comparación de seis grupos; reutilizar todo lo demás por índice y SHA.
Propagar con los mismos núcleos de pico/extremo y conservar la comparación
completa, incluso si una mejora de tasa no mejora la cota nodal numérica.

## Pruebas previstas y alcance

Verificar congruencia y norma en vectores racionales, compilación frente
a productos puntuales independientes, preservación de cancelaciones,
radios dirigidos y todas las 1.024 matrices vértice de una caja simétrica
4×4 manufacturada. Contrastar formas cuadráticas y tasas de familias
conocidas, replay de todas las consultas y cambio exclusivo de M_JJ.
Comprobar fuentes, datos canónicos, destinos y conservación de rechazos.
Congelar datos y tests antes de validar; conservar todos los intentos.

Una tasa negativa con P fija certifica contracción del bloque interno
variable cubierto; no del circuito acoplado ni de una trayectoria no lineal.
Los intervalos siguen no contiguos y P no es común entre ellos. Anclaje,
restos, 1 mV global, fidelidad, audio y deadline siguen pendientes.
