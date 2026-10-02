# Reconstrucción constitutiva y balance integrado: protocolo

Declarado el 2 de octubre de 2026. Se mantienen el circuito condicional,
parámetros sintéticos, gates e informes anteriores. No hay solves nuevos,
cambios de controlador, reseed ni constantes audibles añadidas. Fuentes
y topología son las identificadas por SHA en la reconstrucción interior.

## Cobertura y definición

Se conservan los 496 últimos intervalos reconstruidos y se estudian también
todos los soportes completos cuyo informe anterior cubre algún cero del
knee. Los intervalos seleccionados no son contiguos ni una trayectoria
desde DC; no se suman como si cubrieran todo el tiempo transcurrido.

Sobre nodos cúbicos x(u), la carga polinómica Qp mantiene las 25 memorias
almacenadas. Qc sustituye sólo sus cuatro componentes QBE/QBC por la ley
constitutiva Q(v(x(u))). Las 21 ramas lineales y C10 interno permanecen.
Es una reconstrucción diagnóstica, no un estado publicado del integrador.

Con KCL saliente y dt=h*du, el balance tiene unidades C:

`Bp = h*integral f(x(u)) du + A*(Qp(b)-Qp(a))`.

`Bc = h*integral f(x(u)) du + A*(Qc(b)-Qc(a))`.

Se verifica Bp-Bc=A*(Delta Qp-Delta Qc), conservación dinámica incluidos
terminales fijos, y ambas precisiones. El balance dividido por la duración
da residual medio en A; no es cota del máximo puntual ni error de voltaje.
Las restricciones lineales se integran exactamente como polinomios y se
guardan sus medias en V. No se aplica beta a la incidencia continua.

## Cuadratura y ley por piezas

Simpson anidado de 8/16/32/64 subintervalos, fijado antes de medir;
**32/64** son los niveles finales del contraste. Se conserva cada nivel.
La KCL estática se evalúa en 65 puntos por precisión, reutilizados sólo
dentro de la misma reconstrucción. Coeficientes y entradas se preparan
dentro de Decimal80/100. Las variaciones polinómicas de Qp son racionales
exactas; los valores constitutivos se evalúan con la ley congelada.

Se certifica el dominio exponencial <=45 de todas las ramas estáticas y
de carga en el intervalo reconstruido por cotas Bernstein racionales.
Un certificado fallido queda registrado y bloquea ese diagnóstico.

La cubierta exacta de ceros a profundidad 40 divide el dominio de Qc en
tramos libres de ceros y brackets. Los tramos usan la ley por piezas y
se integra Cj(v)*dv/du. Cada bracket aporta Qc(derecha)-Qc(izquierda):
no se coloca una raíz aproximada ni se integra una derivada suave a través
del bracket. Esta identidad requiere continuidad de Q, que se comprueba
en el knee de la ley condicionada. Una coincidencia idéntica requiere otra
política y se rechaza explícitamente; no se disimula como tramo suave.

La suma de tramos y puentes se contrasta con Delta Qc de los extremos.
El cierre algebraico por extremos y el contraste de cuadratura tienen
funciones distintas. El puente no identifica un instante físico exacto.

## Gates, pruebas y alcance

Gates heredados 1e-30 absoluto +1e-8 relativo para precisión/identidades,
cuadratura estática 32 frente a 64 y carga integrada frente a Delta Qc.
10 pA sólo clasifica el residual medio observado; todos los incumplimientos
se conservan, sin sustituirlos por aceptación de pasos nuevos.
Una diferencia de cuadraturas no es una cota certificada de su resto.

Pruebas: polinomios y Simpson exactos; ley de carga continua en el knee;
cruce manufacturado; 496 balances y soporte mixto a 80/100; integración
Gauss de cuatro puntos independiente en 24 casos; incidencia y puente;
reconstrucción de bytes, fuentes y cada intento fallido preservado.
No se repite toda la suite histórica.

El balance integrado no prueba solución exacta de la DAE, error temporal
global de 1 mV, fidelidad física, audio, deadline o estimador independiente.
