# Reconstrucción interior de cargas: resultados

Productor, álgebra y [protocolo](BIESTABLE_CARGA_INTERIOR_PROTOCOLO.md)
fijados en `e9cf266`, el 2 de octubre de 2026. Son reconstrucciones de
referencias numéricas propias del circuito condicional, con parámetros
sintéticos. No se ejecutan solves nuevos ni se cambia el integrador.

## Interior, restricciones y residual

Se reconstruyen 496 soportes de cuatro estados finos y se consultan
**1.488 puntos interiores**, en 1/4, 1/2 y 3/4 del último intervalo.
Todos pasan precisión Decimal80/100 e identidades; cero errores de dominio.
Máximo error de precisión normalizado: 3,49054e-49, con los gates anteriores.
Los **496 extremos** reproducen los resultados continuos ya archivados.
No se reemplaza ninguno de esos informes ni sus fallos.

Los **10.416 polinomios de restricción capacitiva** (21 por intervalo)
cumplen 10 fV en todo [0,1], por cotas Bernstein racionales exactas.
Máxima cota absoluta 2,87966075575e-15 V. Las 1.488 consultas de esas
restricciones también pasan, incluyendo C10 serie y su memoria interna.
Es una propiedad de esos polinomios; no certifica una trayectoria física.

KCL interpolada cumple 10 pA en **315/1.488** puntos y conserva
**1.173 incumplimientos**. No se usa la cota capacitiva para admitir KCL.

| Ventana | Máx. KCL interior, 2 subpasos (A) | Máx. KCL interior, 4 subpasos (A) | Consultas bajo 10 pA, 2/4 |
| --- | ---: | ---: | ---: |
| Prefijo | 6,13077512956e-11 | 1,55522206902e-11 | 0/129 |
| Ataque | 3,71097219616e-8 | 8,80679450444e-9 | 0/0 |
| Reset | 2,56415599727e-11 | 6,41671657708e-12 | 0/186 |
| Cola | 2,24880698281e-10 | 5,63037686688e-11 | 0/0 |

Cada nivel tiene 186 consultas. Máximo en nodo 92/C2, ataque de dos
subpasos, índice 21 y u=3/4. Los máximos de esta tabla son muestreados;
no se ha acotado KCL entre consultas ni el error global de voltaje.

## Cambio de pieza: soporte frente a intervalo actual

Las cuatro junturas permanecen estrictamente en una pieza en los
**1.984 últimos intervalos reconstruidos**, por sus coeficientes Bernstein.
En los soportes completos, 1.983 de 1.984 tienen el mismo certificado.
El restante es Q25 BC, reset de dos subpasos, índice 45. Su cubierta
racional conserva **un bracket de signos opuestos**, sin brackets
inconclusos, coincidencias idénticas o raíces exactas adicionales.

El bracket temporal del polinomio está entre
0,0024420669657944712611224649483929947 y
0,0024420669657944712616428819910554015 s.
Su anchura exacta, resumida decimalmente, es 5,20417042662e-22 s,
tras 40 subdivisiones del soporte. La incertidumbre corresponde a
esa raíz del polinomio, no a una transición física identificada.

El último intervalo comienza en 0,0024420671463013825 s. El cruce
está antes de ese inicio: el soporte cúbico incluye estados de dos piezas,
aunque el intervalo consultado permanece en una. Por eso una prueba de
regularidad debe especificar si cubre el intervalo actual o todo el historial.
Este certificado tampoco acota el voltaje de la solución desconocida.

Máximo Q interpolada menos Q(v interpolado): 7,01456467852e-23 C,
Q25 BC, reset de dos subpasos, índice 45, u=1/2. Máximo desacuerdo
de tasas Q' frente a Cj(v)*v': 7,96704586907e-13 A, mismo soporte,
u=1/4. Se guardan ambas KCL y su diferencia conservativa. La interpolación
de nodos y cargas por separado puede apartarse de la ley constitutiva;
conservar las restricciones lineales no elimina ese desacuerdo no lineal.

## Regresiones y bytes

**Cinco pruebas**, primer intento, 47,5821524 s; hashes antes/después
idénticos. Cubren los 496 certificados y 1.488 consultas a 80/100,
raíces ocultas con extremos del mismo signo, tangencias y coincidencias,
identidades Bernstein/de Casteljau, 24 soportes reconstruidos mediante
diferencias divididas de Newton independientes, 72 replays racionales de
tasas/ecuaciones y 288 FD locales de la regla de la cadena. Esas FD
no cruzan el knee ni verifican regularidad del soporte completo.

[Datos](../evidence/loudness_latch_bdf_static_precision_dense_charge.json.gz):
10.602.356 bytes; SHA comprimido
`1450cbc168a6d1a7ad215ee2b5f3b54cb42b9db6582fd4603820862a3d3c781c`;
SHA canónico
`a7376de948bf8011235776f1410e85c94eee4e0f9ae0681c1e01497d2fbd9002`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_dense_charge_summary.json)
y [recibo](../evidence/loudness_latch_bdf_static_precision_dense_charge_validation.json)
conservan los gates, fuentes, resultados y alcance.

Siguiente corte: reconstrucción constitutiva por piezas y residual integrado,
con tratamiento explícito del soporte mixto, antes de propagar defecto desde
DC. El criterio de 1 mV, física, audio y deadline permanecen abiertos.
