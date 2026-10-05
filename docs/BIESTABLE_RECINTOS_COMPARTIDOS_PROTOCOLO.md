# Recintos compartidos: protocolo fijado antes de medir

Fuente: los ocho archivos completos del prefijo curvo, índices 8–15,
aceptados hasta ≈125 µs. El control conserva sus 16 soportes y cotas.
La entrada de cada alternativa es el resultado real original del octavo
soporte; nunca el final del control. Mantener P, 22 grupos, pesos y escalas.

## Banco y orden

- Anchos de bloque: 8, 4, 2 y 1, en ese orden. Para cada ancho, empezar en
  índice 8; bloques consecutivos sin solapamientos. Detener esa propagación
  en su primer hueco. Detener el banco en la primera alternativa completa.
- Radios por soporte: 0,1 y 1 µV. Rechazar antes de construir un recinto si
  la cota nodal de entrada no es estrictamente menor que el radio. El primer
  radio siempre queda rechazado por el pico acumulado de la fuente.
- X por bloque: soporte central ordinal inferior, u=1/2; descriptor con
  Decimal100, inversa candidata binary64 finita. X no es una inversa probada.
- Conservar exactamente las curvas reconstruidas con las X/RHS originales
  de las burbujas. Verificar sus SHA, residuos y duraciones de historias.

## Prueba uniforme

Para X fija, comprobar igualdad de toda la constante y los stamps analíticos
sin sus polinomios `power`. En cada término, calcular el rango Bernstein
de cada polinomio completo en [0,1], unir mínimos/máximos y registrar todas
las contribuciones. El polinomio afín [lo, hi-lo] representa ese rango
escalar; **no constituye una nueva curva física**. Inflar por radio y ganancia
de incidencia. Mantener las leyes exponenciales y C(v) por piezas, dominio
45, q<1 y todas las filas del descriptor 119×119.

Una inversa intervalar y tres certificados de tasa por bloque, válidos sobre
la unión completa, se pueden reutilizar. Cada macrocelda conserva su RHS y
forzamiento identificados. Recalcular sus ocho acciones firmadas con X y E
nuevos, cola Neumann y todos los restos independientes. No reutilizar las
acciones del control. Propagar las 22 memorias y cada duración física real;
cerrar estrictamente cada soporte antes de admitirlo.

Los recintos de bloque son pruebas uniformes **condicionales**, incluso sobre
soportes todavía no alcanzados. Sólo el transporte cerrado admite tiempo.
Publicar costes de todas las alternativas ensayadas y de la seleccionada,
tamaño comprimido y control; no equiparar costes de prueba con tiempos de
audio. No ampliar cobertura temporal, cambiar gates o admitir el motor.

## Validación

Reproducir identidad de referencias/RHS, rangos completos, constante y
stamps, cada recinto/inversa/tasa/acción y todos los cierres e interfaces.
Regresiones negativas: extremos e interior fuera de rango, stamp o ley
distinta, reloj/duración o linaje de entrada alterados. Congelar fuentes antes
de medir y datos/tests antes de validar. Archivar corpus y fallos exactos.
