# Segunda variación del circuito y de la memoria: protocolo

Declarado el 2 de octubre de 2026 antes de medir. Sigue los
[fallos individuales](BIESTABLE_DIRECCIONES_EXTREMAS_RESULTADOS.md) y
[controles cero](BIESTABLE_PEQUENA_SENAL_RESULTADOS.md). Conserva el
modelo CA3046 documental, parámetros sintéticos, residual, Newton, BDF2
y publicación. No modifica el integrador ni ajusta coeficientes a respuestas.

## Derivación

Sobre cada trayectoria base y dirección inicial m(epsilon):

`m = m0 + epsilon m1 + epsilon² m2 / 2 + ...`

Seis direcciones congeladas del informe anterior, con m1 de norma doble
1 uV y m2 inicial cero en ambos historiales. Para cada intervalo:

```
virtual1 = (1+gamma) actual1 - gamma previa1
virtual2 = (1+gamma) actual2 - gamma previa2
node1 = X virtual1
memory1 = T virtual1
J node2 = B virtual2 - Hresidual[node1,node1]
memory2 = P node2 + D virtual2 + Hpublicacion[node1,node1]
```

Se conserva D de la rama C10 en serie. La memoria de carga se escala
Q/(1 pF), exclusivamente numérica. El Hessiano residual incluye corrientes
estáticas y Q''/dt efectivo; el Hessiano de publicación incluye Q''/(1 pF).
No omitir este último ni confundir m2 con el término epsilon² m2/2.

Para Ebers-Moll: f'' = Is exp(xBE) (s deltaVBE / VT)², r'' análogo;
IB'' = s(f''/BF+r''/BR), IC'' = s(f''-(1+1/BR)r''), IE'' = -IB''-IC''.
Shockley: I'' = Is exp(x) (deltaV/(n VT))². R y C lineales no tienen
curvatura. Para carga: Qdiff'' = TF Is exp(V/scale)/scale²;
Qdep'' = Cdep M/(VJ-V) debajo del knee; encima es la pendiente constante
de la continuación cuadrática ya declarada. La rama y knee se mantienen.

El [helper analítico](../tools/loudness_latch_directional_curvature.py)
amplía el grafo estático de 66 a 94 nodos con la topología existente del
contorno y R59 como una única rama cruzada. Cita las mismas fuentes locales:
SVC-9 figuras 9-7/9-11/9-8/9-17, [grafo](../evidence/loudness_contour_graph.json),
[leyes estáticas](../tools/circuit66_decimal_static.py),
[cargas condicionadas](../tools/bjt_charge_reference.py) y
[depleción/difusión](../tools/junction_charge_reference.py).
Es una derivación numérica de esas hipótesis, sin parámetros vintage nuevos.

## Plan y gates

Cuatro ventanas de 64 pasos y seis direcciones: **256 solves espaciales
con seis RHS = 1.536 segundas variaciones**, cero solves no lineales nuevos.
Curvaturas en Decimal80/100: error por componente < 1e-30 + 1e-8 |ref|,
en las unidades del vector (A residual; V de coordenada de publicación).
No se recortan contribuciones pequeñas. Solve equilibrado conserva ambos
errores hacia atrás < 1e-10; fallos se archivan y detienen esa ventana.

En índices 0,31,63 de cada ventana: corriente estática Decimal frente a
original (gate 10 pA), solve racional exacto J/RHS levantados de binary64
para seis columnas (gate de mapa max |d2-ref|/(1+|ref|) < 1e-8), y
FD de segunda derivada en Decimal80 con epsilon **2^-10, 2^-12, 2^-14**.
Gate FD igual al de curvatura. Plan: 12 auditorías, 216 contrastes FD de
residual y 216 de publicación; conservar todos los niveles, incluso fallos.
FD comparte grafo/leyes con la derivación: independencia algebraica limitada,
sin oráculo espacial físico completo ni control de todo el resto de Taylor.

Los coeficientes usan sólo base/direcciones/leyes, no respuestas observadas.
Reservar para el bloque siguiente amplitudes **0,75 / 0,375 / 0,1875 uV**,
ambos signos, aún no integradas. Congelar los coeficientes primero; luego
comparar predictor lineal y cuadrático con solves no lineales nuevos y
gate individual 10 nV + 1e-3 |predicción| para nodos/memoria. La mejora
de un predictor no reescribe los fallos previos ni cierra el gate temporal.

SHA de entradas antes/después; historia aceptada base intacta. No se admite
defecto temporal exacto, cota global, física vintage, audio o deadline.
[Productor](../tools/loudness_latch_bdf_static_precision_memory_quadratic.py).
