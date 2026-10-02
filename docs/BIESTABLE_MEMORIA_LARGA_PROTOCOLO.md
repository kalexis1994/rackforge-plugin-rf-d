# Memoria acumulada con Jacobiano compensado: protocolo

Declarado el 2 de octubre de 2026 antes de medir. Diagnóstico del biestable
Q25/Q15 acoplado a la red de 94 nodos; no representa todavía una voz completa
del Model D ni sustituye evidencia vintage externa.

## Entradas y dominio

Se conserva el circuito documental CA3046 y todos los parámetros, cargas,
residuales, Newton y gates del
[integrador explícito](../tools/loudness_latch_bdf_static_precision_integrator.py).
Se usa la trayectoria compensada de DC a 3 ms ya publicada en
[reloj completo](BIESTABLE_RELOJ_COMPLETO_COMPENSADO_RESULTADOS.md), sin
recalcular DC ni elegir raíces. KEY = 10 V. Ningún intervalo menor de 1 ps.
El [productor](../tools/loudness_latch_bdf_static_precision_memory_long.py)
archiva SHA256 de entradas antes/después y contexto de Git.

Las cuatro anclas son el último ensayo E4G8 aceptado con tiempo no mayor
que 2,3 / 2,4222 / 2,44205 / 2,5 ms (prefix, attack, reset, tail).
Se toma la historia doble correspondiente del reloj compensado, y los
**64 intervalos publicados siguientes**, con sus tiempos exactos. Cuadruplica
la ventana anterior de 16 pasos; no atraviesa todo el transitorio ni constituye
una prueba de horizonte global. Las perturbaciones siguen su propia memoria,
sin realimentar los estados de referencia ni retimar la trayectoria.

## Coordenadas y recurrencia

Vector m de 25 coordenadas: 17 capacitores de audio, C10 en serie, tres
capacitores del contorno y Q25 BE/BC, Q15 BE/BC. Las últimas cuatro se
expresan como Q/(1 pF); **1 pF es escala de coordenadas**, no una capacitancia
física añadida. La identificación C2 se hace por referencia del circuito.

Para h actual, k anterior: r = h/k, a0 = (1+2r)/(1+r),
gamma = r²/((1+r)a0), dt efectivo = h/a0.

```
delta_virtual = (1+gamma) delta_actual - gamma delta_anterior
J X = B
delta_nodos = X delta_virtual
T = P X + D
delta_nueva_memoria = T delta_virtual
```

B contiene los sellos de memoria de las ramas y cargas; P la derivada de
publicación; D conserva la memoria directa de C10 con R = 25,5 kohm y
C = 10 uF. Se reutilizan sin cambios los
[sellos derivados](../tools/loudness_latch_bdf_memory_transfer.py).
El solve equilibrado exige ambos errores hacia atrás, binario y Decimal80,
menores de 1e-10. Los productos y propagación son binary64: su incertidumbre
no se presenta como aritmética exacta ni cota del error temporal.

En índices **0, 31 y 63** de cada ventana se reconstruye el Jacobiano
estático de 66 nodos mediante el grafo independiente Decimal80/100; el
contorno y la dinámica mantienen sus leyes compartidas. Se resuelve el
sistema levantado de binary64 en racionales exactos, con multiplicación
independiente JX = B. El Jacobiano estático redondeado debe coincidir a
80/100 dígitos. Comparadores de X y T: max |candidato-referencia| /
(1+|referencia|) < 1e-8, además de ambos errores hacia atrás < 1e-10.
Son **12 auditorías seleccionadas**, no un oráculo espacial completo para
los 256 mapas ni una identificación física de componentes.

## Experimentos fijados

Ocho direcciones por ventana:

1. C2 actual: +1 uV en la memoria actual, anterior cero.
2. C2 común: +1 uV en ambas memorias.
3. C2 diferencial: +1 uV actual, -1 uV anterior.
4. Q25 BE actual: +1 uV de coordenada = 1e-18 C.
5. Q25 BC actual: igual escala.
6. Q15 BE actual: igual escala.
7. Q15 BC actual: igual escala.
8. Diferencia cruda original sombra/full del ancla E4G8, sólo memoria actual.

Para cada dirección: amplitudes 1 y 1/2, signos + y -. Se perturban memorias
almacenadas sin cambiar semillas nodales. Son inyecciones hipotéticas,
**no estados pasados aceptados**. La dirección sombra/full procede del
experimento original, aunque la trayectoria base sea compensada; no es
un defecto temporal exacto ni se aplica como corrección de la solución.

Plan: 256 mapas, 128 continuaciones de 64 pasos = **8.192 solves no
lineales nuevos**, 64 contrastes centrales. Para cada intervalo se guarda
la historia doble, diagnóstico, publicación, diferencias de 94 nodos y
25 memorias, y predicciones. El contraste central es (plus-minus)/2;
gate en cada coordenada: |central-predicción| < **1e-8 V +
1e-3 |predicción|**, para nodos y memoria. En cargas equivale a la escala
anterior; no es un gate físico adicional. Ganancias observadas se dividen
por la norma máxima de la inyección doble: no son normas inducidas globales.

## Fallos y alcance

Se preserva todo fallo, incluyendo historia entrante, candidato si existe,
diagnóstico y publicación. Un fallo de solve/publicación detiene esa
continuación; no se resetea ni se busca otra raíz. Un fallo de gate central
se conserva y no cambia amplitudes, longitud ni tolerancias. Fallos de
auditoría racional no se convierten en aceptación de mapas.

Publicación sin cambios: KCL < 10 pA, ecuación de rama < 1e-14 V,
round trip tipado exacto; Newton conserva corrección < 1e-8 V.
Las continuaciones usan reloj fijo y no ejecutan el gate adaptativo local.
No se admite refinamiento temporal, conmutación física, cota global,
audio ni deadline. El gate temporal de 1 mV sigue separado y pendiente.
