# Protocolo: radio balanceado en la misma base diagonal

Congelar helper, productor y protocolo antes de medir. Reutilizar bases D,
centros y radios del certificado dirigido, los seis candidatos aceptados,
dos rechazos de reset, métricas, conversiones, forzamiento y anclaje.
No calcular otra P, transformada o inversa del circuito; sólo acotar el radio
en la base ya validada. Evaluar los ocho casos y preservar todos los resultados.

## Pesos fijados sin fitting

De cada Di>0 calcular sqrt(1/Di) con las raíces racionales exteriores
anteriores de 256 bits. Gamma_i=ceil_40(sqrt_upper_256(1/Di)). Conservar
bracket, valor exterior, política y SHA de la base. Gamma es estrictamente
positivo y constante en las ocho celdas del intervalo. No buscar pesos
alternativos por ventana o resultado. Estos pesos actúan sólo en la prueba
de perturbación; W, P, norma, escala rho y normalización de anclaje no cambian.

## Majorante ponderado

Para Delta simétrica y |Delta_ij|<=Qij, definir
rGamma_i=sum_j Qij*Gamma_j/Gamma_i. La desigualdad
2|xi*xj|<=Gamma_j/Gamma_i*xi²+Gamma_i/Gamma_j*xj²
prueba Delta<=diag(rGamma). Incluye radios diagonales y todos los términos
pequeños. Un factor positivo común de Gamma no cambia el majorante.
La elección ideal Gamma_i=1/sqrt(Di) balancearía la perturbación respecto
a la energía diagonal; la elección diádica fijada conserva validez sin
tratar una raíz flotante como prueba ni afirmar optimalidad.

U=C+diag(rGamma); alpha*D-U positiva definida certifica la misma tasa
en P. Mantener seeds Rayleigh/Gershgorin y 32 bisecciones racionales del
corte anterior, guard de pivote cero y todas las consultas y factores.
La tasa tiene unidades 1/s tras multiplicar por rho. El inferior del
bracket pertenece al problema auxiliar U, no a la tasa real de la familia.

Siempre intersectar el superior bruto con el anterior dirigido en la misma
métrica, conservando bruto, previo y final. No mezclar normas ni refijar
conversiones. Cambiar sólo M_JJ y reutilizar lo demás por índice y SHA.
Guardar las seis propagaciones calculadas, los dos rechazos y la comparación
completa; una tasa menor no autoriza ocultar un resultado nodal desfavorable.

## Regresiones y alcance

Verificar raíces y redondeo exteriores, gamma positivo, invariancia por
factor común, radios simétricos y pesos no válidos. Contrastar el majorante
ponderado en las 1.024 matrices vértice de una caja simétrica 4×4, por
menores principales exactos. Una familia con D dispar debe mostrar que
el radio balanceado puede certificar contracción que el radio sin balance
no certifica. Replay de todas las consultas, sólo M_JJ cambiado, mismos
forzamientos, ganancias, anclaje, propagaciones, fuentes y bytes.
Congelar datos y tests antes de validar; conservar todos los intentos.

No se certifica el anclaje real, restos no lineales, circuito acoplado,
recorrido completo de intervalos no contiguos o conversión entre P distintas.
1 mV global, física, audio y deadline siguen abiertos. Un superior positivo
no es prueba de crecimiento real o inestabilidad; un inferior auxiliar
positivo tampoco es una cota inferior de error de la trayectoria.
