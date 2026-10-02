# Carga constitutiva y cota superior de magnitud

## Modelo y recintos

El [protocolo congelado](BIESTABLE_MAGNITUD_RESIDUAL_PROTOCOLO.md) amplía
el [recinto estático anterior](BIESTABLE_INTEGRAL_ACOTADA_RESULTADOS.md).
La reconstrucción usa los mismos 94 nodos y 25 memorias: 21 lineales
almacenadas y cuatro junturas Q25/Q15 compuestas como Q(v). Se conservan
parámetros sintéticos, topología, emisividad, tiempos de tránsito y knee
binary64; no se identifican nuevos valores vintage ni se publican estados.

Para bases positivas, log se encierra mediante reducción por potencias
de dos, serie de atanh y cola geométrica. Los productos, sumas, recíprocos
y exponenciales redondean hacia afuera a 256 bits fraccionarios. Se evalúan
las dos piezas vigentes de Q y C, incluyendo M=1 y la continuación desde
el knee FC*VJ redondeado. Se conserva el denominador VJ*(1-FC) de esa
continuación. Q y C son continuas; su segunda derivada no se supone continua.

Con Cj>=0, VJ>0, 0<=M<=1, 0<=FC<1, knee<VJ, T>=0, Is>0 y emisión>0,
C(v) es no decreciente. Un recinto de v en toda una celda permite encerrar
C mediante sus extremos, incluso al cruzar el knee. Multiplicar su recinto
por el de v' y restar Qpol' acota la diferencia de tasas; el factor temporal
es 1/duración. Los guards rechazan dominio inválido sin recorte.

Delta Q constitutiva se sella y suma al recinto estático congelado para
acotar el balance en C y su media en A. Se conserva el contraste Gauss16
mediante una condición suficiente exacta más estricta que el gate binary64
heredado. La clasificación admite dentro, fuera o inconcluso.

## Cota de magnitud y unidades

Se aproxima exp(P) con Taylor centrado de grado 6 y resto uniforme explícito.
Las corrientes y tasas de Qpol producen un residual polinómico de grado <=18.
Se cancelan los sellos antes de redondear coeficientes a la malla diádica;
la suma de sus errores absolutos se añade al resto, válida en z en [0,1].
Bernstein acota ese polinomio en ocho celdas fijas. Se añade por incidencia
la diferencia de tasas constitutivas calculada arriba. Por cada nodo j:

```text
L_j = menor módulo del recinto de integral R_j dt
U_j = sum(celdas, duración/8 * máximo módulo del recinto puntual R_j)
L_j <= integral |R_j(t)| dt <= U_j                [C]
```

El máximo del recinto puntual se conserva en A. Esta cota superior controla
la cancelación interna del balance firmado; puede resultar amplia por pérdida
de dependencia entre v, v', C(v) y Qpol'. Inferior<=superior es una comprobación
de consistencia, no un criterio de estrechez ni de error de voltaje.
Cada cota corresponde a su intervalo reconstruido. Los intervalos seleccionados
omiten subpasos y arranque: no se suman como una trayectoria desde DC.

## Resultados y regresiones

**496/496 intervalos y el soporte mixto** pasan el contraste acotado de
Gauss16 y la consistencia inferior/superior de magnitud.
La media constitutiva queda bajo 10 pA en **105**, por encima en **391**,
sin inconclusos. Las cotas pertenecen a la reconstrucción.

| Ventana | Subpasos | Medias bajo 10 pA | Intervalo completo certificado bajo 10 pA | Límite puntual máximo (A) |
| --- | --- | --- | --- | --- |
| prefix | 2 | 0/62 | 0/62 | 6.65011494e-11 |
| prefix | 4 | 43/62 | 31/62 | 1.91697467e-11 |
| attack | 2 | 0/62 | 0/62 | 4.40456474e-08 |
| attack | 4 | 0/62 | 0/62 | 9.21149069e-09 |
| reset | 2 | 0/62 | 0/62 | 5.34548110e-09 |
| reset | 4 | 62/62 | 0/62 | 2.66647906e-09 |
| tail | 2 | 0/62 | 0/62 | 2.43003768e-10 |
| tail | 4 | 0/62 | 0/62 | 6.54001261e-11 |

**31 intervalos completos** quedan certificados bajo 10 pA por su cota puntual.
Los 391 casos con media sobre el umbral prueban incumplimiento en algún punto;
los **74 restantes** no se resuelven para el máximo puntual con esta cota.
No deben confundirse con los cero inconclusos de la clasificación de la media.

En reset N2/N4, el límite puntual alcanza 5,34548110 nA y 2,66647906 nA,
mientras las medias máximas son 25,6358966 pA y 6,41600024 pA.
El mayor cociente límite puntual/menor máximo medio es **416.363413**.
Es un indicador de amplitud entre magnitudes distintas, no un factor de error.
La pérdida de correlación en C(v)*v′-Qpol′ domina esta amplitud en reset:
su recinto de tasa alcanza 5,06346088 nA y 2,53186436 nA.
El resto polinómico máximo de todo el corpus es sólo 4,53846054e-16 A.
Conservar esta variante conservadora; otra cota deberá declararse antes de medir.

[Datos](../evidence/loudness_latch_bdf_static_precision_constitutive_enclosure.json.gz): **42,630,084 bytes**; SHA comprimido
`d722f66e661a36a48f838dc6058bab7249040489f9af11810579d7a04f01dcf9`; SHA canónico
`56fbf0bc2187a53e20776efa76ea41ba6cf970c089a91ce53ec2f648f73250e3`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_constitutive_enclosure_summary.json).
La [suite](../tests/test_loudness_latch_bdf_static_precision_constitutive_enclosure.py)
pasa **5/5 al segundo intento**, 33.9836499 s.
El [recibo](../evidence/loudness_latch_bdf_static_precision_constitutive_enclosure_validation.json)
conserva ambos intentos, sus SHA antes/después idénticos y la primera fuente completa.
El testigo M=0,T=0 inicial superaba el guard exponencial; se limita al dominio
declarado. Otro testigo era afín y exigía grado 18: se sustituye por uno cúbico.
No se cambian ayudante, productor, protocolo, datos, constantes ni gates.

Las regresiones incluyen series log racionales independientes, fórmulas Q/C
a Decimal200, M=0 exacto y M=1 en ambas piezas, monotonía, signos NPN/PNP,
cancelación lineal, todos los recintos, ocho replays completos y 24 consultas
interiores Decimal120. Cero solves no lineales nuevos.
El [corpus ampliado](BIESTABLE_MAGNITUD_RESIDUAL_ENTRADAS.md) conserva las versiones.

```powershell
python tools/loudness_latch_bdf_static_precision_constitutive_enclosure.py
python tools/validate_bdf_static_precision_constitutive_enclosure.py
```

## Próximo corte

Primero estrechar la cota de tasas conservando la correlación en reset; luego
propagación con memoria y restricciones algebraicas, estabilidad no lineal,
error de anclaje y cobertura temporal completa. Separar la calidad de estas
cotas del error de reconstrucción frente al DAE. El criterio global de 1 mV,
física, voz completa, audio y deadline permanecen abiertos.
