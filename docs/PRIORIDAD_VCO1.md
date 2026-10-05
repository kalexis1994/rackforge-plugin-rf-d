# Prioridad activa: completar el oscilador CA3046

Decisión del usuario, 2026-10-05: completar el oscilador con rigor y avanzar
hacia una voz audible. La extensión de certificados continuos del biestable
queda aplazada; se conservan sus datos, resultados y criterios sin promover
sus 350 µs a una voz o a fidelidad histórica.

## Entrega y orden

1. Construir una netlist ejecutable de VCO 1 desde el grafo cotejado de
   SVC-9 Fig. 9-3 (PDF p. 5), con convertidor CA3046, C1, amplificador FET,
   Schmitt Q5/Q6, reset Q10 y formadores Q2/Q1 y Q11/Q12. Incluir las
   cargas documentadas del panel Fig. 9-17 (PDF p. 19).
2. Identificar las leyes y parámetros de cada dispositivo. Valores de
   laboratorio y parámetros sin identificación física tendrán procedencia,
   unidades y dominio explícitos. C4 de 10/100 pF conserva dos perfiles;
   la incertidumbre Q5/Q6 tampoco se resuelve eligiendo por sonido.
3. Medir arranque, periodicidad, corriente de Qa, frecuencia, amplitudes,
   reset y seguimiento del CV. Contrastar al reducir el paso temporal y
   con otro método de integración, sin usar la concordancia como prueba
   de parecido con un instrumento.
4. Obtener trazas largas y renders de laboratorio reproducibles. Conectar
   después el puerto real del mezclador y validar su carga recíproca.
5. Tras el oráculo, implementar una ruta portable y contrastarla antes de
   optimizar. Contornos, controles restantes y voz completa conservan sus
   criterios separados.

## Criterio de avance

Los certificados formales profundos se retomarán ante una discrepancia,
inestabilidad o necesidad concreta. Para el prototipo experimental se
requieren trazabilidad eléctrica, ausencia de fallos del solver, pruebas
de convergencia y observaciones de señal. Publicar qué pasa y qué sigue
abierto; no reducir umbrales anteriores ni afirmar fidelidad física por
precisión numérica.

La netlist completa con leyes provisionales es un oráculo documental
condicionado. No identifica una unidad vintage, un modelo de fabricante
ni el presupuesto de tiempo real. Los ajustes nominales se documentan
como calibración reproducible, nunca como captura de un ejemplar.
