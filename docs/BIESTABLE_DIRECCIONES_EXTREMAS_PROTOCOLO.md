# C7 y direcciones de máxima norma: protocolo no lineal

Declarado el 2 de octubre de 2026 antes de medir. Sigue la
[base completa](BIESTABLE_BASE_DOBLE_RESULTADOS.md), sin cambiar circuito
CA3046, parámetros sintéticos, Jacobiano compensado, residual ni gates.

## Selección y unidades

Se congelan las cuatro ventanas de 64 intervalos de
[memoria larga](BIESTABLE_MEMORIA_LARGA_RESULTADOS.md) y sus mapas/relojes;
la historia base es la compensada ya publicada, sin DC nuevo ni reseteos.
Se verifica SHA de toda entrada antes/después de medir.

Seis direcciones por ventana, sobre las 50 coordenadas actual/previa:

1. C7 actual, previa cero.
2. C7 común: actual y previa con igual signo, divididas por sqrt(2).
3. C7 diferencial: actual positiva y previa negativa, divididas por sqrt(2).
4. Vector derecho del máximo de norma 2 nodal de la ventana previa.
5. Vector derecho del máximo de norma 2 de memoria de esa ventana.
6. Vector derecho del máximo de norma 2 de historia doble de esa ventana.

C7 se identifica por referencia del circuito (KEY_RC, 100 nF), índice 20
en las 25 memorias guardadas. Los tres máximos se eligen en el **informe
anterior congelado**, con primer índice en empate. Los vectores se usan
exactamente como están archivados, normalizados y con signo fijado;
no se recalcula SVD ni se selecciona una dirección por esta respuesta nueva.
Pueden parecerse entre sí: no se cuentan como evidencia estadística independiente.

Cada vector tiene norma euclídea 1 en la historia doble. Se multiplica por
**1 uV, 0,5 uV y 0,25 uV**, con ambos signos. Las cuatro cargas conservan
Q/(1 pF), escala exclusivamente numérica: una componente de 1 uV implica
1e-18 C. No se alteran las semillas nodales. Las inyecciones de memorias
son hipotéticas, no soluciones anteriores aceptadas.

## Predicción, respuesta central y respuesta por signo

Se reutiliza la recurrencia de los mapas auditados X/T con memoria propia
lineal, y se integra cada inyección con sus memorias no lineales propias
durante los 64 intervalos fijados. No realimentar la trayectoria base.
Plan: **144 continuaciones = 9.216 solves no lineales nuevos**, cero
solves nuevos de mapa espacial, **72 contrastes** por cada métrica.

Para los 94 nodos y 25 memorias se conserva:

- Respuesta central (plus-minus)/2 frente a la predicción positiva.
- Respuesta de cada signo frente a su propia predicción.
- Respuesta par (plus+minus)/2, respecto a la base sin inyección.

Gate central y gate individual por signo: error < **1e-8 V +
1e-3 |predicción|** en cada coordenada/intervalo. La respuesta par se
informa sin un gate nuevo separado: permite ver el sesgo que el contraste
central cancela. Pasar la respuesta central no implica pasar las dos
respuestas individuales. Se conservan los fallos de cada amplitud;
no se cambia la tolerancia ni se afirma un orden asintótico por tres niveles.

## Publicación y alcance

Newton conserva KCL < 10 pA y corrección < 10 nV. Publicación se verifica
directamente desde las historias reales: KCL < 10 pA, ecuación de rama
< 1e-14 V y restauración tipada exacta. Dominio temporal >= 1 ps;
KEY = 10 V. Se archivan estado entrante/candidato/diagnóstico ante fallo
y se detiene sólo esa continuación, sin buscar otra raíz ni resetear.
Un gate de comparación fallido permanece en el resultado.

No se aplica el estimador adaptativo local. Esta selección finita no valida
las 50 direcciones no lineales, no deriva defecto temporal ni cota global.
No admite conmutación vintage, refinamiento, audio ni deadline. El gate
temporal de 1 mV permanece separado.

[Productor](../tools/loudness_latch_bdf_static_precision_memory_extrema.py).
