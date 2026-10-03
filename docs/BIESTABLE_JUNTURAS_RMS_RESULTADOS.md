# Norma RMS de junturas y cancelaciones firmadas

## Variante y conversiones

El [protocolo](BIESTABLE_JUNTURAS_RMS_PROTOCOLO.md), helper y productor se
fijaron en `9728229` antes de medir. Se mantienen los seis grupos físicos,
los pesos, las coordenadas y las 64 celdas. Sólo el grupo de cuatro junturas
usa RMS ponderada ||WJ*eJ||2/2; los otros mantienen máximo ponderado.
La referencia del anclaje sigue siendo el máximo ponderado común de entrada.
RMS<=infinito permite iniciar sus coeficientes con unos, sin conocer el error.

La parte simétrica de BJ=-WJ*Hinv_JJ*WJ^-1 se suma con signo antes de
acotar. Gershgorin da un recinto superior racional de su mayor autovalor,
la medida logarítmica euclídea. Las conversiones de acoplamientos, integral
de forzamiento y salida nodal cambian junto con la norma. Sus raíces usan
isqrt y recintos diádicos de 256 bits; se conserva cero exacto. No se usa
sqrt de coma flotante dentro de la prueba ni se intersectan normas diferentes.

Se reconstruyen las mismas 64 inversas ideales y se reutilizan los núcleos
positivos de extremo/pico. El dominio de norma escalada <=4096 pasa en
todas las celdas, sin clipping ni refinamiento de ventanas. No hay solves
nuevos, cambios del motor, de parámetros físicos ni de gates.

## Resultado mixto, sin selección retrospectiva

La tabla conserva todos los casos. Presenta el término forzado con
**anclaje cero hipotético** y el coeficiente del anclaje ponderado común.
Son cotas del tangente ideal variable, no errores observados del DAE.

| Ventana | Subpasos | Máximo ponderado anterior (V) | Junturas RMS (V) | Coeficiente de anclaje, pico nodal |
| --- | --- | --- | --- | --- |
| prefix | 2 | 0.0595069218 | 52742699.7 | 8.38837975E+14 |
| prefix | 4 | 0.0000337170217 | 0.572593052 | 63844221.3 |
| attack | 2 | 6.26714339E+251 | 8.32609801E+120 | 1.12633588E+129 |
| attack | 4 | 1.03982664E+121 | 3.61955262E+55 | 7.11450951E+64 |
| reset | 2 | 0.00000367506766 | 0.00000367506766 | 198.104053 |
| reset | 4 | 4.86537697E-7 | 4.86537697E-7 | 197.892775 |
| tail | 2 | 3.00335182E+16 | 1644.02471 | 3.56878112E+11 |
| tail | 4 | 4828.01837 | 0.00131060101 | 1854893.98 |

Ataque y cola mejoran; prefijo empeora y reset queda prácticamente igual.
En cola N4 la cota forzada pasa de ~4828 V a **~1,31 mV**. Ese valor no
cierra 1 mV ni permite una afirmación global: el anclaje permanece desconocido,
la cubierta es no contigua y faltan los restos no lineales. En ataque N2
baja de ~6,267e251 a ~8,326e120 V, todavía enorme.

Prefijo N4 empeora de ~33,72 µV a ~0,573 V. La mayor diagonal superior
Gershgorin de junturas pasa de mu_infinito ~5,935e7/s a mu2 ~1,678e8/s;
son medidas de normas distintas, no ganancias físicas. Cambiar norma no
asegura una mejora y los acoplamientos y conversiones también cambian.
No se escoge una norma distinta por ventana ni se reemplaza el informe anterior.
La variante conserva el resultado desfavorable como parte de la evidencia.

## Evidencia y regresiones

[Datos](../evidence/loudness_latch_bdf_static_precision_junction_rms.json.gz):
**8171613 bytes**, SHA comprimido
`9ee4fbc453e9038345e6583c2cf880843d4ef6498c3d0e69a175a54ef20ab355`,
SHA canónico `1c9748a41bf4bf6df076a85604040caf7fb5a91c033d06abb063d93f1b5db25b`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_junction_rms_summary.json).
Cada celda archiva la parte simétrica 4×4, ambas diagonales, normalización,
conversiones completas, E/P y propagación; soportes, pesos y datos previos
quedan identificados por SHA.

La [suite](../tests/test_loudness_latch_junction_rms.py) pasa **5/5 al primer intento**
en 178.1989263 s. Contrasta raíces con desigualdades racionales exactas y
testigos Decimal300, un generador antisimétrico y su incertidumbre intervalar,
conversiones en ambas direcciones, forzamiento por columnas disjuntas,
referencia común de anclaje y forzamiento tardío. El ejemplo conserva mu2=-1
frente a mu_infinito=7, mientras su ganancia nodal empeora de 7 a 10:
refuta deducir mejora de salida sólo de la diagonal. Reconstruye todas las
**64 inversas, partes simétricas, métricas y propagaciones** y verifica
fuentes, destinos, bytes canónicos y alcance. El [recibo](../evidence/loudness_latch_bdf_static_precision_junction_rms_validation.json)
conserva SHA antes/después idénticos.

El [corpus ampliado](BIESTABLE_JUNTURAS_RMS_ENTRADAS.md) conserva fuentes,
recibos y versiones anteriores. **1 mV global, física, audio y deadline
siguen abiertos.** Próximo corte: distinguir pérdida por Gershgorin de
crecimiento de la parte simétrica, mediante una cota espectral racional
verificada y declarada antes de medir, conservando la misma norma RMS.

```powershell
python tools/loudness_latch_bdf_static_precision_junction_rms.py
python tools/validate_bdf_static_precision_junction_rms.py
```
