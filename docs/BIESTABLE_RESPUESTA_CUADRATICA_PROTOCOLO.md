# Respuestas nuevas reservadas frente al predictor cuadrático

Declarado el 2 de octubre de 2026 antes de medir, después de congelar
los [coeficientes derivados](BIESTABLE_CURVATURA_RESULTADOS.md).
No se recalculan ni ajustan con estas respuestas. El integrador no cambia.

## Plan

Cuatro ventanas de 64 pasos, seis direcciones iniciales congeladas;
amplitudes **0,75 / 0,375 / 0,1875 uV** de norma doble, reservadas en
el protocolo de derivación, signos +/-. Plan: **144 continuaciones =
9.216 solves no lineales nuevos**, cero solves nuevos de coeficientes.
Se conserva cada historia propia, reloj y publicación, sin reseed de la base.

Predictor lineal: la recurrencia X/T existente por dirección. Predictor
cuadrático: sumar **a²/2** por la segunda variación congelada (m1 inicial
de norma 1 uV, a multiplicador). El término par tiene el mismo signo en
ambos casos; el lineal cambia de signo. Se conserva la propagación binary64
existente del término lineal; los coeficientes de segundo orden fueron
derivados con la propagación matricial de esas mismas direcciones.

## Gates y separación de métricas

Por cada nivel/dirección se comparan ambos signos, en 94 nodos y 25 memorias,
frente a cada predictor. Gate individual intacto por coordenada/intervalo:
**10 nV + 1e-3 |predicción|**. El denominador usa la predicción de la ruta
que se contrasta, con la misma fórmula y constantes fijadas; no hay ajuste
de tolerancias. Son 72 contrastes individuales por cada predictor.

Además: respuesta par real (plus+minus)/2 frente al término par cuadrático,
con el mismo gate **10 nV + 1e-3 |predicción par|**; 72 contrastes.
Se mantiene la métrica central lineal como diagnóstico, sin confundirla
con el pase individual/par. Conservar fallos y máximos de cada métrica.

Publicación sin cambios: KCL < 10 pA, rama < 1e-14 V y round trip tipado
exacto; corrección Newton < 10 nV. h >= 1 ps, KEY = 10 V. No se aplica
el estimador adaptativo local. Un fallo de solve/publicación detiene sólo
esa continuación y guarda memoria/candidato/diagnóstico disponibles.

No se usan las respuestas reservadas para modificar coeficientes, elegir
otra raíz o descartar un nivel. Las memorias inyectadas son hipotéticas.
Las cargas mantienen Q/(1 pF), escala numérica. SHA de entradas antes/después,
datos previos intactos y sin relajación de gates. Una mejora cuadrática
puede validar sólo esa selección finita, sin resto de Taylor global,
defecto temporal exacto, cota, fidelidad vintage, audio o deadline.

Los fallos lineales anteriores permanecen. El gate temporal de 1 mV desde
DC sigue separado. [Productor](../tools/loudness_latch_bdf_static_precision_memory_quadratic_response.py).
