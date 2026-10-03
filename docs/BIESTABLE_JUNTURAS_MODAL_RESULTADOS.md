# Modos congelados del generador firmado de junturas

## Método fijado y alcance

El [protocolo](BIESTABLE_JUNTURAS_MODAL_PROTOCOLO.md), helper y productor
se congelaron en `a27b982` antes de medir. Las 64 celdas y pesos anteriores
permanecen iguales. Se reconstruye el bloque 4×4 firmado
B=-W_J H_inverse_JJ W_J^-1 a partir de las mismas cubiertas ideales.
Los 16 elementos de cada slice utilizan los 119 términos del producto
Neumann completo, cola por fila e intersecciones previas. No se trunca
el defecto al subbloque ni se resuelve otra inversa del circuito.
La parte simétrica reconstruida coincide exactamente con las 64
matrices intervalares del certificado espectral anterior.

Una potencia de dos positiva rho normaliza B/rho por regla determinista.
Se archivan cinco coeficientes de det(zI-B/rho), sumas firmadas de menores
principales, recintos Delta2/Delta3 y primera columna de Routh. Todo usa
racionales exactos; no se clasifican autovalores flotantes ni sólo el centro.
La [derivación de Routh en Illinois](https://courses.physics.illinois.edu/ece486/fa2026/documentation/handbook/lec07.html)
proporciona la recurrencia utilizada, explicitada para grado cuatro en el protocolo.

## Resultado completo

Ninguna de las 64 consultas queda indeterminada. Los signos estrictos
certifican el mismo conteo para toda matriz de cada recinto, incluyendo
incertidumbre temporal de los coeficientes reconstruidos.

| Ventana | Subpasos | Celdas | Raíces Re(lambda)>0 por matriz congelada | Signos de columna Routh | Signo de mu2 anterior |
| --- | --- | --- | --- | --- | --- |
| prefix | 2 | 8 | 0 | + + + + + | negativo |
| prefix | 4 | 8 | 0 | + + + + + | negativo |
| attack | 2 | 8 | 0 | + + + + + | positivo |
| attack | 4 | 8 | 0 | + + + + + | positivo |
| reset | 2 | 8 | 1 | + + + + - | positivo |
| reset | 4 | 8 | 1 | + + + + - | positivo |
| tail | 2 | 8 | 0 | + + + + + | positivo |
| tail | 4 | 8 | 0 | + + + + + | positivo |

Las **48 celdas de prefijo, ataque y cola** certifican Hurwitz del bloque
interno congelado: todas sus raíces tienen parte real estrictamente negativa.
Las **16 de reset** certifican exactamente una raíz en el semiplano derecho,
con multiplicidad. Su a4 tiene superior negativo: además existe una raíz
**real positiva**, por continuidad del polinomio mónico entre cero e infinito.

Las **32 celdas de ataque y cola** combinan modos congelados estables con
mu2 estrictamente positiva. El bloque es no normal en estas coordenadas:
una matriz normal Hurwitz no tendría esa medida euclídea positiva.
Existe una dirección instantánea de crecimiento de norma; no se demuestra
que el residual o la trayectoria observada exciten esa dirección. El dato
permite investigar amplificación transitoria y una métrica común certificada,
sin atribuir toda la cota enorme a modos inestables.

El reset tiene un modo creciente del bloque aislado, pero esto no prueba
inestabilidad del circuito completo. Los otros 21 estados de memoria y
acoplamientos siguen actuando. Tampoco basta que todas las matrices de
una familia sean Hurwitz para certificar su sistema variable en el tiempo.
Se conserva un contraejemplo manufacturado con dos generadores triangulares
Hurwitz cuyo producto de transiciones tiene un autovalor mayor que uno.

**No cambia ninguna propagación ni cota nodal anterior.** Cola N4 conserva
su término forzado hipotético ~9,92 µV; anclaje común desconocido, restos
no lineales e intervalos no contiguos siguen pendientes. No se obtiene
una cota de error DAE, admisión de 1 mV global, fidelidad vintage ni audio.
Los gates binarios anteriores siguen rechazados y los umbrales no cambian.

## Evidencia y regresiones

[Datos](../evidence/loudness_latch_bdf_static_precision_junction_modal.json.gz):
**1276644 bytes**, SHA comprimido
`48f6ead33032eecfaa2de3c693b1126ff7ccae8ba85dab48ba52b7e1a7daf56b`,
SHA canónico `de3a7d406f51ce8a6cb95ef0594e23d39c0a894c9762d85a966706d56a808d20`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_junction_modal_summary.json).
Cada celda conserva generador firmado, SHA, escala, coeficientes, recintos
Hurwitz, columna y signos, junto con los límites mu2 anteriores.

La [suite](../tests/test_loudness_latch_junction_modal.py) pasa **6/6 al primer intento**,
14.0129066 s. Verifica 0..4 raíces derechas conocidas, pares complejos,
ejemplo cuártico publicado, identidad polinómica por eliminación racional
independiente, divisiones singulares, familia diagonal de 16 vértices,
centro estable con vértice inestable, amplificación no normal y el
contraejemplo de conmutación. Repite los 64 recintos; compara un slice
119×119 real con la construcción Neumann completa y todas las partes
simétricas con las archivadas. Comprueba fuentes, bytes, destinos y alcance.
El [recibo](../evidence/loudness_latch_bdf_static_precision_junction_modal_validation.json)
conserva SHA antes/después idénticos. No hay solves de circuito nuevos.

El [corpus ampliado](BIESTABLE_JUNTURAS_MODAL_ENTRADAS.md) reconstruye
las fuentes y conserva las versiones de tests históricas. Próximo bloque:
métrica cuadrática común sobre ataque/cola con prueba intervalar de su
variación y conversiones; conservar reset, acoplamientos y anclaje explícitos.

```powershell
python tools/loudness_latch_bdf_static_precision_junction_modal.py
python tools/validate_bdf_static_precision_junction_modal.py
```
