# Primer intervalo no lineal certificado por comparación dirigida

## Fuentes y alcance

Modelo nominal documental CA3046, mismos parámetros sintéticos, estados
high+low, residual y recintos medios del [primer tubo](BIESTABLE_PRIMER_TUBO_RESULTADOS.md).
[Protocolo](BIESTABLE_TUBO_BLOQUES_PROTOCOLO.md),
[helper](../tools/loudness_latch_startup_blocks.py) y
[productor](../tools/loudness_latch_bdf_static_precision_startup_blocks.py)
se congelan en `28784e4`. Datos, ocho pruebas y validator se fijan en
`fa2e4c8` antes de validar. No se resuelve nuevamente el circuito ni se
calcula un precondicionador: las 24 inversas exteriores se reconstruyen
desde la fórmula anterior, con certificado y SHA de su matriz completa.

## Banco fijado antes de medir

Tres radios (0,1; 1; 10 µV) por tres normas. Se conservan todos los modos;
selección por primer par radio/modo aceptado. Partición física: audio
0..16; C10 17; C2 18; C4 19; C7 20; cuatro junturas 21..24.

Infinito conserva la comparación dirigida de seis grupos. RMS conserva
la parte simétrica firmada de las junturas. El modo cuadrático deriva un
único P por radio de la envolvente de los ocho generadores medios: solve
racional 10x10, trace(P)=4, nearest-even a 40 bits y LDL exacta. Las tres
métricas son PD y permanecen constantes en **todo el intervalo**.
Se ejecutan **2.376 consultas LDL** para cotas isotrópicas, dirigidas por
congruencia y balanceadas, con intersecciones sólo en la misma métrica.

Los errores iniciales de cada carga provienen del anclaje DC convertido
y del desajuste constitutivo. Cada grupo propaga su propia cota, sin
asignar el máximo global a todas las direcciones. Para la forma cuadrática
se usa una caja simétrica que incluye esos intervalos; puede sobreestimar
correlaciones. Se pagan normas duales P^-1, normalización, acoplamientos,
forcing L1 y salida nodal. No se mezclan ganancias de normas diferentes.

## Resultado completo

| Radio | Infinito por grupos: presupuesto nodal | RMS: presupuesto nodal | Cuadrático balanceado: presupuesto nodal | Cierre |
| --- | --- | --- | --- | --- |
| 0,1 µV | 1,266831 mV | 4,163957e5 V | 0,262576 µV | Todos rechazan |
| 1 µV | 5,110048 mV | 9,038993e5 V | **0,585674 µV** | Sólo cuadrático acepta |
| 10 µV | 4,451001e93 V | 3,812607e92 V | 5,202613e282 V | Todos rechazan |

Los presupuestos de variantes rechazadas son comparaciones condicionales,
no cotas del error real. El banco selecciona **[radio 1 µV, modo cuadrático]**,
con todas las ocho celdas e inversas verificadas y presupuesto estricto
**0,585674474 µV < 1 µV**. Incluye la cota inicial nodal del evento.

Esta inclusión cierra la hipótesis de tubo y, con la raíz inicial, dominio
válido y descriptor medio invertible, prueba continuación y error nodal
para **t=0+ hasta 195,3125 ns**. Es el primer intervalo continuo realmente
certificado de esta trayectoria nominal; no agrega cobertura de ventanas
históricas distintas ni extrapola hasta los 512 endpoints publicados.
La cobertura global de 3 ms y el gate global de 1 mV siguen abiertos.

La diagonal logarítmica de junturas del modo elegido queda por debajo de
**-2,0087e7 /s** en las ocho celdas. Es disipación interna en esa métrica;
los otros grupos, acoplamientos y forcing todavía deben propagarse.
RMS empeora a pesar de conservar cancelaciones: el banco mantiene ese
rechazo, sin concluir estabilidad o inestabilidad física del instrumento.

Los picos de anclaje y forcing se suman por nodo antes de maximizar;
sus máximos separados pueden corresponder a nodos diferentes. En el
modo elegido son 0,483530 µV y 0,252011 µV respectivamente, pero el
máximo conjunto es ≈0,585674 µV, celda 7, índice nodal 21.
La propagación conserva matrices exteriores de endpoint y de pico,
inyección L1 tardía y términos nodales directos.

## Memoria final disponible para continuar

| Grupo | Cota final en su norma /V |
| --- | --- |
| Audio | 2,935805e-9 |
| C10 | 1,479763e-10 |
| C2 | 7,397621e-11 |
| C4 | 1,484283e-10 |
| C7 | 1,935141e-9 |
| Junturas, forma cuadrática normalizada | 1,998124e-10 |

Estas seis cotas, redondeadas hacia arriba, resultan de anclaje más forcing. La norma de junturas
no es infinito por coordenada: antes de otro intervalo se necesita una
conversión exterior a su nueva norma, o conservar la misma P. No reiniciar
con la caja DC ni propagar un error a través de un hueco sin prueba.

## Validación y evidencia

Las **ocho regresiones primarias pasan al primer intento en 90,6609469 s**:
reconstrucción de 24 inversas; todas las métricas, tasas y conversiones;
16 vértices de cajas iniciales; reproducción de kernels y cierres; sistema
no lineal conocido; anclaje anisótropo; forcing tardío; rotación
antisimétrica y guardas de partición/dominio. Los hashes antes/después son
idénticos. [Recibo](../evidence/loudness_latch_bdf_static_precision_startup_blocks_validation.json).

[Datos](../evidence/loudness_latch_bdf_static_precision_startup_blocks.json.gz):
**14472662 bytes**, SHA comprimido
`cd65d1e93207cde24622d5110cf0cf105f4d3370ce6b22e265acb385c07cc9ee`,
canónico `81e5234eb7ec972b0ffe3bdec5b59bf8a67d01da2cdfc65f7d4549a8d656950f`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_startup_blocks_summary.json).
[Corpus](BIESTABLE_TUBO_BLOQUES_ENTRADAS.md): 472 entradas de 82 informes,
con trece versiones fallidas históricas. Las dos pruebas del corpus pasan
al primer intento en 74,2571515 s; diez regresiones nuevas aceptadas en total.

El cierre es numérico, local y del modelo sintético congelado. No identifica
componentes vintage ni semejanza audible, y no admite motor nativo o
deadline. Siguiente bloque: [continuación contigua con memoria certificada](BIESTABLE_CONTINUACION_CERTIFICADA_PLAN.md).
