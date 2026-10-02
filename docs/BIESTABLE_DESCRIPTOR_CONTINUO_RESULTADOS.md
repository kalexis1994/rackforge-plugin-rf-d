# Descriptor continuo y forzamiento con memoria

## Derivación y alcance

El [protocolo continuo](BIESTABLE_DESCRIPTOR_CONTINUO_PROTOCOLO.md) separa
94 voltajes y 25 tasas de memoria. El sistema H tiene dimensión **119**;
usa el Jacobiano estático, incidencias de carga, dQ/dV y R*C de C10.
Las incidencias tienen rango racional **25/25** en las ocho consultas.
Esto no establece índice ni invertibilidad global del DAE.

Se conservan las cuatro ventanas, subdivisiones 2/4, índice 31 y u=1/2.
Las junturas usan Q(vpol) en el diagnóstico continuo; las 21 ramas lineales
conservan sus cargas y restricciones. Los recintos correlacionados aportan
L1 nodal en C; las restricciones aportan L1 en V*s. No se alteran estados
publicados, circuito, sonido o integrador.

Para error exacto menos reconstrucción:
`H [e_v; e_y'] = [-r-N_I; -e_y-d+N_Q/S]`.
Los signos, la resistencia de 25,5 kΩ y la escala de 1 pF de junturas
se verifican explícitamente. N_I/N_Q requieren todavía recintos no lineales.
Una inversa BDF dependiente del paso no sustituye este sistema continuo.

## Dos rutas fallidas y una prueba independiente

La ruta equilibrada falla **8/8** inversas: ambos backward errors rondan 1.
Su [informe](../evidence/loudness_latch_bdf_static_precision_continuous_descriptor.json.gz)
queda intacto. La [ruta racional declarada](BIESTABLE_DESCRIPTOR_EXACTO_PROTOCOLO.md)
resuelve las mismas ocho matrices y verifica H*X=I exactamente, con
**6.549 ceros exactos** por inversa. Tras redondear, Decimal80 backward
queda entre 9,30e-17 y 1,04e-16; el cálculo binary64 conserva un error
0,000100130169 en todas. El gate de 1e-10 sigue fallido **8/8**.
Su [informe exacto](../evidence/loudness_latch_bdf_static_precision_continuous_descriptor_exact.json.gz)
conserva todos los resultados. Cero solves nuevos de trayectorias; ocho
sistemas lineales racionales exactos, exclusivamente fuera del motor.

El testigo peor está en **fila 34, columna 55**, con seis productos no nulos.
En prefijo N2, el denominador binary64 es aproximadamente 4,934e-320 y
el residual -4,94e-324, en régimen subnormal. La evaluación racional de
los mismos productos da ratio **1,03153749e-17**. Un residual subnormal
redondeado no puede representar ese error relativo; no se relaja el gate.

La [consulta Neumann independiente](BIESTABLE_DESCRIPTOR_CERTIFICADO_PROTOCOLO.md)
prueba **8/8** inversas de las matrices binary64 levantadas, con
q entre **4,117e-14 y 3,572e-13**, usando I-D*X*H*D^-1 racional exacto.
El peor backward usa I-H*X: no son la misma evaluación. Los recintos de
inversa están certificados, mientras el mapa binary64 conserva su rechazo.
Decimal80/100 redondean H igual en las ocho consultas; esto no encierra
los coeficientes ideales ni su variación temporal.

## Corrección matemática preservada

La primera consulta certificó correctamente las inversas, pero usó
`max_i integral |f_i|` como cota de `integral max_i |f_i|`.
Las **ocho cotas uniformes originales de memoria/voltaje son inválidas**.
El [informe original](../evidence/loudness_latch_bdf_static_precision_descriptor_certificate.json.gz)
se conserva como intento fallido para ese alcance. Permanecen válidos sus
certificados de inversa, medida logarítmica, presupuestos por fila y
forzamiento puntual. Su suite aprobada no detectó el error matemático.

El [protocolo corregido](BIESTABLE_FORZAMIENTO_NORMA_PROTOCOLO.md) usa
`sum_j max_i |Fr_ij| L1(r_j) + sum_j max_i |Fd_ij| L1(d_j)`.
Dos señales en mitades disjuntas dan integral 1 por fila y norma integrada 2;
la regresión racional exige la cota 2. No se modifica H, X, fuentes,
parámetros, exponentes ni gates. El presupuesto agregado supera al antiguo
máximo de filas por factores **1,0000155 a 1,3106346**.

## Cotas válidas únicamente para operadores congelados

La medida logarítmica infinito y Gronwall acotan cada ODE lineal de
coeficientes congelados. Se conserva el coeficiente de un anclaje desconocido;
la tabla sólo muestra el término forzado de voltaje con **anclaje cero de
esa ODE hipotética**. No es un error del circuito, una observación de sus
trayectorias o una cota global de RF-D. El exponente usa max(mu,0)*duración.

| Ventana | Subpasos | Exponente superior | Término forzado de voltaje congelado (V) |
| --- | --- | --- | --- |
| prefix | 2 | 99,8969573 | 4,20817707e40 |
| prefix | 4 | 49,9482988 | 1,07799256e18 |
| attack | 2 | 296,0521843 | 1,00698840e124 |
| attack | 4 | 148,0248021 | 1,66011325e58 |
| reset | 2 | 0,402755575 | 7,02523097e-6 |
| reset | 4 | 0,201380581 | 8,29181004e-7 |
| tail | 2 | 714,7339666 | 1,88662152e308 |
| tail | 4 | 357,2752375 | 1,35151447e152 |

Reset N2/N4 tiene coeficientes de anclaje **1,49594120 / 1,22309017**.
El anclaje real no se conoce. Las cotas enormes del resto de ventanas
muestran que esta norma sin pesos es insuficiente para un presupuesto útil;
no prueban crecimiento observado ni inestabilidad física.

[Datos corregidos](../evidence/loudness_latch_bdf_static_precision_descriptor_forcing_norm.json.gz):
**1.313.301 bytes**, SHA comprimido
`704e355a8cd52a11bc199bef3e4b20c29330aa701812bf477870e36535a1485f`,
SHA canónico `bad03961664b0b08f59f16d653ea6b7d97e643bd0d518c870a6ec7172aa93586`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_descriptor_forcing_norm_summary.json).

## Regresiones y siguiente bloque

La [suite de descriptor](../tests/test_loudness_latch_continuous_descriptor.py)
pasa **6/6** en el segundo intento: el primero comparó un producto Decimal
con contexto por defecto de 28 cifras contra 100 cifras. Se corrigió sólo
la comparación usando Fraction; fuentes del test fallido y SHA están en
el [recibo](../evidence/loudness_latch_bdf_static_precision_descriptor_certificate_validation.json).
La [suite de norma integrada](../tests/test_loudness_latch_descriptor_forcing_norm.py)
pasa **3/3** al primer intento, incluyendo el contraejemplo disjunto,
RC racional y replay de los ocho presupuestos.
[Recibo corregido](../evidence/loudness_latch_bdf_static_precision_descriptor_forcing_norm_validation.json).
Ambas suites conservan entradas antes/después idénticas. El
[corpus](BIESTABLE_DESCRIPTOR_CONTINUO_ENTRADAS.md) identifica todas las rutas.

Siguiente bloque: fijar coordenadas/pesos antes de medir, contrastar la
medida logarítmica, encerrar la matriz ideal y su variación temporal,
controlar restos no lineales y error inicial y cubrir el recorrido completo.
Los intervalos seleccionados no son contiguos. El criterio global de **1 mV**,
física, voz completa, audio y deadline siguen abiertos.
