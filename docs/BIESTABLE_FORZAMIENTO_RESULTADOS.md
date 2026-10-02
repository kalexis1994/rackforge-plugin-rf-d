# Forzamiento relativo a ventanas refinadas

La [variante de reloj](BIESTABLE_FORZAMIENTO_RELOJ_PROTOCOLO.md), el
[planificador](../tools/loudness_latch_bdf_clock_plan.py) y el
[productor](../tools/loudness_latch_bdf_static_precision_forced_clock.py)
quedaron fijados en **`17d01cc`**, antes de medir, el 2 de octubre de 2026.
Se conserva el [intento inicial](BIESTABLE_FORZAMIENTO_INTENTO_INICIAL.md).

## Referencias y propagación

Las ocho continuaciones completan **1.536 intervalos finos**: cuatro
ventanas de 64 intervalos base con dos y cuatro subpasos. Historiales
propios, destinos base idénticos, fuente y parámetros originales;
ningún reset, fallback o cambio de raíz. Máximo KCL **9,71960e-12 A**,
menor que 10 pA. La máxima diferencia registrada de intervalo frente a
h/N es **6,64746e-19 s**. Todos conservan mínimo 1 ps y razón <=2.

Se completan **512 pasos forzados**, **1.024 solves espaciales** de primera
y segunda variación. Ambos errores hacia atrás pasan en todos: máximo
**9,45822e-11**, frente a 1e-10. Forzamiento de ecuaciones r y desajuste
de publicación z se calculan por diferencias no lineales independientes
del Jacobiano. No se obtienen como J multiplicado por el error observado.

Pasivos y publicación RC serie conservan los coeficientes binary64
levantados; cargas usan Q analítico. La referencia muestreada no se trata
como una trayectoria gruesa aceptada. El forzamiento depende de esa
referencia fina ya calculada, así que sigue siendo diagnóstico a posteriori.

| Contraste | Resultado |
| --- | --- |
| Forzamiento Decimal80/100 | 512/512 pasan, r y z |
| Curvatura Decimal80/100 | 512/512 pasan, residual y publicación |
| Predicción lineal nodal / memoria | 512/512 pasos pasan cada gate |
| Predicción cuadrática nodal / memoria | 512/512 pasos pasan cada gate |
| Auditoría racional | 24 lotes / 48 columnas; residuo exacto cero y mapa pasa |

El gate por componente sigue siendo **10 nV + 1e-3*abs(predicción)**.
El máximo error nodal lineal es **1,72094e-13 V**; cuadrático,
**1,65474e-15 V**. Máximo error de memoria lineal **8,23567e-14 V** de
coordenada; cuadrático **2,17687e-19 V**. La máxima diferencia nodal
referencia menos base es **0,866358 uV**, memoria **2,07667 uV** de
coordenada. La escala Q/(1 pF) no se identifica como capacitancia física.

| Ventana | Máxima diferencia nodal 4 menos 2 subpasos |
| --- | --- |
| Prefijo | 0,0394014 uV |
| Ataque | 0,0275363 uV |
| Reset | 0,0692334 uV |
| Cola | 0,175234 uV |

Estas diferencias son sobre cuatro ventanas cortas desde memoria común;
comparten el error del anclaje. No cierran el gate global desde DC, ni
constituyen una cota de la solución exacta entre muestras.

## Preparación y alcance de precisión

La extracción r/z prepara high+low dentro de Decimal80/100. En el
productor congelado, los nodos pasados al helper de curvatura se preparan
en el contexto ambiental **Decimal28**, antes de evaluar a 80/100.
Ambos contrastes de H condicionan esa misma entrada preparada. La suite
audita también otra preparación Decimal80 en los **24 puntos racionales**;
todos pasan los mismos gates de curvatura. Eso no audita esa preparación
alternativa en los otros 488 puntos ni elimina la limitación del productor.

La extracción del forzamiento usa leyes compartidas y un mapa levantado;
no es una evaluación idéntica en bits al kernel binary64 original. Un
pase de propagación forzada verifica el modelo de diferencias recibido;
no entrega un estimador independiente que funcione sin referencia fina,
el defecto temporal exacto del DAE, un resto global de Taylor, parámetros
vintage, audio o deadline. El gate temporal de **1 mV desde DC** sigue abierto.

## Evidencia y reproducción

[Datos](../evidence/loudness_latch_bdf_static_precision_forced_clock.json.gz):
17.029.756 bytes; SHA comprimido
`875808f508cf856dc32bad0d69ec990b11e688bb2d229ff4060b5a0d05d28c0b`;
SHA canónico
`cfee675e1f8b251712b6814b7bb5b516a0f92843c50ce2ae9fb8fda32d7d5ee5`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_forced_clock_summary.json)
identifica **155 entradas**, calendarios, todas las métricas y auditorías.

El [recibo](../evidence/loudness_latch_bdf_static_precision_forced_clock_validation.json)
registra **5/5 pruebas**, primer intento, **49,2626755 s**, hashes
antes/después idénticos. La
[suite](../tests/test_loudness_latch_bdf_static_precision_forced_clock.py)
verifica todos los intervalos, publicaciones, forzamientos y recurrencias;
24 replays no lineales, cuatro replays racionales con ambos RHS, testigos
de calendario y signos. El testigo escalar usa derivada de Lagrange con
fracciones exactas; no calibra el DAE del circuito.

```powershell
python tools/loudness_latch_bdf_static_precision_forced_clock.py
python tools/validate_bdf_static_precision_forced_clock.py
```

El siguiente trabajo requiere distinguir defecto temporal y forzamiento
relativo: derivar el error de diferenciación de cargas sobre los historiales
reales y comprobarlo en problemas con solución conocida antes de usarlo
para modificar un controlador o certificar el recorrido desde DC.
