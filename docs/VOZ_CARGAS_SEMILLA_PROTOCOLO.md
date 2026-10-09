# Condicionamiento conjunto con cargas de cadena prescritas

2026-10-09. CA3046 nominal, misma escena y tarjetas del
[BUS conjunto](VOZ_BUS_CONJUNTO_PROTOCOLO.md). SVC-9 p.5 para fase C1;
pp.19/13/10 para las 18 incidencias de cadena y valores de capacitores.
No hay ajuste de componentes ni arranque físico admitido.

## Función del bloque

Construir una memoria alternativa sin imponer todas las corrientes DC
iguales a cero. La inicialización anterior retenía C1 y dejaba C27 en DC
del saw retenido; su trayectoria publicada presenta deriva por ciclo.
Un nuevo estado no puede obtenerse cambiando solo BUS o C27 en un lift:
los nodos algebraicos tienen que resolverse con la carga eléctrica.

Para 200 incógnitas conjuntas x y 18 corrientes i, resolver 218 ecuaciones:
`f(x)+E·i=0`, `Eᵀ·x=v_objetivo`. Reemplazar exclusivamente la fila C1
(43) por `x43=0`; reportar su corriente de retención. E tiene +1 en el
terminal a de cada capacitor de cadena y −1 en b, salvo riel fijo. Las
condiciones de este laboratorio no tienen contactos que redirijan esas
filas. C10 es explícito (67,7). Los valores de E son adimensionales,
v=Eᵀx en V, i en A; Q=C·(v−v_fijo) en C, con la referencia
del terminal fijo restada en la tensión física. Para riel constante,
ΔQ=C·Δv. [Aclaración y errata](VOZ_CARGAS_RIELES_NOTA.md).
Una corriente positiva va de a a b.
Las corrientes calculadas son derivadas instantáneas de carga de cadena,
no fuentes añadidas al circuito temporal. En la liberación desaparecen
las restricciones y se usa el motor conjunto original.

Conservar las 18 diferencias de voltaje del lift histórico en objetivo 0.
Objetivo 1 conserva 17 y cambia explícitamente C27 a
`entrada6_DC_histórica − 0,5·media_saw_observada`. La condición necesaria
del panel se deriva en [historia](VOZ_CICLOS_HISTORIA_PROTOCOLO.md):
`media(0,5·saw−BUS)=0` si C27 repite su carga. La media usada aquí es una
cuadratura trapezoidal de endpoints de un periodo histórico, en dos
resoluciones. Es una heurística de semilla, no una integral Radau ni una
media física asentada. Entrada 6 se aproxima por su sesgo histórico;
la realimentación no lineal deja abierta la corrección posterior.

## Gates antes de medir

Newton conserva objetivo inmutable, 64 iteraciones, 24 mitades Armijo,
1e-13 A/1e-11 V de residuo, 2e-9 V/2e-12 A de corrección, fase/cargas
1e-11 V. Incidencia de rango 18; dos semillas por objetivo convergen
dentro de 1 µV/1 nA. Acumulación compensada x e i; dominio heredado.
El solver lineal de laboratorio copia la eliminación escalada existente
sin eliminar coeficientes pequeños (solo ceros exactos).

Oráculo: DC VCO Decimal100 y cadena Python con Jacobiano por diferencias
finitas de 1 µV, más incidencia independiente de las 18 ramas. Residuo
2e-11 A/2e-10 V, cargas/fase 1e-11 V; corrección 1 µV/1 nA, corrientes
de retención comparadas a 2e-11 A. Contrastar 218 filas por raíz. No
llamar raíces independientes a puntos candidatos nativos contrastados.

Liberar cada objetivo por 2 µs (1.048.576 ticks) a medias etapas máximas
125/62,5 ns. Máximo 512 intervalos por perfil; LTE 2 µV/2 nA, KCL BUS y
C1 1e-12 A; contraste de etapas first/last full/mid/end, cargas exactas
al reloj inicial y estados finales al mismo reloj. Restore con replay
exacto de un paso antes de publicarlo. La prueba corta acredita
liberación refinada, no periodicidad. Sin audio nuevo ni deadlines.

Reutilizar biblioteca y compilador ya admitidos; solo compilar caller.
Stack de laboratorio 32 MiB, 180 s por proceso/600 s globales, reserva
1 GiB + 8 MiB estimados, procesos seriales. Preservar fallos y replay
antes de reparar; congelar todos los inputs antiguos y los nuevos.

El bloque incluye errata de enlaces/componentes del resultado previo.
Guardar bytes originales y enlaces inválidos con repetición antes de
corregir; el nuevo QA comprobará los destinos locales de ese documento
y de los documentos cambiados, además de la identidad anterior.
