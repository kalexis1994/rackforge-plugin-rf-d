# Pesos y descriptor ideal a lo largo del intervalo

## Variante y certificado

El [protocolo](BIESTABLE_DESCRIPTOR_PONDERADO_PROTOCOLO.md) fija una norma
max_i |w_i*y_i| antes de medir. Las 21 memorias lineales usan w=1; las
cuatro junturas usan la potencia de dos inferior a S/C del punto medio
archivado. Los pesos son constantes en cada intervalo, no ajustados a
respuestas ni al resultado de la medida logarítmica. No son tolerancias
físicas vintage. C10 mantiene su resistencia serie y las cargas su escala.

Se conserva índice 31, cuatro ventanas y subdivisiones 2/4. Para cada uno
de los **ocho intervalos**, se cubre u=[0,1] con **ocho celdas**.
Las exponenciales, capacitancias, 1/R, beta, C/S y R*C se encierran como
operaciones ideales sobre los parámetros binary64 congelados. Los sellos
analíticos de rango uno se precondicionan antes de acotar sus coeficientes.
C de juntura es monótona continua incluso al atravesar el knee vigente.

**64/64 celdas** tienen q<1 para E(u)=I-D*X*H_ideal(u)*D^-1.
Las ocho inversas ideales quedan encerradas en todo el intervalo seleccionado;
no son sólo las matrices binary64 del punto medio. La prueba incluye la
variación y la diferencia entre coeficientes ideales y redondeados del centro.
No se ejecutan nuevos solves lineales ni no lineales. Las inversas binary64
anteriores conservan su gate rechazado; la prueba es una consulta matemática.

| Ventana | Subpasos | Máximo q de las ocho celdas |
| --- | --- | --- |
| prefix | 2 | 0,00808082794 |
| prefix | 4 | 0,00404779702 |
| attack | 2 | 0,0493816314 |
| attack | 4 | 0,0243442831 |
| reset | 2 | 0,00207796950 |
| reset | 4 | 0,00103917335 |
| tail | 2 | 0,0275133680 |
| tail | 4 | 0,0137594964 |

## Cotas ponderadas y comparación completa

Se usa muW=max_i(Bii+sum(j!=i) wi/wj*|Bij|), máximos de columnas de
W*Fr y W*Fd para la norma integrada del forzamiento, y ||L*W^-1||inf
para convertir memoria a voltaje. El anclaje desconocido mantiene su
coeficiente; se archiva además conversión desde norma sin pesos.
No comparar coeficientes de anclaje de normas distintas sin esa conversión.

Con los recintos uniformes de la inversa ideal se deriva también una cota
para la **ODE tangente con coeficientes variables** a lo largo de cada
interpolante conocido. N_I/N_Q están excluidos de ese forzamiento: todavía
no se cierra el error del DAE no lineal. La tabla sólo presenta términos
forzados con **anclaje cero hipotético**. Son cotas, no voltajes observados.

| Ventana | Subpasos | Congelado sin pesos anterior (V) | Congelado ponderado (V) | Tangente ideal variable ponderado (V) |
| --- | --- | --- | --- | --- |
| prefix | 2 | 4,20817707e40 | 7,580483e2 | 2,856756e8 |
| prefix | 4 | 1,07799256e18 | 5,141389e-2 | 1,023585 |
| attack | 2 | 1,00698840e124 | 1,890289e254 | 3,778218e314 |
| attack | 4 | 1,66011325e58 | 8,369050e122 | 1,557455e140 |
| reset | 2 | 7,02523097e-6 | 5,879416e-6 | 6,520070e-6 |
| reset | 4 | 8,29181004e-7 | 5,581575e-7 | 5,625847e-7 |
| tail | 2 | 1,88662152e308 | 9,264730e18 | 4,356400e43 |
| tail | 4 | 1,35151447e152 | 1,451432e6 | 6,699231e13 |

La escala física local mejora el diagnóstico congelado de prefijo/cola y
el término forzado de reset, pero **empeora ataque**. Se mantienen todos
los casos. El exponente de ataque N2 pasa de 296,052 sin pesos a 597,491
congelado ponderado y 728,927 con recinto temporal ideal. La cota no demuestra
amplificación observada, inestabilidad real ni parecido al Moog.

La cota variable añade incertidumbre de coeficientes, por eso no se espera
que mejore la congelada. El Neumann escalar máximo produce recintos muy
conservadores por entrada. Tampoco se convierte el término ~0,563 µV de
reset N4 en un gate global: el anclaje, restos y recorrido completo faltan.

## Evidencia y regresiones

[Datos](../evidence/loudness_latch_bdf_static_precision_weighted_descriptor.json.gz):
**17.175.067 bytes**, SHA comprimido
`a0c2e0104e4542c5c2ca0c86e68efe8b441ce60c43bbeea4971f44ff613815c8`,
SHA canónico `b4a0407b225a42618454222fa7421f31e1cad4821a9f0c29439950b0630af0dc`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_weighted_descriptor_summary.json).
Cada celda conserva sus recintos de E por entrada, sumas de fila, q y
rangos de cada coeficiente. Cada caso conserva pesos, presupuesto anterior,
forzamiento y coeficientes del anclaje de ambas variantes nuevas.

La [suite](../tests/test_loudness_latch_weighted_descriptor.py) pasa **7/7**
en el segundo intento, 93,8683372 s. Cubren pesos/domino, similitud y
máximos de columna, el término W'W^-1 para pesos variables, un descriptor
ideal RC/diodo manufacturado, bloqueo q>=1, **24 consultas Decimal120**,
64 recintos y cuatro replays completos, presupuestos, fuente y almacenamiento.
El primer test exigió pertenencia exacta de un testigo Decimal120 a un
recinto estructuralmente cero: su producto redondeado dejó ~2,5e-128.
Se corrige sólo la comparación numérica con presupuesto separado
`1e-100*(1+max|H120|)`, propagado por la fila de X y D. Es una tolerancia
del testigo; no un certificado de Decimal, ni parte de la prueba racional,
ni un cambio de gates del circuito. La fuente fallida se archiva en el
[recibo](../evidence/loudness_latch_bdf_static_precision_weighted_descriptor_validation.json).
Los productores y datos quedan intactos durante ambas validaciones.

Antes de la primera medición hubo dos errores de sintaxis: literal de
salto de línea del productor y cierre de tupla del helper. Ambos intentos
conservan fuente exacta, SHA, stderr, comando y revisión Git; ninguna
medición numérica comenzó. Se compilaron ambas fuentes corregidas antes
de congelar la variante efectiva `1652351`. El [corpus](BIESTABLE_DESCRIPTOR_PONDERADO_ENTRADAS.md)
verifica también esas fuentes históricas desde sus blobs originales.

## Próximo corte

Contrastar estabilidad con recintos que conserven más estructura del operador,
para evitar que la norma instantánea y el Neumann escalar dominen las cotas.
Fijar esa variante antes de medir. Después, controlar restos no lineales,
error inicial y cobertura desde DC. Los ocho intervalos seleccionados no
son contiguos. **1 mV global**, física, voz completa, audio y deadline siguen
abiertos. Este bloque no modifica el sonido ni el integrador de RF-D.
