# Recinto racional de la integral reconstruida

## Ley, unidades y prueba del recinto

El [protocolo congelado](BIESTABLE_INTEGRAL_ACOTADA_PROTOCOLO.md) usa el
[grafo condicional anterior](BIESTABLE_BALANCE_GAUSS_RESULTADOS.md), sin
nuevas constantes físicas. Hay 82 resistencias, dos conductancias, 38 BJT
y ocho diodos: 84 términos exponenciales y 94 nodos. Las leyes son las
mismas Ebers-Moll/Shockley nominales, con parámetros binary64 elevados
exactamente a racional. No se identifica otro transistor vintage.

Para cada exponente cúbico P, se normaliza el intervalo a z en [0,1].
Con c=P(1/2), delta=P-c y rho=max|coeficientes Bernstein(delta)|:

```text
exp(P) = exp(c) * sum(k=0..12, delta^k/k!) + resto
|resto| <= exp(c+rho) * rho^13/13!
```

La suma se integra como polinomio racional exacto. La cota puntual del
resto se multiplica por ancho normalizado, h en s e Is en A: resultado C.
Se incluyen el término -Is y los coeficientes BF/BR, polaridades NPN/PNP
y signos terminales. Resistencias y conductancias se integran exactamente.
El máximo Bernstein de cada exponente debe cumplir <=45 en todo el soporte.

La exponencial queda encerrada con una malla diádica de 256 bits, sin
usar Decimal como certificado. Para y en [0,1], cada término positivo se
redondea hacia afuera. Después de 64 términos, la cola no supera dos
veces el primer omitido, porque las razones posteriores son <1/2.
La reducción por potencias de dos se revierte con cuadrados exteriores;
argumentos negativos usan el recinto recíproco. Cada paso conserva el orden.
El rango declarado |argumento|<=4096 es un guard, no un recorte.

## Balance y alcance

Delta Q polinómica se obtiene de extremos racionales y su incidencia
conserva exactamente la carga, incluyendo terminales fijos. Se suman los
recintos de integral f(x) dt a A*Delta Q para encerrar integral R dt;
al dividir por duración positiva se obtiene el recinto de la media en A.
Esta memoria es la interpolación de las cargas almacenadas, no Q(v).

Para Gauss16 guardado, convertido a racional sin perder sus dígitos, se
calcula la distancia máxima a ambos extremos. El certificado emplea
1e-30 exacto +1e-8 exacto*|Gauss16| como condición suficiente. Ambos
coeficientes son estrictamente menores que los binary64 heredados;
por tanto distancia <= ese umbral implica el gate heredado estricto.
La relación se verifica explícitamente. No se relaja el gate ni se exige
que un número redondeado caiga dentro de un recinto más fino que su redondeo.

Por nodo, el menor módulo del recinto del balance aporta una cota inferior
de integral |R_j| dt, en C. No aporta cota superior, máximo puntual,
propagación ni error de voltaje. Los intervalos seleccionados omiten otros
subpasos y no cubren una trayectoria desde DC. No se suman para fingirla.
La ley ideal de esta reconstrucción está acotada; permanecen desconocidos
el error de sus nodos frente a la solución del DAE y frente al circuito físico.

## Medición y regresiones

**496/496 intervalos y el soporte mixto** cumplen el contraste acotado de Gauss16.
Se clasifican **105 medias bajo 10 pA, 391 por encima y cero inconclusas**.
Los fallos del residual quedan confirmados con un recinto, no eliminados.

| Ventana | Subpasos | Medias bajo 10 pA | Mayor radio estático (C) | Mayor media absoluta acotada (A) |
| --- | --- | --- | --- | --- |
| prefix | 2 | 0/62 | 9.29786881e-50 | 6.11115649e-11 |
| prefix | 4 | 43/62 | 5.75569899e-54 | 1.55268841e-11 |
| attack | 2 | 0/62 | 1.49421269e-35 | 3.52891693e-08 |
| attack | 4 | 0/62 | 3.63383168e-40 | 8.81308470e-09 |
| reset | 2 | 0/62 | 1.06723068e-52 | 2.56358728e-11 |
| reset | 4 | 62/62 | 6.52520666e-57 | 6.41599963e-12 |
| tail | 2 | 0/62 | 7.70725973e-56 | 2.24806590e-10 |
| tail | 4 | 0/62 | 4.71544009e-60 | 5.62944669e-11 |

El máximo radio estático es **1,49421269e-35 C**, en ataque con dos subpasos.
Estos radios acotan redondeo y resto del procedimiento racional, no el error de estados.
El soporte mixto de reset conserva media por encima de 10 pA; su memoria polinómica
y ley estática no necesitan cambiar de fórmula al cruzar el knee constitutivo.

[Datos](../evidence/loudness_latch_bdf_static_precision_charge_enclosure.json.gz): **40,882,589 bytes**; SHA comprimido
`9c903f606dd50c12ab09724e8c7b1c2853224dca3ca3bcd994972819efa734db`; SHA canónico
`bc062cbb75a9b8b50bce55862bbbebdbf0c8db1c9268a0ad12e15c3d8e0b637b`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_charge_enclosure_summary.json).
La [suite](../tests/test_loudness_latch_bdf_static_precision_charge_enclosure.py)
pasa **5/5 pruebas al primer intento**, 16.1271199 s, con
[SHA antes/después idénticos](../evidence/loudness_latch_bdf_static_precision_charge_enclosure_validation.json).
Incluye series racionales independientes, extremos ±4096, exponencial afín cerrada,
expansión cúbica sin centrar, signos NPN/PNP, terminal fijo, conservación exacta,
todos los recintos y ocho replays completos seleccionados. Cero solves nuevos.

El [corpus ampliado](BIESTABLE_INTEGRAL_ACOTADA_ENTRADAS.md) preserva las fuentes anteriores.

```powershell
python tools/loudness_latch_bdf_static_precision_charge_enclosure.py
python tools/validate_bdf_static_precision_charge_enclosure.py
```

Siguiente corte: recinto de la memoria constitutiva, cota superior de
magnitud del residual y luego propagación con estabilidad y cobertura.
El criterio global de 1 mV, física, voz completa, audio y deadline siguen abiertos.
