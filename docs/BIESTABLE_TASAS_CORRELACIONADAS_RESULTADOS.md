# Tasas correlacionadas y magnitud del residual

## Variante declarada

El [protocolo](BIESTABLE_TASAS_CORRELACIONADAS_PROTOCOLO.md) conserva el
[recinto rectangular anterior](BIESTABLE_MAGNITUD_RESIDUAL_RESULTADOS.md).
Sólo cambia el certificado de la misma reconstrucción: no se publican
estados, no se alteran los balances firmados, parámetros sintéticos,
trayectorias, topología ni tolerancias. La cota pertenece al modelo nominal
condicional de 94 nodos; no identifica un circuito físico vintage.

En las piezas certificadas se aproxima C(v(z)) con un polinomio de grado
hasta 18 y resto uniforme. El agotamiento usa Taylor binomial6, con
(M)_7*rho^7*(1-rho)^(-M-7)/7!, rho<1; la difusión usa Taylor exponencial6.
Se conservan el knee binary64 y el denominador de su continuación. Se forma
Cpol*v'-Qpol' y se sella junto al residual antes de redondear coeficientes,
con grado máximo 20. El resto de capacitancia se multiplica por max|v'|;
la tasa lleva 1/duración. Se conservan cancelaciones y unidades A.

El grafo filtrado consulta sólo las contribuciones a los nodos conectados
a Q25/Q15, incluyendo cada dispositivo incidente. Las corrientes se
contrastan contra el grafo completo, sin resolver otro circuito. Los
certificados de nodos ajenos se heredan por identidad. Las ocho celdas
se cortan en los límites de piezas y brackets, con cobertura completa.

Dentro del bracket se encierra la corriente puntualmente mediante C monótona
continua. El máximo por ancho aporta una cota L1 en C. No sustituir esa
contribución absoluta por el cambio firmado de Q. La intersección siempre
declarada entre recintos válidos estrecha el certificado; si resulta vacía,
se falla. Se guardan recintos brutos y finales, anchos y tipos de segmento.

## Resultados y regresiones

**496/496 intervalos y el soporte mixto** mantienen cotas no crecientes
y compatibles con sus límites inferiores. Los intervalos completos
certificados bajo 10 pA pasan de **31 a 105**. Los 391 casos con media
sobre el umbral conservan su incumplimiento; no quedan casos inconclusos
para esta clasificación del máximo puntual de la reconstrucción.

| Ventana | Subpasos | Intervalos completos bajo 10 pA | Límite puntual máximo anterior (A) | Límite puntual máximo correlacionado (A) |
| --- | --- | --- | --- | --- |
| prefix | 2 | 0/62 | 6.65011494e-11 | 6.13159998e-11 |
| prefix | 4 | 43/62 | 1.91697467e-11 | 1.55532813e-11 |
| attack | 2 | 0/62 | 4.40456474e-08 | 4.40456474e-08 |
| attack | 4 | 0/62 | 9.21149069e-09 | 9.21149069e-09 |
| reset | 2 | 0/62 | 5.34548110e-09 | 2.56594101e-11 |
| reset | 4 | 62/62 | 2.66647906e-09 | 6.41897764e-12 |
| tail | 2 | 0/62 | 2.43003768e-10 | 2.24883790e-10 |
| tail | 4 | 0/62 | 6.54001261e-11 | 5.63041565e-11 |

En reset N4, **2,66647906 nA → 6,41897764 pA**. En N2,
**5,34548110 nA → 25,6594101 pA**. Se estrecha un certificado;
los estados y el sonido del motor permanecen iguales.
La diferencia de tasas queda acotada en reset N2/N4 por 1,95717072 pA
y 0,0115661958 pA. No interpretar estos límites como valores observados.
El máximo de ataque está en el nodo 92, ajeno a los nodos activos
66, 82, 83 y 87 y conserva su certificado anterior.

[Datos](../evidence/loudness_latch_bdf_static_precision_correlated_enclosure.json.gz): **5,699,240 bytes**; SHA comprimido
`724b5377526665c56ba80398ef5736db1820fba0f43e520b2adf1d7d1f471fb0`; SHA canónico
`80c534a8fdb2bd484bfd44d3e6ae3a67aafeef8b4c73ad2ca6aeb996726a370c`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_correlated_enclosure_summary.json).
La [suite principal](../tests/test_loudness_latch_bdf_static_precision_correlated_enclosure.py) pasa **5/5** al primer intento, 8.8998449 s.
La [suite binomial independiente](../tests/test_loudness_latch_correlated_binomial.py) pasa **2/2** al primer intento, 0.4003204 s.
Sus [recibos principales](../evidence/loudness_latch_bdf_static_precision_correlated_enclosure_validation.json)
y [binomiales](../evidence/loudness_latch_bdf_static_precision_correlated_binomial_validation.json)
conservan fuentes antes/después idénticas, comandos, salidas y entorno.
Se prueban ambas piezas, M=0/M=1, 81 coeficientes binomiales exactos con
amplitud acotada por isqrt racional, guards, continuidad de C en el knee,
consulta de grafo frente a corrientes completas, todos los recintos, ocho
replays, 24 consultas Decimal120 y una consulta dentro del bracket mixto.
Cero solves nuevos. El [corpus](BIESTABLE_TASAS_CORRELACIONADAS_ENTRADAS.md)
mantiene las fuentes y versiones anteriores.

```powershell
python tools/loudness_latch_bdf_static_precision_correlated_enclosure.py
python tools/validate_bdf_static_precision_correlated_enclosure.py
python tools/validate_bdf_static_precision_correlated_binomial.py
```

## Próximo corte

Usar estos límites en una propagación con memoria y restricciones algebraicas,
derivando pesos temporales, estabilidad no lineal y error de anclaje. Los
intervalos seleccionados no cubren el recorrido desde DC. El error del
interpolante frente al DAE y la incertidumbre física siguen separados.
El criterio global de 1 mV, física, voz completa, audio y deadline siguen abiertos.
